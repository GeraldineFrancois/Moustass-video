FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Installer les dépendances système
RUN set -eux; \
    CODENAME=$(grep VERSION_CODENAME /etc/os-release | cut -d= -f2 || echo stable); \
    printf '%s\n' "deb https://deb.debian.org/debian ${CODENAME} main" "deb https://deb.debian.org/debian ${CODENAME}-updates main" "deb https://deb.debian.org/debian-security ${CODENAME}-security main" > /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    gcc \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer le dossier uploads
RUN mkdir -p /app/uploads

# Exposer le port interne
EXPOSE 8000

# Santé check basique sur l'API vidéo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/videos/health/status || exit 1

# Lancer le service FastAPI
CMD ["uvicorn", "src.videos.upload_service:app", "--host", "0.0.0.0", "--port", "8000"]
