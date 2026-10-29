# AI Knowledge Assistant

A full-stack RAG-powered document Q&A application with agentic workflows, built with FastAPI, React, ChromaDB, and Hugging Face.

---

## Features

- Upload PDF, DOCX, and TXT documents
- Ask questions grounded in uploaded content with source citations
- Summarize documents and compare multiple documents
- Controlled agentic workflow (document search, summarization, comparison, optional web search)
- LoRA/QLoRA fine-tuning pipeline (separate workflow)
- Local-first: runs without paid API keys using local Hugging Face models

---

## Minimum Hardware Requirements

| Feature | Requirement |
|---|---|
| Backend + embeddings | 4 GB RAM, any modern CPU |
| Local LLM (phi-2) | 8 GB RAM recommended |
| LoRA fine-tuning | 8 GB RAM (CPU, very slow) |
| QLoRA fine-tuning | NVIDIA GPU with 8+ GB VRAM + CUDA |

---

## Quick Start

### 1. Clone and set up environment

```bash
git clone <repo-url>
cd ai-knowledge-assistant
```

### 2. Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Copy and configure environment:

```bash
cp .env.example .env
```

Edit `.env` — see **Configuration** section below.

Start the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Configuration

Edit `backend/.env`. Key settings:

### LLM Provider Options

**Option A — Local model (no API key, downloads on first use ~1-4 GB):**
```
LLM_PROVIDER=huggingface_local
LLM_MODEL_ID=microsoft/phi-2
LLM_DEVICE=cpu
```

**Option B — Hugging Face Inference API (free tier available):**
```
LLM_PROVIDER=huggingface_api
HUGGINGFACE_API_KEY=hf_your_key_here
HF_INFERENCE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
```

**Option C — OpenAI-compatible API:**
```
LLM_PROVIDER=openai_compatible
OPENAI_API_KEY=sk-your_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

### Embedding Model (local, no API key needed)
```
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## Running Tests

### Backend tests (no paid API required — LLM calls are mocked)

```bash
cd backend
pytest -v
```

### Frontend tests

```bash
cd frontend
npm test
```

---

## Fine-Tuning (Separate Workflow)

> Fine-tuning changes model behavior on training data. It does NOT add uploaded documents to the model's knowledge. Use RAG for document-grounded answers.

### Install fine-tuning dependencies

```bash
pip install peft trl
# For QLoRA (Linux + NVIDIA GPU only):
pip install bitsandbytes
```

### Run LoRA training

```bash
cd backend
python training/scripts/train_lora.py --model facebook/opt-125m
```

### Run QLoRA training (GPU required)

```bash
python training/scripts/train_lora.py --model facebook/opt-125m --qlora
```

### Evaluate adapter

```bash
python training/evaluation/evaluate.py --adapter ./training/output/lora_adapter
```

### Cloud GPU alternative

If your machine lacks a compatible GPU, use:
- [Google Colab](https://colab.research.google.com) (free T4 GPU)
- [Kaggle Notebooks](https://www.kaggle.com/code) (free P100 GPU)
- [AWS SageMaker](https://aws.amazon.com/sagemaker/)

Upload `training/` directory and run the scripts there.

---

## Project Structure

```
backend/
  app/
    api/          # FastAPI route handlers
    core/         # Config, logging, error handling
    schemas/      # Pydantic models
    ingestion/    # File extraction, chunking, embeddings, vector store
    rag/          # RAG chain and prompt building
    agents/       # Agent orchestrator
    tools/        # Agent tools (search, summarize, compare, web)
    database/     # SQLite ORM and repository
    models/       # LLM provider abstraction
    main.py       # FastAPI app entry point
  training/
    datasets/     # Sample JSONL training data
    scripts/      # LoRA/QLoRA training script
    evaluation/   # Before/after evaluation script
  tests/          # pytest test suite
  requirements.txt
  .env.example

frontend/
  src/
    components/   # Reusable UI components
    pages/        # Dashboard, Documents, Chat, Summary, Settings
    services/     # API client (axios)
    types/        # TypeScript interfaces
    utils/        # Helper functions
    test/         # Vitest + React Testing Library tests
    App.tsx
    main.tsx
    styles.css
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/health | Health check |
| GET | /api/documents | List all documents |
| POST | /api/documents/upload | Upload a document |
| GET | /api/documents/{id} | Get document metadata |
| DELETE | /api/documents/{id} | Delete document + vectors |
| POST | /api/documents/{id}/summary | Generate summary |
| POST | /api/documents/compare | Compare documents |
| POST | /api/chat | Ask a question (agent) |
| GET | /api/models/status | Model/system status |
| GET | /api/agent/tools | List available agent tools |

Full interactive docs: http://localhost:8000/docs

---

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (3.10+ required)
- Ensure venv is activated
- Run `pip install -r requirements.txt` again

**Model download is slow or fails:**
- First run downloads the embedding model (~90 MB) and LLM (varies)
- Ensure internet access or pre-download with `huggingface-cli download <model-id>`
- Set `HF_HOME` env var to change cache location

**ChromaDB errors:**
- Delete `backend/data/chroma/` and restart to reset the vector store

**"LLM not ready" in Settings:**
- The local model loads on first chat request, not at startup
- Check logs for download or memory errors
- Switch to `huggingface_api` provider if local model is too large

**CORS errors in browser:**
- Ensure `ALLOWED_ORIGINS` in `.env` includes your frontend URL
- Default: `http://localhost:5173`

**Out of memory with local LLM:**
- Use a smaller model: `LLM_MODEL_ID=facebook/opt-125m` (for testing only)
- Or switch to `huggingface_api` provider

---

## Security Notes

- This application is designed for **local single-user use**.
- Add authentication (e.g., OAuth2, API keys) before exposing to multiple users.
- Never commit `.env` to version control.
- API keys are never logged or returned by any endpoint.
- Uploaded documents are treated as untrusted data — embedded instructions are ignored.

---

## Required Credentials (at the end)

See the **Credentials** section at the bottom of this README after setup.

### Required
- None for local mode (embedding model + local LLM)

### Optional
- `HUGGINGFACE_API_KEY` — for HF Inference API. Get at: https://huggingface.co/settings/tokens
- `OPENAI_API_KEY` — for OpenAI-compatible APIs. Get at: https://platform.openai.com/api-keys
- `SERPAPI_KEY` — for web search tool. Get at: https://serpapi.com/manage-api-key
