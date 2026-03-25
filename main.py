"""
Command-line interface for the brand intelligence pipeline.

This script orchestrates the scraping process and outputs a brand profile
to a JSON file.
"""

import argparse
import datetime
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
from pipeline.scraper import scrape_domain, fetch_wikipedia
from pipeline.models import BrandProfile, MetaData
from pipeline.intelligence import extract_brand_signals
from pipeline.discovery import discover_subdomains


def download_logo_candidates(brand_profile: BrandProfile, output_dir: Path, company: str) -> None:
    """
    Download the top 3 logo candidates and update their local_path.
    
    Args:
        brand_profile: The brand profile containing logo candidates
        output_dir: The output directory path
        company: The company name for filename generation
    """
    # Check if brand_signals and logo_candidates exist
    if not brand_profile.brand_signals:
        return
    
    if not brand_profile.brand_signals.logo_candidates:
        return
    
    # Create assets directory
    assets_dir = output_dir / "assets"
    try:
        assets_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create assets directory: {e}", file=sys.stderr)
        return
    
    # Generate timestamp for filenames
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    
    # Sanitize company name for filename (replace spaces and special chars with underscores)
    safe_company = "".join(c if c.isalnum() else "_" for c in company).lower()
    
    # Get User-Agent from environment variable with default
    user_agent = os.getenv(
        'USER_AGENT',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    headers = {
        'User-Agent': user_agent
    }
    
    # Download up to top 3 logo candidates
    num_to_download = min(3, len(brand_profile.brand_signals.logo_candidates))
    
    for idx in range(num_to_download):
        logo = brand_profile.brand_signals.logo_candidates[idx]
        
        # Normalize URL - handle protocol-relative URLs
        url = logo.url
        if url.startswith('//'):
            url = 'https:' + url
        elif not url.startswith(('http://', 'https://')):
            # Handle relative URLs by prepending https://
            url = 'https://' + url.lstrip('/')
        
        # Infer file extension from URL
        url_lower = logo.url.lower()
        if '.svg' in url_lower:
            ext = 'svg'
        elif '.png' in url_lower:
            ext = 'png'
        elif '.jpg' in url_lower or '.jpeg' in url_lower:
            ext = 'jpg'
        elif '.webp' in url_lower:
            ext = 'webp'
        else:
            ext = 'png'  # default
        
        # Define output file path with company name and timestamp
        logo_filename = f"{safe_company}_logo_{idx}_{timestamp}.{ext}"
        logo_path = assets_dir / logo_filename
        
        # Download the logo
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Write the image to disk
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            
            # Update the local_path in the brand profile
            logo.local_path = str(logo_path)
            
            print(f"- Downloaded logo {idx} to {logo_path}")
            
        except Exception as e:
            print(f"Warning: Failed to download logo {idx} from {url}: {e}", file=sys.stderr)
            logo.local_path = None


def main() -> None:
    """Main CLI entry point."""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate a brand intelligence profile by scraping a company's website."
    )
    parser.add_argument(
        "--company",
        required=True,
        help="The company name (e.g., 'Nike')"
    )
    parser.add_argument(
        "--domain",
        required=True,
        help="The domain to scrape (e.g., 'nike.com')"
    )
    
    args = parser.parse_args()
    
    # Call scraper to get page data
    pages = scrape_domain(args.domain)
    
    # Also fetch Wikipedia page for additional context
    wikipedia_page = fetch_wikipedia(args.company)
    if wikipedia_page:
        pages.append(wikipedia_page)
    
    # Extract brand signals using LLM
    brand_signals = extract_brand_signals(args.company, args.domain, pages)
    
    # Discover subdomains via crt.sh
    infrastructure = discover_subdomains(args.domain)
    
    # Extract scraped URLs from successfully scraped pages
    scraped_urls = [page.url for page in pages]
    
    # Create metadata with current timestamp
    meta = MetaData(
        scraped_urls=scraped_urls,
        generated_at=datetime.datetime.now(datetime.UTC).isoformat()
    )
    
    # Build the brand profile
    brand_profile = BrandProfile(
        company=args.company,
        input_domain=args.domain,
        infrastructure=infrastructure,
        pages=pages,
        brand_signals=brand_signals,
        meta=meta
    )
    
    # Ensure output directory exists
    output_dir = Path("output")
    try:
        output_dir.mkdir(exist_ok=True)
    except Exception as e:
        print(f"Error: Could not create output directory: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Download top 3 logo candidates before writing JSON
    download_logo_candidates(brand_profile, output_dir, args.company)
    
    # Write brand profile to JSON file with timestamp
    timestamp = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
    output_file = output_dir / f"brand_profile_{timestamp}.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(brand_profile.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: Could not write output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print summary
    num_pages = len(pages)
    print(f"Brand profile generated for {args.company}")
    print(f"- Scraped {num_pages} page(s)")
    if brand_signals:
        print(f"- Extracted brand signals (description, {len(brand_signals.keywords)} keywords, {len(brand_signals.key_people)} people, {len(brand_signals.logo_candidates)} logo candidates)")
    else:
        print("- Brand signals extraction skipped (no OpenAI API key or extraction failed)")
    if infrastructure and infrastructure.discovered_subdomains:
        print(f"- Discovered {len(infrastructure.discovered_subdomains)} subdomain(s) via crt.sh")
    else:
        print("- No subdomains discovered (crt.sh query failed or returned no results)")
    print(f"- Output: {output_file}")


if __name__ == "__main__":
    main()
