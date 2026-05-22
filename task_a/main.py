"""
Task A — FastAPI Application
POST /generate-review  → generates a personalised review + star rating
GET  /health           → health check
GET  /users            → list available user IDs (for testing)
"""

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from agent import generate_review, list_user_ids, get_user_profile
import json

# Monkey-patch JSONResponse to never escape unicode (fixes ₦ symbol)
_orig_render = JSONResponse.render
def _utf8_render(self, content):
    return json.dumps(content, ensure_ascii=False,
                      allow_nan=False).encode("utf-8")
JSONResponse.render = _utf8_render

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Team Greenlight — Task A: User Modeling",
    default_response_class=JSONResponse,
    description=(
        "Generates personalised product/service reviews and star ratings "
        "by simulating a user's review style. Outputs are contextualised "
        "in Nigerian English for cultural relevance."
    ),
    version="1.0.0",
)


# ── Request / Response schemas ─────────────────────────────────────────────────
class ReviewRequest(BaseModel):
    user_id: str = Field(
        ...,
        description="The user ID to simulate. Use GET /users to see available IDs.",
        example="yelp_user_0001"
    )
    item_name: str = Field(
        ...,
        description="Name of the item or business to review.",
        example="Chicken Republic Streetburger"
    )
    item_category: str = Field(
        ...,
        description="Category of the item.",
        example="Restaurant"
    )
    item_description: str = Field(
        ...,
        description="Short description of the item.",
        example="Crispy fried chicken burger with coleslaw and spicy sauce"
    )
    price_range: str = Field(
        default="Unknown",
        description="Price range of the item (use ₦ for naira).",
        example="₦2,500 – ₦4,000"
    )

    @field_validator("user_id", "item_name", "item_category", "item_description")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty.")
        return v.strip()

    @field_validator("item_description")
    @classmethod
    def description_length(cls, v: str) -> str:
        if len(v) > 1000:
            raise ValueError("item_description must be under 1000 characters.")
        return v


class ReviewResponse(BaseModel):
    review_text:        str
    star_rating:        float
    confidence:         float
    user_style_matched: bool
    user_found:         bool


class HealthResponse(BaseModel):
    status: str
    task:   str
    model:  str


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
def health():
    """Returns service health status."""
    return {
        "status": "ok",
        "task":   "A - User Modeling",
        "model":  "gemini-2.5-flash",
    }


@app.get("/users", tags=["System"])
def get_users(limit: int = 20):
    """
    Returns a sample of available user IDs.
    Use these IDs in POST /generate-review requests.
    """
    ids = list_user_ids(limit=limit)
    if not ids:
        raise HTTPException(
            status_code=503,
            detail="User profiles not loaded. Run notebooks/build_data.py first."
        )
    return {"user_ids": ids, "count": len(ids)}


@app.get("/users/{user_id}", tags=["System"])
def get_user(user_id: str):
    """Returns the profile for a specific user ID."""
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' not found in profiles."
        )
    return profile


@app.post("/generate-review", response_model=ReviewResponse, tags=["Task A"])
def generate_review_endpoint(request: ReviewRequest):
    """
    ## Generate a Personalised Review

    Simulates how a specific user would review an item, based on their
    historical review patterns (tone, length, vocabulary, rating behaviour).

    All outputs are contextualised in **Nigerian English** for cultural relevance.

    ### Returns
    - **review_text**: The generated review in the user's style
    - **star_rating**: Predicted star rating (1.0 – 5.0)
    - **confidence**: How well the item matches the user's taste (0.0 – 1.0)
    - **user_style_matched**: Whether the user's profile was found and applied
    - **user_found**: Whether the user_id exists in the profiles dataset
    """
    try:
        result = generate_review(
            user_id=request.user_id,
            item_name=request.item_name,
            item_category=request.item_category,
            item_description=request.item_description,
            price_range=request.price_range,
        )
        return result

    except RuntimeError as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Endpoint not found."})


@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error."})


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
