from subprocess import Popen, PIPE
from rabbitmq import RabbitMQ
import requests
import logging
import time
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
OLLAMA_URL = "http://ollama:11434"

rabbitmq = RabbitMQ()

logging.info("Verificando modelo llama3...")
r = requests.post(f"{OLLAMA_URL}/api/pull", json={"model": "deepseek-r1:latest"}, stream=True)

# Leer la respuesta en streaming (Ollama devuelve progreso)
for line in r.iter_lines():
    if line:
        logging.info(line.decode("utf-8"))

logging.info("Modelo llama3 disponible")

def handle_request(ch, method, properties, body):
    logging.info(f"Message received with content = {body}")
    markdown_path = "/app/" + body.decode().strip()
    markdown_text = ""

    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    prompt = "Convierte el contenido a un documento markdown estructurado, infiriendo los lugares" \
             "mas probables para poner títulos, subtítulos y otros elementos de formato. NO agregues " \
             "información adicional a la dada por el contexto, tampoco elimines información dada, simplemente formatea y devuelve un texto" \
             "que soporte una estrategia de segmentación por estructura de documento: " + markdown_text
    
    response = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": "deepseek-r1:latest",
        "prompt": prompt,
        "stream": True
    })
    
    with open(markdown_path.replace(".md","_new.md"), "w", encoding="utf-8") as f:
        for line in response.iter_lines(decode_unicode="utf-8"):
            if line:
                obj = json.loads(line)
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                logging.debug(f"Línea no-JSON: {line!r}")
                continue

            chunk = obj.get("response")
            if chunk:
                logging.info("Procesando línea: %r", chunk)
                f.write(chunk)
                f.flush()

            # Cuando Ollama avisa que terminó, cortamos
            if obj.get("done"):
                break


    logging.info("Generación completada.")

    rabbitmq.publish("vect", "Done")

rabbitmq.consume("format", handle_request)

