"""
Task B — Personalised Recommendation Agent
Pipeline:
  1. REASONING  — LLM summarises what the user needs from their profile + history
  2. RETRIEVAL  — FAISS finds top-20 candidates by embedding similarity
  3. RERANKING  — LLM reranks top-20 into final top-K with Nigerian English explanations
  4. COLD-START — falls back to item-metadata similarity when user has no history
"""

import os
import json
import re
import logging
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT             = Path(__file__).resolve().parent.parent
DATA_DIR         = ROOT / "data"
COMBINED_PATH    = DATA_DIR / "combined_sample.json"
PROFILES_PATH    = DATA_DIR / "user_profiles.json"
FAISS_INDEX_PATH  = DATA_DIR / "faiss_index.pkl"
# Local path for sentence-transformer model (downloaded via PowerShell)
ST_MODEL_PATH     = DATA_DIR / "all-MiniLM-L6-v2"

# ── Gemini setup ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not set. Add it to your .env file.")

genai.configure(api_key=GEMINI_API_KEY)
llm = genai.GenerativeModel(model_name=GEMINI_MODEL)

def _make_gen_config(temperature: float, max_tokens: int) -> genai.GenerationConfig:
    for kwargs in [
        {"temperature": temperature, "max_output_tokens": max_tokens,
         "thinking_config": {"thinking_budget": 0}},
        {"temperature": temperature, "max_output_tokens": max_tokens},
    ]:
        try:
            return genai.GenerationConfig(**kwargs)
        except Exception:
            continue
    return genai.GenerationConfig(temperature=temperature,
                                  max_output_tokens=max_tokens)

REASON_CFG  = _make_gen_config(temperature=0.3, max_tokens=256)
RERANK_CFG  = _make_gen_config(temperature=0.5, max_tokens=4000)


# ── Safe LLM caller ───────────────────────────────────────────────────────────
def _llm_call(prompt: str, config: genai.GenerationConfig) -> str:
    try:
        resp = llm.generate_content(prompt, generation_config=config)
        return resp.text.strip()
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return ""


# ── Data & index loading (lazy, loaded once) ──────────────────────────────────
_RECORDS:    list = []
_PROFILES:   dict = {}
_INDEX             = None   # faiss index
_EMBEDDINGS        = None   # np.ndarray (N, dim)
_ITEM_TEXTS: list  = []     # parallel to _RECORDS
_ST_ENCODER        = None   # cached SentenceTransformer (loaded once)


def _load_data():
    global _RECORDS, _PROFILES
    if _RECORDS:
        return

    if not COMBINED_PATH.exists():
        raise FileNotFoundError(
            f"combined_sample.json not found at {COMBINED_PATH}. "
            "Run notebooks/build_data.py first."
        )
    with open(COMBINED_PATH, "r", encoding="utf-8") as f:
        _RECORDS = json.load(f)

    if not PROFILES_PATH.exists():
        logger.warning("user_profiles.json not found. Cold-start only.")
    else:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        _PROFILES = {p["user_id"]: p for p in profiles}

    logger.info(f"Loaded {len(_RECORDS):,} records, {len(_PROFILES):,} profiles.")


