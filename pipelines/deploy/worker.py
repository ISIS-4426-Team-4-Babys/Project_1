from rabbitmq import RabbitMQ   
import logging
import subprocess
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
rabbitmq = RabbitMQ()

def callback(ch, method, properties, body):
    decoded_message = body.decode().strip()
    logging.info(f"Message received with content = {body}")

    payload = json.loads(decoded_message)
    event = payload.get("event")
    agent_id = payload.get("agent_id")

    image_name = "agent-base"
    container_name = f"agent_{agent_id}"
    

    host_path = f"/home/nico/Desktop/Project_1/pipelines/vectorize/databases/{agent_id}"
    container_path = "/app/database"

    host_port = int(agent_id[-4:], 16) % 10000 + 20000  
    container_port = 8000

    subprocess.run([
        "docker", 
        "run", 
        "-d", 
        "--name", container_name, 
        "-e", f"AGENT_ID={agent_id}", 
        "-e", f"GOOGLE_API_KEY={GOOGLE_API_KEY}",         
        "-p", f"{host_port}:{container_port}", 
        "-v", f"{host_path}:{container_path}", 
        image_name
    ], check = True)

    logging.info(f"Agente desplegado en http://localhost:{host_port} con ID {agent_id}")

rabbitmq.consume("deploy", callback)