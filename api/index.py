"""
Vercel API handler for Baltic Exchange Scraper
This file is specifically for Vercel serverless deployment
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Baltic Exchange Scraper API",
    description="API for scraping and analyzing Baltic Exchange weekly market data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard HTML."""
    return HTMLResponse(content="""
    <html>
        <head>
            <title>Baltic Exchange Scraper</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <h1>Baltic Exchange Scraper Dashboard</h1>
                <p>Welcome to the Baltic Exchange Weekly Market Roundup Scraper!</p>
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">API Documentation</h5>
                                <p class="card-text">Access the interactive API documentation.</p>
                                <a href="/docs" class="btn btn-primary">View API Docs</a>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">Health Check</h5>
                                <p class="card-text">Check the API health status.</p>
                                <a href="/api/health" class="btn btn-success">Health Check</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "Baltic Exchange Scraper", 
        "platform": "FastAPI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "deployment": "Vercel Serverless"
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working."""
    return {
        "message": "Baltic Exchange Scraper API is working!",
        "timestamp": datetime.now().isoformat()
    }

# Export the FastAPI app for Vercel
handler = app
