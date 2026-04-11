import sys
import os

# Add the 'backend' folder to the path so we can import modules from it
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Diagnostic check for httpx (Senior Dev defensive check)
try:
    import httpx
    import pandas
    import groq
except ImportError as e:
    print(f"Error: Missing dependency during startup: {e}")
    # We let it fail naturally so Streamlit logs show the specific missing module
    raise e

# Import the actual app from backend
from backend.streamlit_app import main

if __name__ == "__main__":
    main()
