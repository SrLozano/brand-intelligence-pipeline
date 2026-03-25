# How to Run the Brand Intelligence Pipeline

A simple guide to set up and run the brand intelligence scraper.

## Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **OpenAI API Key** (for brand signal extraction)

## Setup

### 1. Clone or Download the Project

```bash
cd /path/to/redsift
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Create `.env` File

Create a `.env` file in the project root with your OpenAI API key:

```bash
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

Or manually create `.env` with this content:

```
OPENAI_API_KEY=your-api-key-here
```

**Note:** The pipeline will run without an API key, but brand signal extraction (description, keywords, people, logos) will be skipped.

## Usage

### Basic Command

```bash
python main.py --company "CompanyName" --domain "example.com"
```

### Example: Nike

```bash
python main.py --company "Nike" --domain "nike.com"
```

### Example: Apple

```bash
python main.py --company "Apple" --domain "apple.com"
```

## Output

The pipeline generates a timestamped JSON file in the `output/` directory:

```
output/brand_profile_nike_2026-03-22_19-30-45.json
```

### What's Included

- **Company Information**: Name and domain
- **Infrastructure**: Discovered subdomains from crt.sh
- **Scraped Pages**: Content from homepage, about page, and Wikipedia
- **Brand Signals**:
  - Company description
  - Keywords
  - Key people
  - Logo candidates
- **Downloaded Logos**: Top logo candidates saved to `output/assets/` directory
- **Metadata**: Scraped URLs and generation timestamp

### Console Output

```
Brand profile generated for Nike
- Scraped 3 page(s)
- Extracted brand signals (description, 15 keywords, 3 people, 2 logo candidates)
- Discovered 47 subdomain(s) via crt.sh
- Output: output/brand_profile_nike_2026-03-22_19-30-45.json
```

## Troubleshooting

### Issue: `ModuleNotFoundError`

**Solution:** Ensure virtual environment is activated and dependencies are installed:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: `OPENAI_API_KEY not found`

**Solution:** Create `.env` file with your API key (see Configuration section). The pipeline will still run but skip brand signal extraction.

### Issue: `Permission denied` when creating output directory

**Solution:** Check write permissions in the project directory:
```bash
chmod +w output/
```

### Issue: Slow execution or timeouts

**Cause:** Network requests to scrape pages and query crt.sh can be slow.

**Solution:** This is normal. The pipeline typically takes 30-60 seconds depending on network speed and API response times.

### Issue: No subdomains discovered

**Cause:** crt.sh may be unavailable or the domain has no certificate transparency logs.

**Solution:** This is not critical. The pipeline will continue and generate a profile without subdomain data.

## Command-Line Options

| Option | Required | Description | Example |
|--------|----------|-------------|---------|
| `--company` | Yes | Company name | `"Nike"` |
| `--domain` | Yes | Domain to scrape | `"nike.com"` |

## What Gets Scraped

1. **Homepage** (`https://domain.com`)
2. **About Page** (`https://domain.com/about`)
3. **Leadership Page** (`https://domain.com/leadership`)
4. **Wikipedia** (if available)
5. **Subdomains** (via crt.sh certificate transparency logs)

## Logo Downloads

The pipeline automatically downloads the top 3 logo candidates identified by the AI:

- Saved to: `output/assets/`
- Filename format: `{company}_logo_{index}_{timestamp}.{extension}`
- The JSON output includes `local_path` field pointing to downloaded files
- Only successful downloads are included in the output

## Notes

- The pipeline respects a 1-second delay between page requests
- Output files are never overwritten (timestamped filenames)
- The `output/` directory is created automatically if it doesn't exist
- Brand signal extraction requires a valid OpenAI API key