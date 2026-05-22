"""
Standalone version of eda.ipynb — run this if you don't want to use Jupyter.
Usage:  python notebooks/build_data.py
"""
import os
import json
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from datasets import load_dataset
from tqdm.auto import tqdm

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

COMBINED_PATH = DATA_DIR / "combined_sample.json"
PROFILES_PATH = DATA_DIR / "user_profiles.json"

YELP_LIMIT      = int(os.getenv("YELP_SAMPLE_SIZE", 5000))
AMAZON_LIMIT    = int(os.getenv("AMAZON_SAMPLE_SIZE", 3000))
GOODREADS_LIMIT = int(os.getenv("GOODREADS_SAMPLE_SIZE", 2000))
MIN_REVIEWS     = int(os.getenv("MIN_REVIEWS_FOR_PROFILE", 3))

STOPWORDS = {
    'the','a','an','and','or','but','in','on','at','to','for','of','with',
    'is','was','it','this','that','i','my','me','we','our','you','your',
    'they','their','be','been','have','had','do','did','not','no','so',
    'just','very','really','also','are','from','by','as','up','out',
    'get','got','all','more','would','could','should','will','what',
    'if','he','she','his','her','its','there','here','about','one',
    'has','were','which','than','then','when','who','how','much','any'
}


def clean_text(text):
    if not text:
        return ""
    text = str(text).strip()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def top_words(text, n=10):
    words = re.findall(r'[a-z]+', text.lower())
    filtered = [w for w in words if w not in STOPWORDS and len(w) > 2]
    return [w for w, _ in Counter(filtered).most_common(n)]


def sentiment_style(avg_rating):
    if avg_rating >= 4.0:
        return "positive_heavy"
    elif avg_rating <= 2.5:
        return "critical"
    return "balanced"


def review_length_bucket(avg_len):
    if avg_len < 100:
        return "short"
    elif avg_len < 300:
        return "medium"
    return "long"


def stream_yelp():
    print("Streaming Yelp dataset...")
    records = []
    categories = [
        "Restaurant", "Cafe", "Bar", "Hotel", "Salon",
        "Gym", "Retail", "Entertainment", "Healthcare", "Services"
    ]
    ds = load_dataset("Yelp/yelp_review_full", split="train", streaming=True)
    for i, row in enumerate(tqdm(ds, total=YELP_LIMIT, desc="Yelp")):
        if i >= YELP_LIMIT:
            break
        text = clean_text(row.get("text", ""))
        if not text:
            continue
        records.append({
            "user_id": f"yelp_user_{i % 1000:04d}",
            "rating": float(row["label"] + 1),
            "review_text": text,
            "item_name": f"Yelp_Business_{i}",
            "item_category": categories[i % len(categories)],
            "source_dataset": "yelp"
        })
    print(f"Collected {len(records):,} Yelp records")
    return records


def stream_amazon():
    print("Streaming Amazon Food dataset...")
    records = []
    categories = [
        "Snacks", "Beverages", "Condiments", "Baking", "Breakfast",
        "Canned Goods", "Dairy", "Frozen Food", "Organic", "Gourmet"
    ]
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Grocery_and_Gourmet_Food",
        split="full",
        streaming=True,
        trust_remote_code=True
    )
    for i, row in enumerate(tqdm(ds, total=AMAZON_LIMIT, desc="Amazon")):
        if i >= AMAZON_LIMIT:
            break
        text = clean_text(row.get("text", ""))
        if not text:
            continue
        rating = float(row.get("rating", 3.0))
        if not (1.0 <= rating <= 5.0):
            rating = 3.0
        user_id = str(row.get("user_id", f"amz_user_{i:04d}"))
        records.append({
            "user_id": f"amazon_{user_id[:20]}",
            "rating": rating,
            "review_text": text,
            "item_name": clean_text(str(row.get("title", f"Amazon_Product_{i}")))[:120],
            "item_category": categories[i % len(categories)],
            "source_dataset": "amazon"
        })
    print(f"Collected {len(records):,} Amazon records")
    return records


