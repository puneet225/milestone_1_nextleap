import pandas as pd
import os
import ast
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CSV_PATH = "backend/zomato.csv"
OUTPUT_PATH = "backend/zomato.parquet"

_FIELD_CANDIDATES = {
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

def clean_cost(x):
    try:
        return float(str(x).replace(",", ""))
    except:
        return 0.0

def clean_rating(x):
    try:
        return float(str(x).split("/")[0]) if "/" in str(x) else float(x)
    except:
        return 0.0

def parse_reviews(rev_str):
    if not rev_str or rev_str == "[]": return ""
    try:
        reviews = ast.literal_eval(rev_str)
        comments = []
        for _, r_text in reviews[:3]:
            clean_t = r_text.replace("RATED\n", "").replace("\n", " ").strip()
            if clean_t: comments.append(clean_t)
        return " | ".join(comments)
    except:
        return ""

def main():
    if not os.path.exists(CSV_PATH):
        logger.error(f"Source CSV not found at {CSV_PATH}")
        return

    logger.info(f"Step 1: Reading {CSV_PATH}...")
    # Using chunksize or low_memory=False to handle the large file reliably
    df = pd.read_csv(CSV_PATH, low_memory=False)
    logger.info(f"Original shape: {df.shape}")

    # Build rename map
    rename_map = {}
    for canonical, candidates in _FIELD_CANDIDATES.items():
        for c in candidates:
            if c in df.columns:
                rename_map[c] = canonical
                break
    
    if "dish_liked" in df.columns: rename_map["dish_liked"] = "dish_liked"
    if "reviews_list" in df.columns: rename_map["reviews_list"] = "reviews_list"

    df = df.rename(columns=rename_map)
    keep = [c for c in list(_FIELD_CANDIDATES.keys()) + ["dish_liked", "reviews_list"] if c in df.columns]
    df = df[keep].copy()

    logger.info("Step 2: Cleaning data...")
    if "cost_for_two" in df.columns:
        df["cost_for_two"] = df["cost_for_two"].apply(clean_cost)
    if "aggregate_rating" in df.columns:
        df["aggregate_rating"] = df["aggregate_rating"].apply(clean_rating)
    if "reviews_list" in df.columns:
        df["reviews_list"] = df["reviews_list"].apply(parse_reviews)
    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)

    logger.info("Step 3: De-duplication...")
    before_dupes = len(df)
    df = df.drop_duplicates(subset=["name", "location"])
    logger.info(f"Dropped {before_dupes - len(df)} duplicate restaurants.")

    logger.info("Step 4: Dropping nulls in critical fields...")
    critical = [c for c in ["name", "location", "cost_for_two", "aggregate_rating"] if c in df.columns]
    df = df.dropna(subset=critical)
    
    # Normalise strings
    for col in ["name", "location", "cuisines", "rest_type", "url"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    if "location" in df.columns:
        df["location"] = df["location"].str.title()

    logger.info("Step 5: Applying Memory Optimizations...")
    # Truncate reviews as requested
    if "reviews_list" in df.columns:
        df["reviews_list"] = df["reviews_list"].str[:500]

    # Dtypes
    df["cost_for_two"] = df["cost_for_two"].astype("float32")
    df["aggregate_rating"] = df["aggregate_rating"].astype("float32")
    df["votes"] = df["votes"].astype("int32")
    for col in ["location", "cuisines", "rest_type", "online_order", "book_table"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    logger.info(f"Final shape: {df.shape}")
    logger.info(f"Final memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    logger.info(f"Step 6: Saving to {OUTPUT_PATH}...")
    df.to_parquet(OUTPUT_PATH, index=False, engine="pyarrow")
    logger.info("Conversion successful!")

if __name__ == "__main__":
    main()
