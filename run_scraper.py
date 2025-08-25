#!/usr/bin/env python3
"""
Command-line interface for ANP Ports Vessel Scraper.
Provides commands for updating data, viewing statistics, and managing the system.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from scraper import ANPPortsVesselScraper
    from matcher import ANPPortsVesselMatcher
    from adapters.anp_api import ANPAPIClient
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("🚢 ANP Ports Vessel Scraper - Command Line Interface")
    print("=" * 60)
    print("Monitor Moroccan port activities and vessel movements")
    print("=" * 60)

def print_status(scraper: ANPPortsVesselScraper):
    """Print current system status."""
    print("\n📊 System Status:")
    print("-" * 30)
    
    # Get statistics
    stats = scraper.get_statistics()
    
    print(f"Total Vessels: {stats['total_vessels']}")
    print(f"Last Update: {stats.get('last_update', 'Never')}")
    print(f"Update Count: {stats.get('update_count', 0)}")
    
    if stats['total_vessels'] > 0:
        print(f"\nTop Vessel Types:")
        for vessel_type, count in list(stats['vessel_types'].items())[:5]:
            print(f"  {vessel_type}: {count}")
        
        print(f"\nTop Operators:")
        for operator, count in list(stats['operators'].items())[:5]:
            print(f"  {operator}: {count}")
        
        print(f"\nTop Ports:")
        for port, count in list(stats['ports'].items())[:5]:
            print(f"  {port}: {count}")

def update_data(scraper: ANPPortsVesselScraper, force: bool = False):
    """Update vessel data from ANP API."""
    print(f"\n🔄 Updating vessel data...")
    if force:
        print("Force update enabled - ignoring recent data check")
    
    try:
        result = scraper.update_vessel_data(force_update=force)
        
        if result['status'] == 'success':
            print(f"✅ Update successful!")
            print(f"   New vessels: {result['new_vessels']}")
            print(f"   Total vessels: {result['total_vessels']}")
            print(f"   Duration: {result['duration_seconds']}s")
            print(f"   Last update: {result['last_update']}")
        elif result['status'] == 'skipped':
            print(f"⏭️  Update skipped: {result['message']}")
            print(f"   Last update: {result['last_update']}")
            print(f"   Total vessels: {result['total_vessels']}")
        else:
            print(f"❌ Update failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error during update: {e}")
        logger.error(f"Update error: {e}")

def show_statistics(scraper: ANPPortsVesselScraper):
    """Show detailed statistics."""
    print("\n📈 Detailed Statistics:")
    print("-" * 30)
    
    try:
        stats = scraper.get_statistics()
        
        print(f"Total Vessels: {stats['total_vessels']}")
        print(f"Last Update: {stats.get('last_update', 'Never')}")
        print(f"Update Count: {stats.get('update_count', 0)}")
        
        if stats['total_vessels'] > 0:
            print(f"\nVessel Types (Top 10):")
            for vessel_type, count in stats['vessel_types'].items():
                print(f"  {vessel_type}: {count}")
            
            print(f"\nOperators (Top 10):")
            for operator, count in stats['operators'].items():
                print(f"  {operator}: {count}")
            
            print(f"\nPorts (Top 10):")
            for port, count in stats['ports'].items():
                print(f"  {port}: {count}")
            
            print(f"\nSituations (Top 10):")
            for situation, count in stats['situations'].items():
                print(f"  {situation}: {count}")
        else:
            print("No vessel data available")
            
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        logger.error(f"Statistics error: {e}")

def export_csv(scraper: ANPPortsVesselScraper, output_file: str = None):
    """Export data to CSV."""
    print(f"\n📥 Exporting data to CSV...")
    
    try:
        csv_data = scraper.export_csv()
        
        if not csv_data:
            print("❌ No data to export")
            return
        
        if output_file:
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(csv_data)
            print(f"✅ Data exported to: {output_file}")
        else:
            # Print to console
            print("CSV Data:")
            print("-" * 30)
            print(csv_data)
            
    except Exception as e:
        print(f"❌ Error exporting CSV: {e}")
        logger.error(f"Export error: {e}")

def clean_duplicates(scraper: ANPPortsVesselScraper):
    """Clean duplicate vessels."""
    print(f"\n🧹 Cleaning duplicate vessels...")
    
    try:
        result = scraper.clean_duplicates()
        
        if result['status'] == 'success':
            print(f"✅ Cleanup successful!")
            print(f"   Vessels before: {result['vessels_before']}")
            print(f"   Vessels after: {result['vessels_after']}")
            print(f"   Duplicates removed: {result['duplicates_removed']}")
        else:
            print(f"❌ Cleanup failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        logger.error(f"Cleanup error: {e}")

def test_connection(scraper: ANPPortsVesselScraper):
    """Test connection to ANP API."""
    print(f"\n🔌 Testing connection to ANP API...")
    
    try:
        result = scraper.test_connection()
        
        if result['status'] == 'success':
            print(f"✅ Connection successful!")
            print(f"   API Endpoint: {result['api_endpoint']}")
            print(f"   Vessel Count: {result['vessel_count']}")
            print(f"   Response Time: {result['response_time_seconds']}s")
        else:
            print(f"❌ Connection failed: {result['message']}")
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        logger.error(f"Connection test error: {e}")

def show_filter_options(scraper: ANPPortsVesselScraper):
    """Show available filter options."""
    print(f"\n🔍 Available Filter Options:")
    print("-" * 30)
    
    try:
        vessels = scraper.get_vessels()
        if not vessels:
            print("No vessels available for filtering")
            return
        
        # Get filter options from matcher
        matcher = ANPPortsVesselMatcher()
        options = matcher.get_filter_options(vessels)
        
        print(f"Vessel Types ({len(options['vessel_types'])}):")
        for vt in options['vessel_types'][:10]:
            print(f"  {vt}")
        if len(options['vessel_types']) > 10:
            print(f"  ... and {len(options['vessel_types']) - 10} more")
        
        print(f"\nOperators ({len(options['operators'])}):")
        for op in options['operators'][:10]:
            print(f"  {op}")
        if len(options['operators']) > 10:
            print(f"  ... and {len(options['operators']) - 10} more")
        
        print(f"\nPorts ({len(options['ports'])}):")
        for port in options['ports'][:10]:
            print(f"  {port}")
        if len(options['ports']) > 10:
            print(f"  ... and {len(options['ports']) - 10} more")
        
        print(f"\nSituations ({len(options['situations'])}):")
        for situation in options['situations'][:10]:
            print(f"  {situation}")
        if len(options['situations']) > 10:
            print(f"  ... and {len(options['situations']) - 10} more")
            
    except Exception as e:
        print(f"❌ Error getting filter options: {e}")
        logger.error(f"Filter options error: {e}")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="ANP Ports Vessel Scraper - Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update vessel data
  python run_scraper.py --update
  
  # Force update (ignore recent data check)
  python run_scraper.py --update --force
  
  # Show statistics
  python run_scraper.py --stats
  
  # Export to CSV
  python run_scraper.py --export-csv vessels.csv
  
  # Test API connection
  python run_scraper.py --test-connection
  
  # Clean duplicates
  python run_scraper.py --clean-duplicates
        """
    )
    
    # Action arguments
    parser.add_argument('--update', action='store_true',
                       help='Update vessel data from ANP API')
    parser.add_argument('--force', action='store_true',
                       help='Force update even if data is recent')
    parser.add_argument('--stats', action='store_true',
                       help='Show detailed statistics')
    parser.add_argument('--export-csv', metavar='FILE',
                       help='Export data to CSV file')
    parser.add_argument('--clean-duplicates', action='store_true',
                       help='Clean duplicate vessels from database')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test connection to ANP API')
    parser.add_argument('--filter-options', action='store_true',
                       help='Show available filter options')
    parser.add_argument('--status', action='store_true',
                       help='Show system status')
    
    # Data directory
    parser.add_argument('--data-dir', metavar='DIR',
                       help='Data directory (default: ./data)')
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Initialize scraper
    try:
        scraper = ANPPortsVesselScraper(data_dir=args.data_dir)
        print(f"✅ Scraper initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {e}")
        sys.exit(1)
    
    # Show status by default if no other action specified
    if not any([args.update, args.stats, args.export_csv, args.clean_duplicates, 
                args.test_connection, args.filter_options]):
        args.status = True
    
    # Execute actions
    if args.status:
        print_status(scraper)
    
    if args.update:
        update_data(scraper, force=args.force)
    
    if args.stats:
        show_statistics(scraper)
    
    if args.export_csv:
        export_csv(scraper, args.export_csv)
    
    if args.clean_duplicates:
        clean_duplicates(scraper)
    
    if args.test_connection:
        test_connection(scraper)
    
    if args.filter_options:
        show_filter_options(scraper)
    
    print("\n" + "=" * 60)
    print("🏁 CLI session completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
