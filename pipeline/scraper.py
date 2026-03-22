"""
Web scraping functionality for the brand intelligence pipeline.

This module provides functions to scrape web pages and extract structured data
including metadata, headings, body text, and images.
"""

import os
import requests
from bs4 import BeautifulSoup
from pipeline.models import PageData, ImageData


def scrape_domain(domain: str) -> list[PageData]:
    """
    Scrape homepage and common pages from a domain.
    
    Args:
        domain: The domain to scrape (e.g., "nike.com")
        
    Returns:
        List of PageData objects for successfully scraped pages.
        Returns empty list if all pages fail to load.
    """
    urls = [
        f"https://{domain}",
        f"https://{domain}/about",
        f"https://{domain}/leadership"
    ]
    
    pages = []
    for url in urls:
        page_data = _scrape_page(url)
        if page_data:
            pages.append(page_data)
    
    return pages


def _scrape_page(url: str) -> PageData | None:
    """
    Helper function to scrape a single page.
    
    Args:
        url: The full URL to scrape
        
    Returns:
        PageData object if successful, None if page fails to load
    """
    # Get User-Agent from environment variable with default
    user_agent = os.getenv(
        'USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    headers = {
        'User-Agent': user_agent
    }
    
    # Get timeout from environment variable with default
    timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Skip if not successful status code
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', "") if meta_desc_tag else ""
        
        # Extract headings (h1 and h2)
        headings = []
        for heading in soup.find_all(['h1', 'h2']):
            heading_text = heading.get_text(strip=True)
            if heading_text:
                headings.append(heading_text)
        
        # Extract body text
        body_text = soup.get_text(strip=True, separator=' ')
        
        # Extract images
        images = _extract_images(soup)
        
        return PageData(
            url=url,
            title=title,
            meta_description=meta_description,
            headings=headings,
            body_text=body_text,
            images=images
        )
        
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, Exception):
        # Silent failure - return None if any error occurs
        return None


def _extract_images(soup: BeautifulSoup) -> list[ImageData]:
    """
    Helper function to extract image data from a BeautifulSoup object.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        
    Returns:
        List of ImageData objects for all images found on the page
    """
    images = []
    
    for img in soup.find_all('img'):
        # Get src attribute
        src = img.get('src', '')
        
        # Get alt attribute
        alt = img.get('alt', '')
        
        # Get classes as space-separated string
        classes = ' '.join(img.get('class', []))
        
        # Check if image is in header
        in_header = bool(img.find_parents('header'))
        
        images.append(ImageData(
            src=src,
            alt=alt,
            classes=classes,
            in_header=in_header
        ))
    
    return images


def fetch_wikipedia(company: str) -> PageData | None:
    """
    Fetch and parse Wikipedia page for a company using Wikipedia search API.
    
    Uses a two-step approach:
    1. Search for the company page using Wikipedia search API
    2. Fetch and parse the resolved page
    
    Args:
        company: The company name (e.g., "Nike" or "Red Sift")
        
    Returns:
        PageData object if successful, None if page fails to load or not found
    """
    # Get User-Agent from environment variable with default
    user_agent = os.getenv(
        'USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    headers = {
        'User-Agent': user_agent
    }
    
    # Get timeout from environment variable with default
    timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
    
    # Step 1: Search for the correct Wikipedia page
    try:
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': f"{company} company",
            'format': 'json',
            'srlimit': 1
        }
        
        search_response = requests.get(search_url, params=search_params, headers=headers, timeout=timeout)
        
        if search_response.status_code != 200:
            return None
        
        search_data = search_response.json()
        results = search_data.get('query', {}).get('search', [])
        
        if not results:
            # No results found
            return None
        
        # Get the title of the first result
        page_title = results[0]['title']
        
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, Exception):
        # Silent failure - return None if search fails
        return None
    
    # Step 2: Fetch the resolved page
    try:
        # Replace spaces with underscores for Wikipedia URL format
        url_title = page_title.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{url_title}"
        
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Skip if not successful status code
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract meta description
        meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc_tag.get('content', "") if meta_desc_tag else ""
        
        # Extract headings (h1 and h2)
        headings = []
        for heading in soup.find_all(['h1', 'h2']):
            heading_text = heading.get_text(strip=True)
            if heading_text:
                headings.append(heading_text)
        
        # Extract body text
        body_text = soup.get_text(strip=True, separator=' ')
        
        # Extract and prepend infobox data
        infobox_text = _extract_infobox(soup)
        if infobox_text:
            body_text = infobox_text + body_text
        
        # Truncate body text to 2000 characters
        body_text = body_text[:2000]
        
        # Extract images
        images = _extract_images(soup)
        
        return PageData(
            url=url,
            title=title,
            meta_description=meta_description,
            headings=headings,
            body_text=body_text,
            images=images
        )
        
    except (requests.exceptions.RequestException, requests.exceptions.Timeout, Exception):
        # Silent failure - return None if any error occurs
        return None


def _extract_infobox(soup: BeautifulSoup) -> str:
    """
    Extract Wikipedia infobox as formatted text.
    
    Args:
        soup: BeautifulSoup object of the parsed HTML
        
    Returns:
        Formatted infobox text with label-value pairs, or empty string if no infobox found
    """
    infobox = soup.find('table', class_='infobox')
    if not infobox:
        return ""
    
    infobox_lines = []
    for row in infobox.find_all('tr'):
        # Find both th (header) and td (data) in the row
        th = row.find('th')
        td = row.find('td')
        
        if th and td:
            label = th.get_text(strip=True)
            value = td.get_text(strip=True)
            if label and value:
                infobox_lines.append(f"{label}: {value}\n")
    
    return ''.join(infobox_lines)
