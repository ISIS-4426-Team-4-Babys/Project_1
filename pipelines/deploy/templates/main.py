from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, HTTPException
from langchain_chroma import Chroma
from pydantic import BaseModel
import os
import logging

logging.basicConfig(
    level=logging.INFO,  # Muestra info, warning, error
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

PROMPT = os.getenv("PROMPT")
DB_PATH = "/app/database/"

app = FastAPI()

prompt = ChatPromptTemplate.from_template(PROMPT)

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature = 0.5,
)

embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")

def load_vector_store():
    if not os.path.exists(DB_PATH):
        raise RuntimeError(f"No se encontró la base de datos en {DB_PATH}")
    return Chroma( 
        persist_directory = DB_PATH,
        embedding_function = embeddings
    )

vector_store = load_vector_store()

def ask_rag(question: str, vector_store, k = 10):
    retrieved_docs = vector_store.similarity_search(question, k = k)

    logger.info("#total documentos %d", len(retrieved_docs))
    
    # for i, doc in enumerate(retrieved_docs, start=1):
    #    logger.info(f"Documento {i}: {doc.page_content[:500]}...")  # muestra los primeros 500 caracteres
    #    logger.info(f"Metadata {i}: {doc.metadata}")

    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    messages = prompt.invoke({
        "question": question,
        "context": docs_content
    })
    response = llm.invoke(messages)
    return {
        "question": question,
        "answer": response.content,
        # "sources": [doc.metadata.get('source_file', 'unknown') for doc in retrieved_docs]
    }

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
def ask(req: AskRequest):
    try:
        result = ask_rag(req.question, vector_store)
        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))

@app.get("/")
def root():
    return {"message": "Agente RAG con Chroma corriendo 🚀"}
