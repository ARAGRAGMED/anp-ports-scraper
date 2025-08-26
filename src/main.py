"""
Baltic Exchange Scraper - FastAPI Application
Main web application for the Baltic Exchange market monitoring system.
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

try:
    from .baltic_exchange_scraper import BalticExchangeScraper
    from .adapters.baltic_exchange_api import BalticExchangeAPIClient
except ImportError:
    # Fallback for direct execution
    from baltic_exchange_scraper import BalticExchangeScraper
    from adapters.baltic_exchange_api import BalticExchangeAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose logs from adapters to reduce noise
logging.getLogger("adapters.baltic_exchange_api").setLevel(logging.WARNING)

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

# Initialize scraper with correct data directory
data_dir = Path(__file__).parent.parent / "data"
scraper = BalticExchangeScraper(data_dir=str(data_dir))
api_client = BalticExchangeAPIClient()

# Mount static files for Vercel
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"Static directory mounted at /static: {static_dir}")
else:
    print(f"Warning: Static directory not found: {static_dir}")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard HTML."""
    html_file = static_dir / "index.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>Baltic Exchange Scraper</title></head>
            <body>
                <h1>Baltic Exchange Scraper Dashboard</h1>
                <p>Dashboard files not found. Please check the static directory.</p>
                <p><a href="/docs">API Documentation</a></p>
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
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard-data")
async def get_dashboard_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(100, description="Maximum number of results")
):
    """Get filtered dashboard data from local JSON file."""
    try:
        # Read data directly from JSON file instead of calling scraper
        json_file_path = data_dir / "market_data.json"
        
        if not json_file_path.exists():
            return {
                "status": "success",
                "data": [],
                "summary": {
                    "latest_update": None,
                    "total_weekly_reports": 0,
                    "data_structure": "weekly_reports"
                }
            }
        
        # Read and parse JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            all_data = json.loads(f.read())
        
        # Apply date filtering if provided
        if start_date or end_date:
            filtered_data = []
            for entry in all_data:
                entry_date = datetime.fromisoformat(entry['scraped_at'].replace('Z', '+00:00'))
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    if entry_date < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    if entry_date > end_dt:
                        continue
                
                filtered_data.append(entry)
        else:
            filtered_data = all_data
        
        # Apply limit
        if limit:
            filtered_data = filtered_data[:limit]
        
        # Calculate summary statistics
        latest_entry = filtered_data[0] if filtered_data else None
        
        # Count total weekly reports across all entries
        total_weekly_reports = 0
        if filtered_data:
            for entry in filtered_data:
                if entry.get('weekly_reports'):
                    total_weekly_reports += len(entry['weekly_reports'])
        
        return {
            "status": "success",
            "data": filtered_data,
            "summary": {
                "latest_update": latest_entry['scraped_at'] if latest_entry else None,
                "total_weekly_reports": total_weekly_reports,
                "data_structure": "weekly_reports"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-data")
async def update_market_data():
    """Trigger market data update."""
    try:
        result = scraper.update_market_data(force_update=True)
        return {
            "status": "success",
            "message": "Market data update triggered",
            "result": result
        }
    except Exception as e:
        logger.error(f"Error updating market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    """Get scraper statistics."""
    try:
        stats = scraper.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/latest-data")
async def get_latest_data():
    """Get latest market data."""
    try:
        latest_data = scraper.get_latest_data()
        return {
            "status": "success",
            "data": latest_data
        }
    except Exception as e:
        logger.error(f"Error getting latest data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export-csv")
async def export_csv():
    """Export data to CSV."""
    try:
        csv_data = scraper.export_csv()
        if csv_data:
            return JSONResponse(
                content={"status": "success", "csv_data": csv_data},
                media_type="application/json"
            )
        else:
            return JSONResponse(
                content={"status": "error", "message": "No data available for export"},
                status_code=404
            )
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-connection")
async def test_connection():
    """Test connection to Baltic Exchange."""
    try:
        result = scraper.test_connection()
        return {
            "status": "success",
            "connection_test": result
        }
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Vercel handler
app.debug = False
