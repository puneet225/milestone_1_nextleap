# Tech Stack

## Frontend
- Next.js 14 (App Router)
- Tailwind CSS
- shadcn/ui (slider, dropdown, card components)
- Native fetch for API calls

## Backend
- FastAPI (Python)
- Uvicorn (ASGI server)
- python-dotenv

## LLM
- Groq SDK (Python) — model: llama3-70b-8192
- API key loaded from .env as GROQ_API_KEY

## Data
- HuggingFace datasets library
- Pandas

## DevOps
- Docker Compose
- Next.js on port 3000, FastAPI on port 8000

## Why FastAPI is separate from Next.js
HuggingFace and Groq SDKs are Python-native.
Keeping the backend in FastAPI avoids forcing Python logic into JS serverless functions.