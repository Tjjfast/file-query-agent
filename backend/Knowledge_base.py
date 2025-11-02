from agno.vectordb.lancedb import LanceDb
from agno.vectordb.qdrant import Qdrant
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.reader.text_reader import TextReader
from agno.knowledge.reader.csv_reader import CSVReader
from agno.knowledge.reader.docx_reader import DocxReader
from agno.knowledge.chunking.fixed import FixedSizeChunking
from agno.models.google import Gemini
import base64
import os
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from agno.os import AgentOS
from dotenv import load_dotenv
from pathlib import Path
from fastapi import UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import openlit
from langfuse import get_client
 
langfuse = get_client()
load_dotenv()

if not hasattr(openlit, '_instrumented'):
    LANGFUSE_AUTH = base64.b64encode(
        f"{os.getenv('LANGFUSE_PUBLIC_KEY')}:{os.getenv('LANGFUSE_SECRET_KEY')}".encode()
    ).decode()
    
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://eu.cloud.langfuse.com"
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "https://eu.cloud.langfuse.com/api/public/ingestion"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"
    
    trace_provider = TracerProvider()
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(trace_provider)
    
    openlit.init(
        otlp_endpoint="https://eu.cloud.langfuse.com/api/public/ingestion",
        otlp_headers=f"Authorization=Basic {LANGFUSE_AUTH}",
        disable_batch=True,
        disable_metrics=True
    )
    
    openlit._instrumented = True

Path("tmp/library").mkdir(parents=True, exist_ok=True)

api_key = os.getenv("QDRANT_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")

embedder = GeminiEmbedder(
    id="gemini-embedding-001",
    api_key=os.getenv('GOOGLE_API_KEY')
)

knowledge = Knowledge(
    vector_db=Qdrant(
        collection="KnowledgeBase",
        url=qdrant_url,
        api_key=api_key,
        embedder=embedder),
)

instructions = """
You only answer with content from your database.
You don't use your internal knowledge.
If you can't answer with the database, simply return 'I don't know'.
"""

agent = Agent(
    name="KnowledgeBaseAgent",
    model=Gemini(id='gemini-2.5-flash', api_key=os.getenv('GOOGLE_API_KEY')),
    search_knowledge=True,
    instructions=instructions,
    knowledge=knowledge,
    markdown=True,
    debug_mode=True,
    stream=True,
)

agent_os = AgentOS(
    os_id="KnowledgeBaseOS",
    agents=[agent],
)

app = agent_os.get_app()

UPLOAD_DIR = "tmp/library"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://192.168.1.4:3000",
        "*" 
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

async def process_document_async(file_path: str):
    """Process and add document to knowledge base asynchronously"""
    try:
        file_name = Path(file_path).name
        print(f"📄 Processing: {file_name}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            reader = PDFReader(
                name=f"Reader-{file_name}",
                chunking_strategy=FixedSizeChunking(
                    chunk_size=3000,
                    overlap=400
                )
            )
        elif file_ext == '.txt':
            reader = TextReader(
                name=f"Reader-{file_name}",
                chunking_strategy=FixedSizeChunking(
                    chunk_size=1000,
                    overlap=200
                )
            )
        elif file_ext == '.csv':
            reader = CSVReader(
                name=f"Reader-{file_name}",
                chunking_strategy=FixedSizeChunking(
                    chunk_size=1000,
                    overlap=200
                )
            )
        elif file_ext in ['.doc', '.docx']:
            reader = DocxReader(
                name=f"Reader-{file_name}",
                chunking_strategy=FixedSizeChunking(
                    chunk_size=3000,
                    overlap=400
                )
            )
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        await knowledge.add_content_async(
            path=file_path,
            reader=reader,
            skip_if_exists=False,
        )
        
        print(f"✅ Successfully added {file_name} to knowledge base")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {Path(file_path).name}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files and add them to the knowledge base"""
    try:
        saved_files = []
        
        for file in files:
            allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.csv'}
            file_ext = Path(file.filename).suffix.lower()
            
            if file_ext not in allowed_extensions:
                saved_files.append({
                    "original_filename": file.filename,
                    "status": "error",
                    "message": f"File type not supported: {file_ext}"
                })
                continue
            
            original_filename = file.filename
            base_name = os.path.splitext(original_filename)[0]
            extension = os.path.splitext(original_filename)[1]
            
            safe_filename = f"{base_name}{extension}"
            counter = 1
            file_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            while os.path.exists(file_path):
                safe_filename = f"{base_name}_{counter}{extension}"
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                counter += 1
            
            print(f"💾 Saving: {safe_filename}")
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_size = len(content) / 1024  
            print(f"   Size: {file_size:.2f} KB")
            
            file_info = {
                "original_filename": original_filename,
                "saved_filename": safe_filename,
                "saved_path": file_path,
                "size": f"{file_size:.2f} KB",
                "status": "saved"
            }
            
            try:
                print(f"🔄 Adding to knowledge base: {safe_filename}")
                
                await process_document_async(file_path)
                
                file_info["status"] = "processed"
                file_info["message"] = "Successfully added to knowledge base"
                print(f"✅ Complete: {safe_filename}\n")
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                print(f"❌ {error_msg}\n")
                file_info["status"] = "error"
                file_info["message"] = error_msg
            
            saved_files.append(file_info)
        
        successful = sum(1 for f in saved_files if f["status"] == "processed")
        failed = sum(1 for f in saved_files if f["status"] == "error")
        
        return {
            "message": f"Processed {successful}/{len(files)} files successfully",
            "files": saved_files,
            "summary": {
                "total": len(files),
                "successful": successful,
                "failed": failed
            }
        }
    
    except Exception as e:
        print(f"❌ Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files")
async def list_files():
    """List all uploaded files"""
    try:
        files = []
        for file_path in Path(UPLOAD_DIR).iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "size": f"{file_path.stat().st_size / 1024:.2f} KB",
                    "modified": file_path.stat().st_mtime
                })
        return {"files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "api_key_set": bool(os.getenv('GOOGLE_API_KEY')),
        "upload_dir": UPLOAD_DIR,
        "files_count": len(list(Path(UPLOAD_DIR).iterdir()))
    }

if __name__ == "__main__":
    agent_os.serve(
        app="Knowledge_base:app", 
        reload=True, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 1111))
    )