# Multi-stage Dockerfile pour l'application Flask optimisé pour la production
# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Installer les mises à jour de sécurité et outils de build minimaux
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances avec optimisations de sécurité et performance
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user --no-warn-script-location \
    --disable-pip-version-check --no-compile -r requirements.txt && \
    find /root/.local -name "*.pyc" -delete && \
    find /root/.local -name "__pycache__" -type d -exec rm -rf {} + || true

# Stage 2: Production stage - Distroless-like approach
FROM python:3.11-slim AS production

# Installer uniquement les packages de sécurité critiques et nettoyer agressivement
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /var/cache/apt/* \
    && find /usr/share -type f -name "*.md" -delete \
    && find /usr/share -type f -name "*.txt" -delete \
    && rm -rf /usr/share/doc /usr/share/man /usr/share/info

# Créer un utilisateur non-root avec UID/GID spécifiques pour la sécurité
RUN groupadd -r -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -d /home/appuser -s /sbin/nologin \
    -c "Application user" appuser && \
    mkdir -p /home/appuser /app/tmp /app/var/run && \
    chown -R appuser:appuser /home/appuser /app

# Définir le répertoire de travail
WORKDIR /app

# Copier les dépendances installées depuis le stage builder
COPY --from=builder /root/.local /home/appuser/.local

# Copier le code de l'application
COPY app/ ./app/

# Changer la propriété des fichiers vers l'utilisateur non-root
RUN chown -R appuser:appuser /app

# Changer vers l'utilisateur non-root
USER appuser

# Ajouter le répertoire local de l'utilisateur au PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Exposer les ports pour l'application et les métriques
EXPOSE 5000 8080

# Définir les variables d'environnement avec sécurité renforcée
ENV FLASK_APP=app.main:create_app
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV FLASK_ENV=production
ENV GUNICORN_WORKERS=2
ENV GUNICORN_TIMEOUT=60
ENV GUNICORN_KEEPALIVE=5
ENV GUNICORN_MAX_REQUESTS=1000

# Labels pour la traçabilité et la sécurité avec build info
LABEL maintainer="DevOps Team" \
      version="1.0.0" \
      description="Secure Python Flask Application with Monitoring" \
      security.scan="enabled" \
      org.opencontainers.image.source="https://github.com/your-org/python-cicd-pipeline" \
      org.opencontainers.image.documentation="https://github.com/your-org/python-cicd-pipeline/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT"

# Commande de santé pour Docker avec timeout optimisé
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=3)" || exit 1

# Créer un script d'entrée pour une configuration flexible
COPY --chown=appuser:appuser <<EOF /app/entrypoint.sh
#!/bin/sh
set -e

# Configuration dynamique des workers basée sur les ressources disponibles
if [ -z "\$GUNICORN_WORKERS" ]; then
    WORKERS=\$(python -c "import multiprocessing; print(min(4, max(2, multiprocessing.cpu_count())))")
else
    WORKERS=\$GUNICORN_WORKERS
fi

# Lancer Gunicorn avec configuration optimisée pour la production
exec gunicorn \
    --bind 0.0.0.0:5000 \
    --workers \$WORKERS \
    --worker-class sync \
    --worker-connections 1000 \
    --timeout \${GUNICORN_TIMEOUT:-60} \
    --keepalive \${GUNICORN_KEEPALIVE:-5} \
    --max-requests \${GUNICORN_MAX_REQUESTS:-1000} \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --capture-output \
    --enable-stdio-inheritance \
    --chdir /app/app \
    "main:create_app()"
EOF

RUN chmod +x /app/entrypoint.sh

# Commande par défaut utilisant le script d'entrée
CMD ["/app/entrypoint.sh"]