def _build_or_load_index():
    """
    Build retrieval index from item texts, or load from cache.
    Primary:  sentence-transformers + FAISS (neural embeddings)
    Fallback: TF-IDF + cosine similarity (offline, no download needed)
    """
    global _INDEX, _EMBEDDINGS, _ITEM_TEXTS

    if _INDEX is not None:
        return

    _load_data()

    # ── Try loading cached index ──────────────────────────────────────────────
    if FAISS_INDEX_PATH.exists():
        logger.info("Loading cached retrieval index...")
        with open(FAISS_INDEX_PATH, "rb") as f:
            cache = pickle.load(f)
        _INDEX      = cache["index"]
        _EMBEDDINGS = cache["embeddings"]
        _ITEM_TEXTS = cache["item_texts"]
        logger.info(f"Loaded index ({cache.get('method','unknown')} method).")
        return

    _load_data()

    # Build item text corpus
    _ITEM_TEXTS = [
        f"{r['item_name']} {r['item_category']} {r['review_text'][:200]}"
        for r in _RECORDS
    ]

    # ── Try sentence-transformers + FAISS (neural) ────────────────────────────
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        logger.info("Building FAISS index with sentence-transformers...")
        global _ST_ENCODER
        if _ST_ENCODER is None:
            _ST_ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
        encoder = _ST_ENCODER
        _EMBEDDINGS = encoder.encode(
            _ITEM_TEXTS,
            batch_size=256,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")
        dim    = _EMBEDDINGS.shape[1]
        _INDEX = faiss.IndexFlatIP(dim)
        _INDEX.add(_EMBEDDINGS)
        method = "sentence-transformers+faiss"
        logger.info(f"Neural FAISS index built. {_INDEX.ntotal:,} vectors.")

    except Exception as e:
        # ── Fallback: TF-IDF + cosine (offline, no download) ─────────────────
        logger.warning(f"sentence-transformers unavailable ({e}). "
                       "Falling back to TF-IDF retrieval.")
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english",
        )
        _EMBEDDINGS = vectorizer.fit_transform(_ITEM_TEXTS)   # sparse matrix
        _INDEX      = vectorizer   # store vectorizer as "index" for query time
        method      = "tfidf"
        logger.info(f"TF-IDF index built. {_EMBEDDINGS.shape[0]:,} documents, "
                    f"{_EMBEDDINGS.shape[1]:,} features.")

    # Cache to disk
    with open(FAISS_INDEX_PATH, "wb") as f:
        pickle.dump({
            "index":      _INDEX,
            "embeddings": _EMBEDDINGS,
            "item_texts": _ITEM_TEXTS,
            "method":     method,
        }, f)
    logger.info(f"Index saved to {FAISS_INDEX_PATH}.")


# ── Step 1: Reasoning — generate user need summary ───────────────────────────
def _reason_user_needs(profile: Optional[dict],
                       conversation_history: list) -> str:
    if profile is None and not conversation_history:
        return "general popular items across all categories"

    history_text = ""
    if conversation_history:
        history_text = "\n".join(
            f"- {m.get('role','user')}: {m.get('content','')}"
            for m in conversation_history[-6:]   # last 6 turns
        )

    profile_text = ""
    if profile:
        profile_text = f"""
User profile:
- Avg rating: {profile['avg_rating']}/5
- Style: {profile['sentiment_style']}
- Common words: {', '.join(profile.get('common_words', [])[:8])}
- Source platform: {profile['source_dataset']}"""

    prompt = f"""You are a recommendation engine reasoning about what a user needs.
{profile_text}

Recent conversation:
{history_text if history_text else "No conversation history."}

In 2-3 sentences, summarise what this user is looking for and what kind of items
would satisfy them. Be specific about qualities (e.g. "spicy food", "fast-paced thrillers",
"budget-friendly snacks"). Do not recommend specific items — just describe the need."""

    result = _llm_call(prompt, REASON_CFG)
    return result if result else "items matching the user's general taste preferences"


# ── Step 2: Retrieval (FAISS or TF-IDF) ──────────────────────────────────────
def _retrieve_candidates(need_summary: str, top_k: int = 20) -> list:
    """Retrieve top-k candidates using whichever backend was built."""
    _build_or_load_index()

    # ── FAISS (neural) path ───────────────────────────────────────────────────
    try:
        import faiss
        if hasattr(_INDEX, "search"):   # it's a real FAISS index
            from sentence_transformers import SentenceTransformer
            global _ST_ENCODER
            if _ST_ENCODER is None:
                _ST_ENCODER = SentenceTransformer("all-MiniLM-L6-v2")
            encoder = _ST_ENCODER
            query_vec = encoder.encode(
                [need_summary],
                normalize_embeddings=True,
                convert_to_numpy=True,
            ).astype("float32")
            scores, indices = _INDEX.search(query_vec, top_k)
            candidates = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(_RECORDS):
                    continue
                rec = _RECORDS[idx]
                candidates.append({
                    "item_name":      rec["item_name"],
                    "item_category":  rec["item_category"],
                    "source":         rec["source_dataset"],
                    "rating":         rec["rating"],
                    "review_snippet": rec["review_text"][:150],
                    "faiss_score":    float(score),
                })
            return candidates
    except Exception:
        pass

    # ── TF-IDF (offline) path ─────────────────────────────────────────────────
    from sklearn.metrics.pairwise import cosine_similarity
    query_vec = _INDEX.transform([need_summary])   # _INDEX is the TF-IDF vectorizer
    sims      = cosine_similarity(query_vec, _EMBEDDINGS).flatten()
    top_idx   = np.argsort(sims)[::-1][:top_k]

    candidates = []
    for idx in top_idx:
        rec = _RECORDS[idx]
        candidates.append({
            "item_name":      rec["item_name"],
            "item_category":  rec["item_category"],
            "source":         rec["source_dataset"],
            "rating":         rec["rating"],
            "review_snippet": rec["review_text"][:150],
            "faiss_score":    float(sims[idx]),
        })
    return candidates


