# Product brief

## Purpose

Brand-protection and digital-risk teams need a reliable baseline of the public signals associated with an organisation. Creating that baseline manually is slow, inconsistent, and difficult to repeat as a brand's web presence changes.

Brand Intelligence Pipeline turns a company name and a seed domain into a structured, source-aware profile that can be reviewed by an analyst or consumed by downstream monitoring systems.

## Product goals

- Reduce the time required to assemble an initial brand profile.
- Keep discovered signals traceable to their public sources.
- Produce predictable, machine-readable output.
- Degrade gracefully when individual sources are unavailable.
- Separate discovery from verification and enforcement decisions.

## Inputs and outputs

The pipeline requires two inputs:

- a company name;
- a primary or otherwise trusted seed domain.

It produces a timestamped JSON profile containing collected pages, observed subdomains, extracted business context, key people, and candidate brand assets. Logo files that can be downloaded successfully are stored alongside the profile.

## Workflow

1. Collect the seed domain's homepage and common corporate pages.
2. Retrieve relevant public company context from Wikipedia when available.
3. Query Certificate Transparency data for related hostnames.
4. Extract structured brand signals from the collected content.
5. Download top-ranked logo candidates.
6. Validate and export the assembled profile.

## Trust model

The pipeline intentionally treats its output as evidence for review rather than ground truth:

- a discovered hostname is an observation, not proof of ownership;
- a logo candidate may be a partner or product asset rather than the primary brand mark;
- names and roles can be incomplete or outdated;
- source availability and page structure vary between organisations.

Downstream systems should preserve source URLs, apply confidence rules, and require human review for consequential actions.

## Non-goals

The current project does not:

- determine whether a domain is malicious;
- prove legal ownership or trademark infringement;
- crawl an entire website;
- provide continuous monitoring or alerting;
- replace analyst verification.

These boundaries keep the core focused on repeatable profile generation while leaving room for specialised detection and enforcement layers.
