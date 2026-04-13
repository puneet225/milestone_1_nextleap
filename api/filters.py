from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Ensure the backend directory is in the path
sys.path.append(os.path.join(os.getcwd(), "backend"))

import data_loader

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            data_loader.preload()
            locations = data_loader.get_unique_locations()
            cuisines = data_loader.get_unique_cuisines()
            cost_range = data_loader.get_cost_range()
            
            response_data = {
                "locations": locations,
                "cuisines": cuisines,
                "cost_range": cost_range
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
