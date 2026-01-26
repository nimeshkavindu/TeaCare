from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pypdf import PdfReader
import chromadb
from chromadb.api.types import Documents, Embeddings, EmbeddingFunction
from fastembed import TextEmbedding
import os

from app.core.database import get_db
from app.models.sql_models import DiseaseInfo, SystemLog
from app.services.ai_service import ai_manager

router = APIRouter()

# --- HELPER: SYSTEM LOGGING ---
def log_event(db: Session, level: str, source: str, message: str):
    try:
        new_log = SystemLog(level=level, source=source, message=message)
        db.add(new_log)
        db.commit()
    except Exception as e:
        print(f"Logging failed: {e}")

# --- VECTOR DB SETUP ---
class MyFastEmbedFunction(EmbeddingFunction):
    def __init__(self):
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
    
    def __call__(self, input: Documents) -> Embeddings:
        return list(self.model.embed(input))

# Initialize ChromaDB (Singleton-ish pattern for module level)
try:
    chroma_client = chromadb.PersistentClient(path="./tea_vectordb")
    knowledge_collection = chroma_client.get_or_create_collection(
        name="tea_knowledge",
        embedding_function=MyFastEmbedFunction()
    )
    print("✅ Vector Database Ready")
except Exception as e:
    print(f"❌ Vector DB Init Error: {e}")
    knowledge_collection = None

# --- RAG RETRIEVAL LOGIC ---
def retrieve_context(query: str, db: Session):
    try:
        if not knowledge_collection: return "VECTOR_DB_OFFLINE", []

        # A. Query Vector DB
        results = knowledge_collection.query(query_texts=[query], n_results=3)
        
        context_list = []
        sources_found = []

        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                source = meta.get('source', 'Unknown File')
                context_list.append(f"Fact: {doc} (Source: {source})")
                sources_found.append(source)
        
        # B. Fallback to SQL DB
        clean_query = query.replace("?", "").replace(".", "")
        diseases = db.query(DiseaseInfo).filter(DiseaseInfo.name.ilike(f"%{clean_query}%")).limit(1).all()
        
        for d in diseases:
            context_list.append(f"Disease Info: {d.name}. Symptoms: {', '.join(d.symptoms)}.")
            sources_found.append(f"TeaCare Database ({d.name})")

        if not context_list:
            return "NO_DATA_FOUND", []

        return "\n\n".join(context_list), list(set(sources_found))

    except Exception as e:
        print(f"Retrieval Error: {e}")
        return "NO_DATA_FOUND", []

# --- ENDPOINTS ---

@router.post("/upload_book")
async def upload_book(file: UploadFile = File(...), category: str = Form("General"), db: Session = Depends(get_db)):
    if not knowledge_collection:
        raise HTTPException(status_code=503, detail="Vector Database is offline")

    try:
        pdf_reader = PdfReader(file.file)
        full_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text: full_text += text + "\n"
        
        chunk_size = 1000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{file.filename}_part_{i}"
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({"source": file.filename, "category": category})

        knowledge_collection.add(ids=ids, documents=documents, metadatas=metadatas)
        
        log_event(db, "SUCCESS", "Knowledge Base", f"Ingested manual: {file.filename}")
        return {"message": f"Successfully learned {len(chunks)} chunks from '{file.filename}'."}
    except Exception as e:
        log_event(db, "ERROR", "Knowledge Base", f"PDF Ingestion Failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process PDF")

@router.post("/chat_stream")
async def chat_stream(user_query: str = Form(...), db: Session = Depends(get_db)):
    if not ai_manager.llm:
        raise HTTPException(status_code=503, detail="AI LLM Service Unavailable")

    context, sources = retrieve_context(user_query, db)
    log_event(db, "INFO", "Chatbot", f"Query: {user_query[:50]}...")

    if context == "NO_DATA_FOUND":
        system_instruction = "You are a Tea Assistant. Politely apologize and say you only know about topics in the uploaded TeaCare documents."
    else:
        system_instruction = "You are an expert Tea Agronomist. Answer ONLY using the facts provided in the Context."

    prompt = f"""<|im_start|>system
{system_instruction}

Context:
{context}<|im_end|>
<|im_start|>user
{user_query}<|im_end|>
<|im_start|>assistant
"""
    
    def iter_tokens():
        stream = ai_manager.llm(prompt, max_tokens=256, stop=["<|im_end|>"], stream=True, temperature=0.5)
        for output in stream:
            yield output['choices'][0]['text']
        
        if sources:
            yield "\n\n---\n**Sources:**\n"
            for src in sources:
                yield f"• {src}\n"

    return StreamingResponse(iter_tokens(), media_type="text/markdown")