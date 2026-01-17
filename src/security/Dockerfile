# Security Microservice

FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    openssl-dev \
    curl \
    git

# Install Snyk CLI
RUN curl -Lo /usr/local/bin/snyk https://static.snyk.io/cli/latest/snyk-linux && \
    chmod +x /usr/local/bin/snyk

# Créer un utilisateur non-root pour la sécurité
RUN addgroup -S -g 1000 appuser && adduser -S -u 1000 -G appuser appuser

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code avec permissions correctes
COPY src/ /app/src/
RUN chown -R appuser:appuser /app

# Basculer vers l'utilisateur non-root
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run service
CMD ["python", "-m", "src.security.security_service"]
