FROM python:3.11-alpine

WORKDIR /app

ENV PYTHONPATH=/app

# Installer les dépendances système
RUN apk add --no-cache \
    gcc \
    musl-dev \
    mariadb-dev \
    curl

# Créer un utilisateur non-root pour la sécurité
RUN addgroup -S -g 1000 appuser && adduser -S -u 1000 -G appuser appuser

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code avec permissions correctes
COPY . .
RUN chown -R appuser:appuser /app

# Créer le dossier uploads avec permissions correctes
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port interne
EXPOSE 8000

# Santé check basique sur l'API vidéo
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/videos/health/status || exit 1

# Lancer le service FastAPI
CMD ["uvicorn", "src.videos.upload_service:app", "--host", "0.0.0.0", "--port", "8000"]
