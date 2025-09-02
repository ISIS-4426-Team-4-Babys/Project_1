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
    logging.info(f"Message received with content = {body}")
    markdown_path = "/app/" + body.decode().strip()
    markdown_text = ""

    with open(markdown_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    response = client.chat.completions.create(
        model = "gpt-5-nano-iau-ingenieria",
        messages = [
            {
                "role" : "system",
                "content" : prompt
            },
            {
                "role" : "user",
                "content" : markdown_text
            }
        ]
    )

    output = response.choices[0].message.content
    logging.info("Format completed succesfully")

    with open(markdown_path, "w", encoding = "utf-8") as f:
        f.write(output)
    
    # TODO
    message = {
        "db_id": markdown_path.split("/")[4], 
        "file_path": markdown_path
    }

    rabbitmq.publish("vectorize", json.dumps(message))

rabbitmq.consume("format", callback)

