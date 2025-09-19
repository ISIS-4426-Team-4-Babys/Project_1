from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from rabbitmq import RabbitMQ
from pathlib import Path
import logging
import os
import json
import asyncio


logging.basicConfig(level = logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
rabbitmq = RabbitMQ()

headers_to_split_on = [("#", "H1"), ("##", "H2"), ("###", "H3"), ("####", "H4")]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on = headers_to_split_on, strip_headers = False)

recursive_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 700,       
		chunk_overlap = 150,     
		separators = [           
			"\n\n",    
			"\n",      
			". ",      
			", ",      
			" ",       
			""         
		]
)

embeddings = HuggingFaceEmbeddings(
    model_name = "sentence-transformers/all-mpnet-base-v2",
    model_kwargs = {"device": "cpu"},
    encode_kwargs = {"normalize_embeddings": True}
)

BASE_DB_DIR = "databases"


def chunk_file(file_path: str):
    
    logging.info(f"Processing file: {file_path}")

    if not os.path.exists(file_path):
        logging.error(f"The file {file_path} does not exist")
        return None

    with open(file_path, "r", encoding = "utf-8") as f:
        content = f.read()
    
    filename = os.path.basename(file_path)

    structured_chunks = markdown_splitter.split_text(content)
    logging.info(f"{len(structured_chunks)} structured chunks generated from file {filename}")

    final_chunks = []
    for chunk in structured_chunks:
        docs = recursive_splitter.split_text(chunk.page_content)
        for doc in docs:
            final_chunks.append(
                Document(page_content = doc)
            )

    for i, chunk in enumerate(final_chunks):
        chunk.metadata.update({
            "source_file": filename,
            "source_path": file_path,
            "chunk_index": i,
            "total_chunks_in_doc": len(final_chunks),
            "chunking_strategy": "hybrid",
            "chunk_size": len(chunk.page_content)
        })
    
    return final_chunks


def load_to_chromadb(db_id: str, chunks, collection_name = "rag_docs"):

    db_path =  Path(BASE_DB_DIR) / db_id
    os.makedirs(db_path, exist_ok = True)

    if not any(db_path.iterdir()):
        vector_store = Chroma.from_documents(
            collection_name = collection_name,
            documents = chunks, 
            embedding = embeddings,
            persist_directory = str(db_path)
        )
        logging.info(f"Vector database created at {db_path}")
    else:
        db = Chroma(
            collection_name = collection_name,
            embedding_function = embeddings,
            persist_directory = str(db_path)
        )
        db.add_documents(chunks)
        logging.info(f"Chunks added to existing vector database at {db_path}")

    logging.info(f"Persistence completed at {db_path}")
    return str(db_path)


async def callback(message):
    try:
        decoded_message = message.body.decode().strip()
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

        chunks = chunk_file(file_path)
        db_path = load_to_chromadb(db_id, chunks)

        if db_path:

            message = {
                "agent_id": db_id, 
                "total_docs": total_docs
            } 

            await rabbitmq.publish("control", json.dumps(message))
            logging.info(f"Published message to control topic")

    except json.JSONDecodeError:
        logging.error("Failed to decode JSON message")
    except Exception as e:
        logging.error(f"Error processing message: {e}")


async def main():
    await rabbitmq.consume("vectorize", callback)


if __name__ == "__main__":
    asyncio.run(main())