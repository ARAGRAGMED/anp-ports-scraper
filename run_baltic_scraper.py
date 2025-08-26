#!/usr/bin/env python3
"""
Baltic Exchange Weekly Market Roundup Scraper
Main script to run the Baltic Exchange scraper and collect market data.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baltic_exchange_scraper import BalticExchangeScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baltic_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the Baltic Exchange scraper."""
    parser = argparse.ArgumentParser(
        description="Baltic Exchange Weekly Market Roundup Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run scraper with default settings
  python run_baltic_scraper.py
  
  # Force update even if data is recent
  python run_baltic_scraper.py --force
  
  # Export data to CSV
  python run_baltic_scraper.py --export-csv
  
  # Get statistics only
  python run_baltic_scraper.py --stats-only
  
  # Test connection
  python run_baltic_scraper.py --test-connection
        """
    )
    
    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory to store data files (default: data)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update even if data is recent'
    )
    
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Export data to CSV format'
    )
    
    parser.add_argument(
        '--csv-file',
        default=None,
        help='Output CSV file path (default: market_data_YYYY-MM-DD.csv)'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='Show statistics only, do not update data'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test connection to Baltic Exchange website'
    )
    
    parser.add_argument(
        '--trend-days',
        type=int,
        default=30,
        help='Number of days for trend analysis (default: 30)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize scraper
        logger.info("Initializing Baltic Exchange Scraper...")
        scraper = BalticExchangeScraper(data_dir=args.data_dir)
        
        # Test connection if requested
        if args.test_connection:
            logger.info("Testing connection to Baltic Exchange...")
            result = scraper.test_connection()
            print("\n" + "="*50)
            print("CONNECTION TEST RESULTS")
            print("="*50)
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print(f"Response Time: {result['response_time_seconds']}s")
            print(f"Endpoint: {result['api_endpoint']}")
            return
        
        # Show statistics only if requested
        if args.stats_only:
            logger.info("Getting statistics...")
            stats = scraper.get_statistics()
            print("\n" + "="*50)
            print("MARKET DATA STATISTICS")
            print("="*50)
            print(f"Total Entries: {stats['total_entries']}")
            print(f"Last Update: {stats['last_update']}")
            print(f"Update Count: {stats['update_count']}")
            
            if stats['bdi_summary']['current']:
                print(f"\nBDI Summary:")
                print(f"  Current: {stats['bdi_summary']['current']}")
                print(f"  Min: {stats['bdi_summary']['min']}")
                print(f"  Max: {stats['bdi_summary']['max']}")
                print(f"  Average: {stats['bdi_summary']['average']:.2f}")
            
            if stats['p5_summary']['current']:
                print(f"\nP5 Summary:")
                print(f"  Current: {stats['p5_summary']['current']}")
                print(f"  Min: {stats['p5_summary']['min']}")
                print(f"  Max: {stats['p5_summary']['max']}")
                print(f"  Average: {stats['p5_summary']['average']:.2f}")
            
            # Show BDI trend
            trend = scraper.get_bdi_trend(days=args.trend_days)
            if trend['trend'] != 'insufficient_data':
                print(f"\nBDI Trend ({args.trend_days} days):")
                print(f"  Direction: {trend['trend'].upper()}")
                print(f"  Change: {trend['change']} ({trend['change_percentage']}%)")
                print(f"  Start: {trend['start_value']} → End: {trend['end_value']}")
                print(f"  Data Points: {trend['data_points']}")
            else:
                print(f"\nBDI Trend: Insufficient data for {args.trend_days} days")
            
            return
        
        # Update market data
        logger.info("Starting market data update...")
        result = scraper.update_market_data(force_update=args.force)
        
        # Display results
        print("\n" + "="*50)
        print("UPDATE RESULTS")
        print("="*50)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"New Entries: {result['new_entries']}")
            print(f"Total Entries: {result['total_entries']}")
            print(f"Duration: {result['duration_seconds']}s")
            print(f"Last Update: {result['last_update']}")
            
            if result.get('bdi_value'):
                print(f"BDI Value: {result['bdi_value']}")
            if result.get('p5_value'):
                print(f"P5 Value: {result['p5_value']}")
        
        elif result['status'] == 'skipped':
            print(f"Last Update: {result['last_update']}")
            print(f"Total Entries: {result['total_entries']}")
        
        # Show latest data
        latest_data = scraper.get_latest_data()
        if latest_data:
            print(f"\n" + "="*50)
            print("LATEST MARKET DATA")
            print("="*50)
            print(f"Scraped At: {latest_data.get('scraped_at', 'N/A')}")
            
            bdi = latest_data.get('bdi', {})
            if bdi.get('current_value'):
                print(f"BDI: {bdi['current_value']}")
                if bdi.get('change'):
                    change_str = f"{bdi['change']:+}"
                    if bdi.get('change_percentage'):
                        change_str += f" ({bdi['change_percentage']:+.2f}%)"
                    print(f"BDI Change: {change_str}")
            
            p5 = latest_data.get('p5', {})
            if p5.get('summary', {}).get('value'):
                print(f"P5: {p5['summary']['value']}")
            
            bulk_rates = latest_data.get('bulk_rates', {})
            if any(bulk_rates.get(vt, {}).get('rate') for vt in ['capesize', 'panamax', 'supramax', 'handysize']):
                print("Bulk Rates:")
                for vessel_type in ['capesize', 'panamax', 'supramax', 'handysize']:
                    rate = bulk_rates.get(vessel_type, {}).get('rate')
                    if rate:
                        print(f"  {vessel_type.title()}: {rate}")
            
            market_summary = latest_data.get('market_summary', {})
            if market_summary.get('market_sentiment'):
                print(f"Market Sentiment: {market_summary['market_sentiment']}")
        
        # Export to CSV if requested
        if args.export_csv:
            logger.info("Exporting data to CSV...")
            csv_data = scraper.export_csv()
            
            if csv_data:
                # Determine output file
                if args.csv_file:
                    csv_file = args.csv_file
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%d")
                    csv_file = f"market_data_{timestamp}.csv"
                
                # Write CSV file
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write(csv_data)
                
                print(f"\nData exported to: {csv_file}")
                print(f"CSV contains {len(csv_data.splitlines()) - 1} data rows")
            else:
                print("\nNo data available for CSV export")
        
        # Show summary statistics
        stats = scraper.get_statistics()
        print(f"\n" + "="*50)
        print("SUMMARY")
        print("="*50)
        print(f"Total Data Entries: {stats['total_entries']}")
        print(f"Weekly Reports Summary:")
        all_data = scraper.get_market_data()
        if all_data:
            total_reports = 0
            for entry in all_data:
                if entry.get('weekly_reports'):
                    total_reports += len(entry['weekly_reports'])
            print(f"  Total Weekly Reports: {total_reports}")
            print(f"  Data Entries: {len(all_data)}")
        else:
            print(f"  No data available")
        
        logger.info("Baltic Exchange scraper completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
        print("\nScraper interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