# ── Step 3: LLM reranking with Nigerian English explanations ──────────────────
def _rerank(candidates: list, need_summary: str,
            profile: Optional[dict], top_k: int) -> list:
    if not candidates:
        return []

    items_text = "\n".join(
        f"{i+1}. [{c['item_category']}] {c['item_name']} "
        f"(rated {c['rating']}/5, from {c['source']}) — \"{c['review_snippet']}\""
        for i, c in enumerate(candidates)
    )

    profile_line = ""
    if profile:
        profile_line = (f"The user typically rates {profile['avg_rating']}/5 "
                        f"and writes {profile['sentiment_style']} reviews.")

    # Cap rerank to 5 items to stay within token budget
    rerank_k = min(top_k, 5)
    # Pass top 15 candidates to reranker (more candidates = better recall)
    candidates_subset = candidates[:15]
    items_text = "\n".join(
        f"{i+1}. [{c['item_category']}] {c['item_name']} "
        f"(rated {c['rating']}/5, from {c['source']})"
        for i, c in enumerate(candidates_subset)
    )


    prompt = f"""Nigerian recommendation assistant. Pick best {rerank_k} items for this user.

User need: {need_summary}
{profile_line}

Candidates (numbered list — use the EXACT names as shown):
{items_text}

CRITICAL RULE: In the NAME field you MUST copy the item name CHARACTER FOR CHARACTER from the candidates list above. Do NOT rephrase, summarise, or invent a new name. If the name is "Yelp_Business_42" write exactly "Yelp_Business_42". If it is "Amazing taste!" write exactly "Amazing taste!".

Output {rerank_k} items in this exact format:
RANK: 1
NAME: [copy exact name from candidates]
CAT: [category]
SCORE: [0.0-1.0]
SOURCE: [source]
WHY: [1 sentence Nigerian Pidgin why this fits]
---
RANK: 2
NAME: [copy exact name from candidates]
CAT: [category]
SCORE: [0.0-1.0]
SOURCE: [source]
WHY: [1 sentence Nigerian Pidgin why this fits]
---

WHY examples: "Omo this one go sweet you!", "I no go lie e correct for your taste", "Abeg try am, e dey align with wetin you like"
Output only the blocks above, nothing else."""

    raw = _llm_call(prompt, RERANK_CFG)

    # ── Parse line-by-line format ─────────────────────────────────────────────
    ranked = []
    for block in raw.split("---"):
        block = block.strip()
        if not block:
            continue
        item = {}
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("RANK:"):
                try:
                    item["rank"] = int(line.split(":", 1)[1].strip())
                except Exception:
                    pass
            elif line.startswith("NAME:"):
                item["item_name"] = line.split(":", 1)[1].strip()
            elif line.startswith("CAT:"):
                item["category"] = line.split(":", 1)[1].strip()
            elif line.startswith("SCORE:"):
                try:
                    item["score"] = round(float(line.split(":", 1)[1].strip()), 3)
                except Exception:
                    item["score"] = 0.5
            elif line.startswith("SOURCE:"):
                item["source"] = line.split(":", 1)[1].strip()
            elif line.startswith("WHY:"):
                item["explanation"] = line.split(":", 1)[1].strip()

        if "item_name" in item and "explanation" in item:
            item.setdefault("rank",     len(ranked) + 1)
            item.setdefault("category", "General")
            item.setdefault("score",    0.5)
            item.setdefault("source",   "unknown")
            ranked.append(item)

    if ranked:
        logger.info(f"Parsed {len(ranked)} items from reranker.")
        return ranked[:rerank_k]

    # ── Hard fallback ─────────────────────────────────────────────────────────
    logger.warning("Reranker returned no parseable items — using FAISS order.")
    pidgin_phrases = [
        "Omo, this one go suit you well well based on your taste!",
        "Abeg try this one, e dey align with wetin you dey look for.",
        "I no go lie, this one na correct match for person like you.",
        "Chai! This one fit your style well well, make you check am out.",
        "Based on your history, this one go do you good, trust me.",
    ]
    return [
        {
            "rank":        i + 1,
            "item_name":   c["item_name"],
            "category":    c["item_category"],
            "score":       round(c["faiss_score"], 3),
            "explanation": pidgin_phrases[i % len(pidgin_phrases)],
            "source":      c["source"],
        }
        for i, c in enumerate(candidates[:top_k])
    ]


