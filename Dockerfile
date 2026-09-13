# ============================================================
#  Aletheia Core — Dockerfile
#  Multi-stage build for the AI inference engine
# ============================================================

# --------------- Stage 1: Builder ---------------
FROM python:3.12-slim AS builder

WORKDIR /tmp/build

# Instalar dependencias de compilación necesarias para wheels nativos
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compilar todos los wheels en un directorio temporal
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# --------------- Stage 2: Runtime ---------------
FROM python:3.12-slim AS runtime

LABEL maintainer="Shirokague Devs <shirokague@dev.io>"
LABEL description="Aletheia Core — Motor de Inferencia Soberano"
LABEL version="1.0.0"

# Variables de entorno por defecto
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    TZ=America/Bogota

# Dependencias de runtime (audio, video, PDF, fuentes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libportaudio2 \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    ca-certificates \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes Python instalados desde el builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copiar código fuente del proyecto
COPY . .

# Crear directorios necesarios que podrían no existir
RUN mkdir -p /app/logs /app/chroma_db

# Puerto de la API Gateway (FastAPI / System Bridge)
EXPOSE 8000

# Healthcheck contra el endpoint de FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint: levantar la aplicación principal
CMD ["python", "main.py"]
