import streamlit as st
import pandas as pd
import os
import sys

# DEBUG: Visual Filesystem Map for Streamlit Cloud
# If you are seeing this, the app started but might fail on imports
st.set_page_config(page_title="Antigravity Diagnostic", layout="wide")

# Ensure the 'backend' directory is in the path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Diagnostic logging for the UI
def show_diagnostics(error=None):
    st.error(f"🚨 System Error: {error}")
    st.write("---")
    st.subheader("🕵️ Senior Dev Diagnostic Console")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Environment Info**")
        st.write(f"- Python: {sys.version}")
        st.write(f"- CWD: {os.getcwd()}")
    with col2:
        st.write("**Root Filesystem**")
        st.code("\n".join(os.listdir()))
    
    st.write("**Python Path**")
    st.code("\n".join(sys.path))
    
    try:
        import subprocess
        st.write("**Installed Packages (pip list)**")
        result = subprocess.check_output([sys.executable, "-m", "pip", "list"], text=True)
        st.code(result)
    except:
        st.warning("Could not run pip list diagnostic.")

# Aggressive Core Import
try:
    import data_loader
    import recommender
except ImportError as e:
    show_diagnostics(e)
    st.stop()

# --- Custom Styling ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { background-color: #E23744; color: white; border-radius: 12px; font-weight: bold; }
    .restaurant-card { background-color: white; padding: 1.5rem; border-radius: 20px; border: 1px solid #eee; margin-bottom: 1rem; }
    .tag { background-color: #f1f3f5; color: #495057; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; margin-right: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

# --- Data Loading (Optimized Cache) ---
@st.cache_data
def load_and_prep_data():
    """Warms the cache and returns the fully processed dataframe."""
    data_loader.preload()
    return data_loader.get_dataframe()

# --- App Logic ---
def main():
    st.title("🍴 Antigravity")
    st.caption("AI-Powered Restaurant Discovery in Bangalore")

    with st.spinner("Loading culinary data..."):
        try:
            df = load_and_prep_data()
            locations = data_loader.get_unique_locations()
            cuisines = data_loader.get_unique_cuisines()
            costs = data_loader.get_cost_range()
        except Exception as e:
            st.error(f"Data Loading Error: {e}")
            return

    with st.sidebar:
        st.header("🎯 Preferences")
        selected_location = st.selectbox("Area", ["All Areas"] + locations)
        budget = st.slider("Budget", int(costs["min"]), int(costs["max"]), (500, 2000), 50)
        selected_cuisine = st.selectbox("Cuisine", ["All Cuisines"] + cuisines)
        min_rating = st.slider("Min Rating", 1.0, 5.0, 3.5, 0.1)
        extra_prefs = st.text_area("Extras", placeholder="e.g. rooftop")
        find_btn = st.button("Find Restaurants", use_container_width=True)

    if find_btn or 'results' in st.session_state:
        if find_btn:
            df = data_loader.get_dataframe()
            filtered = df.copy()
            if selected_location != "All Areas":
                filtered = filtered[filtered["location"] == selected_location]
            filtered = filtered[(filtered["cost_for_two"] >= budget[0]) & (filtered["cost_for_two"] <= budget[1]) & (filtered["aggregate_rating"] >= min_rating)]
            if selected_cuisine != "All Cuisines":
                filtered = filtered[filtered["cuisines"].str.contains(selected_cuisine, case=False, na=False)]
            filtered = filtered.sort_values(by="aggregate_rating", ascending=False).head(20)
            
            if filtered.empty:
                st.warning("No matches found.")
                return

            with st.spinner("AI analyzing reviews..."):
                user_prefs = {
                    "location": selected_location if selected_location != "All Areas" else "Any",
                    "min_cost": budget[0],
                    "max_cost": budget[1],
                    "cuisine": selected_cuisine if selected_cuisine != "All Cuisines" else "Any",
                    "min_rating": min_rating,
                    "extra_preferences": extra_prefs
                }
                st.session_state.results = recommender.get_recommendations(user_prefs, filtered)

        if 'results' in st.session_state:
            tabs = st.tabs(["✨ AI Best Match", "📜 All Recommendations"])
            results = st.session_state.results
            
            with tabs[0]:
                best = results[0]
                st.markdown(f"<h3>{best['name']}</h3>", unsafe_allow_html=True)
                st.info(best['ai_explanation'])
                st.link_button("View on Zomato", best['url'])

            with tabs[1]:
                for rec in results:
                    st.markdown(f"<div class='restaurant-card'><b>{rec['name']}</b><br>{rec['ai_explanation']}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
