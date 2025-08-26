#!/usr/bin/env python3
"""
Example usage of the Baltic Exchange Weekly Market Roundup Scraper
Demonstrates how to use the scraper programmatically.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baltic_exchange_scraper import BalticExchangeScraper

def main():
    """Example usage of the Baltic Exchange scraper."""
    
    print("Baltic Exchange Scraper - Example Usage")
    print("=" * 50)
    
    try:
        # Initialize the scraper
        print("1. Initializing scraper...")
        scraper = BalticExchangeScraper(data_dir="data")
        print("   ✓ Scraper initialized successfully")
        
        # Test connection
        print("\n2. Testing connection...")
        connection_result = scraper.test_connection()
        if connection_result['status'] == 'success':
            print("   ✓ Connection successful")
            print(f"   Response time: {connection_result['response_time_seconds']}s")
        else:
            print("   ✗ Connection failed")
            return
        
        # Update market data
        print("\n3. Updating market data...")
        result = scraper.update_market_data(force_update=True)
        
        if result['status'] == 'success':
            print("   ✓ Data update successful")
            print(f"   New entries: {result['new_entries']}")
            print(f"   Total entries: {result['total_entries']}")
        else:
            print(f"   ✗ Update failed: {result['message']}")
            return
        
        # Get latest data
        print("\n4. Retrieving latest market data...")
        latest_data = scraper.get_latest_data()
        
        if latest_data:
            print("   ✓ Latest data retrieved")
            
            # Display weekly reports information
            weekly_reports = latest_data.get('weekly_reports', [])
            if weekly_reports:
                print(f"\n   Weekly Reports ({len(weekly_reports)} total):")
                for i, report in enumerate(weekly_reports, 1):
                    print(f"     {i}. Week {report.get('week_number', 'N/A')} - {report.get('date_report', 'N/A')}")
                    print(f"        Category: {report.get('category', 'N/A')}")
                    print(f"        Capesize Content: {len(report.get('capesize_content', ''))} chars")
                    print(f"        Panamax Content: {len(report.get('panamax_content', ''))} chars")
                    print(f"        Ultramax/Supramax Content: {len(report.get('ultramax_supramax_content', ''))} chars")
                    print(f"        Handysize Content: {len(report.get('handysize_content', ''))} chars")
                    print(f"        Report Link: {report.get('link_report', 'N/A')}")
                    if i < len(weekly_reports):
                        print()
            else:
                print("\n   ⚠ No weekly reports available")
            
            # Display data summary
            print(f"\n   Data Summary:")
            print(f"     Total Weekly Reports: {len(weekly_reports)}")
            print(f"     Scraped At: {latest_data.get('scraped_at', 'N/A')}")
            print(f"     Source URL: {latest_data.get('source_url', 'N/A')}")
            print(f"     Method: {latest_data.get('method', 'N/A')}")
        
        # Get statistics
        print("\n5. Getting statistics...")
        stats = scraper.get_statistics()
        print("   ✓ Statistics retrieved")
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   Update count: {stats['update_count']}")
        print(f"   Last update: {stats['last_update']}")
        
        # Show weekly reports summary
        print("\n6. Weekly Reports Summary...")
        all_data = scraper.get_market_data()
        if all_data:
            total_reports = 0
            for entry in all_data:
                if entry.get('weekly_reports'):
                    total_reports += len(entry['weekly_reports'])
            
            print("   ✓ Weekly reports analysis completed")
            print(f"   Total Weekly Reports: {total_reports}")
            print(f"   Data Entries: {len(all_data)}")
            
            if all_data:
                latest_entry = all_data[0]
                print(f"   Latest Update: {latest_entry.get('scraped_at', 'N/A')}")
                print(f"   Source: {latest_entry.get('source_url', 'N/A')}")
        else:
            print("   ⚠ No data available for analysis")
        
        # Export to CSV
        print("\n7. Exporting to CSV...")
        csv_data = scraper.export_csv()
        if csv_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_file = f"example_export_{timestamp}.csv"
            
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(csv_data)
            
            print(f"   ✓ Data exported to: {csv_file}")
            lines = csv_data.splitlines()
            print(f"   CSV contains {len(lines)} lines")
        else:
            print("   ⚠ No data available for CSV export")
        
        print("\n" + "=" * 50)
        print("Example completed successfully!")
        print("Check the generated files and data directory for results.")
        
    except Exception as e:
        print(f"\n❌ Error during example execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
