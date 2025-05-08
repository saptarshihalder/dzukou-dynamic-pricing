# Dzukou Dynamic Pricing

A tool to track and analyze e-commerce product prices over time.

## Features

- Scrapes product prices from multiple e-commerce platforms:
  - Flipkart
  - Amazon
- Uses Selenium to handle JavaScript-rendered content and bypass anti-scraping measures
- Scheduled automatic data collection via GitHub Actions
- Stores historical price data for analysis

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Chrome (required for Selenium)

3. Run the scraper:
```bash
python selenium_scraper.py
```

## Data Output

The scraper saves data in JSON format to `data/raw/prices_YYYYMMDD_HH.json` with the following structure:

```json
[
  {
    "timestamp": "20250508_195743",
    "platform": "flipkart",
    "product_name": "Awenest Bamboo Toothbrush",
    "url": "https://www.flipkart.com/...",
    "title": "awenest Bamboo with Charcoal Activated Bristles...",
    "current_price": "32",
    "original_price": "55",
    "discount": "42% off",
    "stock_status": "In Stock"
  },
  {
    "timestamp": "20250508_195745",
    "platform": "amazon",
    "product_name": "Bamboo India Toothbrush",
    "url": "https://www.amazon.in/...",
    "title": "Bamboo India Toothbrush Pack of 1 (Brown)",
    "current_price": "55",
    "stock_status": "In Stock"
  }
]
```

## Automated Scraping

The scraper runs automatically every 6 hours via GitHub Actions. You can also trigger it manually from the Actions tab in the GitHub repository.

## Development

To add new products or platforms:

1. Update the `PRODUCTS` list in `selenium_scraper.py`
2. For new platforms, add a new scraping method following the pattern of existing ones
3. Test locally before committing

## Future Enhancements

- Add more e-commerce platforms
- Implement price change alerts
- Create data visualization dashboard
- Add product category analysis
