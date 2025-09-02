#!/bin/sh
set -e

# Iniciar Ollama en background
ollama serve &

# Esperar hasta que el modelo llama3 esté disponible
echo "Esperando a que llama3 esté listo..."
while true; do
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"llama3:latest"')
    if [ ! -z "$MODELS" ]; then
        break
    fi
    sleep 1
done

echo "Modelo llama3 listo, arrancando worker..."
python3 worker.py
