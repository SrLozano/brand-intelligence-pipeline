# Operations guide

## Prerequisites

- Python 3.10 or newer
- Network access to target websites, Wikipedia, `crt.sh`, and the OpenAI API
- An OpenAI API key when structured brand-signal extraction is required

## Local setup

```bash
git clone https://github.com/SrLozano/brand-intelligence-pipeline.git
cd brand-intelligence-pipeline

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

Export configuration through the shell:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_MODEL="gpt-5.4-nano"
export REQUEST_TIMEOUT="10"
export CRTSH_TIMEOUT="30"
```

Alternatively, copy the committed template and add local values:

```bash
cp .env.example .env
```

The resulting `.env` file uses the following keys:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.4-nano
REQUEST_TIMEOUT=10
CRTSH_TIMEOUT=30
```

The `.env` file is ignored by Git. Do not commit credentials or generated profiles.

## Run a profile

```bash
python main.py --company "Nike" --domain "nike.com"
```

Both arguments are required:

| Argument | Description | Example |
|---|---|---|
| `--company` | Human-readable organisation name | `"Nike"` |
| `--domain` | Seed domain without protocol or path | `"nike.com"` |

## Generated data

Profiles are written to:

```text
output/brand_profile_{company}_{timestamp}.json
```

Downloaded logo candidates are written to `output/assets/`. Output names include a timestamp, so subsequent runs do not replace earlier profiles.

## Partial results

The pipeline can finish successfully with incomplete data when a website, Wikipedia, `crt.sh`, the LLM, or an asset URL is unavailable. Review the resulting `pages`, `infrastructure`, and `brand_signals` fields before using a profile downstream.

If extraction is empty, check that `OPENAI_API_KEY` is set and that `OPENAI_MODEL` is available to the configured account. If subdomain discovery is empty, retry with a higher `CRTSH_TIMEOUT` and confirm that `crt.sh` is reachable.

## Operational checks

Before integrating a profile into another system:

1. Confirm the input domain belongs to the intended organisation.
2. Review collected source URLs for false matches.
3. Validate important names, roles, and domains independently.
4. Inspect downloaded assets before opening or processing them.
5. Treat absence of a signal as unknown rather than negative evidence.
