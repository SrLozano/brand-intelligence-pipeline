import os
import requests
from pipeline.models import Infrastructure, Subdomain


def discover_subdomains(domain: str, timeout: int | None = None) -> Infrastructure:
    """
    Discover subdomains using crt.sh Certificate Transparency logs.
    
    Args:
        domain: The domain to discover subdomains for
        timeout: Request timeout in seconds (default: 30, configurable via CRTSH_TIMEOUT env var)
    
    Returns:
        Infrastructure object with discovered subdomains
    """
    try:
        # Get timeout from parameter, env var, or default
        if timeout is None:
            timeout = int(os.getenv("CRTSH_TIMEOUT", "30"))
        
        # Query crt.sh API
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        
        # Get User-Agent from environment variable with default
        user_agent = os.getenv(
            'USER_AGENT',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        headers = {
            "User-Agent": user_agent
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Extract and clean subdomains
        subdomains = _parse_crtsh_response(data, domain)
        
        # Convert to Subdomain objects
        subdomain_objects = [
            Subdomain(value=sub, source="crt.sh")
            for sub in subdomains
        ]
        
        return Infrastructure(discovered_subdomains=subdomain_objects)
        
    except (requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            ValueError,
            Exception):
        # Silent failure - return empty Infrastructure
        return Infrastructure(discovered_subdomains=[])


def _clean_subdomain(subdomain: str, domain: str) -> str | None:
    """Clean and validate a single subdomain entry."""
    # Strip whitespace
    subdomain = subdomain.strip()
    
    # Skip email addresses
    if "@" in subdomain:
        return None
    
    # Skip entries with spaces (invalid subdomains)
    if " " in subdomain:
        return None
    
    # Remove wildcard prefix
    if subdomain.startswith("*."):
        subdomain = subdomain[2:]
    
    # Convert to lowercase
    subdomain = subdomain.lower()
    
    # Validate: must end with the domain
    if not subdomain.endswith(domain):
        return None
    
    # Discard if it equals the bare domain
    if subdomain == domain:
        return None
    
    return subdomain


def _parse_crtsh_response(data: list, domain: str) -> list[str]:
    """Parse crt.sh JSON response and extract unique subdomains."""
    subdomains = set()
    
    for entry in data:
        # Get name_value field
        name_value = entry.get("name_value", "")
        
        # Split on newlines to handle multiple values
        names = name_value.split("\n")
        
        for name in names:
            # Clean and validate
            cleaned = _clean_subdomain(name, domain)
            if cleaned:
                subdomains.add(cleaned)
    
    # Sort alphabetically and take first 50
    sorted_subdomains = sorted(subdomains)[:50]
    
    return sorted_subdomains
