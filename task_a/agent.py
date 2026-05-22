"""
Task A — User Modeling Agent
Two-step approach:
  Step 1 → Gemini writes the review as plain text (no JSON = no parse errors)
  Step 2 → Gemini predicts the star rating as a single number
We assemble the final JSON ourselves.
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT          = Path(__file__).resolve().parent.parent
DATA_DIR      = ROOT / "data"
PROFILES_PATH = DATA_DIR / "user_profiles.json"

# ── Gemini setup ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set. Add it to your .env file.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name=GEMINI_MODEL)

# Generation config for review text — disable thinking to save tokens
def _make_gen_config(temperature: float, max_tokens: int) -> genai.GenerationConfig:
    """Build generation config, disabling thinking if the SDK supports it."""
    # Try the ThinkingConfig class (newer SDK versions)
    try:
        return genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config=genai.types.ThinkingConfig(thinking_budget=0),
        )
    except Exception:
        pass
    # Try as a plain dict
    try:
        return genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            thinking_config={"thinking_budget": 0},
        )
    except Exception:
        pass
    # Fallback — no thinking config
    return genai.GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)

REVIEW_GEN_CONFIG = _make_gen_config(temperature=0.9, max_tokens=3000)

# ── Load user profiles once at startup ────────────────────────────────────────
_USER_PROFILES: dict = {}

def _load_profiles() -> dict:
    global _USER_PROFILES
    if _USER_PROFILES:
        return _USER_PROFILES
    if not PROFILES_PATH.exists():
        logger.warning(
            f"user_profiles.json not found at {PROFILES_PATH}. "
            "Run notebooks/build_data.py first."
        )
        return {}
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        profiles = json.load(f)
    _USER_PROFILES = {p["user_id"]: p for p in profiles}
    logger.info(f"Loaded {len(_USER_PROFILES):,} user profiles.")
    return _USER_PROFILES


def get_user_profile(user_id: str) -> Optional[dict]:
    return _load_profiles().get(user_id)


def list_user_ids(limit: int = 50) -> list:
    return list(_load_profiles().keys())[:limit]


# ── Prompt 1: plain-text review ───────────────────────────────────────────────
def _review_prompt(profile: dict, item_name: str, item_category: str,
                   item_description: str, price_range: str) -> str:

    sentiment_map = {
        "positive_heavy": "mostly positive, enthusiastic, and encouraging",
        "balanced":       "balanced — fair with both pros and cons",
        "critical":       "critical and demanding, quick to point out flaws",
    }
    length_map = {
        "short":  "1–2 short sentences (under 80 words)",
        "medium": "3–4 sentences (80–200 words)",
        "long":   "a full paragraph (200–350 words)",
    }

    return f"""You are a Nigerian user writing a review online.

USER PROFILE:
- Review history: {profile['review_count']} reviews, average rating {profile['avg_rating']:.1f}/5
- Writing style: {sentiment_map.get(profile['sentiment_style'], 'balanced')}
- Review length: {length_map.get(profile['typical_length'], '3–4 sentences')}
- Words they often use: {', '.join(profile.get('common_words', [])[:8])}

ITEM:
- Name: {item_name}
- Category: {item_category}
- Description: {item_description}
- Price: {price_range}

