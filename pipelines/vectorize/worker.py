from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from rabbitmq import RabbitMQ
from pathlib import Path
import logging
import os
import json


# Configuración de logging
logging.basicConfig(level = logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()

headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3"), ("####", "H4")]
splitter = MarkdownHeaderTextSplitter(headers_to_split_on = headers_to_split_on, strip_headers = False)
embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")

BASE_DB_DIR = "databases"


def process_and_store(db_id: str, file_path: str):

    logging.info(f"Processing file: {file_path} into DB {db_id}")

    if not os.path.exists(file_path):
        logging.error(f"The file {file_path} does not exist")
        return None

    with open(file_path, "r", encoding = "utf-8") as f:
        markdown_text = f.read()

    filename = os.path.basename(file_path)

    doc = Document(page_content = markdown_text, metadata = {"source_file": filename})
    chunks = splitter.split_text(doc.page_content)

    logging.info(f"{len(chunks)} chunks generated from file {filename}")

    db_path = Path(BASE_DB_DIR) / db_id
    os.makedirs(db_path, exist_ok = True)

    if not any(db_path.iterdir()):
        db = Chroma.from_documents(
            documents = chunks,
            embedding = embeddings,
            persist_directory = str(db_path)
        )
        logging.info(f"Vector database created at {db_path}")
    else:
        db = Chroma(
            embedding_function = embeddings,
            persist_directory = str(db_path)
        )
        db.add_documents(chunks)
        logging.info(f"Chunks added to existing vector database at {db_path}")

    # db.persist()
    logging.info(f"Persistence completed at {db_path}")

    return str(db_path)


def callback(ch, method, properties, body):
    try:
        decoded_message = body.decode().strip()
        logging.info(f"Message received: {decoded_message}")

        payload = json.loads(decoded_message)
        db_id = payload.get("db_id")
        file_path = payload.get("file_path")
        total_docs = payload.get("total_docs")

        if not db_id or not file_path or not total_docs:
            logging.error("Invalid message: 'db_id' or 'file_path' or 'total_docs' missing")
            return

        logging.info(f"Database ID received: {db_id}")
        logging.info(f"Filepath received: {file_path}")
        logging.info(f"Total docs received: {total_docs}")

        db_path = process_and_store(db_id, file_path)

        if db_path:

            message = {
                "agent_id": db_id, 
                "total_docs": total_docs
            } 

            rabbitmq.publish("control", json.dumps(message))
            logging.info(f"Published message to control topic")

    except json.JSONDecodeError:
        logging.error("Failed to decode JSON message")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


rabbitmq.consume("vectorize", callback)