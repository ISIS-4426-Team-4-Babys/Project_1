from markitdown import MarkItDown
from rabbitmq import RabbitMQ
import json
import logging
import os
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
md_converter = MarkItDown(enable_plugins = True) # Set to True to enable plugins
rabbitmq = RabbitMQ()

async def callback(message):
    try:
        decoded_message = message.body.decode().strip()
        logging.info(f"Message received with content = {decoded_message}")

        payload = json.loads(decoded_message)
        filepath = payload.get("filepath")
        total_docs = payload.get("total_docs")

        if not filepath or not total_docs:
            logging.error("Invalid message: 'filepath' or 'total_docs' missing")
            return

        logging.info(f"Filepath received: {filepath}")
        logging.info(f"Number of documents received: {total_docs}")
        
        # Convertir el contenido a Markdown
        result = md_converter.convert(filepath)
        markdown_text = result.text_content

        # Extraer la ruta original del archivo
        original_path = filepath  
        base_dir = os.path.dirname(original_path)  
        filename = os.path.basename(original_path)  
        name_without_ext = os.path.splitext(filename)[0]  

        # Crear la carpeta 'markitdown' dentro del mismo directorio si no existe
        markdown_dir = os.path.join(base_dir, "markitdown")
        os.makedirs(markdown_dir, exist_ok=True)

        # Guardar el archivo .md
        markdown_path = os.path.join(markdown_dir, f"{name_without_ext}.md")
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        logging.info(f"Markdown file saved at {markdown_path}")

        message = {
            "filepath": markdown_path,
            "total_docs": total_docs
        }
        
        await rabbitmq.publish("format", json.dumps(message))

        logging.info(f"Markdown send with {markdown_path}")
    
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        

async def main():
    await rabbitmq.consume("files", callback)

if __name__ == "__main__":
    asyncio.run(main())

