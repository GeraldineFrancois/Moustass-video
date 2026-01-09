FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Outils systèmes requis pour le healthcheck (curl)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code avec permissions correctes
COPY . .
RUN chown -R appuser:appuser /app

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Lancer le service
CMD ["uvicorn", "src.auth.auth_api:app", "--host", "0.0.0.0", "--port", "8000"]
