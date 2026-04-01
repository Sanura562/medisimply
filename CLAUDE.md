# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MediSimply** is a medical text simplification system for elderly Sinhala-speaking patients in Sri Lanka. It takes complex medicine information and returns bilingual (English + Sinhala) simplified explanations across four sections: what it does, how to take it, warnings, and who shouldn't take it.

## Development Commands

### Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Run the API server (from project root)
uvicorn app:app --host 127.0.0.1 --port 8000 --reload

# One-time data setup
python3 build_dataset.py   # Fetch openFDA data → drug_data.json
python3 import_kaggle.py   # Convert Medicine_Details.csv → medicines_db.json
python3 rag.py             # Build FAISS vector index (optional)
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Dev server at http://localhost:5173
npm run build    # Production build
npm run lint     # ESLint
```

## Architecture

### Data Flow
```
User types medicine name
  → GET /search/{query}    (autocomplete, returns top 10 with images)
  → POST /lookup           (full lookup → Gemini LLM → bilingual JSON)
  → Results displayed
```

### Backend (`app.py`)
FastAPI app that loads two databases at startup:
- **`medicines_db.json`** — 11K medicines from Kaggle (images, composition, side effects, manufacturer)
- **`drug_data.json`** — ~25 essential drugs from openFDA (verified clinical text: indications, dosage, warnings, contraindications)

On `/lookup`, it merges data from both sources, builds a structured prompt, and calls **Gemini 2.5-Flash** to produce JSON with `english`/`sinhala` fields for each section plus key points.

`rag.py` is a standalone FAISS-based RAG module (not integrated into `app.py`) that chunks and embeds medicine text using `gemini-embedding-001`.

### Frontend (`frontend/src/`)
React 19 + Vite 8 + Tailwind CSS 4. All state lives in `App.jsx` which coordinates:
- `SearchBox` — debounced autocomplete (300ms) calling `/search`
- `Results` + `ResultCard` — render the bilingual API response
- `Loading`, `Welcome`, `Disclaimer` — supporting UI states

API base URL is hardcoded as `http://127.0.0.1:8000` in `App.jsx`.

### Environment
Requires a `.env` file in the project root:
```
GEMINI_API_KEY=...
GEMINI_EMBED_KEY=...
```

### LLM Response Schema
```python
{
  "medicine_name": str,
  "found_in_database": bool,
  "source": str,
  "image_url": str,
  "composition": str,
  "manufacturer": str,
  "what_it_does": {"english": str, "sinhala": str},
  "how_to_take": {"english": str, "sinhala": str},
  "warnings_and_side_effects": {"english": str, "sinhala": str},
  "who_should_not_take": {"english": str, "sinhala": str},
  "key_points": [str, ...]
}
```

## Key Constraints
- Sinhala text requires `Noto Sans Sinhala` font (loaded via `index.css`)
- The Gemini prompt is tuned for elderly users: short sentences (10–15 words), simple vocabulary, no medical jargon
- Both databases are loaded into memory at startup; no external DB dependency at runtime
