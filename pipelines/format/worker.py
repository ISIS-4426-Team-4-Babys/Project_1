from subprocess import Popen, PIPE
from rabbitmq import RabbitMQ
import logging
import requests
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
OLLAMA_URL = "http://ollama:11434"

rabbitmq = RabbitMQ()

logging.info("Verificando modelo llama3...")
r = requests.post(f"{OLLAMA_URL}/api/pull", json={"model": "llama3"}, stream=True)

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
             "información asicional a la dada por el contexto, simplemente formatea y devuelve un texto" \
             "que soporte una estrategia de segmentación por estructura de documento: " + markdown_text
    
    response = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": "llama3",
        "prompt": prompt,
        "stream": True
    })

    logging.info("yikes")

    output = response.json().get("response", "")

    logging.info(output)

    rabbitmq.publish("vect", "Done")

rabbitmq.consume("format", handle_request)