Write the review now. Rules:
- Write in Nigerian English (Naija Pidgin). Use these expressions naturally — do NOT force all of them in:
  * "I no go lie" (I won't lie) — NOT "e no go lie"
  * "abeg" (please / I'm telling you)
  * "chai!" (expression of surprise or feeling)
  * "omo" (expression of emphasis)
  * "na wa o" (that's something / wow)
  * "e dey sweet" (it tastes/feels good)
  * "no be small thing" (it's no joke / it's serious)
  * "sharp sharp" (quickly / immediately)
  * "correct" (genuine / authentic / good quality)
  * "na so e be" (that's how it is)
  * "wetin" (what)
  * "dem" (they / them)
  * "make you" (you should)
  * "e don do" (it's done / finished)
  * "waka come" (came all the way)
  * "for real for real" (seriously)
- Use ₦ (naira) not $ when mentioning price or value
- Match the user's length and tone exactly
- Do NOT start with the word "I"
- CRITICAL: Write a COMPLETE, fully-finished review. Every sentence must end properly.
  Do not stop in the middle of a thought. Your final sentence must be a proper conclusion.
- Output ONLY the review text. No title, no rating, no label, no extra commentary."""


# ── Local sentiment-based rating (no extra API call, no safety risks) ─────────
_POS_WORDS = {
    "great","good","love","excellent","amazing","fantastic","best","perfect",
    "wonderful","awesome","delicious","recommend","happy","enjoy","nice",
    "correct","sweet","sharp","top","fire","fresh","solid","quality","value",
    "satisfied","pleased","impressed","outstanding","superb","brilliant",
}
_NEG_WORDS = {
    "bad","terrible","awful","horrible","worst","poor","disappointing","hate",
    "disgusting","nasty","overpriced","slow","rude","dirty","cold","stale",
    "wrong","rubbish","trash","waste","never","avoid","mediocre","bland",
    "tasteless","dry","soggy","small","tiny","expensive","overrated",
}

def _sentiment_rating(review_text: str, avg_rating: float) -> float:
    """
    Estimate a star rating from review text sentiment.
    Adjusts the user's average rating up/down based on positive/negative words.
    """
    words = set(re.findall(r'[a-z]+', review_text.lower()))
    pos = len(words & _POS_WORDS)
    neg = len(words & _NEG_WORDS)
    total = pos + neg
    if total == 0:
        return round(avg_rating, 1)
    sentiment_score = (pos - neg) / total   # -1.0 to +1.0
    # Shift avg_rating by up to ±1.5 stars based on sentiment
    adjusted = avg_rating + (sentiment_score * 1.5)
    return round(min(5.0, max(1.0, adjusted)), 1)


# ── Safe response text accessor ───────────────────────────────────────────────
def _safe_text(response, fallback: str = "") -> str:
    """Return response text safely — logs finish reason, returns fallback if blocked."""
    try:
        # Log finish reason for every call so we can debug truncation
        if response.candidates:
            reason = response.candidates[0].finish_reason
            # 1=STOP (normal), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER
            reason_names = {1: "STOP", 2: "MAX_TOKENS", 3: "SAFETY",
                            4: "RECITATION", 5: "OTHER"}
            logger.info(f"Finish reason: {reason_names.get(reason, reason)}")
        return response.text.strip()
    except Exception:
        try:
            reason = response.candidates[0].finish_reason if response.candidates else "unknown"
            logger.warning(f"Response blocked/empty. Finish reason: {reason}")
        except Exception:
            logger.warning("Response blocked or empty.")
        return fallback


# ── Confidence heuristic ──────────────────────────────────────────────────────
def _compute_confidence(profile: dict, star_rating: float) -> float:
    """
    Higher confidence when the predicted rating is close to the user's average.
    Reflects how 'in-character' the generated review is.
    """
    diff = abs(star_rating - profile["avg_rating"])
    confidence = max(0.3, 1.0 - (diff / 4.0))
    return round(confidence, 2)


# ── Main agent function ───────────────────────────────────────────────────────
def generate_review(
    user_id: str,
    item_name: str,
    item_category: str,
    item_description: str,
    price_range: str,
) -> dict:
    """
    Generate a personalised Nigerian English review + star rating for an item.

    Returns:
        {
            "review_text": str,
            "star_rating": float (1.0–5.0),
            "confidence":  float (0.0–1.0),
            "user_style_matched": bool,
            "user_found": bool
        }
    """
    profile = get_user_profile(user_id)

    # ── Cold start ────────────────────────────────────────────────────────────
    if profile is None:
        logger.info(f"User '{user_id}' not in profiles — cold-start fallback.")
        profile = {
            "user_id": user_id,
            "avg_rating": 3.5,
            "review_count": 0,
            "common_words": [],
            "sentiment_style": "balanced",
            "typical_length": "medium",
            "source_dataset": "unknown",
        }
        user_found = False
    else:
        user_found = True

    try:
        # ── Step 1: Generate review text (plain text, no JSON) ────────────────
        review_resp = model.generate_content(
            _review_prompt(profile, item_name, item_category,
                           item_description, price_range),
            generation_config=REVIEW_GEN_CONFIG,
        )
        review_text = _safe_text(review_resp, fallback="No review generated.")

        # Clean up any accidental JSON wrappers the model might add
        if review_text.startswith("{") and "review_text" in review_text:
            try:
                parsed = json.loads(review_text)
                review_text = parsed.get("review_text", review_text)
            except Exception:
                m = re.search(r'"review_text"\s*:\s*"(.*?)"(?:\s*,|\s*})',
                              review_text, re.DOTALL)
                if m:
                    review_text = m.group(1).replace('\\"', '"').replace('\\n', '\n')

        # ── Step 2: Rate from sentiment (local, instant, no safety blocks) ────
        star_rating = _sentiment_rating(review_text, profile["avg_rating"])
        confidence  = _compute_confidence(profile, star_rating)

        logger.info(f"Generated review for {user_id} | rating={star_rating} | "
                    f"confidence={confidence}")

        return {
            "review_text":        review_text,
            "star_rating":        star_rating,
            "confidence":         confidence,
            "user_style_matched": user_found,
            "user_found":         user_found,
        }

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise RuntimeError(f"Review generation failed: {e}") from e


# ── Quick local test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    profiles = _load_profiles()
    if not profiles:
        print("No profiles loaded. Run build_data.py first.")
    else:
        test_uid = list(profiles.keys())[0]
        print(f"Testing with user: {test_uid}\n")
        result = generate_review(
            user_id=test_uid,
            item_name="Chicken Republic Streetburger",
            item_category="Restaurant",
            item_description="Crispy fried chicken burger with coleslaw and spicy sauce",
            price_range="₦2,500 – ₦4,000",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
