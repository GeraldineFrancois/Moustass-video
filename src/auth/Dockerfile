FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

# Outils systèmes requis pour le healthcheck (curl)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code
COPY . .

# Exposer le port
EXPOSE 8000

# Lancer le service
CMD ["uvicorn", "src.auth.auth_api:app", "--host", "0.0.0.0", "--port", "8000"]
