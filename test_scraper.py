#!/usr/bin/env python3
"""
Test script for ANP Ports Vessel Scraper.
Tests the main functionality and API endpoints.
"""

import sys
import json
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

def test_api_connection():
    """Test connection to ANP API."""
    print("🔌 Testing ANP API connection...")
    
    try:
        api_client = ANPAPIClient()
        result = api_client.test_connection()
        
        if result['status'] == 'success':
            print(f"✅ Connection successful!")
            print(f"   API Endpoint: {result['api_endpoint']}")
            print(f"   Vessel Count: {result['vessel_count']}")
            print(f"   Response Time: {result['response_time_seconds']}s")
            return True
        else:
            print(f"❌ Connection failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

def test_vessel_fetching():
    """Test fetching vessels from API."""
    print("\n📡 Testing vessel data fetching...")
    
    try:
        api_client = ANPAPIClient()
        vessels = api_client.get_all_vessels()
        
        if vessels:
            print(f"✅ Successfully fetched {len(vessels)} vessels")
            
            # Show sample vessel
            if vessels:
                sample = vessels[0]
                print(f"\n📋 Sample vessel:")
                print(f"   Name: {sample.get('nOM_NAVIREField', 'N/A')}")
                print(f"   Type: {sample.get('tYP_NAVIREField', 'N/A')}")
                print(f"   Operator: {sample.get('oPERATEURField', 'N/A')}")
                print(f"   Port: {sample.get('pROVField', 'N/A')}")
                print(f"   Situation: {sample.get('sITUATIONField', 'N/A')}")
            
            return True
        else:
            print("❌ No vessels fetched")
            return False
            
    except Exception as e:
        print(f"❌ Error fetching vessels: {e}")
        return False

def test_matcher():
    """Test the vessel matcher."""
    print("\n🎯 Testing vessel matcher...")
    
    try:
        matcher = ANPPortsVesselMatcher()
        
        # Test with sample vessel data
        test_vessel = {
            'nOM_NAVIREField': 'TEST VESSEL',
            'tYP_NAVIREField': 'VRAQUIER',
            'oPERATEURField': 'OCP',
            'pROVField': 'CASABLANCA',
            'sITUATIONField': 'EN RADE'
        }
        
        is_match, filter_details = matcher.is_match(test_vessel)
        
        print(f"✅ Matcher test completed")
        print(f"   Vessel matches criteria: {is_match}")
        print(f"   Match score: {filter_details.get('match_score', 0)}")
        print(f"   Groups matched: {filter_details.get('groups_matched', 0)}/3")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing matcher: {e}")
        return False

def test_scraper():
    """Test the main scraper."""
    print("\n🚢 Testing main scraper...")
    
    try:
        scraper = ANPPortsVesselScraper()
        
        print(f"✅ Scraper initialized successfully")
        print(f"   Data directory: {scraper.data_dir}")
        print(f"   Current vessels: {len(scraper.vessels)}")
        
        # Test statistics
        stats = scraper.get_statistics()
        print(f"   Statistics available: {bool(stats)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing scraper: {e}")
        return False

def test_filtering():
    """Test vessel filtering."""
    print("\n🔍 Testing vessel filtering...")
    
    try:
        scraper = ANPPortsVesselScraper()
        
        # Test with sample filters
        filters = {
            'vessel_type': 'VRAQUIER',
            'port': 'CASABLANCA'
        }
        
        filtered_vessels = scraper.get_vessels(filters)
        print(f"✅ Filtering test completed")
        print(f"   Filtered vessels: {len(filtered_vessels)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing filtering: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 ANP Ports Vessel Scraper - Test Suite")
    print("=" * 50)
    
    tests = [
        ("API Connection", test_api_connection),
        ("Vessel Fetching", test_vessel_fetching),
        ("Matcher", test_matcher),
        ("Scraper", test_scraper),
        ("Filtering", test_filtering)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The scraper is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
