# Analysis: Brand Intelligence Pipeline

## Time Spent

| Phase | Time |
|---|---|
| Planning and researching | ~1 hour |
| Coding the solution | ~1 to 1.5 hours |
| Testing and improving | ~0.5 to 1 hour |
| Documenting and analysing | ~1 hour |

**Total: ~3 to 3.5 hours building + ~1 hour documentation**

---

## What Was Automated

The pipeline takes only **company name + one domain** as input and automatically discovers:

| Manual Task (Before) | Automated Solution (After) | How |
|---|---|---|
| Upload brand logos | Highest-confidence logo candidate detected and downloaded locally | LLM-powered ranking with heuristics (header position, alt text, CSS classes) |
| Provide domain list | Full subdomain inventory discovered automatically | Certificate Transparency logs via crt.sh (up to 50 subdomains) |
| Supply business keywords | Up to 10 keywords extracted with source attribution | LLM-powered structured output from homepage, About, and Wikipedia content |
| Identify key people | Names and roles of executives/founders extracted | LLM-powered structured output from leadership and About pages, with Wikipedia as the primary structured source |
| Write company description | 1-2 sentence brand summary generated | LLM-powered from all aggregated scraped content |

Additionally, the pipeline automatically:
- Scrapes 3 high-signal pages: homepage, `/about`, `/leadership`
- Fetches and parses Wikipedia including structured infobox data
- Validates and normalizes all discovered data via Pydantic
- Generates timestamped JSON output and a local assets folder

---

## Assumptions Made

**About the input:**
- The provided domain is the primary brand domain (e.g. `nike.com`, not a subdomain like `store.nike.com`)
- The company name is in English and has a Wikipedia presence in most cases

**About web structure:**
- Most companies publish key people on either `/about` or `/leadership` paths
- Logo images will appear in the `<header>` element or have "logo" in their alt text, class, or file path
- The homepage, About page, and Wikipedia together capture most brand signals

**About Wikipedia:**
- Wikipedia was used as the primary structured source for executive names and roles. For well-known companies this is highly reliable. For smaller companies it degrades gracefully to whatever the scraper found on the company's own pages.
- The pipeline uses the Wikipedia search API with a company name suffix to disambiguate (e.g. "Nike company" instead of "Nike"). This works well for most large companies but can still resolve incorrectly for ambiguous names or smaller companies with limited Wikipedia presence.

**About infrastructure:**
- All legitimate subdomains of a brand will have SSL certificates registered in public Certificate Transparency logs
- crt.sh provides a sufficiently comprehensive view of a brand's digital footprint for onboarding purposes

---

## Trade-offs Made

**Speed vs. completeness**

The pipeline scrapes only 3 fixed pages (`/`, `/about`, `/leadership`) rather than crawling the full site. This keeps runtime under 30 seconds but may miss logos or people buried in other pages. A full crawl would be more thorough but impractical in a prototype context.

**Reliability vs. coverage for subdomain discovery**

Certificate Transparency logs via crt.sh require no authentication and return reliable, public data, but only cover SSL-certified subdomains. Other discovery methods would find more domains but introduce additional complexity, latency, and potential legal considerations. crt.sh can also be slow (5-15 seconds) for large domains with many certificates. This is an external dependency we do not control and was treated as acceptable for a prototype.

**Structured outputs vs. prompt flexibility**

Using OpenAI's structured JSON output mode guarantees parseable responses with no post-processing, but it constrains the schema. A free-form prompt with post-hoc parsing would be more flexible but far less reliable at scale.

**Single LLM call per run**

All LLM extraction (description, keywords, people, logos) happens in a single structured API call. This keeps cost and latency predictable but means the prompt is large and the model has to do more in one pass. A multi-call architecture with specialised prompts per signal type would likely improve accuracy, especially for people extraction.

**Token efficiency vs. context richness**

Truncating page body text to 2000 characters reduces API cost and latency but risks losing relevant context for less prominent brands. A smarter chunking strategy (e.g. prioritizing headings and first paragraphs) would improve quality on content-heavy pages.

**Logo download strategy**

Rather than downloading all candidates, only the highest-confidence logo URL is downloaded. This reduces noise and avoids storing incorrect assets. In a production system you would want a human review step or Vision API validation before committing any asset, since automated confidence scoring alone is not sufficient to guarantee correctness.

**Silent failures**

Every component is designed to fail silently and return `None` or an empty list rather than raising exceptions. This ensures the pipeline always produces partial output even when some sources are unavailable. This approach is acceptable for a quick prototype but in a production system silent failures need to be taken seriously: all errors should be logged with severity levels, monitored, and surfaced to operators so that data quality issues are visible and actionable.

---

## TODOs / Next Steps

These are the highest-priority improvements ranked by impact:

**Short-term (would do in next session)**

- Add structured logging with severity levels so silent failures are observable
- Validate that downloaded logo images are non-corrupt and meet minimum dimensions before saving
- Parallelize scraping and subdomain discovery (they are currently sequential but independent)

**Medium-term (production readiness)**

- Add executive photo extraction: search LinkedIn or company press pages for headshots, which are a key brand protection signal. This is especially important for less prominent people not covered by Wikipedia.
- Expand scraped pages dynamically: follow internal links to discover team, press, and contact pages
- Add social media discovery: extract Twitter/X, LinkedIn, Instagram handles from scraped content
- Support multiple seed domains as input (many brands own regional TLDs like `nike.co.uk`)
- Persist output to a database rather than flat JSON for querying and deduplication across customers

**Longer-term (platform integration)**

- Build a confidence scoring system for each extracted signal so the brand protection platform can flag low-confidence items for human review
- Implement change detection: re-run the pipeline periodically and alert when brand signals change (new subdomains, executive changes, logo updates)
- Add brand color palette extraction

---

## What I Would Improve With More Time

**Smarter logo detection**

The current approach ranks logo candidates based on heuristics (header position, alt text, CSS classes). With more time I would use a vision model to directly score images on "logo likelihood," which would handle logos embedded in complex SPAs where HTML heuristics break down.

**Key people photos**

The pipeline extracts names and roles but not photos. For a brand protection platform, executive photos are critical to detect impersonation. With more time I would query LinkedIn profiles, press release pages, or company team pages to associate each person with a headshot URL. This is especially valuable for people who are not prominent enough to appear on Wikipedia.

**Wikipedia fallback and enrichment**

If Wikipedia fails or lacks a page, the pipeline has no fallback for company context. Better alternatives would include Crunchbase or a web search (Tavily, Perplexity) for recent news to supplement the scraped content.

**Async pipeline execution**

The pipeline is fully sequential. Scraping, Wikipedia fetching, and subdomain discovery are all I/O-bound and independent, so running them concurrently would meaningfully reduce total runtime.

**Evaluation harness**

There is currently no way to measure extraction quality across companies. A small golden dataset of 10-20 well-known brands with known logos, keywords, and executives would allow automated accuracy measurement and regression testing as the prompt or pipeline changes.

**Confidence scoring**

Every extracted signal should carry a confidence score derived from real pipeline signals, not LLM self-assessment. Source page type, HTML structure, and corroboration across multiple pages are all observable signals that map cleanly to a 0.0-1.0 score. This makes the output actionable for downstream alert systems.
