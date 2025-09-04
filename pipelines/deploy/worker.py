from rabbitmq import RabbitMQ   
import logging
import subprocess
import json


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
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

    subprocess.run([
        "docker", 
        "run", 
        "-d", 
        "--name", container_name, 
        "-v", f"{host_path}:{container_path}", 
        image_name
    ], check = True)

rabbitmq.consume("deploy", callback)