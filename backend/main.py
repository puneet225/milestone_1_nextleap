"""
main.py — FastAPI Backend

Exposes:
  GET  /health     — liveness check
  GET  /filters    — dynamic filter options (locations, cuisines, cost range)
  POST /recommend  — AI-ranked restaurant recommendations
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Setup & Robust Environment Loading
# ---------------------------------------------------------------------------

# 1. Add current directory to path to ensure local imports work regardless 
# of where uvicorn is started from.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Search for .env in current dir and parent dir (root)
load_dotenv() 
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Local Imports (Must come after sys.path/dotenv setup)
# ---------------------------------------------------------------------------

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import data_loader
from recommender import get_recommendations


# ---------------------------------------------------------------------------
# Lifespan: pre-load dataset once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — pre-loading dataset …")
    data_loader.preload()
    logger.info("Dataset ready. Server is live.")
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Restaurant Recommendation API",
    description="Zomato-inspired restaurant recommendations powered by Groq LLM.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    location: str = Field(default="", description="Neighbourhood / area name")
    min_cost: int = Field(default=0, ge=0, description="Minimum cost for two (₹)")
    max_cost: int = Field(default=99999, ge=0, description="Maximum cost for two (₹)")
    cuisine: str = Field(default="", description="Cuisine preference (empty = all)")
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Minimum aggregate rating")
    extra_preferences: str = Field(default="", description="Free-text additional preferences")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}


@app.get("/filters", tags=["Filters"])
async def get_filters():
    """
    Returns dynamic filter options derived from the real dataset.
    The frontend uses this response to populate all dropdowns and slider bounds.
    """
    try:
        locations  = data_loader.get_unique_locations()
        cuisines   = data_loader.get_unique_cuisines()
        cost_range = data_loader.get_cost_range()
        return {
            "locations":  locations,
            "cuisines":   cuisines,
            "cost_range": cost_range,
        }
    except Exception as e:
        logger.exception("Failed to build filters: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend", tags=["Recommendations"])
async def recommend(req: RecommendRequest):
    """
    Filter restaurants from the dataset and use Groq LLM to rank and explain
    the top 5 options matching the user's preferences.
    """
    # Validate API key is set
    if not os.environ.get("GROQ_API_KEY") or os.environ["GROQ_API_KEY"].startswith("your_"):
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured. Please set a real key in your .env file.",
        )

    user_prefs = req.model_dump()

    try:
        filtered_df = data_loader.filter_restaurants(
            location=req.location,
            min_cost=req.min_cost,
            max_cost=req.max_cost,
            cuisine=req.cuisine,
            min_rating=req.min_rating,
            extra_prefs=req.extra_preferences,
        )
        logger.info("Filtered to %d candidate restaurants.", len(filtered_df))

        if filtered_df.empty:
            return {
                "recommendations":    [],
                "total_matches_found": 0,
                "filters_applied":    user_prefs,
            }

        recommendations = get_recommendations(user_prefs, filtered_df)

        return {
            "recommendations":    recommendations,
            "total_matches_found": len(filtered_df),
            "filters_applied":    user_prefs,
        }

    except ValueError as e:
        logger.error("Recommendation engine error: %s", e)
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in /recommend: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
