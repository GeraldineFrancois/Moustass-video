FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
