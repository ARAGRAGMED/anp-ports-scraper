#!/usr/bin/env python3
"""
Test script for Baltic Exchange Weekly Market Roundup Scraper
Tests the scraper functionality and data extraction.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from baltic_exchange_scraper import BalticExchangeScraper
from adapters.baltic_exchange_api import BalticExchangeAPIClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_client():
    """Test the Baltic Exchange API client."""
    print("="*60)
    print("TESTING BALTIC EXCHANGE API CLIENT")
    print("="*60)
    
    try:
        # Initialize API client
        api_client = BalticExchangeAPIClient()
        print("✓ API client initialized successfully")
        
        # Test connection
        print("\nTesting connection...")
        connection_result = api_client.test_connection()
        print(f"Connection Status: {connection_result['status']}")
        print(f"Message: {connection_result['message']}")
        print(f"Response Time: {connection_result['response_time_seconds']}s")
        
        if connection_result['status'] == 'success':
            print("✓ Connection test successful")
            
            # Test data fetching
            print("\nFetching weekly roundup data...")
            market_data = api_client.get_weekly_roundup_data()
            
            if market_data:
                print("✓ Data fetched successfully")
                print(f"Data keys: {list(market_data.keys())}")
                
                # Check BDI data
                bdi_data = market_data.get('bdi', {})
                if bdi_data.get('current_value'):
                    print(f"✓ BDI value found: {bdi_data['current_value']}")
                else:
                    print("⚠ BDI value not found")
                
                # Check P5 data
                p5_data = market_data.get('p5', {})
                if p5_data.get('summary', {}).get('value'):
                    print(f"✓ P5 value found: {p5_data['summary']['value']}")
                else:
                    print("⚠ P5 value not found")
                
                # Check bulk rates data
                bulk_rates = market_data.get('bulk_rates', {})
                rates_found = []
                for vessel_type in ['capesize', 'panamax', 'supramax', 'handysize']:
                    if bulk_rates.get(vessel_type, {}).get('rate'):
                        rates_found.append(f"{vessel_type}: {bulk_rates[vessel_type]['rate']}")
                
                if rates_found:
                    print(f"✓ Bulk rates found: {', '.join(rates_found)}")
                else:
                    print("⚠ No bulk rates found")
                
                # Show raw content info
                raw_content = market_data.get('raw_content', {})
                if raw_content.get('page_title'):
                    print(f"✓ Page title: {raw_content['page_title']}")
                
                # Save sample data for inspection
                sample_file = "sample_market_data.json"
                with open(sample_file, 'w', encoding='utf-8') as f:
                    json.dump(market_data, f, indent=2, ensure_ascii=False, default=str)
                print(f"✓ Sample data saved to: {sample_file}")
                
            else:
                print("✗ No data received from API")
                return False
                
        else:
            print("✗ Connection test failed")
            return False
            
    except Exception as e:
        print(f"✗ API client test failed: {e}")
        logger.error(f"API client test error: {e}")
        return False
    
    return True

def test_scraper():
    """Test the main scraper functionality."""
    print("\n" + "="*60)
    print("TESTING BALTIC EXCHANGE SCRAPER")
    print("="*60)
    
    try:
        # Initialize scraper
        scraper = BalticExchangeScraper(data_dir="test_data")
        print("✓ Scraper initialized successfully")
        
        # Test statistics
        print("\nTesting statistics...")
        stats = scraper.get_statistics()
        print(f"Total entries: {stats['total_entries']}")
        print(f"Last update: {stats['last_update']}")
        print("✓ Statistics retrieved successfully")
        
        # Test market data update
        print("\nTesting market data update...")
        result = scraper.update_market_data(force_update=True)
        
        print(f"Update status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print("✓ Market data update successful")
            print(f"New entries: {result['new_entries']}")
            print(f"Total entries: {result['total_entries']}")
            
            # Test getting latest data
            print("\nTesting latest data retrieval...")
            latest_data = scraper.get_latest_data()
            if latest_data:
                print("✓ Latest data retrieved successfully")
                print(f"Scraped at: {latest_data.get('scraped_at', 'N/A')}")
                
                # Show key metrics
                bdi = latest_data.get('bdi', {})
                if bdi.get('current_value'):
                    print(f"BDI: {bdi['current_value']}")
                
                p5 = latest_data.get('p5', {})
                if p5.get('summary', {}).get('value'):
                    print(f"P5: {p5['summary']['value']}")
                
                # Test CSV export
                print("\nTesting CSV export...")
                csv_data = scraper.export_csv()
                if csv_data:
                    print("✓ CSV export successful")
                    lines = csv_data.splitlines()
                    print(f"CSV contains {len(lines)} lines")
                    
                    # Save CSV for inspection
                    csv_file = "test_market_data.csv"
                    with open(csv_file, 'w', encoding='utf-8') as f:
                        f.write(csv_data)
                    print(f"✓ CSV saved to: {csv_file}")
                else:
                    print("⚠ CSV export returned no data")
            
            # Test trend analysis
            print("\nTesting trend analysis...")
            trend = scraper.get_bdi_trend(days=7)
            print(f"BDI trend (7 days): {trend['trend']}")
            if trend['trend'] != 'insufficient_data':
                print(f"Change: {trend['change']} ({trend['change_percentage']}%)")
            
            # Test filtering
            print("\nTesting data filtering...")
            filtered_data = scraper.get_market_data(filters={'min_data_quality': 1})
            print(f"Filtered data entries: {len(filtered_data)}")
            
        else:
            print(f"✗ Market data update failed: {result['message']}")
            return False
        
        # Test statistics after update
        print("\nTesting updated statistics...")
        updated_stats = scraper.get_statistics()
        print(f"Updated total entries: {updated_stats['total_entries']}")
        print(f"Update count: {updated_stats['update_count']}")
        
        print("✓ All scraper tests completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Scraper test failed: {e}")
        logger.error(f"Scraper test error: {e}")
        return False

def test_data_quality():
    """Test data quality and validation."""
    print("\n" + "="*60)
    print("TESTING DATA QUALITY")
    print("="*60)
    
    try:
        scraper = BalticExchangeScraper(data_dir="test_data")
        
        # Get latest data
        latest_data = scraper.get_latest_data()
        if not latest_data:
            print("⚠ No data available for quality testing")
            return False
        
        print("✓ Data quality test started")
        
        # Check data structure
        required_keys = ['scraped_at', 'bdi', 'p5', 'bulk_rates', 'market_summary']
        missing_keys = [key for key in required_keys if key not in latest_data]
        
        if missing_keys:
            print(f"⚠ Missing required keys: {missing_keys}")
        else:
            print("✓ All required data keys present")
        
        # Check BDI data quality
        bdi = latest_data.get('bdi', {})
        bdi_quality = {
            'has_value': bool(bdi.get('current_value')),
            'has_change': bool(bdi.get('change')),
            'has_percentage': bool(bdi.get('change_percentage')),
            'has_date': bool(bdi.get('date'))
        }
        
        print(f"BDI data quality: {bdi_quality}")
        bdi_score = sum(bdi_quality.values()) / len(bdi_quality) * 100
        print(f"BDI completeness: {bdi_score:.1f}%")
        
        # Check P5 data quality
        p5 = latest_data.get('p5', {})
        p5_quality = {
            'has_summary': bool(p5.get('summary', {}).get('value')),
            'has_routes': bool(p5.get('routes'))
        }
        
        print(f"P5 data quality: {p5_quality}")
        p5_score = sum(p5_quality.values()) / len(p5_quality) * 100
        print(f"P5 completeness: {p5_score:.1f}%")
        
        # Check bulk rates quality
        bulk_rates = latest_data.get('bulk_rates', {})
        vessel_types = ['capesize', 'panamax', 'supramax', 'handysize']
        rates_quality = {}
        
        for vessel_type in vessel_types:
            rates_quality[vessel_type] = bool(bulk_rates.get(vessel_type, {}).get('rate'))
        
        print(f"Bulk rates quality: {rates_quality}")
        rates_score = sum(rates_quality.values()) / len(rates_quality) * 100
        print(f"Bulk rates completeness: {rates_score:.1f}%")
        
        # Overall quality score
        overall_score = (bdi_score + p5_score + rates_score) / 3
        print(f"\nOverall data quality score: {overall_score:.1f}%")
        
        if overall_score >= 80:
            print("✓ Data quality is good")
        elif overall_score >= 60:
            print("⚠ Data quality is acceptable")
        else:
            print("✗ Data quality needs improvement")
        
        return True
        
    except Exception as e:
        print(f"✗ Data quality test failed: {e}")
        logger.error(f"Data quality test error: {e}")
        return False

def main():
    """Run all tests."""
    print("BALTIC EXCHANGE SCRAPER TEST SUITE")
    print("="*60)
    
    test_results = []
    
    # Test API client
    test_results.append(("API Client", test_api_client()))
    
    # Test main scraper
    test_results.append(("Main Scraper", test_scraper()))
    
    # Test data quality
    test_results.append(("Data Quality", test_data_quality()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
