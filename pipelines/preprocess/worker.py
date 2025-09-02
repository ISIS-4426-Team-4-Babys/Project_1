from markitdown import MarkItDown
from rabbitmq import RabbitMQ
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
md_converter = MarkItDown(enable_plugins = True) # Set to True to enable plugins
rabbitmq = RabbitMQ()

def callback(ch, method, properties, body):
    logging.info(f"Message received with content = {body}")
    decoded_message = body.decode().strip()
    
    # Convertir el contenido a Markdown
    result = md_converter.convert(decoded_message)
    markdown_text = result.text_content

    # Extraer la ruta original del archivo
    original_path = decoded_message  
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

    rabbitmq.publish("format", markdown_path)

    logging.info(f"Markdown send with {markdown_path}")

rabbitmq.consume("files", callback)
