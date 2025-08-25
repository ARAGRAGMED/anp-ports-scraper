"""
ANP Ports Vessel Data Matcher
Implements filtering logic for vessel movement data.
Uses the same 3-group logic as the original EUR-Lex scraper.
"""

import re
import logging
from typing import Dict, List, Tuple, Set

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ANPPortsVesselMatcher:
    """Matches ANP vessel data against filtering criteria."""
    
    def __init__(self):
        """Initialize category groups for vessel data filtering."""
        
        # Group A: Vessel Types (Optional)
        self.vessel_type_keywords = {
            "VRAQUIER", "CHIMIQUIER", "TANKER", "PORTE CONTENEUR",
            "PASSAGERS", "GAZIER", "PETROLIER", "CONVENTIONEL",
            "BULKER", "CONTAINER", "PASSENGER", "CHEMICAL",
            "OIL", "GAS", "GENERAL CARGO", "RO-RO",
            # Broader terms
            "CARGO", "SHIP", "VESSEL", "NAVIRE", "BATEAU"
        }
        
        # Group B: Operators (Optional)
        self.operator_keywords = {
            "OCP", "MARSA MAROC", "SOMAPORT", "SOSIPO",
            "MASS CEREALES", "COMATAM", "AGEMAFRIC", "SOMASHIP",
            "CMA CGM MAROC", "INTERCONA", "NAXCO MAROC",
            "TARROS MAROC", "TRUST SHIPING", "MARITIME SHIP",
            "GLOBE MARINE", "MEDISHIP", "IDEA MAROC",
            "SOMATIME AGADIR", "SOCONAV", "SEATRADE",
            # Broader terms
            "SHIPPING", "MARINE", "NAVIGATION", "TRANSPORT"
        }
        
        # Group C: Ports/Locations (Mandatory)
        self.port_location_keywords = {
            # Major Moroccan Ports
            "CASABLANCA", "SAFI", "TANGER MED", "AGADIR", "JORF LASFAR",
            "MOHAMMEDIA", "KENITRA", "LARACHE", "TANGER", "NADOR",
            
            # International Ports
            "VANCOUVER", "BEAUMONT", "NECOCHEA", "MALTA", "UST'-LUGA",
            "ALMERIA", "DUNKERQUE", "MARSEILLE", "VALENCIA", "GIBRALTAR",
            "CARTAGENA", "SANTAREM", "ROUEN", "PALAMÓS", "LA SPEZIA",
            "EL ISKANDARIYA", "MERSIN", "SALERNO", "GENOVA", "BARCELONA",
            "ALEXANDRIA", "HOUSTON", "AMBARLI", "GEBZE", "ALIAGA",
            "CONSTANTA", "DISTRIPARK", "FREEPORT",
            
            # Broader geographic terms
            "MEDITERRANEAN", "ATLANTIC", "EUROPE", "AFRICA", "AMERICA"
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ""
        return text.upper().strip()
    
    def _find_keyword_matches(self, text: str, keywords: Set[str]) -> List[str]:
        """Find matching keywords in text."""
        if not text:
            return []
        
        normalized_text = self._normalize_text(text)
        matches = []
        
        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            
            # Handle wildcard matching (e.g., VRAQUI* matches VRAQUIER)
            if '*' in normalized_keyword:
                pattern = normalized_keyword.replace('*', r'\w*')
                if re.search(r'\b' + pattern + r'\b', normalized_text):
                    matches.append(keyword)
            else:
                # Word boundary matching for exact matches (prevents partial matches)
                # Also handle common prefixes like "inPort", "fromPort", etc.
                pattern = r'(?:\b|(?<=\bin)|(?<=\bfrom)|(?<=\bto)|(?<=\bof))' + re.escape(normalized_keyword) + r'\b'
                if re.search(pattern, normalized_text):
                    matches.append(keyword)
        
        return matches
    
    def _extract_matching_snippets(self, text: str, matched_keywords: List[str]) -> List[str]:
        """Extract text snippets around matched keywords."""
        if not text or not matched_keywords:
            return []
        
        snippets = []
        normalized_text = self._normalize_text(text)
        
        for keyword in matched_keywords:
            normalized_keyword = self._normalize_text(keyword)
            
            # Find keyword position
            if '*' in normalized_keyword:
                pattern = normalized_keyword.replace('*', r'\w*')
                match = re.search(r'\b' + pattern + r'\b', normalized_text)
            else:
                match = re.search(re.escape(normalized_keyword), normalized_text)
            
            if match:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                snippet = text[start:end].strip()
                if snippet:
                    snippets.append(f"...{snippet}...")
        
        return snippets
    
    def is_match(self, vessel: Dict) -> Tuple[bool, Dict]:
        """
        Check if vessel matches our filtering criteria.
        
        Implements modified logic: 
        - Group C (Ports/Locations) is MANDATORY
        - Groups A (Vessel Types) and B (Operators) are OPTIONAL (at least one required)
        
        Args:
            vessel: ANP vessel data with fields like nOM_NAVIREField, tYP_NAVIREField, etc.
        
        Returns:
            Tuple of (is_match, filter_details)
        """
        
        # Combine searchable text fields
        searchable_text = " ".join([
            vessel.get('nOM_NAVIREField', ''),  # Vessel name
            vessel.get('tYP_NAVIREField', ''),  # Vessel type
            vessel.get('oPERATEURField', ''),   # Operator
            vessel.get('pROVField', ''),        # Provenance/Port
            vessel.get('sITUATIONField', ''),   # Situation
            vessel.get('cONSIGNATAIREField', '') # Consignee
        ])
        
        # Debug logging to see what text we're searching
        logger.debug(f"Searching text for vessel {vessel.get('nOM_NAVIREField', 'Unknown')}: {searchable_text[:200]}...")
        
        # Find matches in each keyword group
        vessel_type_matches = self._find_keyword_matches(searchable_text, self.vessel_type_keywords)
        operator_matches = self._find_keyword_matches(searchable_text, self.operator_keywords)
        port_location_matches = self._find_keyword_matches(searchable_text, self.port_location_keywords)
        
        # Debug logging for matches
        logger.debug(f"Vessel {vessel.get('nOM_NAVIREField', 'Unknown')} matches: "
                    f"Types: {vessel_type_matches}, Operators: {operator_matches}, Ports: {port_location_matches}")
        
        # Modified logic: Group C (Ports/Locations) is MANDATORY, Groups A & B are OPTIONAL
        # At least Group C + one other group must match
        is_match = (
            len(port_location_matches) > 0 and    # Group C: Ports/Locations (MANDATORY)
            (len(vessel_type_matches) > 0 or      # Group A: Vessel Types (OPTIONAL)
             len(operator_matches) > 0)           # Group B: Operators (OPTIONAL)
        )
        
        # Calculate match score and details
        match_score = len(vessel_type_matches) + len(operator_matches) + len(port_location_matches)
        groups_matched = sum([
            len(vessel_type_matches) > 0,
            len(operator_matches) > 0,
            len(port_location_matches) > 0
        ])
        
        # Extract matching snippets for context
        matched_snippets = self._extract_matching_snippets(searchable_text, 
                                                         vessel_type_matches + operator_matches + port_location_matches)
        
        filter_details = {
            "vessel_type_keywords": vessel_type_matches,
            "operator_keywords": operator_matches,
            "port_location_keywords": port_location_matches,
            "groups_matched": groups_matched,
            "total_groups": 3,
            "matched_text_snippets": matched_snippets,
            "match_score": match_score
        }
        
        return is_match, filter_details
    
    def filter_vessels(self, vessels: List[Dict]) -> List[Dict]:
        """
        Filter vessels based on matching criteria.
        
        Args:
            vessels: List of vessel dictionaries to filter
            
        Returns:
            List of vessels that match the criteria
        """
        if not vessels:
            return []
        
        matched_vessels = []
        total_vessels = len(vessels)
        
        logger.info(f"Filtering {total_vessels} vessels...")
        
        for i, vessel in enumerate(vessels):
            if i % 100 == 0 and i > 0:
                logger.info(f"Processed {i}/{total_vessels} vessels...")
            
            is_match, filter_details = self.is_match(vessel)
            
            if is_match:
                # Add filter details to vessel
                vessel['filter_details'] = filter_details
                matched_vessels.append(vessel)
        
        logger.info(f"Filtering complete: {total_vessels} -> {len(matched_vessels)} matches")
        return matched_vessels
    
    def extract_entities(self, vessel: Dict) -> Dict:
        """
        Extract categorized entities from vessel data.
        
        Args:
            vessel: Vessel dictionary
            
        Returns:
            Dictionary with extracted entities
        """
        # Combine searchable text
        searchable_text = " ".join([
            vessel.get('nOM_NAVIREField', ''),
            vessel.get('tYP_NAVIREField', ''),
            vessel.get('oPERATEURField', ''),
            vessel.get('pROVField', ''),
            vessel.get('sITUATIONField', ''),
            vessel.get('cONSIGNATAIREField', '')
        ])
        
        # Extract entities
        vessel_types = self._find_keyword_matches(searchable_text, self.vessel_type_keywords)
        operators = self._find_keyword_matches(searchable_text, self.operator_keywords)
        port_locations = self._find_keyword_matches(searchable_text, self.port_location_keywords)
        
        return {
            "vessel_type": vessel_types[0] if vessel_types else None,
            "operator": operators[0] if operators else None,
            "port_location": port_locations[0] if port_locations else None,
            "all_vessel_types": vessel_types,
            "all_operators": operators,
            "all_port_locations": port_locations
        }
    
    def get_filter_options(self, vessels: List[Dict]) -> Dict:
        """
        Get available filter options from vessel data.
        
        Args:
            vessels: List of vessels to analyze
            
        Returns:
            Dictionary with available filter options
        """
        if not vessels:
            return {
                "vessel_types": [],
                "operators": [],
                "ports": [],
                "situations": []
            }
        
        vessel_types = set()
        operators = set()
        ports = set()
        situations = set()
        
        for vessel in vessels:
            vessel_types.add(vessel.get('tYP_NAVIREField', ''))
            operators.add(vessel.get('oPERATEURField', ''))
            ports.add(vessel.get('pROVField', ''))
            situations.add(vessel.get('sITUATIONField', ''))
        
        # Remove empty values and sort
        return {
            "vessel_types": sorted([vt for vt in vessel_types if vt]),
            "operators": sorted([op for op in operators if op]),
            "ports": sorted([p for p in ports if p]),
            "situations": sorted([s for s in situations if s])
        }
