from openai import AzureOpenAI
from rabbitmq import RabbitMQ
import logging
import os
import json
import asyncio
import anyio
from typing import List
import tempfile
import uuid


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

async def atomic_write_text(final_path: str, content: str) -> None:
    dirpath = os.path.dirname(final_path) or "."
    tmp_path = os.path.join(dirpath, f".tmp_{uuid.uuid4().hex}")

    try:
        async with await anyio.open_file(tmp_path, "w", encoding="utf-8") as f:
            await f.write(content)

        os.replace(tmp_path, final_path)

    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            
async def chunk_markdown_lines(path: str, target_chars: int = 7000, overlap_chars: int = 500) -> List[str]:
    chunks: List[str] = []
    buf: List[str] = []
    buf_len = 0

    async with await anyio.open_file(path, "r", encoding="utf-8") as f:
        async for line in f:
            buf.append(line)
            buf_len += len(line)
            if buf_len >= target_chars:
                chunk = "".join(buf)
                chunks.append(chunk)

                if overlap_chars > 0 and len(chunk) > overlap_chars:
                    tail = chunk[-overlap_chars:]
                    buf = [tail]
                    buf_len = len(tail)
                else:
                    buf, buf_len = [], 0

    if buf_len > 0:
        chunks.append("".join(buf))

    return chunks

SAFE_WRAPPER = (
    "Sigue las políticas de seguridad. Si el fragmento incluye contenido sensible o no apto, "
    "omite esos detalles y limita la salida a un Markdown limpio solo con lo permitido."
)

async def format_chunk(system_prompt: str, chunk_text: str, idx: int, total: int) -> str:
    user_prompt = (
        f"Fragmento {idx+1}/{total}\n"
        "Convierte únicamente este fragmento a Markdown claro en español. No agregues información nueva. "
        "No des explicaciones fuera del propio contenido. " + SAFE_WRAPPER + "\n"
        "-----\n" + chunk_text
    )

    def _sync():
        return client.chat.completions.create(
            model="gpt-5-nano-iau-ingenieria",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    try:
        resp = await anyio.to_thread.run_sync(_sync)
        return resp.choices[0].message.content or ""
    except Exception as e:
        logging.error(f"Chunk {idx+1}/{total} falló: {e}")
        return chunk_text  

async def format_large_markdown(markdown_path: str, system_prompt: str) -> str:
    chunks = await chunk_markdown_lines(markdown_path)
    total = len(chunks)
    logging.info(f"Processing {total} chunks sequentally...")

    results = []
    for i, ch in enumerate(chunks):
        formatted = await format_chunk(system_prompt, ch, i, total)
        results.append(formatted)

    return "\n".join(results)


def make_callback(system_prompt: str):
    async def callback(message):
        try:
            decoded_message = message.body.decode().strip()
            logging.info(f"Message received: {decoded_message}")

            payload = json.loads(decoded_message)
            filepath = payload.get("filepath")
            total_docs = payload.get("total_docs")

            markdown_path = "/app/" + filepath

            formatted_all = await format_large_markdown(markdown_path, system_prompt)
            if formatted_all:
                await atomic_write_text(markdown_path, formatted_all)
                logging.info("Formateo completado correctamente.")
            else:
                logging.info("No hubo nada que escribir.")

            message_out = {
                "db_id": markdown_path.split("/")[4],
                "file_path": markdown_path,
                "total_docs": total_docs,
            }
            await rabbitmq.publish("vectorize", json.dumps(message_out))

        except Exception as e:
            logging.error(f"Error procesando mensaje: {e}")

    return callback
        

async def main():
    
    prompt_text = await load_text("prompt.txt")

    await rabbitmq.consume("format", make_callback(prompt_text))


if __name__ == "__main__":
    asyncio.run(main())

