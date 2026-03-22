"""
People enrichment module for extracting key people information.

This module enriches key people information using a two-layer fallback strategy:
1. First checking scraper results from intelligence.py
2. Then falling back to Wikipedia infobox parsing

The module handles all errors gracefully and never propagates exceptions.
"""

import re
import requests
from bs4 import BeautifulSoup
from pipeline.models import KeyPerson


def enrich_key_people(company: str, existing_people: list[KeyPerson] | None) -> list[KeyPerson]:
    """
    Enrich key people using two-layer fallback strategy.
    
    Args:
        company: The company name to search for
        existing_people: Key people already extracted from scraper results
        
    Returns:
        List of KeyPerson objects with proper source attribution.
        Returns empty list if no people are found or on any error.
    """
    # Layer 1: Check scraper results
    if existing_people and len(existing_people) > 0:
        # Update source field to "scraper" and return
        for person in existing_people:
            person.source = "scraper"
        return existing_people
    
    # Layer 2: Wikipedia infobox
    try:
        html = _fetch_wikipedia_page(company)
        if html:
            people = _parse_wikipedia_infobox(html)
            if people:
                return people
    except Exception:
        # Silent failure - return empty list
        pass
    
    return []


def _fetch_wikipedia_page(company: str) -> str | None:
    """
    Fetch Wikipedia page HTML for the company.
    
    Args:
        company: The company name to search for
        
    Returns:
        HTML content as string if successful, None otherwise
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Try with company name as-is first
        url = f"https://en.wikipedia.org/wiki/{company}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.text
        
        # If 404, try with underscores instead of spaces
        if response.status_code == 404:
            company_with_underscores = company.replace(' ', '_')
            url = f"https://en.wikipedia.org/wiki/{company_with_underscores}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.text
    
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, Exception):
        # Silent failure
        pass
    
    return None


def _parse_wikipedia_infobox(html: str) -> list[KeyPerson]:
    """
    Parse Wikipedia infobox to extract key people.
    
    Args:
        html: The HTML content of the Wikipedia page
        
    Returns:
        List of KeyPerson objects extracted from the infobox
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find the infobox table
        infobox = soup.find('table', class_='infobox')
        if not infobox:
            return []
        
        people = []
        
        # Iterate over rows
        rows = infobox.find_all('tr')
        for row in rows:
            th = row.find('th')
            td = row.find('td')
            
            if not th or not td:
                continue
            
            # Get the role label from header
            role_label = th.get_text(strip=True).lower()
            
            # Check if this row contains people information
            target_roles = [
                'key people',
                'founders',
                'founder',
                'ceo',
                'chief executive',
                'president',
                'chairman'
            ]
            
            if not any(target in role_label for target in target_roles):
                continue
            
            # Extract people from this row
            if 'key people' in role_label:
                # Key people row often has multiple entries
                # Split by <br> tags and newlines
                td_html = str(td)
                entries = re.split(r'<br\s*/?>\s*|\n', td_html)
                
                for entry in entries:
                    # Remove HTML tags to get clean text
                    entry_soup = BeautifulSoup(entry, 'html.parser')
                    entry_text = entry_soup.get_text(strip=True)
                    
                    if not entry_text:
                        continue
                    
                    # Parse name and role
                    parsed = _parse_person_entry(entry_text, role_label)
                    if parsed:
                        name, role = parsed
                        people.append(KeyPerson(
                            name=name,
                            role=role,
                            source_url=None,
                            source="wikipedia"
                        ))
            else:
                # Single person rows (CEO, Founder, etc.)
                # Extract text from td, handling links
                name_text = td.get_text(strip=True)
                
                if name_text:
                    # Try to parse if there's a role in parentheses
                    parsed = _parse_person_entry(name_text, role_label)
                    if parsed:
                        name, role = parsed
                    else:
                        # Use the row label as role
                        name = name_text
                        role = th.get_text(strip=True)
                    
                    people.append(KeyPerson(
                        name=name,
                        role=role,
                        source_url=None,
                        source="wikipedia"
                    ))
        
        return people
    
    except Exception:
        # Silent failure
        return []


def _parse_person_entry(entry: str, default_role: str) -> tuple[str, str] | None:
    """
    Parse a person entry to extract name and role.
    
    Handles entries like "John Donahoe (President and CEO)" or just "John Donahoe".
    
    Args:
        entry: The text entry to parse
        default_role: The default role to use if parsing fails
        
    Returns:
        Tuple of (name, role) if successful, None if entry is invalid
    """
    if not entry or not entry.strip():
        return None
    
    entry = entry.strip()
    
    # Try to match pattern: "Name (Role)"
    match = re.match(r'^(.+?)\s*\((.+?)\)$', entry)
    
    if match:
        name = match.group(1).strip()
        role = match.group(2).strip()
        return (name, role)
    
    # If no role in parentheses, use the entry as name and default_role as role
    return (entry, default_role)
