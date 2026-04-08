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
    """Load the dataset (local or URL), rename columns, clean nulls."""
    logger.info("CTO: Decoupled loading starting...")
    
    if os.path.exists(LOCAL_CSV_PATH):
        logger.info("Loading from local cache: %s", LOCAL_CSV_PATH)
        raw = pd.read_csv(LOCAL_CSV_PATH)
    else:
        logger.info("No local CSV found. Attempting to download: %s", ZOMATO_CSV_URL)
        try:
            raw = pd.read_csv(ZOMATO_CSV_URL)
            # Cache it locally for next time (CTO performance win)
            raw.to_csv(LOCAL_CSV_PATH, index=False)
            logger.info("Successfully fetched and cached dataset.")
        except Exception as e:
            logger.error("Failed to fetch dataset: %s", e)
            raise RuntimeError(f"Could not load restaurant dataset. Please provide zomato.csv in {LOCAL_CSV_PATH}") from e

    logger.info("Raw dataset shape: %s  |  Columns: %s", raw.shape, list(raw.columns))

    # Build rename map: original-column → canonical-name
    rename_map: dict[str, str] = {}
    missing: list[str] = []
    for canonical, candidates in _FIELD_CANDIDATES.items():
        found = _pick_column(raw, canonical, candidates)
        if found is None:
            missing.append(canonical)
        elif found != canonical:
            rename_map[found] = canonical

    if missing:
        logger.warning("Missing canonical fields: %s — they will be absent from the DataFrame", missing)

    df = raw.rename(columns=rename_map)

    # Keep only the canonical columns that we actually have
    keep = [c for c in _FIELD_CANDIDATES.keys() if c in df.columns]
    df = df[keep].copy()

    # ---- Type coercions ----
    if "cost_for_two" in df.columns:
        # Handle comma-separated strings (e.g. "1,200")
        df["cost_for_two"] = (
            df["cost_for_two"]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.extract(r"(\d+)")
            [0]
            .pipe(pd.to_numeric, errors="coerce")
        )

    if "aggregate_rating" in df.columns:
        # Some datasets store rating as "4.1/5" or "NEW" — coerce to float
        df["aggregate_rating"] = (
            df["aggregate_rating"]
            .astype(str)
            .str.extract(r"(\d+\.?\d*)")[0]
            .astype(float)
        )

    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    # ---- Drop rows missing critical fields ----
    critical = [c for c in ["name", "location", "cost_for_two", "aggregate_rating"] if c in df.columns]
    before = len(df)
    df = df.dropna(subset=critical)
    logger.info("Dropped %d rows with null critical fields. Remaining: %d", before - len(df), len(df))

    # Normalise string fields
    for col in ["name", "location", "cuisines", "rest_type", "url"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Normalise location to title-case for consistent matching
    if "location" in df.columns:
        df["location"] = df["location"].str.title()

    logger.info("Dataset ready. Shape: %s", df.shape)
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
            df = df[df["location"].str.contains(loc_norm, case=False, na=False)]

    # Cost range filter
    if "cost_for_two" in df.columns:
        df = df[(df["cost_for_two"] >= min_cost) & (df["cost_for_two"] <= max_cost)]

    # Cuisine filter — substring, case-insensitive
    if cuisine and cuisine.strip() and cuisine.lower() not in ("all", "all cuisines"):
        if "cuisines" in df.columns:
            df = df[df["cuisines"].str.contains(cuisine.strip(), case=False, na=False)]

    # Rating filter
    if "aggregate_rating" in df.columns:
        df = df[df["aggregate_rating"] >= min_rating]

    # Sort by rating descending, then return top 20
    if "aggregate_rating" in df.columns:
        df = df.sort_values("aggregate_rating", ascending=False)

    return df.head(20).reset_index(drop=True)
