"""
Baltic Exchange Weekly Market Roundup Scraper
Main orchestration logic for scraping and processing Baltic Exchange market data.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

try:
    from .adapters.baltic_exchange_api import BalticExchangeAPIClient
except ImportError:
    # Fallback for direct execution
    from adapters.baltic_exchange_api import BalticExchangeAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalticExchangeScraper:
    """Main scraper orchestration class for Baltic Exchange market data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the scraper with data directory and components."""
        
        # Initialize components
        self.api_client = BalticExchangeAPIClient()
        
        # File paths
        self.data_dir = Path(data_dir) if data_dir else Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        self.market_data_file = self.data_dir / "market_data.json"
        self.state_file = self.data_dir / "state.json"
        
        # Load existing data
        self.market_data = self._load_market_data()
        self.state = self._load_state()
        
        logger.info(f"Baltic Exchange Scraper initialized. Data directory: {self.data_dir}")
        logger.info(f"Loaded {len(self.market_data)} existing market data entries")
    
    def _load_market_data(self) -> List[Dict]:
        """Load existing market data from JSON file."""
        if not self.market_data_file.exists():
            logger.info("No existing market data file found. Starting fresh.")
            return []
        
        try:
            with open(self.market_data_file, 'r', encoding='utf-8') as f:
                market_data = json.load(f)
                logger.info(f"Loaded {len(market_data)} market data entries from {self.market_data_file}")
                return market_data
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            return []
    
    def _save_market_data(self, market_data: List[Dict]) -> None:
        """Save market data to JSON file."""
        try:
            with open(self.market_data_file, 'w', encoding='utf-8') as f:
                json.dump(market_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved {len(market_data)} market data entries to {self.market_data_file}")
        except Exception as e:
            logger.error(f"Error saving market data: {e}")
    
    def _load_state(self) -> Dict:
        """Load application state from JSON file."""
        if not self.state_file.exists():
            logger.info("No existing state file found. Starting fresh.")
            return {
                "last_update": None,
                "total_entries": 0,
                "update_count": 0,
                "last_error": None,
                "bdi_history": [],
                "p5_history": [],
                "bulk_rates_history": []
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
                "total_entries": 0,
                "update_count": 0,
                "last_error": None,
                "bdi_history": [],
                "p5_history": [],
                "bulk_rates_history": []
            }
    
    def _save_state(self, state: Dict) -> None:
        """Save application state to JSON file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Saved state to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _deduplicate_market_data(self, market_data: List[Dict]) -> List[Dict]:
        """Remove duplicate market data based on weekly report content."""
        unique_data = []
        seen_weekly_reports = set()
        
        for entry in market_data:
            weekly_reports = entry.get('weekly_reports', [])
            if not weekly_reports:
                # If no weekly reports, keep entry but mark as duplicate
                logger.debug(f"Entry without weekly reports skipped: {entry.get('scraped_at', '')}")
                continue
                
            # Check if this entry has any new weekly reports
            new_reports = []
            for report in weekly_reports:
                # Create unique identifier: week_number + date_report + category
                report_id = f"{report.get('week_number', '')}_{report.get('date_report', '')}_{report.get('category', '')}"
                
                if report_id not in seen_weekly_reports:
                    seen_weekly_reports.add(report_id)
                    new_reports.append(report)
                else:
                    logger.debug(f"Duplicate weekly report skipped: {report_id}")
            
            # Only keep entry if it has new weekly reports
            if new_reports:
                # Update entry to only include new reports
                entry['weekly_reports'] = new_reports
                unique_data.append(entry)
                logger.info(f"Added entry with {len(new_reports)} new weekly reports")
            else:
                logger.info(f"Entry skipped - all weekly reports already exist")
        
        logger.info(f"Deduplication: {len(market_data)} -> {len(unique_data)} entries")
        return unique_data
    
    def _merge_weekly_reports(self, new_data: Dict) -> Dict:
        """Merge new weekly reports with existing data, avoiding duplicates."""
        if not self.market_data:
            # First time, return new data as is
            return new_data
        
        existing_entry = self.market_data[0]
        existing_reports = existing_entry.get('weekly_reports', [])
        new_reports = new_data.get('weekly_reports', [])
        
        # Create set of existing report IDs
        existing_report_ids = set()
        for report in existing_reports:
            report_id = f"{report.get('week_number', '')}_{report.get('date_report', '')}_{report.get('category', '')}"
            existing_report_ids.add(report_id)
        
        # Add only new reports
        merged_reports = existing_reports.copy()
        for report in new_reports:
            report_id = f"{report.get('week_number', '')}_{report.get('date_report', '')}_{report.get('category', '')}"
            if report_id not in existing_report_ids:
                merged_reports.append(report)
                logger.info(f"Added new weekly report: {report_id}")
            else:
                logger.debug(f"Weekly report already exists: {report_id}")
        
        # Update the data with merged reports
        merged_data = new_data.copy()
        merged_data['weekly_reports'] = merged_reports
        merged_data['scraped_at'] = datetime.now().isoformat()  # Update timestamp
        
        logger.info(f"Merged weekly reports: {len(existing_reports)} existing + {len(new_reports)} new = {len(merged_reports)} total")
        return merged_data
    
    def _enrich_market_data(self, market_data: Dict) -> Dict:
        """Enrich market data with additional metadata."""
        # Add timestamp if not present
        if 'scraped_at' not in market_data:
            market_data['scraped_at'] = datetime.now().isoformat()
        
        # Add weekly reports summary
        weekly_reports = market_data.get('weekly_reports', [])
        if weekly_reports:
            market_data['weekly_reports_summary'] = {
                'total_reports': len(weekly_reports),
                'weeks_covered': [report.get('week_number', 'N/A') for report in weekly_reports],
                'categories': list(set(report.get('category', 'N/A') for report in weekly_reports))
            }
        
        # Add data freshness indicator
        if market_data.get('scraped_at'):
            try:
                scraped_time = datetime.fromisoformat(market_data['scraped_at'])
                market_data['data_age_hours'] = (datetime.now() - scraped_time).total_seconds() / 3600
            except (ValueError, TypeError):
                market_data['data_age_hours'] = None
        
        return market_data
    
    def update_market_data(self, force_update: bool = False) -> Dict:
        """
        Update market data from Baltic Exchange.
        
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
                if datetime.now() - last_update < timedelta(hours=1):  # Update every hour for market data
                    logger.info("Skipping update - data is recent")
                    return {
                        "status": "skipped",
                        "message": "Data is recent, skipping update",
                        "last_update": self.state['last_update'],
                        "total_entries": len(self.market_data)
                    }
            
            logger.info("Starting market data update from Baltic Exchange...")
            
            # Fetch new data from API
            new_market_data = self.api_client.get_weekly_roundup_data()
            
            if not new_market_data:
                logger.warning("No market data received from API")
                return {
                    "status": "error",
                    "message": "No market data received from API",
                    "new_entries": 0,
                    "total_entries": len(self.market_data)
                }
            
            logger.info(f"Received market data from Baltic Exchange API")
            
            # Enrich market data
            enriched_data = self._enrich_market_data(new_market_data)
            
            # Merge new weekly reports with existing data
            merged_data = self._merge_weekly_reports(enriched_data)
            
            # Calculate new reports
            new_reports_count = len(merged_data.get('weekly_reports', [])) - len(self.market_data[0].get('weekly_reports', [])) if self.market_data else len(merged_data.get('weekly_reports', []))
            
            # Update market data and state
            if self.market_data:
                # Update existing entry with merged data
                self.market_data[0].update(merged_data)
            else:
                # First time, create new entry
                self.market_data = [merged_data]
            self.state.update({
                "last_update": datetime.now().isoformat(),
                "total_entries": len(self.market_data),
                "update_count": self.state.get("update_count", 0) + 1,
                "last_error": None
            })
            
            # Update historical data
            self._update_historical_data(enriched_data)
            
            # Save data
            self._save_market_data(self.market_data)
            self._save_state(self.state)
            
            duration = time.time() - start_time
            
            logger.info(f"Update complete: {new_reports_count} new reports, "
                       f"{len(self.market_data)} total entries, {duration:.2f}s")
            
            return {
                "status": "success",
                "message": "Successfully updated market data",
                "new_entries": new_reports_count,
                "total_entries": len(self.market_data),
                "duration_seconds": round(duration, 2),
                "last_update": self.state["last_update"],
                "bdi_value": enriched_data.get('bdi', {}).get('current_value'),
                "p5_value": enriched_data.get('p5', {}).get('summary', {}).get('value')
            }
            
        except Exception as e:
            error_msg = f"Error updating market data: {str(e)}"
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
                "new_entries": 0,
                "total_entries": len(self.market_data)
            }
    
    def _update_historical_data(self, new_data: Dict) -> None:
        """Update historical data tracking for trends analysis."""
        try:
            # Update BDI history
            if new_data.get('bdi', {}).get('current_value'):
                bdi_entry = {
                    'timestamp': new_data['scraped_at'],
                    'value': new_data['bdi']['current_value'],
                    'change': new_data['bdi'].get('change'),
                    'change_percentage': new_data['bdi'].get('change_percentage')
                }
                self.state['bdi_history'].append(bdi_entry)
                
                # Keep only last 100 entries
                if len(self.state['bdi_history']) > 100:
                    self.state['bdi_history'] = self.state['bdi_history'][-100:]
            
            # Update P5 history
            if new_data.get('p5', {}).get('summary', {}).get('value'):
                p5_entry = {
                    'timestamp': new_data['scraped_at'],
                    'value': new_data['p5']['summary']['value']
                }
                self.state['p5_history'].append(p5_entry)
                
                # Keep only last 100 entries
                if len(self.state['p5_history']) > 100:
                    self.state['p5_history'] = self.state['p5_history'][-100:]
            
            # Update bulk rates history
            bulk_rates = new_data.get('bulk_rates', {})
            if any(bulk_rates.get(vt, {}).get('rate') for vt in ['capesize', 'panamax', 'supramax', 'handysize']):
                rates_entry = {
                    'timestamp': new_data['scraped_at'],
                    'capesize': bulk_rates.get('capesize', {}).get('rate'),
                    'panamax': bulk_rates.get('panamax', {}).get('rate'),
                    'supramax': bulk_rates.get('supramax', {}).get('rate'),
                    'handysize': bulk_rates.get('handysize', {}).get('rate')
                }
                self.state['bulk_rates_history'].append(rates_entry)
                
                # Keep only last 100 entries
                if len(self.state['bulk_rates_history']) > 100:
                    self.state['bulk_rates_history'] = self.state['bulk_rates_history'][-100:]
                    
        except Exception as e:
            logger.error(f"Error updating historical data: {e}")
    
    def get_market_data(self, filters: Dict = None) -> List[Dict]:
        """
        Get market data with optional filtering.
        
        Args:
            filters: Dictionary with filter options
            
        Returns:
            List of filtered market data
        """
        if not filters:
            return self.market_data
        
        filtered_data = []
        
        for entry in self.market_data:
            # Apply filters
            if self._matches_filters(entry, filters):
                filtered_data.append(entry)
        
        logger.info(f"Filtered {len(self.market_data)} entries -> {len(filtered_data)} results")
        return filtered_data
    
    def _matches_filters(self, entry: Dict, filters: Dict) -> bool:
        """Check if market data entry matches all specified filters."""
        
        # Date range filter
        if 'start_date' in filters and filters['start_date']:
            try:
                start_date = datetime.fromisoformat(filters['start_date'])
                entry_date = datetime.fromisoformat(entry.get('scraped_at', '1900-01-01'))
                if entry_date < start_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        if 'end_date' in filters and filters['end_date']:
            try:
                end_date = datetime.fromisoformat(filters['end_date'])
                entry_date = datetime.fromisoformat(entry.get('scraped_at', '2100-01-01'))
                if entry_date > end_date:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Data quality filter
        if 'min_data_quality' in filters and filters['min_data_quality']:
            quality_score = sum([
                1 if entry.get('data_quality', {}).get('bdi_complete') else 0,
                1 if entry.get('data_quality', {}).get('p5_complete') else 0,
                1 if entry.get('data_quality', {}).get('bulk_rates_complete') else 0
            ])
            if quality_score < filters['min_data_quality']:
                return False
        
        # BDI value filter
        if 'min_bdi' in filters and filters['min_bdi']:
            bdi_value = entry.get('bdi', {}).get('current_value')
            if not bdi_value or bdi_value < filters['min_bdi']:
                return False
        
        if 'max_bdi' in filters and filters['max_bdi']:
            bdi_value = entry.get('bdi', {}).get('current_value')
            if not bdi_value or bdi_value > filters['max_bdi']:
                return False
        
        return True
    
    def get_latest_data(self) -> Dict:
        """Get the most recent market data entry."""
        if not self.market_data:
            return {}
        
        # Sort by scraped_at timestamp and get the latest
        sorted_data = sorted(self.market_data, key=lambda x: x.get('scraped_at', ''), reverse=True)
        return sorted_data[0] if sorted_data else {}
    
    def get_bdi_trend(self, days: int = 30) -> Dict:
        """Get BDI trend data for the specified number of days."""
        if not self.state.get('bdi_history'):
            return {"trend": "insufficient_data", "data_points": 0}
        
        # Filter history to requested time period
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_data = [
            entry for entry in self.state['bdi_history']
            if datetime.fromisoformat(entry['timestamp']) > cutoff_time
        ]
        
        if len(recent_data) < 2:
            return {"trend": "insufficient_data", "data_points": len(recent_data)}
        
        # Calculate trend
        values = [entry['value'] for entry in recent_data if entry.get('value')]
        if len(values) < 2:
            return {"trend": "insufficient_data", "data_points": len(values)}
        
        trend = "up" if values[-1] > values[0] else "down" if values[-1] < values[0] else "stable"
        change = values[-1] - values[0]
        change_percentage = (change / values[0]) * 100 if values[0] != 0 else 0
        
        return {
            "trend": trend,
            "data_points": len(values),
            "start_value": values[0],
            "end_value": values[-1],
            "change": change,
            "change_percentage": round(change_percentage, 2),
            "period_days": days
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about the market data."""
        if not self.market_data:
            return {
                "total_entries": 0,
                "last_update": None,
                "data_quality_summary": {},
                "bdi_summary": {},
                "p5_summary": {},
                "bulk_rates_summary": {}
            }
        
        # Data quality summary
        quality_summary = {
            "total_entries": len(self.market_data),
            "complete_bdi": sum(1 for e in self.market_data if e.get('data_quality', {}).get('bdi_complete')),
            "complete_p5": sum(1 for e in self.market_data if e.get('data_quality', {}).get('p5_complete')),
            "complete_bulk_rates": sum(1 for e in self.market_data if e.get('data_quality', {}).get('bulk_rates_complete'))
        }
        
        # BDI summary
        bdi_values = [e.get('bdi', {}).get('current_value') for e in self.market_data if e.get('bdi', {}).get('current_value')]
        bdi_summary = {
            "current": bdi_values[-1] if bdi_values else None,
            "min": min(bdi_values) if bdi_values else None,
            "max": max(bdi_values) if bdi_values else None,
            "average": sum(bdi_values) / len(bdi_values) if bdi_values else None
        }
        
        # P5 summary
        p5_values = [e.get('p5', {}).get('summary', {}).get('value') for e in self.market_data if e.get('p5', {}).get('summary', {}).get('value')]
        p5_summary = {
            "current": p5_values[-1] if p5_values else None,
            "min": min(p5_values) if p5_values else None,
            "max": max(p5_values) if p5_values else None,
            "average": sum(p5_values) / len(p5_values) if p5_values else None
        }
        
        # Bulk rates summary
        bulk_rates_summary = {}
        for vessel_type in ['capesize', 'panamax', 'supramax', 'handysize']:
            rates = [e.get('bulk_rates', {}).get(vessel_type, {}).get('rate') for e in self.market_data if e.get('bulk_rates', {}).get(vessel_type, {}).get('rate')]
            if rates:
                bulk_rates_summary[vessel_type] = {
                    "current": rates[-1],
                    "min": min(rates),
                    "max": max(rates),
                    "average": sum(rates) / len(rates)
                }
        
        return {
            "total_entries": len(self.market_data),
            "last_update": self.state.get("last_update"),
            "update_count": self.state.get("update_count", 0),
            "data_quality_summary": quality_summary,
            "bdi_summary": bdi_summary,
            "p5_summary": p5_summary,
            "bulk_rates_summary": bulk_rates_summary
        }
    
    def export_csv(self, filters: Dict = None) -> str:
        """Export market data to CSV format."""
        import csv
        import io
        
        data = self.get_market_data(filters)
        
        if not data:
            return ""
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [
            'Scraped At', 'BDI Value', 'BDI Change', 'BDI Change %', 'P5 Value',
            'Capesize Rate', 'Panamax Rate', 'Supramax Rate', 'Handysize Rate',
            'Market Sentiment', 'Data Quality Score'
        ]
        writer.writerow(headers)
        
        # Write data
        for entry in data:
            bdi = entry.get('bdi', {})
            p5 = entry.get('p5', {})
            bulk_rates = entry.get('bulk_rates', {})
            market_summary = entry.get('market_summary', {})
            data_quality = entry.get('data_quality', {})
            
            # Calculate data quality score
            quality_score = sum([
                1 if data_quality.get('bdi_complete') else 0,
                1 if data_quality.get('p5_complete') else 0,
                1 if data_quality.get('bulk_rates_complete') else 0
            ])
            
            row = [
                entry.get('scraped_at', ''),
                bdi.get('current_value', ''),
                bdi.get('change', ''),
                bdi.get('change_percentage', ''),
                p5.get('summary', {}).get('value', ''),
                bulk_rates.get('capesize', {}).get('rate', ''),
                bulk_rates.get('panamax', {}).get('rate', ''),
                bulk_rates.get('supramax', {}).get('rate', ''),
                bulk_rates.get('handysize', {}).get('rate', ''),
                market_summary.get('market_sentiment', ''),
                quality_score
            ]
            writer.writerow(row)
        
        return output.getvalue()
    
    def test_connection(self) -> Dict:
        """Test connection to Baltic Exchange."""
        return self.api_client.test_connection()
