# Usa Ubuntu como base
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Instala dependencias básicas
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instala Ollama usando el script oficial
RUN curl -fsSL https://ollama.com/install.sh | sh

# Asegúrate de que el binario esté en PATH
ENV PATH="/root/.ollama/bin:${PATH}"

# Copiar el código y el entrypoint
COPY . /opt/ollama/
WORKDIR /opt/ollama

# Dar permisos de ejecución al entrypoint
RUN chmod +x /opt/ollama/entrypoint.sh

# Exponer puerto del servidor web de Ollama
EXPOSE 11434

# Ejecutar entrypoint al iniciar el contenedor
ENTRYPOINT ["/opt/ollama/entrypoint.sh"]
