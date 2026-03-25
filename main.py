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
        
        # Download the logo
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Detect file extension from Content-Type header first
            content_type = response.headers.get('Content-Type', '').lower()
            ext = None
            
            if 'image/svg' in content_type:
                ext = 'svg'
            elif 'image/png' in content_type:
                ext = 'png'
            elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
                ext = 'jpg'
            elif 'image/webp' in content_type:
                ext = 'webp'
            elif 'image/gif' in content_type:
                ext = 'gif'
            
            # Fallback to URL-based detection if Content-Type didn't help
            if not ext:
                url_lower = url.lower()
                # Extract extension from URL path (before query params)
                url_path = url_lower.split('?')[0].split('#')[0]
                if url_path.endswith('.svg'):
                    ext = 'svg'
                elif url_path.endswith('.png'):
                    ext = 'png'
                elif url_path.endswith(('.jpg', '.jpeg')):
                    ext = 'jpg'
                elif url_path.endswith('.webp'):
                    ext = 'webp'
                elif url_path.endswith('.gif'):
                    ext = 'gif'
                else:
                    ext = 'png'  # default
            
            # Define output file path with company name and timestamp
            logo_filename = f"{safe_company}_logo_{idx}_{timestamp}.{ext}"
            logo_path = assets_dir / logo_filename
            
            # Write the image to disk
            with open(logo_path, 'wb') as f:
                f.write(response.content)
            
            # Update the local_path in the brand profile
            logo.local_path = str(logo_path)
            
            print(f"- Downloaded logo {idx} to {logo_path}")
            
        except Exception as e:
            print(f"Warning: Failed to download logo {idx} from {url}: {e}", file=sys.stderr)
            logo.local_path = None


def print_summary(brand_profile: BrandProfile, output_file: Path) -> None:
    """
    Print a formatted summary of the brand profile to stdout.
    
    Args:
        brand_profile: The brand profile to summarize
        output_file: Path to the output JSON file
    """
    company = brand_profile.company
    domain = brand_profile.input_domain
    
    print(f"\nBrand Profile: {company} ({domain})")
    print("-" * 30)
    
    # Description
    if brand_profile.brand_signals and brand_profile.brand_signals.description:
        desc = brand_profile.brand_signals.description
        if len(desc) > 80:
            desc = desc[:77] + "..."
        print(f"Description:   {desc}")
    else:
        print("Description:   none found")
    
    # Keywords
    if brand_profile.brand_signals and brand_profile.brand_signals.keywords:
        keywords = brand_profile.brand_signals.keywords
        first_three = [kw.value for kw in keywords[:3]]
        keywords_str = ", ".join(first_three)
        if len(keywords) > 3:
            keywords_str += f" (+ {len(keywords) - 3} more)"
        print(f"Keywords:      {keywords_str}")
    else:
        print("Keywords:      none found")
    
    # Key people
    if brand_profile.brand_signals and brand_profile.brand_signals.key_people:
        people = brand_profile.brand_signals.key_people
        people_strs = [f"{p.name} ({p.role})" for p in people]
        people_str = ", ".join(people_strs)
        # Get source from first person
        source = people[0].source if people else ""
        if source:
            people_str += f"  [{source}]"
        print(f"Key people:    {people_str}")
    else:
        print("Key people:    none found")
    
    # Logo
    if brand_profile.brand_signals and brand_profile.brand_signals.logo_candidates:
        top_logo = brand_profile.brand_signals.logo_candidates[0]
        if top_logo.local_path:
            logo_str = top_logo.local_path
        else:
            logo_str = f"{top_logo.url}  (not found)"
        print(f"Logo:          {logo_str}")
    else:
        print("Logo:          not found")
    
    # Subdomains
    if brand_profile.infrastructure and brand_profile.infrastructure.discovered_subdomains:
        count = len(brand_profile.infrastructure.discovered_subdomains)
        print(f"Subdomains:    {count} discovered via crt.sh")
    else:
        print("Subdomains:    none found. Try setting CRTSH_TIMEOUT to a higher value")
    
    print("-" * 30)
    print(f"Output written to {output_file}")
    print()


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
    output_file = output_dir / f"brand_profile_{args.company.lower()}_{timestamp}.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(brand_profile.model_dump_json(indent=2))
    except Exception as e:
        print(f"Error: Could not write output file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print formatted summary
    print_summary(brand_profile, output_file)


if __name__ == "__main__":
    main()
