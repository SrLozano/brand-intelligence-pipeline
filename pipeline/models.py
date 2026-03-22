"""
Data models for the brand intelligence pipeline.

This module defines Pydantic models for representing scraped webpage data
and the final brand profile output.
"""

from pydantic import BaseModel, Field


class ImageData(BaseModel):
    """
    Represents an image found on a webpage.
    
    Captures image metadata including source URL, alt text, CSS classes,
    and whether the image appears in the page header.
    """
    src: str
    alt: str = Field(default="")
    classes: str = Field(default="")
    in_header: bool


class PageData(BaseModel):
    """
    Represents data scraped from a single webpage.
    
    Contains all relevant content extracted from a page including metadata,
    headings, body text, and images.
    """
    url: str
    title: str = Field(default="")
    meta_description: str = Field(default="")
    headings: list[str] = Field(default_factory=list)
    body_text: str = Field(default="")
    images: list[ImageData] = Field(default_factory=list)


class MetaData(BaseModel):
    """
    Metadata about the scraping operation.
    
    Tracks which URLs were scraped and when the profile was generated.
    """
    scraped_urls: list[str]
    generated_at: str


class Keyword(BaseModel):
    """
    Represents a business keyword or product category extracted from content.
    
    Keywords help identify the company's business focus and product offerings.
    """
    value: str
    source: str


class KeyPerson(BaseModel):
    """
    Represents a key person associated with the company.
    
    Captures leadership and important team members found on the website.
    """
    name: str
    role: str
    source_url: str


class LogoCandidate(BaseModel):
    """
    Represents a potential company logo image.
    
    Identifies images that may be the company's logo for brand recognition.
    """
    url: str
    source_url: str


class BrandSignals(BaseModel):
    """
    Container for all extracted brand intelligence signals.
    
    Aggregates LLM-extracted insights including company description,
    keywords, key people, and logo candidates.
    """
    description: str
    keywords: list[Keyword] = Field(default_factory=list)
    key_people: list[KeyPerson] = Field(default_factory=list)
    logo_candidates: list[LogoCandidate] = Field(default_factory=list)


class Subdomain(BaseModel):
    """
    Represents a discovered subdomain from Certificate Transparency logs.
    
    Captures subdomains found through crt.sh for infrastructure discovery.
    """
    value: str
    source: str


class Infrastructure(BaseModel):
    """
    Container for infrastructure discovery results.
    
    Aggregates discovered subdomains and other infrastructure data
    from various sources like Certificate Transparency logs.
    """
    discovered_subdomains: list[Subdomain] = Field(default_factory=list)


class BrandProfile(BaseModel):
    """
    The complete brand profile output.
    
    Aggregates all scraped page data along with company information
    and scraping metadata into a single exportable profile.
    """
    company: str
    input_domain: str
    pages: list[PageData]
    meta: MetaData
    brand_signals: BrandSignals | None = Field(default=None)
    infrastructure: Infrastructure | None = Field(default=None)
