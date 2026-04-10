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
- Load dataset: `zomato.csv` (local/HuggingFace)
- **De-duplication**: Drop duplicates based on `name` and `location` to resolve redundant listings.
- **Rich Data Extraction**: Map `dish_liked` and `reviews_list` for specialized AI analysis.
- **Review Parsing**: Extract and clean the top 3 most relevant user reviews per restaurant.
- Clean: Coerce cost to float, rating to 0.0-5.0 scale, and drop rows missing critical fields.
- Cache: Store cleaned DataFrame in memory at startup.

## Phase 3 — Groq LLM Integration (recommender.py)
- **Model**: `llama-3.3-70b-versatile` (128K context) for processing large candidate lists.
- **Expert Persona**: The AI act as a "Culinary Expert" specializing in Bangalore's food scene.
- **Rich Synthesis**: Analyze `dish_liked` and `reviews` to provide a cohesive summary covering:
  - **Ambiance**: Synthetically derived from review keywords (e.g. rooftop, rustic).
  - **Must-Try Dishes**: Explicitly listed from the database.
  - **Hospitality**: Sentiment derived from recent user experiences.
- **Strict Grounding**: 
  - Never invent ambiance or dishes if the data fields are empty.
  - Mandatory 100% accurate Zomato URLs from the original source.
  - No "flavor text" hallucinations—everything must be evidence-based.

## Phase 5 — Frontend (Next.js 14, App Router)
- **Tabbed Results View**:
  - **All Recommendations**: The traditional ranked grid of restaurants.
  - **AI Best Match**: A featured, premium view highlighting the #1 recommendation with detailed reasoning.
- **Enhanced Precision Controls**:
  - **Rating Slider**: Updated to 0.1 precision (step 0.1) for granular filtering (e.g. 3.6+).
  - **Budget Interaction**: Auto-rounding to ₹50 increments for intuitive sliding.
- **Resilience**: Added a "Connectivity Error" UI to handle backend downtime gracefully.

## Hard Constraints (Updated)
1. **Fact-Only Summaries**: AI must only use provided review snippets; no generic placeholder descriptions.
2. **De-duplicated Results**: Users should never see the same restaurant branch twice in a single result set.
3. **URL Integrity**: Every Zomato link must be valid and directly as provided in the dataset.
4. **Resilient Mocking**: Support `NEXT_PUBLIC_USE_MOCK=true` with dynamic imports for offline development.