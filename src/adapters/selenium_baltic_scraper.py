"""
Selenium-based Baltic Exchange Scraper
Alternative approach using browser automation to bypass bot protection.
"""

import logging
import time
from typing import Dict, Optional
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available. Install with: pip install selenium")

logger = logging.getLogger(__name__)

class SeleniumBalticScraper:
    """Selenium-based scraper for Baltic Exchange data."""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """Initialize Selenium scraper."""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required but not installed")
        
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.base_url = "https://www.balticexchange.com"
        self.weekly_roundup_url = "/en/data-services/WeeklyRoundup.html"
        
        logger.info("Selenium Baltic Exchange scraper initialized")
    
    def _setup_driver(self):
        """Set up Chrome driver with appropriate options."""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Additional options to avoid detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except WebDriverException as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            logger.info("Make sure Chrome and ChromeDriver are installed")
            raise
    
    def get_market_data(self) -> Dict:
        """
        Get market data using Selenium browser automation.
        
        Returns:
            Dictionary with market data or error information
        """
        try:
            self.driver = self._setup_driver()
            url = f"{self.base_url}{self.weekly_roundup_url}"
            
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Wait for body element to be present
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Additional wait for content to load
            time.sleep(5)
            
            # Check if we're still on a challenge page
            page_title = self.driver.title
            logger.info(f"Page title: {page_title}")
            
            if "challenge" in page_title.lower() or "validation" in page_title.lower():
                logger.warning("Still on challenge page after Selenium navigation")
                return self._handle_challenge_page()
            
            # Extract data from the rendered page
            market_data = self._extract_market_data()
            
            logger.info("Successfully extracted market data using Selenium")
            return market_data
            
        except TimeoutException:
            logger.error("Page load timeout")
            return {
                "status": "timeout",
                "message": "Page load timeout",
                "scraped_at": datetime.now().isoformat()
            }
        except WebDriverException as e:
            logger.error(f"WebDriver error: {e}")
            return {
                "status": "webdriver_error",
                "message": str(e),
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "scraped_at": datetime.now().isoformat()
            }
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _handle_challenge_page(self) -> Dict:
        """Handle challenge page detection."""
        return {
            "status": "challenge_detected",
            "message": "Bot protection challenge still active with Selenium",
            "scraped_at": datetime.now().isoformat(),
            "recommendations": [
                "Selenium approach also blocked by anti-bot protection",
                "Consider using official API access",
                "Try alternative data sources",
                "Implement longer delays and proxy rotation"
            ]
        }
    
    def _extract_market_data(self) -> Dict:
        """Extract market data from the rendered page."""
        try:
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            logger.info(f"Page text length: {len(page_text)}")
            logger.info(f"First 500 characters: {page_text[:500]}")
            
            # Extract data using the same patterns as the regular scraper
            market_data = {
                "scraped_at": datetime.now().isoformat(),
                "source_url": f"{self.base_url}{self.weekly_roundup_url}",
                "method": "selenium",
                "bdi": self._extract_bdi_data(page_text),
                "p5": self._extract_p5_data(page_text),
                "bulk_rates": self._extract_bulk_rates_data(page_text),
                "market_summary": self._extract_market_summary(page_text),
                "raw_content": {
                    "page_title": self.driver.title,
                    "text_length": len(page_text),
                    "selenium_success": True
                }
            }
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error extracting market data: {e}")
            return {
                "status": "extraction_error",
                "message": str(e),
                "scraped_at": datetime.now().isoformat()
            }
    
    def _extract_bdi_data(self, page_text: str) -> Dict:
        """Extract BDI data from page text."""
        import re
        
        bdi_data = {
            "current_value": None,
            "change": None,
            "change_percentage": None,
            "date": None
        }
        
        try:
            # BDI patterns
            bdi_patterns = [
                r'BDI[:\s]*([0-9,]+)',
                r'Baltic\s+Dry\s+Index[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*BDI',
                r'BDI\s*=\s*([0-9,]+)',
            ]
            
            for pattern in bdi_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    bdi_data["current_value"] = int(match.group(1).replace(',', ''))
                    break
            
            # Change patterns
            change_patterns = [
                r'([+-]?\d+(?:\.\d+)?)\s*\(([+-]?\d+(?:\.\d+)?)%\)',
                r'([+-]?\d+(?:\.\d+)?)\s*%',
            ]
            
            for pattern in change_patterns:
                match = re.search(pattern, page_text)
                if match:
                    if len(match.groups()) == 2:
                        bdi_data["change"] = float(match.group(1))
                        bdi_data["change_percentage"] = float(match.group(2))
                    else:
                        bdi_data["change_percentage"] = float(match.group(1))
                    break
            
        except Exception as e:
            logger.error(f"Error extracting BDI data: {e}")
        
        return bdi_data
    
    def _extract_p5_data(self, page_text: str) -> Dict:
        """Extract P5 data from page text."""
        import re
        
        p5_data = {
            "routes": {},
            "summary": {}
        }
        
        try:
            # P5 patterns
            p5_patterns = [
                r'5TC[:\s]*([0-9,]+)',
                r'P5[:\s]*([0-9,]+)',
            ]
            
            for pattern in p5_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    p5_data["summary"]["value"] = int(match.group(1).replace(',', ''))
                    break
            
        except Exception as e:
            logger.error(f"Error extracting P5 data: {e}")
        
        return p5_data
    
    def _extract_bulk_rates_data(self, page_text: str) -> Dict:
        """Extract bulk rates data from page text."""
        import re
        
        bulk_rates = {
            "capesize": {},
            "panamax": {},
            "supramax": {},
            "handysize": {}
        }
        
        try:
            # Vessel type patterns
            vessel_patterns = [
                r'(Capesize|Panamax|Supramax|Handysize)[:\s]*([0-9,]+)',
            ]
            
            for pattern in vessel_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for vessel_type, value in matches:
                    vessel_type = vessel_type.lower()
                    if vessel_type in bulk_rates:
                        bulk_rates[vessel_type]["rate"] = int(value.replace(',', ''))
            
        except Exception as e:
            logger.error(f"Error extracting bulk rates data: {e}")
        
        return bulk_rates
    
    def _extract_market_summary(self, page_text: str) -> Dict:
        """Extract market summary from page text."""
        import re
        
        summary = {
            "market_sentiment": None,
            "key_highlights": [],
            "trends": []
        }
        
        try:
            # Sentiment patterns
            sentiment_patterns = [
                r'(bullish|bearish|neutral|positive|negative)',
                r'(strengthening|weakening|stable|volatile)',
                r'(up|down|flat|steady)',
            ]
            
            for pattern in sentiment_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    summary["market_sentiment"] = match.group(1).lower()
                    break
            
        except Exception as e:
            logger.error(f"Error extracting market summary: {e}")
        
        return summary
    
    def test_connection(self) -> Dict:
        """Test Selenium connection and page access."""
        try:
            start_time = time.time()
            data = self.get_market_data()
            duration = time.time() - start_time
            
            return {
                "status": data.get("status", "unknown"),
                "message": data.get("message", "Test completed"),
                "data_retrieved": data.get("status") == "success",
                "response_time_seconds": round(duration, 2),
                "method": "selenium",
                "selenium_available": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Selenium test failed: {str(e)}",
                "data_retrieved": False,
                "response_time_seconds": 0,
                "method": "selenium",
                "selenium_available": True
            }
