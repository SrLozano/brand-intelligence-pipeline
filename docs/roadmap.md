# Roadmap

The roadmap prioritises trustworthiness and operability before expanding the number of signals collected.

## Reliability and observability

- Add structured logs and explicit partial-run status.
- Introduce retry policies and per-source timeout controls.
- Validate downloaded asset type, integrity, and dimensions.
- Add unit tests for URL normalisation, Certificate Transparency parsing, and model validation.

## Data quality

- Attach confidence and evidence metadata to every extracted signal.
- Add deterministic checks for domains, roles, and asset URLs.
- Build a reference dataset across organisations of different sizes and regions.
- Measure extraction precision, coverage, and regression by signal type.

## Collection coverage

- Discover relevant internal pages instead of relying on fixed paths.
- Support multiple seed domains and regional properties.
- Handle JavaScript-rendered sites through an optional collection adapter.
- Add organisation-controlled social profiles and product taxonomy signals.

## Platform integration

- Run independent network-bound stages concurrently.
- Persist profiles and evidence in a queryable store.
- Compare profile versions and emit material-change events.
- Add analyst review queues for low-confidence or conflicting signals.
- Expose the pipeline through a service interface for scheduled monitoring.
