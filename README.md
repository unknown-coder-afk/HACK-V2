# Synthetic Data Platform

A schema-aware synthetic data generation platform with a modern Next.js frontend and FastAPI backend.

## Features
- **Tabular Generation** – Build custom schemas with 14 column types, null/outlier injection, and privacy controls (mask, hash, noise).
- **Relational Generation** – Auto-generate linked tables (Customers → Orders) with FK integrity validation.
- **Document Generation** – Realistic invoices, bank statements, and receipts.
- **Live Preview** – Interactive table view, JSON explorer, and validation dashboard.
- **Export** – Download results as CSV or JSON.

## Project Structure
```
HACK-V2/
├── backend/              # FastAPI Python backend
│   ├── main.py           # App entry point
│   ├── config.py         # Env var config
│   ├── requirements.txt  # Python dependencies
│   ├── engine/           # Core data generation
│   │   ├── distribution.py   # Sampling engine
│   │   ├── tabular.py        # Table generation
│   │   ├── relational.py     # Multi-table generation
│   │   ├── documents.py      # Invoice/statement generation
│   │   ├── privacy.py        # Masking/hashing/noise
│   │   └── validation.py     # Quality checks
│   ├── routers/          # API route handlers
│   │   ├── generate.py   # /api/generate/*
│   │   ├── export.py     # /api/export/*
│   │   ├── upload.py     # /api/upload/*
│   │   └── ai.py         # /api/ai/*
│   ├── models/
│   │   └── schemas.py    # Pydantic models
│   └── ai/
│       ├── client.py     # OpenAI client (optional)
│       └── text_pools.py # Fallback text pools
├── frontend/             # Next.js 16 frontend
│   ├── src/app/
│   │   ├── page.tsx      # Main UI
│   │   ├── layout.tsx    # Root layout
│   │   └── globals.css   # Dark theme styles
│   ├── next.config.ts    # API proxy config
│   └── package.json
└── vercel.json           # Vercel deployment config
```

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m backend.main
# API at http://127.0.0.1:8000
# Docs at http://127.0.0.1:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# UI at http://localhost:3000
```

## Environment Variables

Copy `.env` and set:
| Variable | Description |
|---|---|
| `LOCAL_API_KEY` | Local dev API key |
| `SERVER_HOST` | Backend host (default `127.0.0.1`) |
| `SERVER_PORT` | Backend port (default `8000`) |
| `OPENAI_API_KEY` | Optional: enables AI text generation |

## Deployment (Vercel)

1. Push to GitHub
2. Import repo in [Vercel](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Add env var: `NEXT_PUBLIC_API_URL=https://your-backend-url`
5. Deploy!

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/generate/tabular` | Generate custom tabular dataset |
| POST | `/api/generate/relational` | Generate multi-table relational data |
| POST | `/api/generate/relational/preset/ecommerce` | E-commerce preset |
| POST | `/api/generate/document` | Generate invoices / bank statements |
| POST | `/api/export/csv` | Download data as CSV |
| POST | `/api/export/json` | Download data as JSON |
| POST | `/api/upload/schema` | Upload a JSON schema file |
| POST | `/api/upload/infer` | Infer schema from CSV |
| GET  | `/api/ai/column-types` | List supported column types |
| GET  | `/health` | Health check |
