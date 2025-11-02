# Knowledge Base Management System

A full-stack application for managing and querying documents in a knowledge base, featuring file uploads, document processing, and semantic search capabilities.

## Features

- **Multi-format Support**: Upload and process PDF, DOCX, DOC, TXT, and CSV files
- **Document Chunking**: Intelligent document splitting with configurable chunk sizes
- **Vector Embeddings**: Utilizes Gemini for generating document embeddings
- **Semantic Search**: Find relevant documents using natural language queries
- **Observability**: Integrated with Langfuse for monitoring and tracing
- **RESTful API**: Built with FastAPI for high performance and scalability
- **Modern Frontend**: Responsive React-based user interface

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Web framework
- **Agno** - Knowledge base and document processing
- **Qdrant** - Vector database for semantic search
- **Google Gemini** - For generating document embeddings
- **Langfuse** - Observability and tracing
- **Uvicorn** - ASGI server

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

## Prerequisites

- Python 3.11+
- Node.js 18+
- Qdrant server (local or cloud)
- Google Cloud API key with Gemini access
- Langfuse account (optional)

## Setup

### Backend Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd KB
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```env
   # Required
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_URL=your_qdrant_url
   GOOGLE_API_KEY=your_google_api_key
   
   # Optional
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   UPLOAD_DIR=tmp/library
   PORT=1111
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file in the frontend directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:1111
   ```

## Running the Application

### Start the Backend

From the project root:
```bash
uvicorn Knowledge_base:app --reload --port 1111
```

The API will be available at `http://localhost:1111`

### Start the Frontend

From the frontend directory:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

- `POST /upload` - Upload files to the knowledge base
- `GET /files` - List all uploaded files
- `GET /files/{filename}` - Download a specific file
- `DELETE /files/{filename}` - Delete a file
- `POST /query` - Query the knowledge base
- `GET /health` - Health check endpoint

## File Processing

The system supports the following file types:
- **PDF** - Processed using PDFReader
- **DOCX/DOC** - Processed using PDFReader (converted internally)
- **TXT** - Processed using TextReader
- **CSV** - Processed using CSVReader

### Chunking Configuration
- **PDF/DOCX/DOC**:
  - Chunk size: 3000 characters
  - Overlap: 400 characters
- **TXT/CSV**:
  - Chunk size: 1000 characters
  - Overlap: 200 characters

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `QDRANT_API_KEY` | Yes | - | API key for Qdrant vector database |
| `QDRANT_URL` | Yes | - | URL of the Qdrant instance |
| `GOOGLE_API_KEY` | Yes | - | Google Cloud API key for Gemini |
| `LANGFUSE_PUBLIC_KEY` | No | - | Public key for Langfuse |
| `LANGFUSE_SECRET_KEY` | No | - | Secret key for Langfuse |
