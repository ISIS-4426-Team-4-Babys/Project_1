from openai import AzureOpenAI
from rabbitmq import RabbitMQ
import logging
import os
import json
import asyncio
import anyio


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

client = AzureOpenAI(
    api_key = os.getenv("NANO_KEY"),
    api_version = "2024-12-01-preview",
    azure_endpoint = "https://uniandes-dev-ia-resource.openai.azure.com/"
)

rabbitmq = RabbitMQ()

async def load_text(path: str) -> str:
    async with await anyio.open_file(path, "r", encoding="utf-8") as f:
        return await f.read()


def make_callback(prompt: str):
    async def callback(message):
        try:
            decoded_message = message.body.decode().strip()
            logging.info(f"Message received with content = {decoded_message}")
            
            payload = json.loads(decoded_message)
            filepath = payload.get("filepath")

            prompt_path = "/app/" + filepath
            prompt_text = ""

            async with await anyio.open_file(prompt_path, "r", encoding = "utf-8") as f:
                prompt_text = await f.read()

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

            async with await anyio.open_file(prompt_path, "w", encoding = "utf-8") as f:
                await f.write(output)
        
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    
    return callback

async def main():
    prompt = await load_text("prompt.txt")
    
    await rabbitmq.consume("prompt", make_callback(prompt))


if __name__ == "__main__":
    asyncio.run(main())