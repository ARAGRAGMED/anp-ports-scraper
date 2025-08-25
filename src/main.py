"""
ANP Ports Vessel Scraper - FastAPI Application
Main web application for the ANP ports vessel monitoring system.
"""

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
    from .scraper import ANPPortsVesselScraper
    from .matcher import ANPPortsVesselMatcher
    from .adapters.anp_api import ANPAPIClient
except ImportError:
    # Fallback for direct execution
    from scraper import ANPPortsVesselScraper
    from matcher import ANPPortsVesselMatcher
    from adapters.anp_api import ANPAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ANP Ports Vessel Scraper API",
    description="API for scraping and analyzing ANP vessel movement data",
    version="1.0.0"
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
scraper = ANPPortsVesselScraper(data_dir=str(data_dir))
matcher = ANPPortsVesselMatcher()
api_client = ANPAPIClient()

# Mount static files
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    print(f"Web directory mounted at /static: {web_dir}")
else:
    print(f"Warning: Web directory not found: {web_dir}")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the main dashboard HTML."""
    html_file = web_dir / "index.html"
    if html_file.exists():
        with open(html_file, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>ANP Ports Vessel Scraper</title></head>
            <body>
                <h1>ANP Ports Vessel Scraper Dashboard</h1>
                <p>Dashboard files not found. Please check the web directory.</p>
                <p><a href="/docs">API Documentation</a></p>
            </body>
        </html>
        """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "service": "ANP Ports Vessel Scraper", 
        "platform": "FastAPI",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/dashboard-data")
async def get_dashboard_data(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vessel_type: Optional[str] = Query(None, description="Vessel type filter"),
    operator: Optional[str] = Query(None, description="Operator filter"),
    port: Optional[str] = Query(None, description="Port filter"),
    situation: Optional[str] = Query(None, description="Situation filter"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: Optional[int] = Query(100, description="Maximum number of results")
):
    """Get filtered dashboard data."""
    try:
        # Build filters
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if vessel_type:
            filters['vessel_type'] = vessel_type
        if operator:
            filters['operator'] = operator
        if port:
            filters['port'] = port
        if situation:
            filters['situation'] = situation
        if search:
            filters['search'] = search
        
        # Get vessels with filters
        vessels = scraper.get_vessels(filters)
        
        # Apply limit
        if limit and limit > 0:
            vessels = vessels[:limit]
        
        # Get statistics
        stats = scraper.get_statistics()
        
        return {
            "status": "success",
            "vessels": vessels,
            "statistics": stats,
            "filters_applied": filters,
            "total_results": len(vessels),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update")
async def update_vessel_data(force_update: bool = Query(False, description="Force update even if recent")):
    """Trigger vessel data update from ANP API."""
    try:
        result = scraper.update_vessel_data(force_update=force_update)
        return result
    except Exception as e:
        logger.error(f"Error updating vessel data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
async def get_statistics():
    """Get vessel data statistics."""
    try:
        stats = scraper.get_statistics()
        return {
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vessels")
async def get_vessels(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vessel_type: Optional[str] = Query(None, description="Vessel type filter"),
    operator: Optional[str] = Query(None, description="Operator filter"),
    port: Optional[str] = Query(None, description="Port filter"),
    situation: Optional[str] = Query(None, description="Situation filter"),
    search: Optional[str] = Query(None, description="Search term"),
    limit: Optional[int] = Query(100, description="Maximum number of results")
):
    """Get vessels with optional filtering."""
    try:
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if vessel_type:
            filters['vessel_type'] = vessel_type
        if operator:
            filters['operator'] = operator
        if port:
            filters['port'] = port
        if situation:
            filters['situation'] = situation
        if search:
            filters['search'] = search
        
        vessels = scraper.get_vessels(filters)
        
        if limit and limit > 0:
            vessels = vessels[:limit]
        
        return {
            "status": "success",
            "vessels": vessels,
            "total_results": len(vessels),
            "filters_applied": filters,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting vessels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vessels/{vessel_id}")
async def get_vessel(vessel_id: str):
    """Get specific vessel by ID (escale number)."""
    try:
        vessels = scraper.get_vessels()
        for vessel in vessels:
            if str(vessel.get('nUMERO_ESCALEField', '')) == vessel_id:
                return {
                    "status": "success",
                    "vessel": vessel,
                    "timestamp": datetime.now().isoformat()
                }
        
        raise HTTPException(status_code=404, detail="Vessel not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vessel {vessel_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/csv")
async def export_csv(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    vessel_type: Optional[str] = Query(None, description="Vessel type filter"),
    operator: Optional[str] = Query(None, description="Operator filter"),
    port: Optional[str] = Query(None, description="Port filter"),
    situation: Optional[str] = Query(None, description="Situation filter"),
    search: Optional[str] = Query(None, description="Search term")
):
    """Export vessels to CSV format."""
    try:
        filters = {}
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if vessel_type:
            filters['vessel_type'] = vessel_type
        if operator:
            filters['operator'] = operator
        if port:
            filters['port'] = port
        if situation:
            filters['situation'] = situation
        if search:
            filters['search'] = search
        
        csv_data = scraper.export_csv(filters)
        
        if not csv_data:
            raise HTTPException(status_code=404, detail="No data to export")
        
        return JSONResponse(
            content={"csv_data": csv_data},
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/filter-options")
async def get_filter_options():
    """Get available filter options."""
    try:
        vessels = scraper.get_vessels()
        options = matcher.get_filter_options(vessels)
        
        return {
            "status": "success",
            "filter_options": options,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clean-duplicates")
async def clean_duplicates():
    """Clean duplicate vessels from the database."""
    try:
        result = scraper.clean_duplicates()
        return result
    except Exception as e:
        logger.error(f"Error cleaning duplicates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-connection")
async def test_connection():
    """Test connection to ANP API."""
    try:
        result = scraper.test_connection()
        return result
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Check if we're running on Vercel
    if os.environ.get('VERCEL_ENV'):
        logger.info("Running on Vercel - using temporary data directory")
        scraper = ANPPortsVesselScraper(data_dir="/tmp/data")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
