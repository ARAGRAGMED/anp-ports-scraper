"""
ANP API Client
Client for fetching vessel movement data from ANP (Agence Nationale des Ports) API.
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, date
import time
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ANPAPIClient:
    """API client for ANP vessel movement data."""
    
    def __init__(self, delay_between_requests: float = 1.0):
        """Initialize ANP API client."""
        
        self.base_url = "https://www.anp.org.ma"
        self.vessels_endpoint = "/_vti_bin/WS/Service.svc/mvmnv/all"
        self.delay = delay_between_requests
        
        # Set up session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8,ar;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
        logger.info("ANP API client initialized successfully")
    
    def get_all_vessels(self) -> List[Dict]:
        """
        Fetch all vessel movement data from ANP API.
        
        Returns:
            List of vessel dictionaries
        """
        try:
            url = f"{self.base_url}{self.vessels_endpoint}"
            logger.info(f"Fetching vessel data from: {url}")
            
            # Add delay to be respectful
            if self.delay > 0:
                time.sleep(self.delay)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse JSON response
            vessels = response.json()
            
            if not isinstance(vessels, list):
                logger.error(f"Expected list response, got: {type(vessels)}")
                return []
            
            logger.info(f"Successfully retrieved {len(vessels)} vessels from ANP API")
            
            # Validate and clean vessel data
            cleaned_vessels = self._clean_vessel_data(vessels)
            
            return cleaned_vessels
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching vessels: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching vessels: {e}")
            return []
    
    def _clean_vessel_data(self, vessels: List[Dict]) -> List[Dict]:
        """
        Clean and validate vessel data.
        
        Args:
            vessels: Raw vessel data from API
            
        Returns:
            Cleaned vessel data
        """
        cleaned = []
        
        for vessel in vessels:
            if not isinstance(vessel, dict):
                logger.warning(f"Skipping non-dict vessel: {type(vessel)}")
                continue
            
            # Check for required fields
            vessel_name = vessel.get('nOM_NAVIREField')
            if not vessel_name:
                logger.warning("Skipping vessel without name")
                continue
            
            # Clean empty or null values
            cleaned_vessel = {}
            for key, value in vessel.items():
                if value is not None and value != "":
                    cleaned_vessel[key] = value
                else:
                    cleaned_vessel[key] = None
            
            # Ensure we have at least basic vessel info
            if cleaned_vessel.get('nOM_NAVIREField') and cleaned_vessel.get('tYP_NAVIREField'):
                cleaned.append(cleaned_vessel)
            else:
                logger.debug(f"Skipping vessel with insufficient data: {vessel_name}")
        
        logger.info(f"Cleaned {len(cleaned)} vessels from {len(vessels)} raw entries")
        return cleaned
    
    def test_connection(self) -> Dict:
        """
        Test connection to ANP API.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            start_time = time.time()
            vessels = self.get_all_vessels()
            duration = time.time() - start_time
            
            return {
                "status": "success",
                "message": f"Successfully connected to ANP API",
                "vessel_count": len(vessels),
                "response_time_seconds": round(duration, 2),
                "api_endpoint": f"{self.base_url}{self.vessels_endpoint}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to ANP API: {str(e)}",
                "vessel_count": 0,
                "response_time_seconds": 0,
                "api_endpoint": f"{self.base_url}{self.vessels_endpoint}"
            }
