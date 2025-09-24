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


def make_callback(prompt_text: str):
    async def callback(message):
        try:
            decoded_message = message.body.decode().strip()
            logging.info(f"Message received with content = {decoded_message}")

            payload = json.loads(decoded_message)
            filepath = payload.get("filepath")
            total_docs = payload.get("total_docs")

            markdown_path = "/app/" + filepath

            # Leer el markdown de forma asíncrona
            async with await anyio.open_file(markdown_path, "r", encoding="utf-8") as f:
                markdown_text = await f.read()

            # Llamada al modelo (cliente síncrono de AzureOpenAI está bien aquí)
            response = client.chat.completions.create(
                model="gpt-5-nano-iau-ingenieria",
                messages=[
                    {"role": "system", "content": prompt_text},
                    {"role": "user", "content": markdown_text},
                ],
            )

            output = response.choices[0].message.content
            logging.info("Format completed succesfully")

            # Escribir el resultado de forma asíncrona
            async with await anyio.open_file(markdown_path, "w", encoding="utf-8") as f:
                await f.write(output)

            message_out = {
                "db_id": markdown_path.split("/")[4],
                "file_path": markdown_path,
                "total_docs": total_docs,
            }

            await rabbitmq.publish("vectorize", json.dumps(message_out))

        except Exception as e:
            logging.error(f"Error processing message: {e}")

    return callback
        

async def main():
    
    prompt_text = await load_text("prompt.txt")

    await rabbitmq.consume("format", make_callback(prompt_text))


if __name__ == "__main__":
    asyncio.run(main())