# ── Main recommendation function ──────────────────────────────────────────────
def recommend(
    user_id: str,
    conversation_history: Optional[list] = None,
    top_k: int = 10,
) -> dict:
    """
    Generate personalised recommendations for a user.

    Returns:
        {
            "recommendations": [...],
            "user_need_summary": str,
            "is_cold_start": bool
        }
    """
    _load_data()

    if conversation_history is None:
        conversation_history = []

    profile = _PROFILES.get(user_id)
    is_cold_start = profile is None

    if is_cold_start:
        logger.info(f"Cold-start: user '{user_id}' not found in profiles.")

    # Step 1 — Reasoning
    need_summary = _reason_user_needs(profile, conversation_history)
    logger.info(f"Need summary: {need_summary[:100]}...")

    # Step 2 — FAISS retrieval
    # Use the user's actual review texts as the retrieval signal — this grounds
    # the search in what the user has genuinely experienced rather than a
    # generic LLM-generated description, improving recall of relevant items.
    user_reviews = [r for r in _RECORDS if r["user_id"] == user_id]
    if len(user_reviews) >= 2:
        # Prefer high-rated reviews as positive signal
        pos_reviews = [r for r in user_reviews if r["rating"] >= 4]
        if not pos_reviews:
            pos_reviews = user_reviews
        # Concatenate up to 5 recent positive review snippets
        review_query = " ".join(r["review_text"][:100] for r in pos_reviews[-5:])
        candidates = _retrieve_candidates(review_query, top_k=50)
        logger.info(f"Retrieved {len(candidates)} FAISS candidates (review-text query).")
    else:
        candidates = _retrieve_candidates(need_summary, top_k=20)
        logger.info(f"Retrieved {len(candidates)} FAISS candidates (need-summary query).")

    # Step 3 — LLM reranking
    recommendations = _rerank(candidates, need_summary, profile, top_k)
    logger.info(f"Returning {len(recommendations)} recommendations.")

    return {
        "recommendations":  recommendations,
        "user_need_summary": need_summary,
        "is_cold_start":    is_cold_start,
    }


# ── Cold-start by category/description ───────────────────────────────────────
def recommend_cold_start(
    item_category: str,
    description_of_what_i_want: str,
    top_k: int = 10,
) -> dict:
    """
    Recommend items for a brand-new user with no history.
    Uses category + description as the search query directly.
    """
    need_summary = (
        f"User wants {item_category} items. "
        f"Specifically: {description_of_what_i_want}"
    )

    candidates = _retrieve_candidates(need_summary, top_k=20)
    # Filter to matching category if possible
    cat_matches = [c for c in candidates
                   if c["item_category"].lower() == item_category.lower()]
    if len(cat_matches) >= 5:
        candidates = cat_matches

    recommendations = _rerank(candidates, need_summary, profile=None, top_k=top_k)

    return {
        "recommendations":   recommendations,
        "user_need_summary": need_summary,
        "is_cold_start":     True,
    }


# ── Quick local test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Building index and testing recommendation...")
    result = recommend(
        user_id="yelp_user_0001",
        conversation_history=[],
        top_k=5,
    )
    print("\nUser need summary:")
    print(" ", result["user_need_summary"])
    print(f"\nCold start: {result['is_cold_start']}")
    print(f"\nTop {len(result['recommendations'])} recommendations:")
    for r in result["recommendations"]:
        print(f"\n  [{r.get('rank','?')}] {r.get('item_name','?')}")
        print(f"       Category : {r.get('category','?')}")
        print(f"       Score    : {r.get('score','?')}")
        print(f"       Source   : {r.get('source','?')}")
        print(f"       Why      : {r.get('explanation','?')}")
