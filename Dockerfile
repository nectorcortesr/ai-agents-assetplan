# Imagen base ligera de Python
FROM python:3.12-slim

# Variables de entorno para rendimiento
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema para Playwright y scraping
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libgtk-3-0 libasound2 libxss1 \
    libx11-xcb1 libxext6 libxfixes3 libxrender1 libxcb1 libx11-6 \
    fonts-liberation build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -ms /bin/bash appuser

# Instalar uv y Playwright
RUN pip install --no-cache-dir uv playwright

# Directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración
COPY pyproject.toml .
COPY uv.lock .

# Instalar dependencias Python (incluyendo Playwright)
RUN uv pip install --system -r pyproject.toml

# Instalar dependencias de navegador (root)
RUN playwright install-deps

# Copiar código de la aplicación
COPY . .

# Ajustar permisos y cambiar a usuario no-root
RUN chown -R appuser:appuser /app
USER appuser

# Crear directorio de datos
RUN mkdir -p /app/data

# Instalar navegadores Playwright (appuser)
RUN playwright install

# Exponer puerto de la API
EXPOSE 8000

# Comando por defecto para iniciar la API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]