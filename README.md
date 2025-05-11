# Dzukou Dynamic Pricing

A collection of scrapers for e-commerce platforms to track product prices and implement dynamic pricing strategies.

## Overview

This project provides tools to scrape product information from e-commerce platforms (Amazon, Flipkart, Myntra) and track price changes over time. It supports multiple scraping approaches:

1. **CSV-based scraping** - Provide a CSV with platform, product name, and optional direct URLs
2. **Master CSV scraping** - Use your master product catalog with SKUs to scrape prices
3. **Scrapy-based scraping** - Use the Scrapy framework for more robust crawling

## New Features

### Product Name Matching

The scraper now includes intelligent product name matching to identify and reject false matches:

- **Semantic Matching**: Uses sentence transformers (all-MiniLM-L6-v2) to compare product names
- **Category Validation**: Ensures products belong to the same category (e.g., sunglasses, thermoses)
- **Exclusion Terms**: Automatically rejects accessories like "case", "cover" or clothing with the product name
- **Configurable Threshold**: Set your preferred similarity threshold (0.6-0.8 recommended)

To use product matching:

```bash
python run_scraper.py products.csv --type master --similarity-threshold 0.7
```

If you need stricter matching (fewer false positives):
```bash
python run_scraper.py products.csv --type master --similarity-threshold 0.8
```

For more lenient matching (fewer rejections):
```bash
python run_scraper.py products.csv --type master --similarity-threshold 0.6
```

### Fallback Mode

If the sentence transformer model is unavailable, the system will automatically fall back to rule-based matching using Jaccard similarity (word overlap).

## Directory Structure

```
├── data/
│   ├── raw/         # Raw JSON data from scrapers
│   └── processed/   # Cleaned CSV data for analysis
├── logs/            # Log files and debug HTML
├── src/
│   └── scrapers/    # Main scrapers implementation
├── spiders/         # Scrapy spider implementations
├── products.csv     # Sample product list for scraping
├── requirements.txt # Python dependencies
└── run_scraper.py   # Main runner script
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dzukou-dynamic-pricing.git
cd dzukou-dynamic-pricing
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with:

```bash
python run_scraper.py [CSV_FILE] --type [csv|master|scrapy] [OPTIONS]
```

Options:
- `--headless`: Run in headless mode (default: True)
- `--debug`: Enable debug mode (default: True)
- `--platforms`: Platforms to scrape (default: amazon flipkart myntra)
- `--specialty-products`: Enable specialty products mode for unique items
- `--similarity-threshold`: Threshold for product name matching (0.0-1.0, default: 0.7)

Examples:

```bash
# Basic usage with default settings
python run_scraper.py products.csv --type master

# Scrape only Amazon with stricter product matching
python run_scraper.py products.csv --type master --platforms amazon --similarity-threshold 0.8

# Scrape specialty products with more lenient matching
python run_scraper.py specialty_products.csv --type master --specialty-products --similarity-threshold 0.6
```

## Features

- 🛒 Support for multiple e-commerce platforms
- 📊 Multiple scraper implementations for different needs
- 🤖 Anti-bot detection measures
- 📈 Output in both JSON and CSV formats
- 🔄 Price tracking over time
- 🪲 Debug mode for troubleshooting

## License

MIT

## Contributing

To add new products or platforms:

1. Update the `PRODUCTS` list in `selenium_scraper.py`
2. For new platforms, add a new scraping method following the pattern of existing ones
3. Test locally before committing
