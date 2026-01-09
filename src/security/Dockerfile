# Security Microservice

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN set -eux; \
    CODENAME=$(grep VERSION_CODENAME /etc/os-release | cut -d= -f2 || echo stable); \
    printf '%s\n' "deb https://deb.debian.org/debian ${CODENAME} main" "deb https://deb.debian.org/debian ${CODENAME}-updates main" "deb https://deb.debian.org/debian-security ${CODENAME}-security main" > /etc/apt/sources.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    gcc \
    g++ \
    libssl-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Snyk CLI
RUN curl -Lo /usr/local/bin/snyk https://static.snyk.io/cli/latest/snyk-linux && \
    chmod +x /usr/local/bin/snyk

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY src/ /app/src/

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Run service
CMD ["python", "-m", "src.security.security_service"]