def stream_goodreads():
    # mayank-mishra/goodreads was removed from HuggingFace Hub.
    # Replacement: McAuley-Lab Amazon Books reviews — same book-review domain,
    # confirmed available, labelled "goodreads" to keep the unified schema consistent.
    print("Streaming Books dataset (Amazon Books reviews, goodreads-equivalent)...")
    records = []
    categories = [
        "Fiction", "Non-Fiction", "Mystery", "Fantasy", "Science Fiction",
        "Romance", "Biography", "History", "Self-Help", "Thriller"
    ]
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        "raw_review_Books",
        split="full",
        streaming=True,
        trust_remote_code=True
    )
    for i, row in enumerate(tqdm(ds, total=GOODREADS_LIMIT, desc="Books")):
        if i >= GOODREADS_LIMIT:
            break
        text = clean_text(row.get("text", ""))
        if not text:
            continue
        rating = float(row.get("rating", 3.0))
        rating = min(5.0, max(1.0, rating))
        user_id = str(row.get("user_id", f"gr_user_{i:04d}"))
        book_title = clean_text(str(row.get("title", f"Book_{i}")))[:120]
        records.append({
            "user_id": f"gr_{user_id[:20]}",
            "rating": rating,
            "review_text": text,
            "item_name": book_title,
            "item_category": categories[i % len(categories)],
            "source_dataset": "goodreads"
        })
    print(f"Collected {len(records):,} Goodreads records")
    return records


def build_profiles(all_records):
    print("Building user profiles...")
    user_data = defaultdict(lambda: {"ratings": [], "texts": [], "source_dataset": None})
    for rec in all_records:
        uid = rec["user_id"]
        user_data[uid]["ratings"].append(rec["rating"])
        user_data[uid]["texts"].append(rec["review_text"])
        user_data[uid]["source_dataset"] = rec["source_dataset"]

    profiles = []
    skipped = 0
    for uid, data in tqdm(user_data.items(), desc="Profiling users"):
        if len(data["ratings"]) < MIN_REVIEWS:
            skipped += 1
            continue
        avg_rating = round(float(np.mean(data["ratings"])), 2)
        combined_text = " ".join(data["texts"])
        avg_len = float(np.mean([len(t) for t in data["texts"]]))
        profiles.append({
            "user_id": uid,
            "avg_rating": avg_rating,
            "review_count": len(data["ratings"]),
            "common_words": top_words(combined_text, n=10),
            "sentiment_style": sentiment_style(avg_rating),
            "typical_length": review_length_bucket(avg_len),
            "avg_review_length": round(avg_len, 1),
            "source_dataset": data["source_dataset"]
        })
    print(f"Profiles built: {len(profiles):,}  (skipped {skipped:,} with < {MIN_REVIEWS} reviews)")
    return profiles


def print_stats(all_records, profiles):
    df = pd.DataFrame(all_records)
    df["review_length"] = df["review_text"].str.len()
    print("\n" + "=" * 50)
    print("SUMMARY STATS")
    print("=" * 50)
    print(f"  Total records:    {len(df):,}")
    print(f"  Total profiles:   {len(profiles):,}")
    print(f"  Mean rating:      {df['rating'].mean():.2f}")
    print(f"  Mean review len:  {df['review_length'].mean():.0f} chars")
    print("\nRecords by source:")
    for src, count in df["source_dataset"].value_counts().items():
        print(f"  {src:<15} {count:,}")


if __name__ == "__main__":
    print(f"Data dir: {DATA_DIR.resolve()}\n")

    yelp      = stream_yelp()
    amazon    = stream_amazon()
    goodreads = stream_goodreads()

    all_records = yelp + amazon + goodreads

    with open(COMBINED_PATH, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    print(f"\nSaved combined_sample.json  ({COMBINED_PATH.stat().st_size / 1e6:.1f} MB)")

    profiles = build_profiles(all_records)

    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, ensure_ascii=False, indent=2)
    print(f"Saved user_profiles.json    ({PROFILES_PATH.stat().st_size / 1e6:.1f} MB)")

    print_stats(all_records, profiles)
    print("\nDone. Ready for Step 4 (Task A) and Step 5 (Task B).")
