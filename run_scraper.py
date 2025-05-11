#!/usr/bin/env python
import argparse
import os
import sys
from datetime import datetime

def ensure_directories():
    """Ensure required directories exist"""
    required_dirs = [
        'data',
        'data/raw',
        'data/processed',
        'logs'
    ]
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

def main():
    # Create required directories
    ensure_directories()
    
    parser = argparse.ArgumentParser(description='Run the e-commerce scrapers')
    parser.add_argument('csv_file', nargs='?', default='products.csv', 
                        help='CSV file with products to scrape (default: products.csv)')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run in headless mode (default: True)')
    parser.add_argument('--debug', action='store_true', default=True,
                        help='Enable debug mode (default: True)')
    parser.add_argument('--platforms', nargs='+', default=['amazon', 'flipkart', 'myntra'],
                        help='Platforms to scrape (default: amazon flipkart myntra)')
    parser.add_argument('--type', choices=['csv', 'master'], default='csv',
                        help='Type of scraper to use: csv or master (default: csv)')
    parser.add_argument('--specialty-products', action='store_true', default=False,
                        help='Enable specialty products mode for unique items that need broader searches')
    parser.add_argument('--similarity-threshold', type=float, default=0.7,
                        help='Threshold for product name similarity (0.0 to 1.0, default: 0.7)')
    
    args = parser.parse_args()
    
    # Print banner
    print("=" * 80)
    print(f"Dzukou E-commerce Scraper - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check if CSV file exists
    if not os.path.exists(args.csv_file):
        print(f"Error: CSV file '{args.csv_file}' not found")
        return 1
    
    # Run the selected scraper
    if args.type == 'csv':
        from src.scrapers.csv_scraper import CSVEcommerceScraper, main as csv_main
        print(f"Running CSV scraper with {args.csv_file}")
        csv_main(args)
    elif args.type == 'master':
        from src.scrapers.master_csv_scraper import main as master_main
        print(f"Running Master CSV scraper with {args.csv_file}")
        
        # Set specialty products mode for master CSV scraper if needed
        if args.specialty_products:
            print("Enabling specialty products mode for unique items")
            # Pass the specialty_products flag to the master scraper
            original_csv_file = args.csv_file
            args.specialty_products_mode = True
            args.csv_file = original_csv_file
            
        # Set similarity threshold
        print(f"Using product similarity threshold: {args.similarity_threshold}")
            
        master_main(args)
    
    print("=" * 80)
    print(f"Scraping completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 