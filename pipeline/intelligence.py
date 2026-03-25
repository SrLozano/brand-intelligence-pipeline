"""
LLM-based brand intelligence extraction module.

This module uses OpenAI's models with structured outputs to extract
brand intelligence signals from scraped web content.
"""

import os
import json
from openai import OpenAI
from pipeline.models import PageData, BrandSignals, Keyword, KeyPerson, LogoCandidate


def extract_brand_signals(company: str, domain: str, pages: list[PageData]) -> BrandSignals | None:
    """
    Extract brand intelligence signals using OpenAI's models
    
    Args:
        company: The company name
        domain: The company domain
        pages: List of scraped PageData objects
        
    Returns:
        BrandSignals object with extracted intelligence, or None if extraction fails
    """
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-5.4-nano")
        
        # Prepare input data
        formatted_pages = _format_pages(pages)
        formatted_images = _format_images(pages)
        
        # Build the prompt
        system_message = (
            "You are a brand intelligence extraction engine.\n"
            "Your job is to extract structured signals from raw web content.\n"
            "Return only the requested JSON. No commentary.\n"
            "Use only english in your responses. Translate terms in other languages."
        )
        
        user_message = (
            f"Company: {company}\n"
            f"Domain: {domain}\n\n"
            f"--- Scraped pages ---\n"
            f"{formatted_pages}\n\n"
            f"--- Image URLs found ---\n"
            f"{formatted_images}\n\n"
            f"Extract:\n"
            f"1. A 1-2 sentence company description\n"
            f"2. Up to 10 business keywords or product categories\n"
            f"   For each, include which part of the page it came from:\n"
            f'   "meta_description", "title", "h1", "h2", or "body"\n'
            f"3. Key people: name and role only\n"
            f"   For each, include the URL of the page they were found on\n"
            f"4. Logo candidates: pick up to 3 image URLs most likely to be\n"
            f"   the brand logo based on src path, alt text, class names,\n"
            f"   and whether the image is in the page header"
        )
        
        # Make API call with structured outputs
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            response_format=_build_json_schema()
        )
        
        # Parse response
        content = response.choices[0].message.content
        if not content:
            return None
            
        # Parse JSON and construct BrandSignals
        data = json.loads(content)
        
        # Convert to Pydantic models
        keywords = [Keyword(**kw) for kw in data.get("keywords", [])]
        key_people = [KeyPerson(**kp) for kp in data.get("key_people", [])]
        logo_candidates = [LogoCandidate(**lc) for lc in data.get("logo_candidates", [])]
        
        return BrandSignals(
            description=data.get("description", ""),
            keywords=keywords,
            key_people=key_people,
            logo_candidates=logo_candidates
        )
        
    except Exception:
        # Silent failure - return None on any error
        return None


def _format_pages(pages: list[PageData]) -> str:
    """
    Format scraped pages for LLM input.
    
    Args:
        pages: List of PageData objects
        
    Returns:
        Formatted text block with page content
    """
    formatted = []
    
    for page in pages:
        # Build page block
        block = f"[Page: {page.url}]\n"
        block += f"Title: {page.title}\n"
        block += f"Meta: {page.meta_description}\n"
        
        # Format headings
        headings_str = ", ".join(page.headings) if page.headings else ""
        block += f"Headings: {headings_str}\n"
        
        # Truncate body text to 2000 characters
        body = page.body_text[:2000] if page.body_text else ""
        block += f"Body: {body}\n"
        
        formatted.append(block)
    
    return "\n".join(formatted)


def _format_images(pages: list[PageData]) -> str:
    """
    Format image metadata for LLM input.
    
    Filters images to include only those with:
    - File extension in src (.svg, .png, .jpg, .jpeg, .webp, .gif)
    - OR non-empty alt attribute
    - OR non-empty classes attribute
    
    Args:
        pages: List of PageData objects
        
    Returns:
        Formatted text block with image metadata
    """
    formatted = []
    
    # Valid image extensions
    valid_extensions = ('.svg', '.png', '.jpg', '.jpeg', '.webp', '.gif')
    
    for page in pages:
        for img in page.images:
            # Check if image should be included
            has_extension = any(ext in img.src.lower() for ext in valid_extensions)
            has_alt = bool(img.alt.strip())
            has_classes = bool(img.classes.strip())
            
            if has_extension or has_alt or has_classes:
                block = f"- URL: {img.src}\n"
                block += f"  Alt: {img.alt}\n"
                block += f"  Classes: {img.classes}\n"
                block += f"  In Header: {img.in_header}\n"
                block += f"  Source Page: {page.url}\n"
                formatted.append(block)
    
    return "\n".join(formatted) if formatted else "No images found"


def _build_json_schema() -> dict:
    """
    Build the JSON schema for structured outputs.
    
    Returns:
        Schema dictionary for OpenAI's response_format parameter
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "brand_signals",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "keywords": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "value": {"type": "string"},
                                "source": {"type": "string"}
                            },
                            "required": ["value", "source"],
                            "additionalProperties": False
                        }
                    },
                    "key_people": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "role": {"type": "string"},
                                "source_url": {"type": ["string", "null"]},
                                "source": {"type": "string"}
                            },
                            "required": ["name", "role", "source_url", "source"],
                            "additionalProperties": False
                        }
                    },
                    "logo_candidates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "source_url": {"type": "string"}
                            },
                            "required": ["url", "source_url"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["description", "keywords", "key_people", "logo_candidates"],
                "additionalProperties": False
            }
        }
    }
