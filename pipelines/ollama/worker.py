from subprocess import Popen, PIPE
from rabbitmq import RabbitMQ
import logging
import requests
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
OLLAMA_URL ="http://localhost:11434"


while True:
    try:
        if requests.get(f"{OLLAMA_URL}/v1/models").status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        pass
    logging.info("Esperando a que Ollama esté listo...")
    time.sleep(1)

logging.info("Ollama listo")
rabbitmq = RabbitMQ()


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
        "stream": False
    })

    logging.info("yikes")

    output = response.json().get("response", "")

    logging.info(output)

    rabbitmq.publish("vect", "Done")

rabbitmq.consume("format", handle_request)

