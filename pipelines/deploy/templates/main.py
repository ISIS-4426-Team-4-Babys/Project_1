from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, HTTPException
from langchain_chroma import Chroma
from pydantic import BaseModel
import os

DB_PATH = "/app/database/"
PROMPT_TEMPLATE = os.getenv("PROMPT_TEMPLATE")

app = FastAPI()

# Prompt personalizado
prompt = ChatPromptTemplate.from_template("""
Eres un asistente especializado en responder preguntas sobre documentación administrativa de un curso.
Utiliza únicamente la información del contexto proporcionado para responder la pregunta.
Si no conoces la respuesta basándote en el contexto, indica claramente que no tienes esa información.
Mantén las respuestas concisas, precisas y usa máximo tres oraciones.

Pregunta: {question}

Contexto: {context}

Respuesta:
""")

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature = 0.1,
    max_tokens = 200
)

embeddings = GoogleGenerativeAIEmbeddings(model = "models/gemini-embedding-001")

def load_vector_store():
    if not os.path.exists(DB_PATH):
        raise RuntimeError(f"No se encontró la base de datos en {DB_PATH}")
    return Chroma( 
        persist_directory = DB_PATH,
        embedding_function = embeddings
    )

vector_store = load_vector_store()

def ask_rag(question: str, vector_store, k = 3):
    retrieved_docs = vector_store.similarity_search(question, k = k)
    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
    messages = prompt.invoke({
        "question": question,
        "context": docs_content
    })
    response = llm.invoke(messages)
    return {
        "question": question,
        "answer": response.content,
        "sources": [doc.metadata.get('source_file', 'unknown') for doc in retrieved_docs]
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
