# E-commerce Product Scrapers

This directory contains scrapers to extract product data from multiple e-commerce platforms.

## Available Scrapers

1. **CSV-Based E-commerce Scraper** (`csv_scraper.py`)
   - Uses a simple CSV with platform, product name, and optional URL
   - Good for ad-hoc scraping of arbitrary products

2. **Master Product Scraper** (`master_csv_scraper.py`) - NEW!
   - Uses the master product CSV file format
   - Automatically searches for your products across multiple platforms
   - Includes master price and cost data in the results

## Master Product Scraper

### Features

- 🛒 Supports multiple e-commerce platforms (Flipkart, Amazon, Myntra)
- 📊 Reads from your master product catalog CSV file
- 🔍 Automatically searches for products by name across platforms
- 🤖 Implements anti-bot detection mechanisms 
- 📈 Outputs data in both JSON and CSV formats with SKU references
- 🐛 Includes debugging capabilities

### Master CSV File Format

The scraper expects a master CSV file with the following columns:

- `name` (required): The name of the product
- `sku` (required): Your internal SKU for the product
- `current_price_eur` (optional): Current price in EUR
- `unit_cost_eur` (optional): Unit cost in EUR
- `ingested_at` (optional): Timestamp when the product was added

Example:

```csv
name,sku,current_price_eur,unit_cost_eur,ingested_at
Reiek Peak Wooden Sunglasses,SG0001,57.95,14.23,2025-05-06 16:42:23.626192
Fibonacci Wooden Sunglasses,SG0002,61.5,14.23,2025-05-06 16:42:23.626192
```

### Usage

```bash
# Basic usage
python src/scrapers/master_csv_scraper.py data/master/product_master_clean.csv

# Specify platforms to scrape
python src/scrapers/master_csv_scraper.py data/master/product_master_clean.csv --platforms amazon flipkart

# With additional options
python src/scrapers/master_csv_scraper.py data/master/product_master_clean.csv --headless --debug
```

Command-line options:
- `--platforms`: Specify which platforms to scrape (default: amazon, flipkart, myntra)
- `--headless`: Run the browser in headless mode (no UI)
- `--debug`: Enable debug mode (save HTML pages for troubleshooting)

### Output

The scraper generates:
1. JSON data: `data/raw/price_data_YYYYMMDD_HHMMSS.json`
2. CSV data: `data/processed/price_data_YYYYMMDD_HHMMSS.csv` 
3. Log file: `logs/scraper_log_YYYYMMDD_HHMMSS.txt`
4. Debug HTML files (if debug mode enabled)

## Original CSV Scraper

# CSV-Based E-commerce Scraper

A robust Selenium-based scraper that extracts product data from multiple e-commerce platforms using a CSV file input.

## Features

- 🛒 Supports multiple e-commerce platforms (Flipkart, Amazon, Myntra)
- 📋 Uses CSV file input to define products to scrape
- 🤖 Implements anti-bot detection mechanisms
- 📊 Outputs data in both JSON and CSV formats
- 🐛 Includes debugging capabilities

## Requirements

- Python 3.6+
- Chrome browser
- Required packages:
  - selenium
  - webdriver_manager
  - and others in requirements.txt

## CSV File Format

The scraper expects a CSV file with the following columns:

- `platform` (required): The platform to scrape (flipkart, amazon, myntra)
- `product_name` (required): The name of the product to find
- `url` (optional): Direct URL to the product (if omitted, will search for the product)

Example CSV file content:

```csv
platform,product_name,url
flipkart,Bamboo Toothbrush,https://www.flipkart.com/awenest-bamboo-charcoal-activated-bristles-treated-neem-oil-extra-soft-toothbrush/p/itm5a51260c0237e
amazon,Bamboo Toothbrush with Charcoal Bristles,
myntra,Bamboo Cotton Swabs,
```

## Usage

1. Create a CSV file with your products using the format described above
2. Run the scraper:

```bash
# Basic usage
python src/scrapers/csv_scraper.py products.csv

# With additional options
python src/scrapers/csv_scraper.py products.csv --headless --debug
```

Command-line options:
- `--headless`: Run the browser in headless mode (no UI)
- `--debug`: Enable debug mode (save HTML pages for troubleshooting)

## Output Files

The scraper generates the following output files:

1. JSON data: `data/raw/price_data_YYYYMMDD_HHMMSS.json`
2. CSV data: `data/processed/price_data_YYYYMMDD_HHMMSS.csv`
3. Log file: `logs/scraper_log_YYYYMMDD_HHMMSS.txt`
4. Debug HTML (if debug mode enabled): `data/raw/{platform}_debug_YYYYMMDD_HHMMSS.html`

## Troubleshooting

If you encounter issues with the scraper:

1. Enable debug mode to save the HTML content of problematic pages
2. Check the log files for detailed error messages
3. Adjust the wait times if sites are loading slowly
4. Consider using proxies if you're being blocked by the websites 