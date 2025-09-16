from rabbitmq import RabbitMQ   
import logging
import subprocess
import json
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BASE_PATH = os.getenv("BASE_PATH")

rabbitmq = RabbitMQ()


def callback(ch, method, properties, body):
    try:
        decoded_message = body.decode().strip()
        logging.info(f"Message received with content = {body}")

        payload = json.loads(decoded_message)
        agent_id = payload.get("agent_id")

        image_name = "agent-base"
        container_name = f"agent_{agent_id}"
        
        host_path = BASE_PATH + agent_id
        container_path = "/app/database"

        host_port = int(agent_id[-4:], 16) % 10000 + 20000  
        container_port = 8000

        prompt_path = f"/app/prompts/{agent_id}/prompt.txt" 
        PROMPT = ""
        with open(prompt_path, "r") as f:
            PROMPT += f.read()

        subprocess.run([
            "docker", 
            "run", 
            "-d", 
            "--name", container_name, 
            "--network", "project_1_default",
            "-e", f"AGENT_ID={agent_id}", 
            "-e", f"GOOGLE_API_KEY={GOOGLE_API_KEY}", 
            "-e", f"PROMPT={PROMPT}",
            "-e", f"VIRTUAL_HOST={container_name}",
            "-e", f"VIRTUAL_PORT={container_port}",
            "-p", f"{host_port}:{container_port}", 
            "-v", f"{host_path}:{container_path}", 
            image_name
        ], check = True)

        ch.basic_ack(method.delivery_tag)
        logging.info(f"Agent deployed in http://localhost:{host_port} with ID {agent_id}")

    except Exception as e:
        logging.error(f"Error processing message: {e}")
        ch.basic_nack(method.delivery_tag, requeue = True)

rabbitmq.consume("deploy", callback)