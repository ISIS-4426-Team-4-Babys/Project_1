from openai import AzureOpenAI
from rabbitmq import RabbitMQ
import logging
import os
import json


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

client = AzureOpenAI(
    api_key = os.getenv("NANO_KEY"),
    api_version = "2024-12-01-preview",
    azure_endpoint = "https://uniandes-dev-ia-resource.openai.azure.com/"
)

rabbitmq = RabbitMQ()

prompt = ""
with open("prompt.txt", "r", encoding = "utf-8") as f:
    prompt = f.read()


def callback(ch, method, properties, body):
    try:
        decoded_message = body.decode().strip()
        logging.info(f"Message received with content = {body}")
        
        payload = json.loads(decoded_message)
        filepath = payload.get("filepath")

        prompt_path = "/app/" + filepath
        prompt_text = ""

        with open(prompt_path, "r", encoding = "utf-8") as f:
            prompt_text = f.read()

        response = client.chat.completions.create(
            model = "gpt-5-nano-iau-ingenieria",
            messages = [
                {
                    "role" : "system",
                    "content" : prompt
                },
                {
                    "role" : "user",
                    "content" : prompt_text
                }
            ]
        )

        output = response.choices[0].message.content
        logging.info("Prompt improvement completed succesfully")

        with open(prompt_path, "w", encoding = "utf-8") as f:
            f.write(output)
        
        ch.basic_ack(method.delivery_tag)
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        ch.basic_nack(method.delivery_tag, requeue = True)

rabbitmq.consume("prompt", callback)