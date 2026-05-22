"""
Task B — FastAPI Application
POST /recommend              → personalised recommendations for a known user
POST /recommend/cold-start   → recommendations for a brand-new user
GET  /health                 → health check
"""

import json
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from agent import recommend, recommend_cold_start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# UTF-8 patch so ₦ and other unicode render correctly
_orig_render = JSONResponse.render
def _utf8_render(self, content):
    return json.dumps(content, ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
JSONResponse.render = _utf8_render

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Team Greenlight — Task B: Recommendation",
    description=(
        "Delivers personalised recommendations using a 3-step agentic pipeline: "
        "LLM reasoning → FAISS retrieval → LLM reranking. "
        "Explanations are contextualised in Nigerian English."
    ),
    version="1.0.0",
    default_response_class=JSONResponse,
)


# ── Schemas ───────────────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="The user ID. Use GET /users on Task A to see available IDs.",
        example="yelp_user_0001"
    )
    conversation_history: list = Field(
        default=[],
        description=(
            "Optional multi-turn conversation context. "
            "Each item: {\"role\": \"user\"|\"assistant\", \"content\": \"...\"}."
        ),
        example=[]
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of recommendations to return (1–20)."
    )

    @field_validator("user_id")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty.")
        return v.strip()


class ColdStartRequest(BaseModel):
    item_category: str = Field(
        ...,
        description="The category of items you want.",
        example="Restaurant"
    )
    description_of_what_i_want: str = Field(
        ...,
        description="Plain English description of what you are looking for.",
        example="Spicy Nigerian street food, budget-friendly, good portions"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=20,
        description="Number of recommendations to return (1–20)."
    )

    @field_validator("item_category", "description_of_what_i_want")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty.")
        return v.strip()


class RecommendationItem(BaseModel):
    item_name:   str
    category:    str
    score:       float
    explanation: str
    source:      str


class RecommendResponse(BaseModel):
    recommendations:   list
    user_need_summary: str
    is_cold_start:     bool


class HealthResponse(BaseModel):
    status: str
    task:   str
    model:  str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Returns service health status."""
    return {
        "status": "ok",
        "task":   "B - Recommendation",
        "model":  "gemini-2.5-flash",
    }


@app.post("/recommend", response_model=RecommendResponse, tags=["Task B"])
def recommend_endpoint(request: RecommendRequest):
    """
    ## Personalised Recommendations

    3-step agentic pipeline:
    1. **Reasoning** — LLM generates a user need summary from profile + conversation
    2. **Retrieval** — FAISS finds top-20 candidates by semantic similarity
    3. **Reranking** — LLM reranks into final top-K with Nigerian English explanations

    Handles **cold-start** automatically if the user_id is unknown.
    Supports **cross-domain** recommendations (Yelp user can get book recs, etc).
    """
    try:
        result = recommend(
            user_id=request.user_id,
            conversation_history=request.conversation_history,
            top_k=request.top_k,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {e}")


@app.post("/recommend/cold-start", response_model=RecommendResponse, tags=["Task B"])
def cold_start_endpoint(request: ColdStartRequest):
    """
    ## Cold-Start Recommendations

    For brand-new users with no history. Provide a category and description
    of what you want — the agent finds and ranks the best matches.

    Example:
    - category: "Fiction"
    - description: "I want a gripping thriller that I cannot put down,
      something with plot twists and a Nigerian or African setting"
    """
    try:
        result = recommend_cold_start(
            item_category=request.item_category,
            description_of_what_i_want=request.description_of_what_i_want,
            top_k=request.top_k,
        )
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Cold-start error: {e}")
        raise HTTPException(status_code=500, detail=f"Cold-start failed: {e}")


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(status_code=404, content={"error": "Endpoint not found."})

@app.exception_handler(500)
async def server_error(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error."})


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
