"""
ANP Ports Vessel Movement Scraper
Main orchestration logic for scraping and processing ANP vessel data.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

try:
    from .matcher import ANPPortsVesselMatcher
    from .adapters.anp_api import ANPAPIClient
except ImportError:
    # Fallback for direct execution
    from matcher import ANPPortsVesselMatcher
    from adapters.anp_api import ANPAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ANPPortsVesselScraper:
    """Main scraper orchestration class for ANP ports vessel data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the scraper with data directory and components."""
        
        # Initialize components
        self.api_client = ANPAPIClient()
        self.matcher = ANPPortsVesselMatcher()
        
        # File paths
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.vessels_file = self.data_dir / "vessels.json"
        self.state_file = self.data_dir / "state.json"
        
        # Load existing data
        self.vessels = self._load_vessels()
        self.state = self._load_state()
        
        logger.info(f"ANP Ports Vessel Scraper initialized. Data directory: {self.data_dir}")
        logger.info(f"Loaded {len(self.vessels)} existing vessels")
    
    def _load_vessels(self) -> List[Dict]:
        """Load existing vessel data from JSON file."""
        if not self.vessels_file.exists():
            logger.info("No existing vessels file found. Starting fresh.")
            return []
        
        try:
            with open(self.vessels_file, 'r', encoding='utf-8') as f:
                vessels = json.load(f)
                logger.info(f"Loaded {len(vessels)} vessels from {self.vessels_file}")
                return vessels
        except Exception as e:
            logger.error(f"Error loading vessels: {e}")
            return []
    
    def _save_vessels(self, vessels: List[Dict]) -> None:
        """Save vessel data to JSON file."""
        try:
            with open(self.vessels_file, 'w', encoding='utf-8') as f:
                json.dump(vessels, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved {len(vessels)} vessels to {self.vessels_file}")
        except Exception as e:
            logger.error(f"Error saving vessels: {e}")
    
    def _load_state(self) -> Dict:
        """Load application state from JSON file."""
        if not self.state_file.exists():
            logger.info("No existing state file found. Starting fresh.")
            return {
                "last_update": None,
                "total_vessels": 0,
                "update_count": 0,
                "last_error": None
            }
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                logger.info(f"Loaded state from {self.state_file}")
                return state
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {
                "last_update": None,
                "total_vessels": 0,
                "update_count": 0,
                "last_error": None
            }
    
    def _save_state(self, state: Dict) -> None:
        """Save application state to JSON file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _deduplicate_vessels(self, vessels: List[Dict]) -> List[Dict]:
        """Remove duplicate vessels based on vessel name and escale number."""
        seen = set()
        unique_vessels = []
        
        for vessel in vessels:
            # Create unique identifier: vessel name + escale number
            vessel_name = vessel.get('nOM_NAVIREField', '')
            escale_number = vessel.get('nUMERO_ESCALEField', '')
            unique_id = f"{vessel_name}_{escale_number}"
            
            if unique_id not in seen:
                seen.add(unique_id)
                unique_vessels.append(vessel)
            else:
                logger.debug(f"Duplicate vessel skipped: {vessel_name} (Escale: {escale_number})")
        
        logger.info(f"Deduplication: {len(vessels)} -> {len(unique_vessels)} vessels")
        return unique_vessels
    
    def _enrich_vessel_data(self, vessel: Dict) -> Dict:
        """Enrich vessel data with additional metadata."""
        # Add timestamp
        vessel['scraped_at'] = datetime.now().isoformat()
        
        # Parse date if available
        date_field = vessel.get('dATE_SITUATIONField', '')
        if date_field and date_field.startswith('/Date('):
            try:
                # Extract timestamp from /Date(1755817200000+0100)/ format
                timestamp_str = date_field.split('(')[1].split(')')[0].split('+')[0]
                timestamp_ms = int(timestamp_str)
                vessel['parsed_date'] = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
            except (ValueError, IndexError):
                vessel['parsed_date'] = None
        
        return vessel
    
    def update_vessel_data(self, force_update: bool = False) -> Dict:
        """
        Update vessel data from ANP API.
        
        Args:
            force_update: Force update even if recently updated
            
        Returns:
            Dictionary with update results
        """
        start_time = time.time()
        
        try:
            # Check if update is needed
            if not force_update and self.state.get('last_update'):
                last_update = datetime.fromisoformat(self.state['last_update'])
                if datetime.now() - last_update < timedelta(minutes=5):
                    logger.info("Skipping update - data is recent")
                    return {
                        "status": "skipped",
                        "message": "Data is recent, skipping update",
                        "last_update": self.state['last_update'],
                        "total_vessels": len(self.vessels)
                    }
            
            logger.info("Starting vessel data update from ANP API...")
            
            # Fetch new data from API
            new_vessels = self.api_client.get_all_vessels()
            
            if not new_vessels:
                logger.warning("No vessels received from API")
                return {
                    "status": "error",
                    "message": "No vessels received from API",
                    "new_vessels": 0,
                    "total_vessels": len(self.vessels)
                }
            
            logger.info(f"Received {len(new_vessels)} vessels from API")
            
            # Filter vessels using matcher
            matched_vessels = self.matcher.filter_vessels(new_vessels)
            logger.info(f"Filtering: {len(new_vessels)} -> {len(matched_vessels)} matches")
            
            # Enrich vessel data
            enriched_vessels = [self._enrich_vessel_data(v) for v in matched_vessels]
            
            # Combine with existing vessels and deduplicate
            all_vessels = self.vessels + enriched_vessels
            unique_vessels = self._deduplicate_vessels(all_vessels)
            
            # Calculate new vessels
            new_vessel_count = len(unique_vessels) - len(self.vessels)
            
            # Update vessels and state
            self.vessels = unique_vessels
            self.state.update({
                "last_update": datetime.now().isoformat(),
                "total_vessels": len(self.vessels),
                "update_count": self.state.get("update_count", 0) + 1,
                "last_error": None
            })
            
            # Save data
            self._save_vessels(self.vessels)
            self._save_state(self.state)
            
            duration = time.time() - start_time
            
            logger.info(f"Update complete: {new_vessel_count} new vessels, "
                       f"{len(self.vessels)} total, {duration:.2f}s")
            
            return {
                "status": "success",
                "message": "Successfully updated vessel data",
                "new_vessels": new_vessel_count,
                "total_vessels": len(self.vessels),
                "duration_seconds": round(duration, 2),
                "last_update": self.state["last_update"]
            }
            
        except Exception as e:
            error_msg = f"Error updating vessel data: {str(e)}"
            logger.error(error_msg)
            
            # Update state with error
            self.state.update({
                "last_error": error_msg,
                "last_update": datetime.now().isoformat()
            })
            self._save_state(self.state)
            
            return {
                "status": "error",
                "message": error_msg,
                "new_vessels": 0,
                "total_vessels": len(self.vessels)
            }
    
    def get_vessels(self, filters: Dict = None) -> List[Dict]:
        """
        Get vessels with optional filtering.
        
        Args:
            filters: Dictionary with filter options
            
        Returns:
            List of filtered vessels
        """
        if not filters:
            return self.vessels
        
        filtered_vessels = []
        
        for vessel in self.vessels:
            # Apply filters
            if self._matches_filters(vessel, filters):
                filtered_vessels.append(vessel)
        
        logger.info(f"Filtered {len(self.vessels)} vessels -> {len(filtered_vessels)} results")
        return filtered_vessels
    
    def _matches_filters(self, vessel: Dict, filters: Dict) -> bool:
        """Check if vessel matches all specified filters."""
        
        # Date range filter
        if 'start_date' in filters and filters['start_date']:
            try:
                start_date = datetime.fromisoformat(filters['start_date'])
                vessel_date = datetime.fromisoformat(vessel.get('parsed_date', '1900-01-01'))
                if vessel_date < start_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        if 'end_date' in filters and filters['end_date']:
            try:
                end_date = datetime.fromisoformat(filters['end_date'])
                vessel_date = datetime.fromisoformat(vessel.get('parsed_date', '2100-01-01'))
                if vessel_date > end_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Vessel type filter
        if 'vessel_type' in filters and filters['vessel_type']:
            if vessel.get('tYP_NAVIREField') != filters['vessel_type']:
                return False
        
        # Operator filter
        if 'operator' in filters and filters['operator']:
            if vessel.get('oPERATEURField') != filters['operator']:
                return False
        
        # Port filter
        if 'port' in filters and filters['port']:
            if vessel.get('pROVField') != filters['port']:
                return False
        
        # Situation filter
        if 'situation' in filters and filters['situation']:
            if vessel.get('sITUATIONField') != filters['situation']:
                return False
        
        # Search filter
        if 'search' in filters and filters['search']:
            search_term = filters['search'].lower()
            vessel_text = " ".join([
                str(vessel.get('nOM_NAVIREField', '')),
                str(vessel.get('tYP_NAVIREField', '')),
                str(vessel.get('oPERATEURField', '')),
                str(vessel.get('pROVField', ''))
            ]).lower()
            
            if search_term not in vessel_text:
                return False
        
        return True
    
    def get_statistics(self) -> Dict:
        """Get statistics about the vessel data."""
        if not self.vessels:
            return {
                "total_vessels": 0,
                "vessel_types": {},
                "operators": {},
                "ports": {},
                "situations": {},
                "last_update": None
            }
        
        # Count categories
        vessel_types = {}
        operators = {}
        ports = {}
        situations = {}
        
        for vessel in self.vessels:
            # Vessel types
            vessel_type = vessel.get('tYP_NAVIREField', 'Unknown')
            vessel_types[vessel_type] = vessel_types.get(vessel_type, 0) + 1
            
            # Operators
            operator = vessel.get('oPERATEURField', 'Unknown')
            operators[operator] = operators.get(operator, 0) + 1
            
            # Ports
            port = vessel.get('pROVField', 'Unknown')
            ports[port] = ports.get(port, 0) + 1
            
            # Situations
            situation = vessel.get('sITUATIONField', 'Unknown')
            situations[situation] = situations.get(situation, 0) + 1
        
        return {
            "total_vessels": len(self.vessels),
            "vessel_types": dict(sorted(vessel_types.items(), key=lambda x: x[1], reverse=True)[:10]),
            "operators": dict(sorted(operators.items(), key=lambda x: x[1], reverse=True)[:10]),
            "ports": dict(sorted(ports.items(), key=lambda x: x[1], reverse=True)[:10]),
            "situations": dict(sorted(situations.items(), key=lambda x: x[1], reverse=True)[:10]),
            "last_update": self.state.get("last_update"),
            "update_count": self.state.get("update_count", 0)
        }
    
    def export_csv(self, filters: Dict = None) -> str:
        """Export vessels to CSV format."""
        import csv
        import io
        
        vessels = self.get_vessels(filters)
        
        if not vessels:
            return ""
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            'Vessel Name', 'Escale Number', 'Lloyd Number', 'Vessel Type',
            'Operator', 'Provenance/Port', 'Situation', 'Consignee',
            'Date', 'Scraped At'
        ]
        writer.writerow(headers)
        
        # Write data
        for vessel in vessels:
            row = [
                vessel.get('nOM_NAVIREField', ''),
                vessel.get('nUMERO_ESCALEField', ''),
                vessel.get('nUMERO_LLOYDField', ''),
                vessel.get('tYP_NAVIREField', ''),
                vessel.get('oPERATEURField', ''),
                vessel.get('pROVField', ''),
                vessel.get('sITUATIONField', ''),
                vessel.get('cONSIGNATAIREField', ''),
                vessel.get('parsed_date', ''),
                vessel.get('scraped_at', '')
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def clean_duplicates(self) -> Dict:
        """Clean duplicate vessels from the database."""
        initial_count = len(self.vessels)
        
        # Deduplicate
        unique_vessels = self._deduplicate_vessels(self.vessels)
        
        # Update if changes made
        if len(unique_vessels) < initial_count:
            self.vessels = unique_vessels
            self.state['total_vessels'] = len(self.vessels)
            self._save_vessels(self.vessels)
            self._save_state(self.state)
        
        removed_count = initial_count - len(unique_vessels)
        
        return {
            "status": "success",
            "message": f"Cleaned {removed_count} duplicate vessels",
            "vessels_before": initial_count,
            "vessels_after": len(unique_vessels),
            "duplicates_removed": removed_count
        }
    
    def test_connection(self) -> Dict:
        """Test connection to ANP API."""
        return self.api_client.test_connection()
