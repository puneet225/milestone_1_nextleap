from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Ensure the backend logic directory is in the path
sys.path.append(os.path.join(os.getcwd(), "backend_logic"))

import data_loader
from recommender import get_recommendations

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            req = json.loads(post_data)
            
            data_loader.preload()
            
            # Use the same filtering logic as main.py/streamlit
            filtered_df = data_loader.filter_restaurants(
                location=req.get("location", ""),
                min_cost=req.get("min_cost", 0),
                max_cost=req.get("max_cost", 9999),
                cuisine=req.get("cuisine", ""),
                min_rating=req.get("min_rating", 0.0),
                extra_prefs=req.get("extra_preferences", "")
            )
            
            if filtered_df.empty:
                response = {"recommendations": [], "total_matches_found": 0}
            else:
                user_prefs = {
                    "location": req.get("location", "Any"),
                    "min_cost": req.get("min_cost", 0),
                    "max_cost": req.get("max_cost", 9999),
                    "cuisine": req.get("cuisine", "Any"),
                    "min_rating": req.get("min_rating", 0.0),
                    "extra_preferences": req.get("extra_preferences", "")
                }
                recs = get_recommendations(user_prefs, filtered_df)
                response = {
                    "recommendations": recs,
                    "total_matches_found": len(filtered_df)
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
