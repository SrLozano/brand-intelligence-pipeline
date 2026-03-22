"""
Command-line interface for the brand intelligence pipeline.

This script orchestrates the scraping process and outputs a brand profile
to a JSON file.
"""

import argparse
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv
from pipeline.scraper import scrape_domain
from pipeline.models import BrandProfile, MetaData
from pipeline.intelligence import extract_brand_signals
from pipeline.discovery import discover_subdomains


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
