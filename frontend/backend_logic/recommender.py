"""
recommender.py — Groq LLM Integration

Builds prompts from user preferences + filtered restaurant data,
calls the Groq API, and returns a ranked list of recommendations as JSON.
"""

from __future__ import annotations

import os
import json
import logging
import re
import time

# Ensure Streamlit Cloud proxy doesn't interfere with Groq API
os.environ["no_proxy"] = "*"

import pandas as pd
from groq import Groq

logger = logging.getLogger(__name__)

MODEL = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(user_prefs: dict, filtered_df: pd.DataFrame) -> str:
    """
    Construct the LLM prompt from user preferences and filtered restaurant data.

    The prompt:
    1. Summarises user preferences in plain English.
    2. Serialises up to 20 candidate restaurants as compact JSON.
    3. Gives strict instructions: rank top 5, 1-2 sentence explanation each,
       return ONLY valid JSON array — no markdown, no prose, no invented data.
    """
    location       = user_prefs.get("location", "any location")
    min_cost       = user_prefs.get("min_cost", 0)
    max_cost       = user_prefs.get("max_cost", 99999)
    cuisine        = user_prefs.get("cuisine", "any cuisine")
    min_rating     = user_prefs.get("min_rating", 0.0)
    extra_prefs    = user_prefs.get("extra_preferences", "").strip()

    # --- Plain-English user summary ---
    summary_parts = [
        f"Location: {location}",
        f"Budget: ₹{min_cost}–₹{max_cost} for two people",
        f"Cuisine preference: {cuisine if cuisine else 'Any'}",
        f"Minimum rating: {min_rating}+",
    ]
    if extra_prefs:
        summary_parts.append(f"Additional preferences: {extra_prefs}")
    user_summary = "\n".join(f"  - {p}" for p in summary_parts)

    # --- Candidate restaurants as compact JSON ---
    cols_to_include = [c for c in ["name", "cuisines", "cost_for_two", "aggregate_rating",
                                    "rest_type", "url"] if c in filtered_df.columns]
    candidates_data = filtered_df[cols_to_include].rename(
        columns={"cuisines": "cuisine", "aggregate_rating": "rating"}
    ).to_dict(orient="records")

    candidates_json = json.dumps(candidates_data, ensure_ascii=False)

    output_schema = json.dumps([
        {
            "rank": 1,
            "name": "Restaurant Name",
            "cuisine": "North Indian",
            "dish_liked": "Butter Chicken, Naan",
            "reviews": "Great ambiance and service.",
            "cost_for_two": 600,
            "rest_type": "Casual Dining",
            "url": "https://www.zomato.com/...",
            "ai_explanation": "Personalized 1-2 sentence explanation of why this fits the user."
        }
    ], indent=2)

    prompt = f"""You are a restaurant recommendation expert. A user is looking for restaurants with the following preferences:

{user_summary}

Below is a list of candidate restaurants that match their filters (provided as JSON):

{candidates_json}

Your task:
1. Select the TOP 5 restaurants from the list above that best match the user's preferences.
2. Rank them from best (#1) to 5th best.
3. For each restaurant, write a 1-2 sentence personalized explanation of why it is a good match for THIS user's specific preferences.
4. Return your answer as a JSON array ONLY — no markdown code fences, no prose before or after, no extra keys.

STRICT RULES (violation = failure):
- RICH PERSONALIZATION: Your "ai_explanation" must be a cohesive, expert summary. Use the "dish_liked" and "reviews" data to describe:
  * AMBIANCE: (e.g., rooftop, cozy, rustic, family-friendly)
  * MUST-TRY DISHES: (specifically mention items from "dish_liked")
  * SERVICE: (comment on hospitality if mentioned in reviews)
- STRICT GROUNDING: ONLY use facts from the candidate list. NEVER describe ambiance or service quality unless those specific keywords are present in the provided "reviews" or "rest_type" fields. If data is missing for these fields, focus only on budget and cuisine match.
- NO HALLUCINATION: NEVER guest or "flavor" the response with invented details.
- EXPLICIT MATCHING: Clearly state how the restaurant bits the user's filtered preferences.
- The "url" field MUST be copied exactly from the candidate list — never guess or construct a URL.
- If fewer than 5 candidates exist, return all of them.
- Output ONLY valid JSON — the response must start with "[" and end with "]".

Required output schema (one object per restaurant):
{output_schema}
"""
    return prompt


# ---------------------------------------------------------------------------
# Main recommendation function
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if the LLM adds them despite instructions."""
    text = text.strip()
    # Remove opening fence
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    # Remove closing fence
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    return text.strip()


def get_recommendations(user_prefs: dict, filtered_df: pd.DataFrame) -> list[dict]:
    """
    Call Groq API and return a ranked list of restaurant recommendations.

    Args:
        user_prefs:   dict with location, min_cost, max_cost, cuisine, min_rating, extra_preferences
        filtered_df:  DataFrame of pre-filtered candidate restaurants (max 20 rows)

    Returns:
        List of recommendation dicts with rank, name, cuisine, rating,
        cost_for_two, rest_type, url, ai_explanation.

    Raises:
        ValueError: if all retries are exhausted or response is not valid JSON.
    """
    if filtered_df.empty:
        return []

    client = Groq(
        api_key=os.environ["GROQ_API_KEY"]
    )
    prompt = build_prompt(user_prefs, filtered_df)

    last_exception: Exception | None = None

    for attempt, backoff in enumerate(BACKOFF_SECONDS, start=1):
        try:
            logger.info("Groq API call attempt %d/%d …", attempt, MAX_RETRIES)
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a restaurant recommendation assistant. "
                            "You ALWAYS respond with valid JSON arrays only. "
                            "You NEVER fabricate data. "
                            "You NEVER add markdown fences or explanatory prose."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )

            raw_content = response.choices[0].message.content
            logger.debug("Groq raw response: %s", raw_content[:500])

            cleaned = _strip_markdown_fences(raw_content)
            recommendations: list[dict] = json.loads(cleaned)

            if not isinstance(recommendations, list):
                raise ValueError(f"Expected a JSON array, got: {type(recommendations)}")

            logger.info("Successfully parsed %d recommendations.", len(recommendations))
            return recommendations

        except (json.JSONDecodeError, ValueError) as e:
            last_exception = e
            logger.warning("Attempt %d failed (parse error): %s", attempt, e)
        except Exception as e:
            last_exception = e
            logger.warning("Attempt %d failed (API error): %s", attempt, e)

        if attempt < MAX_RETRIES:
            logger.info("Retrying in %ds …", backoff)
            time.sleep(backoff)

    raise ValueError(
        f"Failed to get valid recommendations from Groq after {MAX_RETRIES} attempts. "
        f"Last error: {last_exception}"
    )
