# Imagen base ligera de Python
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    curl git unzip build-essential \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install matplotlib

# Copiar el código de la app
COPY . .

# Ejecutar el script principal
CMD ["python", "LLM.py"]
