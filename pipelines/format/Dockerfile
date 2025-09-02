# Imagen base ligera de Python
FROM python:3.13-slim

# Definir directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .

# Instalar dependencias (y paquetes útiles para compilación si alguno lo necesita)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la app
COPY . .

# Comando por defecto para correr el consumidor
CMD ["python", "worker.py"]