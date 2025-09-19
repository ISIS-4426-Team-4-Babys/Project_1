from openai import AzureOpenAI
from rabbitmq import RabbitMQ
import logging
import os
import json
import asyncio


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


async def callback(message):
    try:
        decoded_message = message.body.decode().strip()
        logging.info(f"Message received with content = {decoded_message}")
        
        payload = json.loads(decoded_message)
        filepath = payload.get("filepath")
        total_docs = payload.get("total_docs")

        markdown_path = "/app/" + filepath
        markdown_text = ""

        with open(markdown_path, "r", encoding = "utf-8") as f:
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
        
        message = {
            "db_id": markdown_path.split("/")[4], 
            "file_path": markdown_path,
            "total_docs": total_docs
        }

        await rabbitmq.publish("vectorize", json.dumps(message))
        
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        

async def main():
    await rabbitmq.consume("format", callback)


if __name__ == "__main__":
    asyncio.run(main())

