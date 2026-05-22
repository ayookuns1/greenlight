# Team Greenlight 🟢
### DSN x BCT LLM Agent Hackathon 3.0

> *"Design agents that understand how people behave, what they want, and what they'll choose next."*

A dual-task LLM agent system for personalised **user modelling** and **recommendation**, contextualised in **Nigerian English** with authentic Pidgin expressions throughout all outputs.

---

## Overview

| Service | Task | Port | Description |
|---------|------|------|-------------|
| Task A | User Modelling | `8001` | Generates personalised reviews + star ratings in a user's writing style |
| Task B | Recommendation | `8002` | Delivers personalised recommendations using FAISS retrieval + LLM reranking |

Both services are containerised FastAPI applications powered by **Google Gemini 2.5 Flash** and **sentence-transformers (all-MiniLM-L6-v2)**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Team Greenlight                       │
│                                                         │
│  ┌──────────────────┐      ┌──────────────────────────┐ │
│  │   Task A · 8001  │      │     Task B · 8002        │ │
│  │  User Modelling  │      │     Recommendation       │ │
│  │                  │      │                          │ │
│  │ 1. Load profile  │      │ 1. Reason user needs     │ │
│  │ 2. Gemini review │      │ 2. FAISS retrieval       │ │
│  │ 3. Local rating  │      │ 3. LLM reranking         │ │
│  └────────┬─────────┘      └────────────┬─────────────┘ │
│           │                             │               │
│           └──────────┬──────────────────┘               │
│                      ▼                                  │
│           ┌──────────────────┐                          │
│           │   data/          │                          │
│           │ combined_sample  │                          │
│           │ user_profiles    │                          │
│           │ faiss_index      │                          │
│           └──────────────────┘                          │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker + Docker Compose
- Google Gemini API key ([get one free at aistudio.google.com](https://aistudio.google.com))

### 1. Clone and configure
```bash
git clone <repo-url>
cd greenlight
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Build the data (one-time setup)
```bash
pip install -r task_a/requirements.txt
pip install -r task_b/requirements.txt
python notebooks/build_data.py
```
This streams ~10,000 reviews from Yelp and Amazon (HuggingFace), builds user profiles, and creates the FAISS neural index. Takes ~25 minutes on first run; results are cached.

### 3. Run with Docker Compose
```bash
docker-compose up --build
```

Both services will be available at:
- Task A: http://localhost:8001/docs
- Task B: http://localhost:8002/docs

### 4. Run locally (without Docker)
```bash
# Terminal 1 — Task A
cd task_a
python -m uvicorn main:app --host 0.0.0.0 --port 8001

# Terminal 2 — Task B
cd task_b
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

---

## API Reference

### Task A — Generate Review
**POST** `http://localhost:8001/generate-review`

```json
{
  "user_id": "yelp_user_0228",
  "item_name": "Chicken Republic Streetburger",
  "item_category": "Restaurant",
  "item_description": "Crispy fried chicken burger with coleslaw and spicy sauce",
  "price_range": "₦2,500 – ₦4,000"
}
```

**Response:**
```json
{
  "review_text": "I no go lie, this Streetburger na serious something...",
  "star_rating": 4.2,
  "confidence": 0.88,
  "user_style_matched": true,
  "user_found": true
}
```

**PowerShell:**
```powershell
$body = '{"user_id":"yelp_user_0228","item_name":"Chicken Republic","item_category":"Restaurant","item_description":"Fried chicken","price_range":"N2500"}'
Invoke-WebRequest -Uri http://localhost:8001/generate-review -Method POST -ContentType "application/json" -Body $body | Select-Object -ExpandProperty Content
```

---

### Task B — Get Recommendations
**POST** `http://localhost:8002/recommend`

```json
{
  "user_id": "yelp_user_0228",
  "conversation_history": [],
  "top_k": 5
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "rank": 1,
      "item_name": "Yelp_Business_3228",
      "category": "Restaurant",
      "score": 0.87,
      "explanation": "Omo this one go sweet you well well, e match your taste!",
      "source": "yelp"
    }
  ],
  "user_need_summary": "User enjoys reliable, high-quality dining experiences...",
  "is_cold_start": false
}
```

### Task B — Cold Start (New Users)
**POST** `http://localhost:8002/recommend/cold-start`

```json
{
  "item_category": "Restaurant",
  "description_of_what_i_want": "spicy Nigerian street food, affordable, large portions",
  "top_k": 5
}
```

---

## Health Checks

```bash
# Task A
curl http://localhost:8001/health
# {"status":"ok","task":"A - User Modeling","model":"gemini-2.5-flash"}

# Task B
curl http://localhost:8002/health
# {"status":"ok","task":"B - Recommendation","model":"gemini-2.5-flash"}
```

---

## Evaluation Results

### Task A — User Modelling (16 users)

| Metric | Score |
|--------|-------|
| Avg ROUGE-L | 0.1357 |
| RMSE (star rating) | 0.8725 |
| MAE (star rating) | 0.6625 |
| Style match rate | 100% |
| Avg review length | 1,142 chars |

### Task B — Recommendation (20 users)

| Metric | Score |
|--------|-------|
| Hit Rate@5 | 0.6500 (65%) |
| NDCG@5 | 0.2968 |
| Cold-start success | 5/5 (100%) |

---

## Project Structure

```
greenlight/
├── task_a/                    # Task A — User Modelling API
│   ├── agent.py               # Gemini pipeline + local sentiment rating
│   ├── main.py                # FastAPI routes + Pydantic models
│   ├── requirements.txt
│   └── Dockerfile
├── task_b/                    # Task B — Recommendation API
│   ├── agent.py               # FAISS retrieval + Gemini reranking
│   ├── main.py                # FastAPI routes
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── combined_sample.json   # 9,999 unified reviews (Yelp + Amazon)
│   ├── user_profiles.json     # 1,271 user profiles
│   └── faiss_index.pkl        # Pre-built FAISS neural index
├── notebooks/
│   ├── build_data.py          # Data pipeline
│   ├── evaluate_task_a.ipynb  # ROUGE-L + RMSE evaluation
│   └── evaluate_task_b.ipynb  # Hit Rate@5 + NDCG@5 evaluation
├── results/
│   ├── task_a_results.json
│   └── task_b_results.json
├── docker-compose.yml
├── .env                       # GEMINI_API_KEY (not committed)
└── README.md
```

---

## Key Design Decisions

**Task A — Why two steps instead of JSON schema?**
Gemini's structured output mode caused double-nested JSON when thinking tokens were enabled. A plain-text review followed by local sentiment-based rating is more robust and avoids safety filter issues on the rating call.

**Task B — Why review-text retrieval instead of LLM need summaries?**
Semantic search using the user's actual review history directly grounds retrieval in demonstrated preferences rather than a generic LLM description, achieving 90% recall of ground-truth items in the top-50 candidates.

**Why Nigerian English?**
All outputs are contextualised with authentic Nigerian Pidgin phrases ("I no go lie", "e dey sweet", "abeg", "omo") embedded directly in prompts, making outputs culturally relevant for Nigerian markets.

**Why FAISS over collaborative filtering?**
FAISS with all-MiniLM-L6-v2 embeddings captures semantic similarity across review text, enabling cross-domain recommendations and cold-start handling without requiring user-item interaction matrices.

---

## Datasets

| Dataset | Source | Records |
|---------|--------|---------|
| Yelp Reviews | `Yelp/yelp_review_full` (HuggingFace) | 5,000 |
| Amazon Grocery | `McAuley-Lab/Amazon-Reviews-2023` | 3,000 |
| Amazon Books | `McAuley-Lab/Amazon-Reviews-2023` (Books proxy for Goodreads) | 2,000 |

*Note: Goodreads data is no longer publicly distributed. Amazon Books is used as a high-quality substitute with appropriate disclosure per competition rules.*

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model name |

---

## Team

**Team Greenlight** · DSN x BCT LLM Agent Hackathon 3.0 · May 2026
