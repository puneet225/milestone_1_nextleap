"""
data_loader.py — Data Layer (CTO Pass: Decoupled)

Loads the Zomato dataset once at startup, cleans it,
caches a Pandas DataFrame, and exposes filter/lookup functions.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)

# Official HuggingFace Raw CSV URL for fallback
ZOMATO_CSV_URL = "https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation/resolve/main/zomato.csv"
LOCAL_CSV_PATH = os.path.join(os.path.dirname(__file__), "zomato.csv")
LOCAL_PARQUET_PATH = os.path.join(os.path.dirname(__file__), "zomato.parquet")

# ---------------------------------------------------------------------------
# Column-name mapping from HuggingFace dataset candidates (raw CSV strings)
# ---------------------------------------------------------------------------
_FIELD_CANDIDATES: dict[str, list[str]] = {
    "name":             ["name", "restaurant_name", "Name"],
    "location":         ["location", "Location", "neighbourhood", "area"],
    "cuisines":         ["cuisines", "Cuisines", "cuisine", "cuisine_type"],
    "cost_for_two":     ["cost_for_two", "approx_cost(for two people)", "average_cost_for_two", "cost"],
    "aggregate_rating": ["aggregate_rating", "rate", "rating", "Rating"],
    "votes":            ["votes", "Votes"],
    "online_order":     ["online_order", "online_ordering"],
    "book_table":       ["book_table", "table_booking"],
    "rest_type":        ["rest_type", "restaurant_type", "type"],
    "url":              ["url", "restaurant_url", "link"],
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pick_column(df: pd.DataFrame, canonical: str, candidates: list[str]) -> str | None:
    """Return the first column name that exists in df for a given canonical key."""
    for c in candidates:
        if c in df.columns:
            return c
    logger.warning("Column '%s' not found in dataset. Tried: %s", canonical, candidates)
    return None


def _load_and_clean() -> pd.DataFrame:
    """Load the dataset (Parquet preferred, CSV fallback), rename columns, clean nulls, and optimize memory."""
    logger.info("CTO: Optimized loading starting...")
    
    # 1. Loading Logic (Parquet -> CSV -> URL)
    if os.path.exists(LOCAL_PARQUET_PATH):
        logger.info("Loading from optimized Parquet cache: %s", LOCAL_PARQUET_PATH)
        df = pd.read_parquet(LOCAL_PARQUET_PATH)
        # Verify columns are present (parquet already has rename/cleaning applied usually)
    else:
        if os.path.exists(LOCAL_CSV_PATH):
            logger.info("Loading from local CSV cache: %s", LOCAL_CSV_PATH)
            raw = pd.read_csv(LOCAL_CSV_PATH, low_memory=False)
        else:
            logger.info("No local data found. Attempting to download CSV: %s", ZOMATO_CSV_URL)
            try:
                raw = pd.read_csv(ZOMATO_CSV_URL, low_memory=False)
                # Cache it locally for next time
                raw.to_csv(LOCAL_CSV_PATH, index=False)
                logger.info("Successfully fetched and cached raw dataset.")
            except Exception as e:
                logger.error("Failed to fetch dataset: %s", e)
                raise RuntimeError(f"Could not load restaurant dataset. Please provide zomato.csv or zomato.parquet in {LOCAL_CSV_PATH}") from e

        # Standard Cleaning from CSV
        logger.info("Raw dataset shape: %s  |  Columns: %s", raw.shape, list(raw.columns))

        # Build rename map
        rename_map: dict[str, str] = {}
        for canonical, candidates in _FIELD_CANDIDATES.items():
            found = _pick_column(raw, canonical, candidates)
            if found:
                rename_map[found] = canonical
        
        if "dish_liked" in raw.columns: rename_map["dish_liked"] = "dish_liked"
        if "reviews_list" in raw.columns: rename_map["reviews_list"] = "reviews_list"

        df = raw.rename(columns=rename_map)
        keep = [c for c in list(_FIELD_CANDIDATES.keys()) + ["dish_liked", "reviews_list"] if c in df.columns]
        df = df[keep].copy()

        # ---- Cleaning Functions ----
        def clean_cost(x):
            try: return float(str(x).replace(",", ""))
            except: return 0.0

        def clean_rating(x):
            try: return float(str(x).split("/")[0]) if "/" in str(x) else float(x)
            except: return 0.0

        def parse_reviews(rev_str):
            if not rev_str or rev_str == "[]": return ""
            try:
                import ast
                reviews = ast.literal_eval(rev_str)
                comments = []
                for _, r_text in reviews[:3]:
                    clean_t = r_text.replace("RATED\n", "").replace("\n", " ").strip()
                    if clean_t: comments.append(clean_t)
                return " | ".join(comments)
            except: return ""

        if "cost_for_two" in df.columns:
            df["cost_for_two"] = df["cost_for_two"].apply(clean_cost)
        if "aggregate_rating" in df.columns:
            df["aggregate_rating"] = df["aggregate_rating"].apply(clean_rating)
        if "reviews_list" in df.columns:
            df["reviews_list"] = df["reviews_list"].apply(parse_reviews)
        if "votes" in df.columns:
            df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

        # Drop duplicates and nulls
        df = df.drop_duplicates(subset=["name", "location"])
        critical = [c for c in ["name", "location", "cost_for_two", "aggregate_rating"] if c in df.columns]
        df = df.dropna(subset=critical)

        # Normalise strings
        for col in ["name", "location", "cuisines", "rest_type", "url"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        if "location" in df.columns:
            df["location"] = df["location"].str.title()

        # Save to Parquet for next time
        logger.info("Auto-generating Parquet cache for future performance...")
        df.to_parquet(LOCAL_PARQUET_PATH, index=False)

    # 2. Memory Optimizations (Every load)
    # Truncate reviews to save significant RAM
    if "reviews_list" in df.columns:
        df["reviews_list"] = df["reviews_list"].str[:500]

    # Downcast numeric types
    if "cost_for_two" in df.columns:
        df["cost_for_two"] = df["cost_for_two"].astype("float32")
    if "aggregate_rating" in df.columns:
        df["aggregate_rating"] = df["aggregate_rating"].astype("float32")
    if "votes" in df.columns:
        df["votes"] = df["votes"].astype("int32")

    # Category types for low-cardinality strings
    for col in ["location", "cuisines", "rest_type", "online_order", "book_table"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    logger.info("Dataset ready. Final Shape: %s | Memory Usage: %.2f MB", 
                df.shape, df.memory_usage(deep=True).sum() / 1024**2)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Module-level singleton — loaded once on first import / startup
# ---------------------------------------------------------------------------
_df: pd.DataFrame | None = None


def get_dataframe() -> pd.DataFrame:
    """Return the cached DataFrame, loading it if necessary."""
    global _df
    if _df is None:
        _df = _load_and_clean()
    return _df


def preload() -> None:
    """Call at application startup to warm the cache."""
    get_dataframe()
    logger.info("Dataset pre-loaded and cached.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_unique_locations() -> list[str]:
    """Return a sorted list of unique neighbourhood/location names."""
    df = get_dataframe()
    if "location" not in df.columns:
        return []
    # If categorical, use .categories
    if hasattr(df["location"], "cat"):
        return sorted(df["location"].cat.categories.tolist())
    return sorted(df["location"].dropna().unique().tolist())


def get_unique_cuisines() -> list[str]:
    """
    Return a sorted, deduplicated list of individual cuisine strings.
    Handles comma-separated cuisine fields (e.g. "North Indian, Chinese").
    """
    df = get_dataframe()
    if "cuisines" not in df.columns:
        return []
    all_cuisines: set[str] = set()
    for entry in df["cuisines"].dropna():
        for part in str(entry).split(","):
            c = part.strip()
            if c and c.lower() != "nan":
                all_cuisines.add(c)
    return sorted(all_cuisines)


def get_cost_range() -> dict[str, int]:
    """Return the min and max cost_for_two from the dataset."""
    df = get_dataframe()
    if "cost_for_two" not in df.columns:
        return {"min": 0, "max": 5000}
    return {
        "min": int(df["cost_for_two"].min()),
        "max": int(df["cost_for_two"].max()),
    }


def filter_restaurants(
    location: str = "",
    min_cost: int = 0,
    max_cost: int = 99999,
    cuisine: str = "",
    min_rating: float = 0.0,
    extra_prefs: str = "",
) -> pd.DataFrame:
    """
    Filter restaurants based on user preferences.

    Args:
        location:   neighbourhood name (case-insensitive substring match)
        min_cost:   minimum cost_for_two (inclusive)
        max_cost:   maximum cost_for_two (inclusive)
        cuisine:    cuisine substring (case-insensitive)
        min_rating: minimum aggregate_rating (inclusive)
        extra_prefs: free-text (not used for hard filtering — passed to LLM)

    Returns:
        DataFrame with up to 20 rows, sorted by rating descending.
    """
    df = get_dataframe().copy()

    # Location filter — case-insensitive exact match on title-cased location
    if location and location.strip():
        loc_norm = location.strip().title()
        if "location" in df.columns:
            # Handle categorical comparison
            df = df[df["location"].astype(str).str.contains(loc_norm, case=False, na=False)]

    # Cost range filter
    if "cost_for_two" in df.columns:
        df = df[(df["cost_for_two"] >= min_cost) & (df["cost_for_two"] <= max_cost)]

    # Cuisine filter — substring, case-insensitive
    if cuisine and cuisine.strip() and cuisine.lower() not in ("all", "all cuisines"):
        if "cuisines" in df.columns:
            df = df[df["cuisines"].astype(str).str.contains(cuisine.strip(), case=False, na=False)]

    # Rating filter
    if "aggregate_rating" in df.columns:
        df = df[df["aggregate_rating"] >= min_rating]

    # Sort by rating descending, then return top 20
    if "aggregate_rating" in df.columns:
        df = df.sort_values("aggregate_rating", ascending=False)

    return df.head(20).reset_index(drop=True)

