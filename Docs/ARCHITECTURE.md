# Architecture

## Folder Structure
```
/backend
  main.py
  recommender.py
  data_loader.py
  requirements.txt
/frontend
  (Next.js 14 app)
.env
.env.example
docker-compose.yml
README.md
```

## Phase 1 — Project Scaffold
- Create the folder structure above
- .env must contain GROQ_API_KEY=your_key_here as placeholder only
- .env must be in .gitignore
- README must tell the user to replace the placeholder with their real key

## Phase 2 — Data Layer (data_loader.py)
- Load dataset: ManikaSaini/zomato-restaurant-recommendation from HuggingFace
- Inspect schema first, then extract: name, location, cuisines, cost_for_two (int),
  aggregate_rating (float), votes, online_order, book_table, rest_type, url
- Clean: drop rows with null name / location / cost / rating
- Cache DataFrame in memory at startup (load once, reuse on every request)
- get_unique_locations() → sorted list of unique neighbourhood names
- get_unique_cuisines() → sorted list of unique cuisine strings
- filter_restaurants(location, min_cost, max_cost, cuisine, min_rating, extra_prefs)
  → case-insensitive location match, cost range, cuisine substring, rating ≥ min_rating
  → return max 20 rows sorted by rating desc

## Phase 3 — Groq LLM Integration (recommender.py)
- build_prompt(user_prefs, filtered_df) → str
  - Summarise user preferences in plain English at the top
  - Serialize filtered restaurants as compact JSON (name, cuisine, cost_for_two,
    rating, rest_type, url)
  - Instruct LLM: rank top 5, write 1-2 sentence personalized explanation per
    restaurant, return ONLY valid JSON, no markdown fences, no prose
  - Output schema per item: rank, name, cuisine, rating, cost_for_two,
    rest_type, url, ai_explanation
  - Hard instruction in prompt: never invent a restaurant, never fabricate a URL,
    only use records from the provided list
- get_recommendations(user_prefs, filtered_df)
  - Call Groq, strip markdown fences, parse JSON
  - Retry 3 times with 1s / 2s / 4s backoff
  - Raise clear exception on failure

## Phase 4 — Backend API (main.py)
- POST /recommend
  - Request: location, min_cost, max_cost, cuisine, min_rating, extra_preferences
  - Response: ranked list + total_matches_found + filters_applied
- GET /filters
  - Response: { locations: [...], cuisines: [...], cost_range: { min, max } }
  - Frontend calls this on load to populate all controls dynamically
- GET /health → { status: "ok" }
- CORS: allow all origins
- Pre-load dataset on startup

## Phase 5 — Frontend (Next.js 14, App Router)
- On load: call GET /filters, use response to populate all controls dynamically.
  Never hardcode dropdown options or slider bounds.
- Left panel — preference form:
  - Location: searchable dropdown, label "Area in Bangalore"
  - Budget: dual-handle range slider showing ₹{min} – ₹{max} live
    Bounds from API cost_range.min and cost_range.max
  - Cuisine: dropdown, default "All Cuisines"
  - Minimum Rating: slider 1.0–5.0 step 0.5, display as "⭐ 3.5+"
  - Additional Preferences: free text, placeholder "e.g. rooftop, family-friendly"
  - Submit: "Find Restaurants" button with spinner while loading
- Right panel — results:
  - Up to 5 restaurant cards
  - Each card: name (bold), rank badge, cuisine tags, rating with star,
    cost-for-two, rest_type pill, ai_explanation (italicised)
  - "View on Zomato" button → opens restaurant.url in new tab
    Color: #E23744 (Zomato red)
  - 0 results: "No restaurants found — try relaxing your filters"
  - API error: non-blocking toast with error message
- Color theme: white cards, #E23744 accent, clean sans-serif

## Phase 6 — Docker + README
- docker-compose.yml: boots both services with docker compose up
- Backend reads .env via env_file directive
- README: prerequisites, setup, how to add Groq key, run with/without Docker

## Hard Constraints (never violate these)
1. LLM only ranks and explains — never invents restaurant names or URLs
2. Zomato URL must be the raw url field from dataset — never constructed or guessed
3. Slider bounds must come from the real dataset min/max — never hardcoded
4. Location dropdown must come from the real dataset — never hardcoded
5. All API errors must surface in the UI — no silent failures
6. Never commit the real API key