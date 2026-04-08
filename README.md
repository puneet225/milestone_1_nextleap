# 🍽️ AI Restaurant Recommendation System

An AI-powered restaurant recommendation service inspired by Zomato. Enter your preferences — location, budget, cuisine, and rating — and get personalized, LLM-ranked restaurant recommendations with explanations.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [Groq API Key](https://console.groq.com) (free tier available)
- Docker + Docker Compose (optional, for containerised run)

---

## Setup

### 1. Clone & configure your API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your real Groq API key:

```
GROQ_API_KEY=your_real_groq_api_key_here
```

> ⚠️ **Never commit your real API key.** `.env` is in `.gitignore`.

---

## Running Without Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`.

---

## Running With Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

To stop:
```bash
docker compose down
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/filters` | Get dynamic filter options (locations, cuisines, cost range) |
| POST | `/recommend` | Get AI-ranked restaurant recommendations |

---

## Dataset

Uses the [ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation) dataset from HuggingFace. Downloaded automatically on first run.
