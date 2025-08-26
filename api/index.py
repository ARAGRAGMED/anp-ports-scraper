"""
Vercel API handler for Baltic Exchange Scraper
This file is specifically for Vercel serverless deployment
"""

from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/':
            response = {
                "message": "Welcome to Baltic Exchange Scraper API",
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "endpoints": [
                    "/api/health",
                    "/api/test"
                ]
            }
        elif self.path == '/api/health':
            response = {
                "status": "healthy", 
                "service": "Baltic Exchange Scraper", 
                "platform": "Vercel Serverless",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        elif self.path == '/api/test':
            response = {
                "message": "Baltic Exchange Scraper API is working!",
                "timestamp": datetime.now().isoformat()
            }
        else:
            response = {
                "error": "Endpoint not found",
                "path": self.path,
                "timestamp": datetime.now().isoformat()
            }
        
        self.wfile.write(json.dumps(response).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return
