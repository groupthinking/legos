#!/usr/bin/env python3
"""
FastAPI backend for LLM-powered License RAG System

This server provides an Active RAG (Retrieval-Augmented Generation) system
that combines the Blob+Map architecture with vector search and LLM analysis.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from openai import OpenAI

# CONFIGURATION
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
INPUT_FILE = "licenses.jsonl"  # Default input file
CHROMA_PERSIST_DIR = "./chroma_db"  # Persistent storage for ChromaDB
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")  # CORS origins

# Model configuration (can be overridden via environment)
MODEL_CHAT = os.environ.get("MODEL_CHAT", "gpt-4o")
MODEL_AUDIT = os.environ.get("MODEL_AUDIT", "gpt-4o-mini")

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    print("[WARN] OPENAI_API_KEY not set. Chat features will be disabled.")

# --- VECTOR DATABASE SETUP ---
# Use PersistentClient for data persistence across server restarts
chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
collection = chroma_client.get_or_create_collection(name="licenses")


def ingest_licenses(input_file: str) -> int:
    """
    Ingest licenses from JSONL file into vector database.
    
    Args:
        input_file: Path to JSONL file
        
    Returns:
        Number of licenses ingested
    """
    if not Path(input_file).exists():
        print(f"[WARN] Input file '{input_file}' not found. Skipping ingestion.")
        return 0
    
    print(f"[INFO] Ingesting licenses from: {input_file}")
    
    count = 0
    with open(input_file, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                
                # Extract fields (handle different formats)
                library = data.get('name', data.get('library', f'Unknown-{idx}'))
                license_text = data.get('content', data.get('license_text', ''))
                license_type = data.get('license_type', 'Unknown')
                source = data.get('source', data.get('links', [''])[0] if 'links' in data else '')
                
                # Create document for vector search
                doc_text = f"Library: {library}\nLicense Type: {license_type}\nLicense Text: {license_text}"
                
                collection.add(
                    documents=[doc_text],
                    metadatas=[{
                        "library": library,
                        "license_type": license_type,
                        "source": str(source)
                    }],
                    ids=[f"id_{idx}"]
                )
                count += 1
                
            except json.JSONDecodeError as e:
                print(f"[WARN] Skipping invalid JSON at line {idx}: {e}")
                continue
            except Exception as e:
                print(f"[WARN] Error processing line {idx}: {e}")
                continue
    
    print(f"[INFO] Ingestion complete: {count} licenses indexed")
    return count


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the vector database on startup."""
    ingest_licenses(INPUT_FILE)
    yield
    # Cleanup on shutdown (if needed)


# Create FastAPI app with lifespan
app = FastAPI(
    title="License RAG API",
    description="Retrieval-Augmented Generation system for license analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS (Allow frontend to talk to backend)
# For production, set ALLOWED_ORIGINS environment variable
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATA MODELS ---

class ChatRequest(BaseModel):
    message: str


class LicensePreview(BaseModel):
    library: str
    preview: str


# --- ENDPOINTS ---

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "License RAG API",
        "openai_enabled": client is not None,
        "indexed_licenses": collection.count()
    }


@app.get("/licenses", response_model=List[LicensePreview])
def get_license_list():
    """
    Returns the simple list for the UI sidebar (Google Style).
    
    This provides a quick overview of all licenses in the system.
    """
    if not Path(INPUT_FILE).exists():
        return []
    
    results = []
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                library = data.get('name', data.get('library', 'Unknown'))
                license_text = data.get('content', data.get('license_text', ''))
                preview = license_text[:100] + "..." if len(license_text) > 100 else license_text
                
                results.append({
                    "library": library,
                    "preview": preview
                })
            except Exception:
                continue
    
    return results


@app.post("/generate_ideas")
def generate_ideas():
    """
    Proactive: Asks LLM to audit the whole list for ideas/risks.
    
    This endpoint performs a high-level analysis of all licenses to identify:
    - Commercial risks (e.g., GPL vs MIT)
    - Optimization opportunities
    - Consolidation suggestions
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    # Grab library metadata
    metadata = collection.get()
    all_libs = [m.get('library', 'Unknown') for m in metadata['metadatas']]
    all_types = [m.get('license_type', 'Unknown') for m in metadata['metadatas']]
    
    if not all_libs:
        return {"analysis": "No licenses found in the database. Please ingest licenses first."}
    
    # Create a summary for the LLM
    license_summary = {}
    for lib, lic_type in zip(all_libs, all_types):
        license_summary[lib] = lic_type
    
    prompt = f"""
Analyze this list of software dependencies and their licenses:

{json.dumps(license_summary, indent=2)}

Please provide:
1. **Commercial Risk Assessment**: Identify any viral/copyleft licenses (GPL, AGPL, etc.) that could restrict commercial use.
2. **Compliance Recommendations**: Highlight licenses requiring attribution or disclosure.
3. **Optimization Suggestions**: Identify redundant dependencies or suggest alternatives with more permissive licenses.

Format your response as clean HTML with proper sections and bullet points.
"""
    
    try:
        response = client.chat.completions.create(
            model=MODEL_AUDIT,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"analysis": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")


@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    """
    Reactive: Answers user questions based on the license data.
    
    Uses vector search to find relevant licenses and LLM to generate answers.
    """
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
        )
    
    # 1. Search Vector DB for relevant licenses
    try:
        results = collection.query(query_texts=[req.message], n_results=3)
        
        if not results['documents'] or not results['documents'][0]:
            return {"reply": "I couldn't find any relevant licenses matching your query."}
        
        context = "\n\n---\n\n".join(results['documents'][0])
        
        # 2. Send to LLM
        system_prompt = """You are a Senior Compliance Engineer specializing in open source license analysis. 
Answer questions using ONLY the provided license context. 
Be precise, cite specific licenses when relevant, and highlight any compliance risks or requirements."""
        
        user_prompt = f"Context:\n{context}\n\nQuestion: {req.message}"
        
        response = client.chat.completions.create(
            model=MODEL_CHAT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        return {"reply": response.choices[0].message.content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting License RAG API Server")
    print(f"[INFO] OpenAI API: {'Enabled' if client else 'Disabled (set OPENAI_API_KEY)'}")
    print(f"[INFO] Input file: {INPUT_FILE}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
