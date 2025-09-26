from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers import ContextualCompressionRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticToolsParser
from langchain_core.prompts import ChatPromptTemplate
from fastapi import FastAPI, HTTPException
from langchain_chroma import Chroma
from pydantic import BaseModel, Field
import logging
import sys
import os

class ParaphrasedQuery(BaseModel):
    """Has realizado una expansión de la consulta para generar una paráfrasis de una pregunta."""

    paraphrased_query: str = Field(
        description="Una paráfrasis única de la pregunta original.",
    )

logging.basicConfig(level = logging.INFO,  format = "%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

embeddings = HuggingFaceEmbeddings(
    model_name = "sentence-transformers/all-mpnet-base-v2",
    model_kwargs = {"device": "cpu"},
    encode_kwargs = {"normalize_embeddings": True}
)

hf_cross_encoder = HuggingFaceCrossEncoder(model_name = "BAAI/bge-reranker-v2-m3")
reranker = CrossEncoderReranker(model = hf_cross_encoder, top_n = 10)


PROMPT = os.getenv("PROMPT", "")
DB_PATH = "/app/database/"

SYSTEM_REWRITE = """Eres un asistente útil que genera subconsultas a partir de una sola pregunta del usuario.
Descompón la pregunta original en partes más pequeñas y específicas, de modo que cada subconsulta capture un aspecto clave de la intención del usuario.
Si existen varias formas comunes de formular cada parte o sinónimos relevantes, incluye dichas variantes en las subconsultas.
Si hay siglas o palabras que no conoces, no intentes reformularlas."""

PROMPT_REWRITE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_REWRITE),
        ("human", "{question}"),
    ]
)

app = FastAPI()

prompt = ChatPromptTemplate.from_template(PROMPT)

llm = ChatGoogleGenerativeAI(
        model = "gemini-2.5-flash",
        temperature = 0.5,
    )

llm_with_tools = llm.bind_tools([ParaphrasedQuery])
query_analizer = PROMPT_REWRITE | llm_with_tools | PydanticToolsParser(tools = [ParaphrasedQuery])


def load_vector_store():
    if not os.path.exists(DB_PATH):
        logger.warning(f"No se encontró la base de datos en {DB_PATH}")
        return None
    return Chroma( 
        collection_name = "rag_docs",
        persist_directory = DB_PATH,
        embedding_function = embeddings
    )

vector_store = load_vector_store()
compression_retriever = None

def create_compression_retriever(vector_store, reranker, k = 15, search_type = "similarity"):
    logger.info("Creando retriever base con search_type='%s' y k=%d", search_type, k)

    retriever = vector_store.as_retriever(
        search_type=search_type,
        search_kwargs={"k": k}
    )

    logger.info("Creando ContextualCompressionRetriever con reranker %s", reranker.__class__.__name__)

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=retriever
    )

    return compression_retriever


if vector_store:
    compression_retriever = create_compression_retriever(vector_store, reranker)
    logger.info("DB encontrada: servidor FastAPI listo para recibir requests")
else:
    logger.warning("No hay DB: el servidor no se iniciará")
    # Aquí hacemos que el contenedor termine automáticamente
    sys.exit(0)


def ask_rag(question: str, prompt, llm, compression_retriever):
    logger.info("=== Nueva pregunta RAG ===")
    logger.info("Pregunta: %s", question)

    queries = query_analizer.invoke({"question":question})

    contexts = []
    for query in queries:
        logger.info("Pregunta: %s", query)
        contexts = contexts + compression_retriever.invoke(query.paraphrased_query)
    
    contexts = contexts + compression_retriever.invoke(question)

    seen = set()
    unique_contexts = []
    for doc in contexts:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            unique_contexts.append(doc)

    contexts = unique_contexts

    logger.info("Documentos unicos recuperados: %d", len(contexts))

    for i, doc in enumerate(contexts, start=1):
        score = doc.metadata.get("relevance_score", "N/A")
        snippet = doc.page_content[:200].replace("\n", " ")
        logger.info("Doc #%d (score=%s, source=%s): %s...", 
                    i, score, doc.metadata.get("source_file", "unknown"), snippet)

    for i, doc in enumerate(contexts, start=1):
        snippet = doc.page_content[:200].replace("\n", " ")
        logger.debug("Doc #%d (source=%s): %s...", 
                     i, doc.metadata.get("source_file", "unknown"), snippet)

    # Construir contexto
    docs_content = "\n\n".join(doc.page_content for doc in contexts)

    messages = prompt.invoke({
        "question": question,
        "context": docs_content
    })
    response = llm.invoke(messages)

    logger.info("Respuesta generada con longitud %d caracteres", len(response.content))

    return {
        "question": question,
        "answer": response.content,
        "sources": [doc.metadata.get("source_file", "unknown") for doc in contexts]
    }


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    if compression_retriever is None:
        raise HTTPException(
            status_code = 500,
            detail = "No hay base de datos cargada, el retriever no está inicializado"
        )
    try:
        result = ask_rag(req.question, prompt, llm, compression_retriever)
        return result
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))


@app.get("/")
def root():
    return {"message": "Agente RAG con Chroma corriendo 🚀"}
