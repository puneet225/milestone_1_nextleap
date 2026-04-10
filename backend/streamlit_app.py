import streamlit as st
import pandas as pd
import os
import data_loader
import recommender

# --- Page Config ---
st.set_page_config(
    page_title="Antigravity | Zomato AI Recommender",
    page_icon="🍴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling (Rich Aesthetics) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #E23744;
        color: white;
        border-radius: 12px;
        padding: 0.5rem 2rem;
        border: none;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #c12b36;
        border: none;
        color: white;
        transform: translateY(-2px);
    }
    .restaurant-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid #eee;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .rank-badge {
        background-color: #FFBA08;
        color: #856404;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .tag {
        background-color: #f1f3f5;
        color: #495057;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        margin-right: 0.5rem;
        font-weight: 500;
    }
    .best-match-featured {
        background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
        border: 2px solid #ffccd5;
        padding: 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- App Logic ---
def main():
    st.title("🍴 Antigravity")
    st.caption("AI-Powered Restaurant Discovery in Bangalore")

    # Load Data
    with st.spinner("Warming up the kitchen (Loading data)..."):
        data_loader.preload()
        locations = data_loader.get_unique_locations()
        cuisines = data_loader.get_unique_cuisines()
        costs = data_loader.get_cost_range()

    # --- Sidebar ---
    with st.sidebar:
        st.header("🎯 Your Preferences")
        
        selected_location = st.selectbox("Area in Bangalore", ["All Areas"] + locations)
        
        budget = st.slider(
            "Budget (for two)", 
            min_value=int(costs["min"]), 
            max_value=int(costs["max"]), 
            value=(500, 2000),
            step=50
        )
        
        selected_cuisine = st.selectbox("Cuisine Type", ["All Cuisines"] + cuisines)
        
        min_rating = st.slider("Minimum Rating", 1.0, 5.0, 3.5, step=0.1)
        
        extra_prefs = st.text_area("Additional Preferences", placeholder="e.g. rooftop, family friendly, spicy food...")
        
        find_btn = st.button("Find Restaurants", use_container_width=True)

    # --- Main Panel ---
    if find_btn or 'results' in st.session_state:
        if find_btn:
            # Re-fetch on button click
            df = data_loader.get_dataframe()
            # Filter Logic (reused from FastAPI)
            filtered = df.copy()
            if selected_location != "All Areas":
                filtered = filtered[filtered["location"] == selected_location]
            
            filtered = filtered[
                (filtered["cost_for_two"] >= budget[0]) & 
                (filtered["cost_for_two"] <= budget[1]) &
                (filtered["aggregate_rating"] >= min_rating)
            ]
            
            if selected_cuisine != "All Cuisines":
                filtered = filtered[filtered["cuisines"].str.contains(selected_cuisine, case=False, na=False)]
            
            # Sort by rating desc
            filtered = filtered.sort_values(by="aggregate_rating", ascending=False).head(20)
            
            if filtered.empty:
                st.warning("No restaurants found — try relaxing your filters!")
                return

            with st.spinner("AI is analyzing your matches..."):
                user_prefs = f"Location: {selected_location}, Budget: {budget[0]}-{budget[1]}, Cuisine: {selected_cuisine}, Min Rating: {min_rating}, Prefs: {extra_prefs}"
                recs = recommender.get_recommendations(user_prefs, filtered)
                st.session_state.results = recs

        # tab switching
        tabs = st.tabs(["✨ AI Best Match", "📜 All Recommendations"])
        
        if 'results' in st.session_state and st.session_state.results:
            results = st.session_state.results
            
            # --- AI Best Match Tab ---
            with tabs[0]:
                best = results[0]
                st.markdown(f"""
                    <div class="best-match-featured">
                        <span class="rank-badge">🏆 #1 BEST MATCH</span>
                        <h2 style='margin-top: 0.5rem;'>{best['name']}</h2>
                        <div style='margin-bottom: 1rem;'>
                            <span class="tag">{best['cuisine']}</span>
                            <span class="tag">⭐ {best['rating']}</span>
                            <span class="tag">₹{best['cost_for_two']} for two</span>
                        </div>
                        <div style='background-color: #fff; padding: 1.2rem; border-radius: 12px; border-left: 4px solid #E23744;'>
                            <p style='font-style: italic; color: #555;'>"{best['ai_explanation']}"</p>
                        </div>
                        <a href="{best['url']}" target="_blank">
                            <button style='margin-top: 1.5rem; width: 100%; height: 45px; cursor: pointer; background: #E23744; color: white; border: none; border-radius: 10px; font-weight: bold;'>View on Zomato</button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)

            # --- All Recommendations Tab ---
            with tabs[1]:
                cols = st.columns(1) # Simple vertical list for readability
                for rec in results:
                    with st.container():
                        st.markdown(f"""
                            <div class="restaurant-card">
                                <div style='display: flex; justify-content: space-between; align-items: start;'>
                                    <div>
                                        <b style='font-size: 1.2rem;'>#{rec['rank']} {rec['name']}</b>
                                        <p style='color: #666; font-size: 0.9rem;'>{rec['rest_type']}</p>
                                    </div>
                                    <div style='text-align: right;'>
                                        <span style='color: #E23744; font-weight: bold;'>⭐ {rec['rating']}</span>
                                    </div>
                                </div>
                                <div style='margin: 0.8rem 0;'>
                                    <span class="tag">{rec['cuisine']}</span>
                                    <span class="tag">₹{rec['cost_for_two']} for two</span>
                                </div>
                                <p style='font-size: 0.9rem; color: #444;'>{rec['ai_explanation']}</p>
                                <a href="{rec['url']}" target="_blank" style="text-decoration:none;">
                                    <button style='width: 100%; cursor: pointer; background: transparent; color: #E23744; border: 1px solid #E23744; border-radius: 8px; font-size: 0.8rem; height: 32px;'>Details</button>
                                </a>
                            </div>
                        """, unsafe_allow_html=True)
    else:
        # Welcome State
        st.info("👈 Fill in your preferences and click **Find Restaurants** to get started!")

if __name__ == "__main__":
    main()
