FROM python:3.11-alpine

WORKDIR /app

ENV PYTHONPATH=/app

# Outils systèmes requis pour le healthcheck (curl)
RUN apk add --no-cache curl

# Créer un utilisateur non-root pour la sécurité
RUN addgroup -S -g 1000 appuser && adduser -S -u 1000 -G appuser appuser

# Copier les requirements
COPY requirements.txt .

# Mettre à jour pip et installer les dépendances
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copier tout le code avec permissions correctes
COPY . .
RUN chown -R appuser:appuser /app

# Basculer vers l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Lancer le service
CMD ["uvicorn", "src.auth.auth_api:app", "--host", "0.0.0.0", "--port", "8000"]
