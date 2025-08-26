"""
Baltic Exchange API Client
Client for scraping weekly market roundup data from Baltic Exchange website.
"""

import requests
import logging
from typing import List, Dict, Optional
from datetime import datetime, date
import time
import json
from bs4 import BeautifulSoup
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalticExchangeAPIClient:
    """API client for Baltic Exchange weekly market roundup data."""
    
    def __init__(self, delay_between_requests: float = 2.0):
        """Initialize Baltic Exchange API client."""
        
        self.base_url = "https://www.balticexchange.com"
        self.weekly_roundup_url = "/en/data-services/WeeklyRoundup.html"
        # New JSON endpoint for weekly reports
        self.reports_json_url = "/bin/public/balticexchange/consumer/articlefilterlist.json"
        self.delay = delay_between_requests
        
        # Set up session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Don't accept compressed content
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Referer': 'https://www.balticexchange.com/en/data-services/WeeklyRoundup.html',
            'DNT': '1',
            'X-Requested-With': 'XMLHttpRequest',
        })
        
        logger.info("Baltic Exchange API client initialized successfully")
    
    def get_weekly_roundup_data(self) -> Dict:
        """
        Fetch weekly market roundup data from Baltic Exchange using JSON endpoint.
        
        Returns:
            Dictionary with weekly market data including BDI, P5, and bulk rates
        """
        try:
            # Use the JSON endpoint instead of HTML scraping
            url = f"{self.base_url}{self.reports_json_url}"
            params = {
                'resource': '/content/balticexchange/consumer/en/data-services/WeeklyRoundup/jcr:content/articlefilterpane',
                'start': 0,
                'selectedYear': 0,
                'loadedCount': 0
            }
            
            logger.info(f"Fetching weekly reports data from: {url}")
            logger.info(f"Parameters: {params}")
            
            # Add delay to be respectful
            if self.delay > 0:
                time.sleep(self.delay)
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Log response info for debugging
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response encoding: {response.encoding}")
            logger.info(f"Response content length: {len(response.content)}")
            
            # Parse JSON response
            try:
                reports_data = response.json()
                logger.info(f"Successfully parsed JSON response")
                logger.info(f"Response keys: {list(reports_data.keys())}")
                
                # Extract market data from JSON
                market_data = self._extract_market_data_from_json(reports_data)
                
                logger.info(f"Successfully extracted market data from JSON endpoint")
                
                return market_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.info(f"Response content: {response.text[:500]}")
                
                # Check if we hit a challenge page
                if "challenge validation" in response.text.lower():
                    logger.warning("JSON endpoint also hitting challenge page, trying alternative approach...")
                    return self._try_alternative_json_access()
                
                return {
                    "status": "json_error",
                    "message": f"Failed to parse JSON response: {e}",
                    "scraped_at": datetime.now().isoformat()
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching weekly reports: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching weekly reports: {e}")
            return {}
    
    def _is_challenge_page(self, soup: BeautifulSoup) -> bool:
        """Check if the page is a challenge/anti-bot protection page."""
        page_title = soup.title.string if soup.title else ""
        page_text = soup.get_text().lower()
        
        challenge_indicators = [
            "challenge validation",
            "challenge",
            "security check",
            "bot protection",
            "cloudflare",
            "please wait",
            "checking your browser",
            "ddos protection"
        ]
        
        for indicator in challenge_indicators:
            if indicator in page_title.lower() or indicator in page_text:
                return True
        
        # Check for very short content (typical of challenge pages)
        if len(page_text.strip()) < 100:
            return True
        
        return False
    
    def _handle_challenge_page(self, soup: BeautifulSoup, url: str) -> Dict:
        """Handle challenge pages and provide alternative approaches."""
        challenge_data = {
            "scraped_at": datetime.now().isoformat(),
            "source_url": url,
            "status": "challenge_detected",
            "message": "Bot protection challenge detected",
            "recommendations": [
                "The website has anti-bot protection enabled",
                "Consider using a real browser or waiting between requests",
                "Alternative data sources may be available",
                "Contact Baltic Exchange for API access if needed"
            ],
            "challenge_details": {
                "page_title": soup.title.string if soup.title else None,
                "content_length": len(soup.get_text()),
                "detected_as_challenge": True
            },
            "alternative_approaches": [
                "Use Selenium with real browser",
                "Implement longer delays between requests",
                "Use rotating user agents",
                "Check for RSS feeds or alternative endpoints",
                "Consider official API access"
            ]
        }
        
        return challenge_data
    
    def _extract_market_data_from_json(self, reports_data: Dict) -> Dict:
        """
        Extract weekly report data from the JSON response.
        
        Args:
            reports_data: JSON response from the reports endpoint
            
        Returns:
            Dictionary with extracted weekly report data
        """
        market_data = {
            "scraped_at": datetime.now().isoformat(),
            "source_url": f"{self.base_url}{self.reports_json_url}",
            "method": "json_api",
            "raw_content": {}
        }
        
        try:
            # Store raw content for debugging
            market_data["raw_content"] = {
                "has_more": reports_data.get('hasMore', False),
                "total_articles": len(reports_data.get('articles', [])),
                "response_structure": list(reports_data.keys())
            }
            
            logger.info(f"Processing {len(reports_data.get('articles', []))} articles")
            
            # Find all Dry (bulk) reports from 2025
            articles = reports_data.get('articles', [])
            dry_reports = [article for article in articles if article.get('categoryId') == 'dry']
            
            if dry_reports:
                logger.info(f"Found {len(dry_reports)} dry reports")
                
                # Process all dry reports from 2025
                all_weekly_reports = []
                
                for report in dry_reports:
                    report_title = report.get('newsTitle', '')
                    report_date = report.get('date', '')
                    
                    # Check if it's from 2025
                    if '2025' in report_date or '2025' in report_title:
                        logger.info(f"Processing report: {report_title} - {report_date}")
                        
                        # Try to fetch the actual report content
                        report_content = self._fetch_report_content(report.get('link'))
                        if report_content:
                            # Extract weekly report data
                            weekly_data = self._extract_weekly_report_content(report_content)
                            weekly_report = {
                                "week_number": report_title.split('Week ')[-1] if 'Week ' in report_title else '',
                                "date_report": report_date,
                                "category": report.get('category', ''),
                                "link_report": report.get('link'),
                                "capesize_content": weekly_data.get('capesize', ''),
                                "panamax_content": weekly_data.get('panamax', ''),
                                "ultramax_supramax_content": weekly_data.get('ultramax_supramax', ''),
                                "handysize_content": weekly_data.get('handysize', '')
                            }
                            all_weekly_reports.append(weekly_report)
                        else:
                            logger.warning(f"Could not fetch content for report: {report_title}")
                    else:
                        logger.info(f"Skipping report from different year: {report_title} - {report_date}")
                
                # Store all weekly reports
                market_data["weekly_reports"] = all_weekly_reports
                logger.info(f"Successfully processed {len(all_weekly_reports)} weekly reports from 2025")
            else:
                logger.warning("No dry reports found in the response")
            
            # Log what we found
            logger.info(f"Weekly report extraction result: {market_data}")
            
        except Exception as e:
            logger.error(f"Error extracting market data from JSON: {e}")
            market_data["error"] = str(e)
        
        return market_data
    
    def _extract_weekly_report_content(self, text_content: str) -> Dict:
        """
        Extract weekly report content by vessel type sections.
        
        Args:
            text_content: Full report text content
            
        Returns:
            Dictionary with vessel type content sections
        """
        weekly_data = {
            "capesize": "",
            "panamax": "",
            "ultramax_supramax": "",
            "handysize": ""
        }
        
        try:
            # Use regex to find sections more reliably
            import re
            
            # More robust section extraction - look for section headers and capture until next section
            sections = []
            
            # Find all section headers first
            section_patterns = [
                (r'Capesize', 'capesize'),
                (r'Panamax', 'panamax'), 
                (r'Ultramax.*?Supramax', 'ultramax_supramax'),
                (r'Handysize', 'handysize')
            ]
            
            # Find positions of all section headers
            section_positions = []
            for pattern, section_name in section_patterns:
                matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
                for match in matches:
                    section_positions.append((match.start(), section_name, match.group(0)))
            
            # Sort by position
            section_positions.sort(key=lambda x: x[0])
            
            # Extract content for each section
            for i, (start_pos, section_name, header) in enumerate(section_positions):
                # Find end position (next section or end of text)
                if i + 1 < len(section_positions):
                    end_pos = section_positions[i + 1][0]
                else:
                    # For last section, go until common ending markers
                    end_markers = ['Previous', 'Next', 'Latest News', 'Read More']
                    end_pos = len(text_content)
                    for marker in end_markers:
                        marker_pos = text_content.find(marker, start_pos)
                        if marker_pos != -1 and marker_pos < end_pos:
                            end_pos = marker_pos
                
                # Extract section content
                section_content = text_content[start_pos:end_pos].strip()
                
                # Clean up the content
                if section_content:
                    # Remove common boilerplate text
                    section_content = self._clean_section_content(section_content)
                    weekly_data[section_name] = section_content
                    
                    logger.info(f"Extracted {section_name}: {len(section_content)} characters")
                else:
                    logger.warning(f"No content found for {section_name}")
            
            # Fallback: if no sections found with headers, try alternative patterns
            if not any(weekly_data.values()):
                logger.info("No sections found with headers, trying alternative patterns...")
                self._extract_with_alternative_patterns(text_content, weekly_data)
            

            
            logger.info(f"Weekly report content extracted: {list(weekly_data.keys())}")
            logger.info(f"Content lengths: Capesize={len(weekly_data['capesize'])}, Panamax={len(weekly_data['panamax'])}, Ultramax/Supramax={len(weekly_data['ultramax_supramax'])}, Handysize={len(weekly_data['handysize'])}")
            
        except Exception as e:
            logger.error(f"Error extracting weekly report content: {e}")
        
        return weekly_data
    
    def _clean_section_content(self, content: str) -> str:
        """Clean up section content by removing boilerplate text."""
        # Remove common boilerplate text
        boilerplate_texts = [
            'This site uses cookies',
            'We use cookies to ensure that we give you the best experience on our website',
            'If you click "Accept Cookies", or continue without changing your settings, you consent to their use',
            'You can change your settings at any time',
            'To learn more about how we collect and use cookies, and how you configure or disable cookies please read our Cookie Policy',
            'Menu Home Who We Are',
            'Data Services',
            'Membership Services',
            'Media & Events',
            'Free Trial KYC Emissions',
            'Who We Are',
            'Data Services',
            'Membership Services',
            'Media & Events',
            'Free Trial KYC Emissions',
            '中文 My Baltic',
            'What can we help you find?',
            'Home Data Services Weekly Market Roundups 2025 Dry Back to All',
            'Previous Next Latest News Read More About',
            'Who we are Corporate Governance Our History Membership Services FAQ\'s',
            'Data services Free Trial Market Information Freight Derivatives Methodology',
            'Connect Apply Newsletter News & Events Baltic App Contact us',
            'Follow X LinkedIn Vimeo Instagram',
            'Data Policy Privacy Policy Terms and Conditions Baltic Rules Cookies Sitemap'
        ]
        
        for text in boilerplate_texts:
            content = content.replace(text, '')
        
        # Clean up multiple spaces and normalize
        content = ' '.join(content.split())
        return content
    
    def _extract_with_alternative_patterns(self, text_content: str, weekly_data: Dict) -> None:
        """Fallback extraction using alternative patterns when header-based extraction fails."""
        import re
        
        # Alternative patterns that look for content after specific keywords
        alternative_patterns = [
            # Capesize patterns
            (r'Capesize.*?The Capesize market.*?(?=Panamax|$)', 'capesize'),
            (r'Capesize.*?market.*?(?=Panamax|$)', 'capesize'),
            
            # Panamax patterns  
            (r'Panamax.*?The excitement.*?(?=Ultramax|Supramax|$)', 'panamax'),
            (r'Panamax.*?market.*?(?=Ultramax|Supramax|$)', 'panamax'),
            
            # Ultramax/Supramax patterns
            (r'Ultramax.*?Supramax.*?(?=Handysize|$)', 'ultramax_supramax'),
            (r'Ultramax.*?Despite.*?(?=Handysize|$)', 'ultramax_supramax'),
            
            # Handysize patterns
            (r'Handysize.*?Like.*?(?=Previous|Next|$)', 'handysize'),
            (r'Handysize.*?sector.*?(?=Previous|Next|$)', 'handysize')
        ]
        
        for pattern, section_name in alternative_patterns:
            if not weekly_data.get(section_name):  # Only extract if not already found
                match = re.search(pattern, text_content, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(0).strip()
                    if content:
                        content = self._clean_section_content(content)
                        weekly_data[section_name] = content
                        logger.info(f"Alternative pattern found for {section_name}: {len(content)} characters")
                        break
    
    def _try_alternative_json_access(self) -> Dict:
        """Try alternative methods to access the JSON endpoint."""
        logger.info("Attempting alternative JSON access methods...")
        
        # Method 1: Try with different headers
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://www.balticexchange.com/',
                'Origin': 'https://www.balticexchange.com',
            }
            
            url = f"{self.base_url}{self.reports_json_url}"
            params = {
                'resource': '/content/balticexchange/consumer/en/data-services/WeeklyRoundup/jcr:content/articlefilterpane',
                'start': 0,
                'selectedYear': 0,
                'loadedCount': 0
            }
            
            logger.info("Trying alternative headers approach...")
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    reports_data = response.json()
                    logger.info("Alternative headers approach successful!")
                    return self._extract_market_data_from_json(reports_data)
                except json.JSONDecodeError:
                    logger.warning("Alternative headers still returning invalid JSON")
        
        except Exception as e:
            logger.error(f"Alternative headers approach failed: {e}")
        
        # Method 2: Try with a POST request
        try:
            logger.info("Trying POST request approach...")
            post_data = {
                'resource': '/content/balticexchange/consumer/en/data-services/WeeklyRoundup/jcr:content/articlefilterpane',
                'start': 0,
                'selectedYear': 0,
                'loadedCount': 0
            }
            
            response = self.session.post(url, data=post_data, timeout=30)
            
            if response.status_code == 200:
                try:
                    reports_data = response.json()
                    logger.info("POST request approach successful!")
                    return self._extract_market_data_from_json(reports_data)
                except json.JSONDecodeError:
                    logger.warning("POST request still returning invalid JSON")
        
        except Exception as e:
            logger.error(f"POST request approach failed: {e}")
        
        # If all methods fail, return error
        logger.error("All alternative JSON access methods failed")
        return {
            "status": "all_methods_failed",
            "message": "All JSON access methods are blocked by anti-bot protection",
            "scraped_at": datetime.now().isoformat(),
            "recommendations": [
                "The JSON endpoint is also protected by anti-bot measures",
                "Consider using official API access",
                "Try alternative data sources",
                "Use Selenium with real browser automation"
            ]
        }
    
    def _fetch_report_content(self, report_url: str) -> Optional[str]:
        """
        Fetch the actual content of a weekly report.
        
        Args:
            report_url: URL of the specific report
            
        Returns:
            Report content as text, or None if failed
        """
        try:
            logger.info(f"Fetching report content from: {report_url}")
            
            # Add delay to be respectful
            if self.delay > 0:
                time.sleep(self.delay)
            
            response = self.session.get(report_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML to extract text content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the main content area
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            
            if main_content:
                content_text = main_content.get_text(separator=' ', strip=True)
                logger.info(f"Successfully extracted {len(content_text)} characters of report content")
                return content_text
            else:
                # Fallback to body text
                content_text = soup.get_text(separator=' ', strip=True)
                logger.info(f"Using fallback content extraction: {len(content_text)} characters")
                return content_text
                
        except Exception as e:
            logger.error(f"Error fetching report content: {e}")
            return None
    
    def _extract_bdi_data_from_text(self, text_content: str) -> Dict:
        """Extract BDI data from text content."""
        return self._extract_bdi_data_from_text_common(text_content)
    
    def _extract_p5_data_from_text(self, text_content: str) -> Dict:
        """Extract P5 data from text content."""
        return self._extract_p5_data_from_text_common(text_content)
    
    def _extract_bulk_rates_data_from_text(self, text_content: str) -> Dict:
        """Extract bulk rates data from text content."""
        return self._extract_bulk_rates_data_from_text_common(text_content)
    
    def _extract_market_summary_from_text(self, text_content: str) -> Dict:
        """Extract market summary from text content."""
        return self._extract_market_summary_from_text_common(text_content)
    
    def _extract_bdi_data_from_text_common(self, text_content: str) -> Dict:
        """Common BDI extraction logic for text content."""
        bdi_data = {
            "current_value": None,
            "change": None,
            "change_percentage": None,
            "date": None,
            "components": {}
        }
        
        try:
            # Search for BDI patterns with more variations
            bdi_patterns = [
                r'BDI[:\s]*([0-9,]+)',
                r'Baltic\s+Dry\s+Index[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*BDI',
                r'BDI\s*=\s*([0-9,]+)',
                r'BDI\s*([0-9,]+)',
                r'([0-9,]+)\s*Baltic',
                r'Index[:\s]*([0-9,]+)',
            ]
            
            for i, pattern in enumerate(bdi_patterns):
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    logger.info(f"BDI pattern {i+1} matched: {match.group(0)}")
                    bdi_data["current_value"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for BCI 5TC patterns (Baltic Capesize Index)
            bci_patterns = [
                r'BCI\s*5TC\s*(?:shedding|closing|at|reaching)\s*\$?([0-9,]+)',
                r'BCI\s*5TC[:\s]*\$?([0-9,]+)',
                r'5TC\s*(?:shedding|closing|at|reaching)\s*\$?([0-9,]+)',
                r'BCI\s*5TC\s*\$?([0-9,]+)',
                r'BCI\s*5TC\s*shedding\s*more\s*than\s*\$?[0-9,]+.*?closing\s*at\s*\$?([0-9,]+)',
                r'5TC\s*shedding\s*more\s*than\s*\$?[0-9,]+.*?closing\s*at\s*\$?([0-9,]+)',
                r'closing\s*at\s*\$?([0-9,]+)',
            ]
            
            for i, pattern in enumerate(bci_patterns):
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    logger.info(f"BCI 5TC pattern {i+1} matched: {match.group(0)}")
                    bdi_data["components"]["bci_5tc"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for BPI 5TC patterns (Baltic Panamax Index)
            bpi_patterns = [
                r'BPI\s*5TC\s*(?:at|reaching|closing|around)\s*\$?([0-9,]+)',
                r'BPI\s*5TC[:\s]*\$?([0-9,]+)',
                r'Panamax\s*5TC\s*(?:at|reaching|closing|around)\s*\$?([0-9,]+)',
                r'Panamax\s*5TC[:\s]*\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading\s*(?:at|reported)\s*\$?([0-9,]+)',
                r'Panamax.*?(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading\s*(?:at|reported)\s*\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*Panamax\s*(?:at|reported)\s*\$?([0-9,]+)',
                r'Panamax.*?(\d{1,2}[-,\s]\d{1,2})\s*months?\s*at\s*\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*at\s*\$?([0-9,]+).*?Panamax',
                # Look for specific Panamax rates mentioned in the text
                r'Panamax.*?\$?([0-9,]+).*?delivery.*?Korea',
                r'Panamax.*?(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading.*?\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading.*?Panamax.*?\$?([0-9,]+)',
                # Look for the specific rate mentioned: "9 to 11 months trading reported late in the week at $15,250"
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading.*?reported.*?\$?([0-9,]+)',
                # Look for Panamax rates in context: "$30,000 reported on a super-spec 87,000-dwt type delivery Continent"
                r'Panamax.*?\$?([0-9,]+).*?reported.*?delivery',
                r'Panamax.*?(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading.*?\$?([0-9,]+)',
                # Look for the specific rate: "9 to 11 months trading reported late in the week at $15,250"
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading.*?reported.*?at\s*\$?([0-9,]+)',
            ]
            
            for i, pattern in enumerate(bpi_patterns):
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    logger.info(f"BPI 5TC pattern {i+1} matched: {match.group(0)}")
                    # Extract the rate value from the matched text
                    if len(match.groups()) == 2:
                        # For patterns with 2 groups like (period, rate)
                        rate_value = match.group(2)
                    else:
                        # For patterns with 1 group like (rate)
                        rate_value = match.group(1)
                    
                    # Clean and validate the rate value
                    if rate_value and rate_value.strip():
                        try:
                            bdi_data["components"]["bpi_5tc"] = int(rate_value.replace(',', ''))
                            logger.info(f"Successfully extracted BPI 5TC: {bdi_data['components']['bpi_5tc']}")
                            break
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Failed to parse BPI 5TC rate '{rate_value}': {e}")
                            continue
                    else:
                        logger.warning(f"Empty rate value found in BPI 5TC pattern {i+1}")
                        continue
            
            # Look for BSI 5TC patterns (Baltic Supramax Index)
            bsi_patterns = [
                r'BSI\s*5TC\s*(?:at|reaching|closing|around)\s*\$?([0-9,]+)',
                r'BSI\s*5TC[:\s]*\$?([0-9,]+)',
                r'Supramax\s*5TC\s*(?:at|reaching|closing|around)\s*\$?([0-9,]+)',
                r'Supramax\s*5TC[:\s]*\$?([0-9,]+)',
                r'ultramax\s*(?:from|delivery|basis)\s*.*?\$?([0-9,]+)',
                r'supramax\s*(?:from|delivery|basis)\s*.*?\$?([0-9,]+)',
            ]
            
            for i, pattern in enumerate(bsi_patterns):
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    logger.info(f"BSI 5TC pattern {i+1} matched: {match.group(0)}")
                    bdi_data["components"]["bsi_5tc"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for change information with more patterns
            change_patterns = [
                r'([+-]?\d+(?:\.\d+)?)\s*\(([+-]?\d+(?:\.\d+)?)%\)',
                r'([+-]?\d+(?:\.\d+)?)\s*%',
                r'([+-]?\d+(?:\.\d+)?)\s*points?',
                r'([+-]?\d+(?:\.\d+)?)\s*change',
                r'shedding\s*more\s*than\s*\$?([0-9,]+)',
                r'uptick\s*of\s*\$?([0-9,]+)',
            ]
            
            for i, pattern in enumerate(change_patterns):
                match = re.search(pattern, text_content)
                if match:
                    logger.info(f"Change pattern {i+1} matched: {match.group(0)}")
                    if len(match.groups()) == 2:
                        bdi_data["change"] = float(match.group(1))
                        bdi_data["change_percentage"] = float(match.group(2))
                    else:
                        bdi_data["change_percentage"] = float(match.group(1))
                    break
            
            # Extract date information with more patterns
            date_patterns = [
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            ]
            
            for i, pattern in enumerate(date_patterns):
                match = re.search(pattern, text_content)
                if match:
                    logger.info(f"Date pattern {i+1} matched: {match.group(0)}")
                    bdi_data["date"] = match.group(1)
                    break
            
            # Look for BHSI (Baltic Handysize Index) patterns
            bhsi_patterns = [
                r'BHSI[:\s]*([0-9,]+)',
                r'(\d{1,3})%\s*of\s*BHSI',
                r'BHSI\s*for\s*(\d{1,2})\s*years?\s*trading',
            ]
            
            for i, pattern in enumerate(bhsi_patterns):
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    logger.info(f"BHSI pattern {i+1} matched: {match.group(0)}")
                    bdi_data["components"]["bhsi"] = match.group(1)
                    break
            
            # Log what we found
            logger.info(f"BDI extraction result: {bdi_data}")
            
        except Exception as e:
            logger.error(f"Error extracting BDI data: {e}")
        
        return bdi_data
    
    def _extract_p5_data_from_text_common(self, text_content: str) -> Dict:
        """Common P5 extraction logic for text content."""
        p5_data = {
            "routes": {},
            "summary": {}
        }
        
        try:
            # Look for P5/5TC route information
            p5_patterns = [
                r'5TC[:\s]*([0-9,]+)',
                r'P5[:\s]*([0-9,]+)',
                r'5\s*Route\s*TC[:\s]*([0-9,]+)',
                r'P5\s*rates?[:\s]*\$?([0-9,]+)',
                r'P5\s*around\s*\$?([0-9,]+)',
            ]
            
            for pattern in p5_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    p5_data["summary"]["value"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for individual route information with more context
            route_patterns = [
                r'(C3|C4|C5|C7|C9|C10|C14|C16)[:\s]*\$?([0-9,]+)',
                r'(Panamax|Capesize|Supramax|Handysize)[:\s]*([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading\s*(?:at|reported)\s*\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*at\s*\$?([0-9,]+)',
            ]
            
            for pattern in route_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit() or ',' in match[0]:
                            value, route = match
                        else:
                            route, value = match
                        
                        if route.isdigit() or ',' in route:
                            # This is a time charter period
                            p5_data["summary"]["time_charter"] = {
                                "period": route,
                                "rate": int(value.replace(',', ''))
                            }
                        else:
                            # This is a route
                            p5_data["routes"][route.upper()] = int(value.replace(',', ''))
            
            # Look for specific P5 route mentions
            p5_context_patterns = [
                r'P5\s*(?:route|rates?)\s*(?:around|at|of)\s*\$?([0-9,]+)',
                r'P5\s*(?:delivery|basis)\s*.*?\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*P5\s*at\s*\$?([0-9,]+)',
            ]
            
            for pattern in p5_context_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    if len(match.groups()) == 2:
                        period, rate = match.groups()
                        p5_data["summary"]["time_charter"] = {
                            "period": period,
                            "rate": int(rate.replace(',', ''))
                        }
                    else:
                        rate = match.group(1)
                        p5_data["summary"]["value"] = int(rate.replace(',', ''))
                    break
            
        except Exception as e:
            logger.error(f"Error extracting P5 data: {e}")
        
        return p5_data
    
    def _extract_bulk_rates_data_from_text_common(self, text_content: str) -> Dict:
        """Common bulk rates extraction logic for text content."""
        bulk_rates = {
            "capesize": {},
            "panamax": {},
            "supramax": {},
            "handysize": {},
            "summary": {}
        }
        
        try:
            # Look for vessel type rates
            vessel_patterns = [
                r'(Capesize|Panamax|Supramax|Handysize)[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*(Capesize|Panamax|Supramax|Handysize)',
            ]
            
            for pattern in vessel_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit() or ',' in match[0]:
                            value, vessel_type = match
                        else:
                            vessel_type, value = match
                        
                        vessel_type = vessel_type.lower()
                        if vessel_type in bulk_rates:
                            bulk_rates[vessel_type]["rate"] = int(value.replace(',', ''))
            
            # Look for specific route rates with more context
            route_patterns = [
                r'(C3|C4|C5|C7|C9|C10|C14|C16)[:\s]*\$?([0-9,]+)',
                r'([0-9,]+)\s*(C3|C4|C5|C7|C9|C10|C14|C16)',
                r'(C3|C4|C5|C7|C9|C10|C14|C16)\s*(?:rates?|bids?)\s*(?:around|at|of)\s*\$?([0-9,]+)',
                r'(?:rates?|bids?)\s*(?:around|at|of)\s*\$?([0-9,]+)\s*(?:for|on)\s*(C3|C4|C5|C7|C9|C10|C14|C16)',
            ]
            
            for pattern in route_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit() or ',' in match[0]:
                            value, route = match
                        else:
                            route, value = match
                        
                        # Map routes to vessel types
                        if route in ['C3', 'C4', 'C5', 'C7']:
                            bulk_rates["capesize"][route] = int(value.replace(',', ''))
                        elif route in ['C9', 'C10']:
                            bulk_rates["panamax"][route] = int(value.replace(',', ''))
                        elif route in ['C14', 'C16']:
                            bulk_rates["supramax"][route] = int(value.replace(',', ''))
            
            # Look for specific rate mentions in context
            context_patterns = [
                r'C5\s*rates?\s*below\s*\$?([0-9,]+)',
                r'C5\s*rates?\s*around\s*\$?([0-9,]+)',
                r'C3\s*bids?\s*around\s*\$?([0-9,]+)',
                r'C3\s*bids?\s*at\s*\$?([0-9,]+)',
                r'C9\s*rates?\s*around\s*\$?([0-9,]+)',
                r'C10\s*rates?\s*around\s*\$?([0-9,]+)',
            ]
            
            for pattern in context_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # Extract route from pattern
                    if 'C5' in pattern:
                        bulk_rates["capesize"]["C5"] = int(value.replace(',', ''))
                    elif 'C3' in pattern:
                        bulk_rates["capesize"]["C3"] = int(value.replace(',', ''))
                    elif 'C9' in pattern:
                        bulk_rates["panamax"]["C9"] = int(value.replace(',', ''))
                    elif 'C10' in pattern:
                        bulk_rates["panamax"]["C10"] = int(value.replace(',', ''))
            
            # Look for time charter rates
            tc_patterns = [
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*trading\s*(?:at|reported)\s*\$?([0-9,]+)',
                r'(\d{1,2}[-,\s]\d{1,2})\s*months?\s*at\s*\$?([0-9,]+)',
            ]
            
            for pattern in tc_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        period, rate = match
                        bulk_rates["summary"]["time_charter"] = {
                            "period": period,
                            "rate": int(rate.replace(',', ''))
                        }
            
        except Exception as e:
            logger.error(f"Error extracting bulk rates data: {e}")
        
        return bulk_rates
    
    def _extract_market_summary_from_text_common(self, text_content: str) -> Dict:
        """Common market summary extraction logic for text content."""
        summary = {
            "market_sentiment": None,
            "key_highlights": [],
            "trends": []
        }
        
        try:
            # Look for market sentiment indicators
            sentiment_patterns = [
                r'(bullish|bearish|neutral|positive|negative)',
                r'(strengthening|weakening|stable|volatile)',
                r'(up|down|flat|steady)',
            ]
            
            for pattern in sentiment_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    summary["market_sentiment"] = match.group(1).lower()
                    break
            
            # Look for key highlights (numbers and percentages)
            highlight_patterns = [
                r'([0-9,]+)\s*%',
                r'([0-9,]+)\s*(increase|decrease|rise|fall|gain|loss)',
            ]
            
            for pattern in highlight_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        value, change = match
                        summary["key_highlights"].append(f"{value}% {change}")
                    else:
                        summary["key_highlights"].append(f"{match[0]}%")
            
            # Look for trend indicators
            trend_patterns = [
                r'(trending|trend|direction)[:\s]*(up|down|sideways|stable)',
                r'(market|freight|rates)[:\s]*(up|down|sideways|stable)',
            ]
            
            for pattern in trend_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        summary["trends"].append(f"{match[0]} {match[1]}")
            
        except Exception as e:
            logger.error(f"Error extracting market summary: {e}")
        
        return summary
    
    def _extract_bdi_data(self, soup: BeautifulSoup) -> Dict:
        """Extract BDI (Baltic Dry Index) data."""
        bdi_data = {
            "current_value": None,
            "change": None,
            "change_percentage": None,
            "date": None,
            "components": {}
        }
        
        try:
            # Look for BDI mentions in the content
            page_text = soup.get_text()
            logger.info(f"Page text length: {len(page_text)}")
            logger.info(f"First 500 characters: {page_text[:500]}")
            
            # Search for BDI patterns with more variations
            bdi_patterns = [
                r'BDI[:\s]*([0-9,]+)',
                r'Baltic\s+Dry\s+Index[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*BDI',
                r'BDI\s*=\s*([0-9,]+)',
                r'BDI\s*([0-9,]+)',
                r'([0-9,]+)\s*Baltic',
                r'Index[:\s]*([0-9,]+)',
            ]
            
            for i, pattern in enumerate(bdi_patterns):
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    logger.info(f"BDI pattern {i+1} matched: {match.group(0)}")
                    bdi_data["current_value"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for change information with more patterns
            change_patterns = [
                r'([+-]?\d+(?:\.\d+)?)\s*\(([+-]?\d+(?:\.\d+)?)%\)',
                r'([+-]?\d+(?:\.\d+)?)\s*%',
                r'([+-]?\d+(?:\.\d+)?)\s*points?',
                r'([+-]?\d+(?:\.\d+)?)\s*change',
            ]
            
            for i, pattern in enumerate(change_patterns):
                match = re.search(pattern, page_text)
                if match:
                    logger.info(f"Change pattern {i+1} matched: {match.group(0)}")
                    if len(match.groups()) == 2:
                        bdi_data["change"] = float(match.group(1))
                        bdi_data["change_percentage"] = float(match.group(2))
                    else:
                        bdi_data["change_percentage"] = float(match.group(1))
                    break
            
            # Extract date information with more patterns
            date_patterns = [
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{1,2}/\d{1,2}/\d{4})',
                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            ]
            
            for i, pattern in enumerate(date_patterns):
                match = re.search(pattern, page_text)
                if match:
                    logger.info(f"Date pattern {i+1} matched: {match.group(0)}")
                    bdi_data["date"] = match.group(1)
                    break
            
            # Log what we found
            logger.info(f"BDI extraction result: {bdi_data}")
            
        except Exception as e:
            logger.error(f"Error extracting BDI data: {e}")
        
        return bdi_data
    
    def _extract_p5_data(self, soup: BeautifulSoup) -> Dict:
        """Extract P5 (5TC routes) data."""
        p5_data = {
            "routes": {},
            "summary": {}
        }
        
        try:
            page_text = soup.get_text()
            
            # Look for P5/5TC route information
            p5_patterns = [
                r'5TC[:\s]*([0-9,]+)',
                r'P5[:\s]*([0-9,]+)',
                r'5\s*Route\s*TC[:\s]*([0-9,]+)',
            ]
            
            for pattern in p5_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    p5_data["summary"]["value"] = int(match.group(1).replace(',', ''))
                    break
            
            # Look for individual route information
            route_patterns = [
                r'(C3|C4|C5|C7|C9)[:\s]*([0-9,]+)',
                r'(Panamax|Capesize|Supramax)[:\s]*([0-9,]+)',
            ]
            
            for pattern in route_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for route, value in matches:
                    p5_data["routes"][route.upper()] = int(value.replace(',', ''))
            
        except Exception as e:
            logger.error(f"Error extracting P5 data: {e}")
        
        return p5_data
    
    def _extract_bulk_rates_data(self, soup: BeautifulSoup) -> Dict:
        """Extract bulk rates data."""
        bulk_rates = {
            "capesize": {},
            "panamax": {},
            "supramax": {},
            "handysize": {},
            "summary": {}
        }
        
        try:
            page_text = soup.get_text()
            
            # Look for vessel type rates
            vessel_patterns = [
                r'(Capesize|Panamax|Supramax|Handysize)[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*(Capesize|Panamax|Supramax|Handysize)',
            ]
            
            for pattern in vessel_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit() or ',' in match[0]:
                            value, vessel_type = match
                        else:
                            vessel_type, value = match
                        
                        vessel_type = vessel_type.lower()
                        if vessel_type in bulk_rates:
                            bulk_rates[vessel_type]["rate"] = int(value.replace(',', ''))
            
            # Look for specific route rates
            route_patterns = [
                r'(C3|C4|C5|C7|C9|C10|C14|C16)[:\s]*([0-9,]+)',
                r'([0-9,]+)\s*(C3|C4|C5|C7|C9|C10|C14|C16)',
            ]
            
            for pattern in route_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        if match[0].isdigit() or ',' in match[0]:
                            value, route = match
                        else:
                            route, value = match
                        
                        # Map routes to vessel types
                        if route in ['C3', 'C4', 'C5', 'C7']:
                            bulk_rates["capesize"][route] = int(value.replace(',', ''))
                        elif route in ['C9', 'C10']:
                            bulk_rates["panamax"][route] = int(value.replace(',', ''))
                        elif route in ['C14', 'C16']:
                            bulk_rates["supramax"][route] = int(value.replace(',', ''))
            
        except Exception as e:
            logger.error(f"Error extracting bulk rates data: {e}")
        
        return bulk_rates
    
    def _extract_market_summary(self, soup: BeautifulSoup) -> Dict:
        """Extract general market summary information."""
        summary = {
            "market_sentiment": None,
            "key_highlights": [],
            "trends": []
        }
        
        try:
            page_text = soup.get_text()
            
            # Look for market sentiment indicators
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
            
            # Look for key highlights (numbers and percentages)
            highlight_patterns = [
                r'([0-9,]+)\s*%',
                r'([0-9,]+)\s*(increase|decrease|rise|fall|gain|loss)',
            ]
            
            for pattern in highlight_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        value, change = match
                        summary["key_highlights"].append(f"{value}% {change}")
                    else:
                        summary["key_highlights"].append(f"{match[0]}%")
            
            # Look for trend indicators
            trend_patterns = [
                r'(trending|trend|direction)[:\s]*(up|down|sideways|stable)',
                r'(market|freight|rates)[:\s]*(up|down|sideways|stable)',
            ]
            
            for pattern in trend_patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        summary["trends"].append(f"{match[0]} {match[1]}")
            
        except Exception as e:
            logger.error(f"Error extracting market summary: {e}")
        
        return summary
    
    def get_historical_data(self, year: int = None) -> List[Dict]:
        """
        Get historical weekly roundup data.
        
        Args:
            year: Specific year to fetch (optional)
            
        Returns:
            List of historical weekly roundup data
        """
        try:
            # For now, we'll just get current data
            # In the future, this could be extended to fetch historical archives
            current_data = self.get_weekly_roundup_data()
            
            if year:
                current_year = datetime.now().year
                if year == current_year:
                    return [current_data]
                else:
                    logger.warning(f"Historical data for year {year} not yet implemented")
                    return []
            
            return [current_data]
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []
    
    def test_connection(self) -> Dict:
        """
        Test connection to Baltic Exchange website.
        
        Returns:
            Dictionary with connection test results
        """
        try:
            start_time = time.time()
            data = self.get_weekly_roundup_data()
            duration = time.time() - start_time
            
            # Check if we hit a challenge
            if data.get('status') == 'challenge_detected':
                return {
                    "status": "challenge",
                    "message": "Bot protection challenge detected",
                    "data_retrieved": False,
                    "response_time_seconds": round(duration, 2),
                    "api_endpoint": f"{self.base_url}{self.weekly_roundup_url}",
                    "recommendations": data.get('recommendations', [])
                }
            
            return {
                "status": "success",
                "message": f"Successfully connected to Baltic Exchange",
                "data_retrieved": bool(data),
                "response_time_seconds": round(duration, 2),
                "api_endpoint": f"{self.base_url}{self.weekly_roundup_url}"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect to Baltic Exchange: {str(e)}",
                "data_retrieved": False,
                "response_time_seconds": 0,
                "api_endpoint": f"{self.base_url}{self.weekly_roundup_url}"
            }

    def _calculate_bdi(self, capesize_5tc: int, panamax_5tc: int, supramax_5tc: int) -> float:
        """
        Calculate BDI using the official formula:
        BDI = (0.40 × Capesize_5TC + 0.30 × Panamax_5TC + 0.30 × Supramax_5TC) × 0.1098
        
        Args:
            capesize_5tc: Capesize 5TC rate
            panamax_5tc: Panamax 5TC rate  
            supramax_5tc: Supramax 5TC rate
            
        Returns:
            Calculated BDI value
        """
        try:
            bdi = (0.40 * capesize_5tc + 0.30 * panamax_5tc + 0.30 * supramax_5tc) * 0.1098
            logger.info(f"BDI calculation: ({0.40} × {capesize_5tc} + {0.30} × {panamax_5tc} + {0.30} × {supramax_5tc}) × {0.1098} = {bdi}")
            return round(bdi, 2)
        except Exception as e:
            logger.error(f"Error calculating BDI: {e}")
            return None
