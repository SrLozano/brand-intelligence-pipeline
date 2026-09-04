# Architecture and design decisions

## System overview

The pipeline is a synchronous CLI application with four stages: collection, discovery, extraction, and export. Each external source is isolated so a partial profile can still be produced when one dependency fails.

```text
Company + seed domain
        |
        +-- website collection --------+
        +-- Wikipedia enrichment ------+--> structured extraction --> brand signals
        +-- Certificate Transparency --+
                                                                  +--> validated JSON
        logo candidates ------------------------------------------+--> local assets
```

## Collection

`pipeline/scraper.py` requests the homepage, `/about`, and `/leadership`. It captures page titles, descriptions, headings, body text, and image metadata. Wikipedia is queried separately and contributes structured company context when a suitable result is available.

The bounded page set keeps execution and model context predictable. It also means non-standard corporate sites may require configurable discovery or a focused crawler.

## Infrastructure discovery

`pipeline/discovery.py` queries `crt.sh` for Certificate Transparency records, normalises wildcard entries, removes malformed values, deduplicates results, and returns up to 50 observed subdomains.

Certificate data provides broad, unauthenticated coverage, but it is historical evidence rather than proof of current ownership. Results should be validated with DNS, HTTP, registration, and organisation-specific data before use in risk decisions.

## Structured extraction

`pipeline/intelligence.py` sends bounded page content and image metadata to the configured OpenAI model. A strict JSON schema constrains the response to the project's domain model:

- company description;
- sourced business keywords;
- key people and roles;
- logo candidates and source pages.

A single model call keeps latency and cost predictable. More specialised deployments may split extraction by signal type, add evidence scoring, and compare results across models or deterministic extractors.

## Validation and export

`pipeline/models.py` defines the contract between collectors, extraction, and consumers. Pydantic validates the assembled profile before `main.py` writes a timestamped JSON document. Successfully downloaded logo candidates receive a local asset path in the exported record.

## Failure model

External collection failures currently return empty values rather than stopping the full run. This supports best-effort discovery but limits operational visibility. A production deployment should add:

- structured logs with source and failure category;
- bounded retries with backoff;
- per-source latency and success metrics;
- run-level quality indicators;
- explicit exit codes for complete, partial, and failed profiles.

## Security and privacy

- API credentials are supplied at runtime and must not be committed.
- Collected text and URLs may contain personal information published on public pages.
- Output retention should match the operator's privacy and security requirements.
- Downloaded assets are untrusted input and should be validated before further processing.
- Automated collection should honour applicable terms, rate limits, and legal constraints.

## Current constraints

- Collection is sequential and limited to a fixed set of paths.
- JavaScript-rendered content may not be visible to the scraper.
- Wikipedia resolution can be ambiguous for smaller organisations.
- Logo ranking uses textual and structural hints rather than image analysis.
- Extraction quality is not yet measured against a reference dataset.

Planned work is tracked in the [roadmap](roadmap.md).
