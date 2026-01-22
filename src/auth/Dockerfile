FROM python:3.11-slim
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libssl-dev libffi-dev curl git \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements (we'll keep a project-wide requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and ui
COPY src/ /app/src/
COPY ui/ /app/ui/
RUN chmod -R a+rX /app

EXPOSE 8001

CMD ["uvicorn", "src.auth.auth_api:app", "--host", "0.0.0.0", "--port", "8001"]
