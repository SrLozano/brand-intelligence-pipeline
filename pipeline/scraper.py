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
