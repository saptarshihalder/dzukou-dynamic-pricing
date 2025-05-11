import json
import os
import time
import random
import csv
import re
import argparse
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import quote_plus

# Import our product matcher
from .utils.product_matcher import ProductMatcher

class MasterProductScraper:
    def __init__(self, master_csv_file, headless=True, debug_mode=True, platforms=None, specialty_products_mode=False, similarity_threshold=0.7):
        """
        Initialize the scraper with configurable options
        
        Args:
            master_csv_file: Path to the master CSV file with products to scrape
            headless: Whether to run browser in headless mode
            debug_mode: Whether to save debug files
            platforms: List of platforms to scrape (default: ["amazon", "flipkart", "myntra"])
            specialty_products_mode: Whether to use specialized search for unique products
            similarity_threshold: Threshold for product name similarity (0.0 to 1.0)
        """
        self.master_csv_file = master_csv_file
        self.setup_driver(headless)
        self.results = []
        self.debug_mode = debug_mode
        self.platforms = platforms or ["amazon", "flipkart", "myntra"]
        self.specialty_products_mode = specialty_products_mode
        self.debug_files = []  # Track debug files created
        self.max_debug_files = 2  # Maximum number of debug files to keep per platform
        self.similarity_threshold = similarity_threshold
        
        # Initialize the product matcher
        try:
            self.product_matcher = ProductMatcher(threshold=similarity_threshold)
            self.log(f"Product matcher initialized with threshold {similarity_threshold}")
        except Exception as e:
            self.log(f"Error initializing product matcher: {e}")
            self.log("Will proceed without product similarity checking")
            self.product_matcher = None
        
        # Create data directories if they don't exist
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Setup logging
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f'logs/scraper_log_{self.timestamp}.txt'
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"MasterProductScraper initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except UnicodeEncodeError:
            with open(self.log_file, 'w', encoding='ascii', errors='replace') as f:
                f.write(f"MasterProductScraper initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Now that log_file is initialized, we can log specialty mode status
        if self.specialty_products_mode:
            self.log("Specialty products mode enabled for better product matching")
        
        # Validate CSV file exists
        if not os.path.exists(master_csv_file):
            self.log(f"Error: Master CSV file '{master_csv_file}' not found")
            raise FileNotFoundError(f"CSV file '{master_csv_file}' not found")
    
    def log(self, message):
        """Log a message to both console and log file"""
        # Handle potential encoding issues with rupee symbol
        if isinstance(message, str):
            message = message.replace('\u20b9', 'Rs.').replace('₹', 'Rs.')
            # Fix double 'Rs.' if it occurs
            message = message.replace('Rs.Rs.', 'Rs.')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + "\n")
        except UnicodeEncodeError:
            # If encoding error occurs, try with a safe encoding
            with open(self.log_file, 'a', encoding='ascii', errors='replace') as f:
                f.write(log_message + "\n")
    
    def setup_driver(self, headless=True):
        """Set up the Selenium WebDriver with robust anti-detection measures"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        # Basic options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Enhanced anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Random user agent from a more comprehensive list
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Additional headers to mimic a real browser
        chrome_options.add_argument("--accept-language=en-US,en;q=0.9")
        chrome_options.add_argument("--accept=text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
        
        try:
            # Install and setup Chrome driver
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Modify navigator.webdriver flag to prevent detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set longer timeouts for more stability
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            self.log(f"Error setting up WebDriver: {e}")
            raise
    
    def random_sleep(self, min_seconds=0.5, max_seconds=2):
        """Sleep for a random amount of time to mimic human behavior"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        if self.debug_mode:
            self.log(f"Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection but with reduced sleeping times"""
        # Randomized scrolling pattern - but less scrolls and shorter sleeps
        scroll_count = random.randint(2, 4)
        for i in range(scroll_count):
            scroll_amount = random.randint(100, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount})")
            self.random_sleep(0.2, 0.7)
        
        # Sometimes scroll back up partially
        if random.random() > 0.5:
            self.driver.execute_script(f"window.scrollBy(0, -{random.randint(300, 600)})")
            self.random_sleep(0.2, 0.5)
        
        # Finally scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0)")
        self.random_sleep(0.3, 1)

    def search_for_product(self, platform, product_name):
        """Search for a product on a specific platform and return search results page URL"""
        try:
            # For specialty products, extract key terms from the product name
            # to increase chances of finding similar items
            specialty_mode = hasattr(self, 'specialty_products_mode') and self.specialty_products_mode
            
            if specialty_mode:
                # Extract key terms for better search results with specialty products
                keywords = self.extract_search_keywords(product_name)
                search_term = quote_plus(keywords)
                self.log(f"Specialty products mode: Using keywords '{keywords}' instead of '{product_name}'")
            else:
                search_term = quote_plus(product_name)
            
            if platform.lower() == "amazon":
                search_url = f"https://www.amazon.in/s?k={search_term}"
                self.driver.get(search_url)
                self.random_sleep(1, 3)
                
                # Check if we need to solve a CAPTCHA or if we're blocked
                if "Sorry, we just need to make sure you're not a robot" in self.driver.page_source:
                    self.log(f"⚠️ Amazon CAPTCHA detected when searching for {product_name}")
                    return None
                
                # Try to find the first product result
                try:
                    # Look for product links in search results - use multiple selectors for better matching
                    product_selectors = [
                        "a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal",
                        "a.a-link-normal.a-text-normal",
                        "div.sg-col-inner h2 a",
                        "h2.a-size-mini a",
                        "h2 a.a-link-normal"
                    ]
                    
                    # Try each selector
                    for selector in product_selectors:
                        product_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if product_links and len(product_links) > 0:
                            # Get the first product URL
                            product_url = product_links[0].get_attribute("href")
                            if product_url:
                                # Extract the base product URL (remove tracking parameters)
                                product_url = product_url.split("/ref=")[0]
                                return product_url
                    
                    # If we couldn't find with selectors, try with JavaScript
                    product_url = self.driver.execute_script(
                        "return document.querySelector('a[href*=\"/dp/\"]').getAttribute('href')"
                    )
                    if product_url:
                        return product_url.split("/ref=")[0]
                        
                except Exception as e:
                    self.log(f"Error finding Amazon product: {e}")
                    return None
                
            elif platform.lower() == "flipkart":
                search_url = f"https://www.flipkart.com/search?q={search_term}"
                self.driver.get(search_url)
                self.random_sleep(1, 3)
                
                # Check if we need to close a login popup
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")
                    close_button.click()
                    self.random_sleep(0.5, 1)
                except:
                    pass  # No login popup to close
                
                # Try to find the first product result with multiple selectors
                try:
                    product_selectors = [
                        "a._1fQZEK", 
                        "a._2rpwqI", 
                        "a.s1Q9rs",
                        "a[href*='/p/']",
                        "div._13oc-S a",
                        "div._4ddWXP a"
                    ]
                    
                    # Try each selector
                    for selector in product_selectors:
                        product_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if product_links and len(product_links) > 0:
                            # Get the first product URL
                            product_url = product_links[0].get_attribute("href")
                            if product_url:
                                return product_url.split("&lid=")[0]
                    
                    # If we couldn't find with selectors, try with JavaScript
                    product_url = self.driver.execute_script(
                        "return document.querySelector('a[href*=\"/p/\"]').getAttribute('href')"
                    )
                    if product_url:
                        return product_url
                        
                except Exception as e:
                    self.log(f"Error finding Flipkart product: {e}")
                    return None
                    
            elif platform.lower() == "myntra":
                search_url = f"https://www.myntra.com/{search_term.replace('+', '-')}"
                self.driver.get(search_url)
                self.random_sleep(1, 3)
                
                # Try to find the first product result with multiple selectors
                try:
                    product_selectors = [
                        "a.product-base",
                        "li.product-base a",
                        "a[href*='/p/']",
                        "ul.results-base li a"
                    ]
                    
                    # Try each selector
                    for selector in product_selectors:
                        product_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if product_links and len(product_links) > 0:
                            # Get the first product URL
                            product_url = product_links[0].get_attribute("href")
                            if product_url:
                                return product_url
                    
                    # If still no match, try JavaScript
                    product_url = self.driver.execute_script(
                        "return document.querySelector('a[data-refreshpage=\"true\"]').getAttribute('href')"
                    )
                    if product_url:
                        return "https://www.myntra.com" + product_url if not product_url.startswith("http") else product_url
                
                except Exception as e:
                    self.log(f"Error finding Myntra product: {e}")
                    return None
            
            self.log(f"No search results found for '{product_name}' on {platform}")
            return None
            
        except Exception as e:
            self.log(f"Error searching for '{product_name}' on {platform}: {e}")
            return None

    def extract_search_keywords(self, product_name):
        """Extract meaningful keywords from product name for better search results"""
        # List of category identifiers to look for
        categories = ['Sunglasses', 'Thermos', 'Bottle', 'Mug', 'Phone Stand', 
                     'Notebook', 'Lunchbox', 'Stole', 'Silk']
        
        # Find which category matches the product
        matched_category = None
        for category in categories:
            if category.lower() in product_name.lower():
                matched_category = category
                break
        
        if matched_category:
            # For wooden products, ensure 'wooden' is included for better matches
            if 'wooden' in product_name.lower():
                return f"Wooden {matched_category}"
            # For specialty materials, include them in the search
            elif 'silk' in product_name.lower():
                return f"Silk {matched_category}"
            else:
                return matched_category
        
        # If no category match, extract the last 2-3 words which often indicate product type
        words = product_name.split()
        if len(words) >= 3:
            return ' '.join(words[-3:])
        else:
            return product_name

    def clean_price_string(self, price_str):
        """Clean up price string by removing currency symbols and formatting"""
        if not price_str:
            return None
            
        # Replace rupee symbol with Rs. only if Rs. is not already there
        if '\u20b9' in price_str or '₹' in price_str:
            price_str = price_str.replace('\u20b9', 'Rs.').replace('₹', 'Rs.')
            # Fix double 'Rs.' if it occurs
            price_str = price_str.replace('Rs.Rs.', 'Rs.')
            
        # Remove commas and extra spaces
        return price_str.replace(',', '').strip()
        
    def extract_price_number(self, price_str):
        """Extract just the number from a price string"""
        if not price_str:
            return None
            
        # Clean the price string first
        price_str = self.clean_price_string(price_str)
        
        # Extract numbers
        if price_str:
            # Different regex patterns depending on format
            patterns = [
                r'[\d]+\.[\d]+',  # e.g., 123.45
                r'[\d]+'           # e.g., 123
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, price_str)
                if matches:
                    return matches[0]
                    
        return None

    def save_debug_html(self, platform, html_content):
        """Save debug HTML with limits to avoid filling disk space"""
        if not self.debug_mode:
            return None
            
        # Generate debug file path
        debug_file = f"data/raw/{platform}_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            # Write HTML content to file
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Add to list of debug files
            self.debug_files.append(debug_file)
            
            # Keep track of files by platform
            platform_files = [f for f in self.debug_files if f'{platform}_debug_' in f]
            
            # If we have too many debug files for this platform, remove oldest
            if len(platform_files) > self.max_debug_files:
                # Sort by timestamp (newest last)
                platform_files.sort()
                # Remove oldest files (keeping max_debug_files)
                for old_file in platform_files[:-self.max_debug_files]:
                    try:
                        os.remove(old_file)
                        self.debug_files.remove(old_file)
                        self.log(f"Removed old debug file: {old_file}")
                    except Exception as e:
                        self.log(f"Error removing old debug file {old_file}: {e}")
            
            self.log(f"Saved debug HTML to {debug_file}")
            return debug_file
        except Exception as e:
            self.log(f"Error saving debug HTML: {e}")
            return None
        
    def cleanup_debug_files(self):
        """Clean up any debug files after scraping is complete"""
        if not self.debug_mode:
            return
            
        try:
            # Remove all debug files
            for debug_file in self.debug_files:
                try:
                    if os.path.exists(debug_file):
                        os.remove(debug_file)
                except Exception as e:
                    self.log(f"Error removing debug file {debug_file}: {e}")
            
            self.debug_files = []
            self.log("Cleaned up all debug files")
        except Exception as e:
            self.log(f"Error cleaning up debug files: {e}")
            
    def scrape_flipkart(self, product_name, product_sku, product_info, url=None):
        """Scrape product information from Flipkart"""
        self.log(f"Scraping Flipkart: {product_name} (SKU: {product_sku})")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("flipkart", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'flipkart',
                        'sku': product_sku,
                        'product_name': product_name,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': 'Could not find product'
                    }
            
            # Add random query parameters to avoid caching
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            full_url = url + (random_param if "?" not in url else f"&rand={random.randint(1000000, 9999999)}")
            
            # Open the product page
            self.log(f"Opening URL: {full_url}")
            self.driver.get(full_url)
            
            # Initial wait for page to load
            self.random_sleep(3, 5)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging if enabled
            debug_file = None
            if self.debug_mode:
                debug_file = self.save_debug_html("flipkart", self.driver.page_source)
            
            # Extract product details using multiple strategies
            # Strategy 1: Standard selectors
            title = None
            try:
                title_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.B_NuCI, h1.yhB1nd")))
                title = title_element.text
            except (TimeoutException, NoSuchElementException):
                # Strategy 2: Alternative selectors
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, "h1._31qSD5, h1.yhB1nd, h1._30jeq3")
                    title = title_element.text
                except NoSuchElementException:
                    # Strategy 3: JavaScript to extract title
                    try:
                        title = self.driver.execute_script("return document.querySelector('h1').innerText")
                    except:
                        title = product_name  # Use default name if not found
            
            # Validate that the product matches what we're looking for
            is_valid_product = True
            similarity = 0.0
            validation_message = ""
            
            if title and title != product_name:  # Only validate if we found a title and it's not just a copy of the search term
                is_valid_product, similarity, validation_message = self.validate_product_match(product_name, title)
                self.log(f"Product validation: {validation_message}")
                
                if not is_valid_product:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'flipkart',
                        'sku': product_sku,
                        'product_name': product_name,
                        'title': title,
                        'url': url,
                        'similarity_score': similarity,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': f'Product name mismatch: {validation_message}'
                    }
            
            # Extract price using multiple selectors and strategies
            price_selectors = [
                "div._30jeq3._16Jk6d",
                "div._30jeq3",
                ".CEmiEU div._16Jk6d",
                ".CEmiEU ._30jeq3",
                "div[data-price]"
            ]
            
            price = None
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price = price_element.text
                    if price:
                        break
                except NoSuchElementException:
                    continue
            
            # If still no price, try JavaScript
            if not price:
                try:
                    price = self.driver.execute_script(
                        "return Array.from(document.querySelectorAll('div')).find(el => el.innerText && el.innerText.includes('₹') && !el.innerText.includes('off')).innerText"
                    )
                except:
                    price = None
            
            # Extract other product details
            original_price = None
            try:
                original_price_element = self.driver.find_element(By.CSS_SELECTOR, "div._3I9_wc._2p6lqe, div._3I9_wc")
                original_price = original_price_element.text
            except NoSuchElementException:
                pass
                
            discount = None
            try:
                discount_element = self.driver.find_element(By.CSS_SELECTOR, "div._3Ay6Sb._31Dcoz, div._3Ay6Sb")
                discount = discount_element.text
            except NoSuchElementException:
                pass
            
            # Check if out of stock
            try:
                self.driver.find_element(By.CSS_SELECTOR, "div._16FRp0")
                stock_status = "Out of Stock"
            except NoSuchElementException:
                stock_status = "In Stock"
            
            # Get ratings if available
            rating = None
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, "div._3LWZlK, span._1lRcqv")
                rating = rating_element.text
            except NoSuchElementException:
                pass
            
            # Clean price data
            clean_price = self.extract_price_number(price)
            clean_original_price = self.extract_price_number(original_price)
            
            # Create data object
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'flipkart',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'title': title,
                'current_price_inr': clean_price,
                'original_price_inr': clean_original_price,
                'discount': discount,
                'rating': rating,
                'stock_status': stock_status,
                'status': 'success'
            }
            
            if self.debug_mode:
                data['debug_file'] = debug_file
            
            self.log(f"Flipkart data extracted: {title} - ₹{clean_price}")
            return data
            
        except Exception as e:
            self.log(f"Error scraping Flipkart {product_name}: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'flipkart',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_amazon(self, product_name, product_sku, product_info, url=None):
        """Scrape product information from Amazon"""
        self.log(f"Scraping Amazon: {product_name} (SKU: {product_sku})")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("amazon", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'amazon',
                        'sku': product_sku,
                        'product_name': product_name,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': 'Could not find product'
                    }
            
            # Add random query parameters to avoid caching
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            full_url = url + (random_param if "?" not in url else f"&rand={random.randint(1000000, 9999999)}")
            
            # Open the product page
            self.log(f"Opening URL: {full_url}")
            self.driver.get(full_url)
            
            # Initial wait for page to load
            self.random_sleep(3, 5)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging if enabled
            debug_file = None
            if self.debug_mode:
                debug_file = self.save_debug_html("amazon", self.driver.page_source)
            
            # Extract product details using multiple approaches
            # 1. Try to extract title
            title = None
            title_selectors = [
                "span#productTitle",
                "h1.a-size-large",
                "h1.product-title-word-break",
                "div.product-title-container h1",
                "div.product-title h1"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except NoSuchElementException:
                    continue
                    
            if not title:
                # Try JavaScript as a last resort
                try:
                    title = self.driver.execute_script("return document.querySelector('h1').innerText")
                except:
                    title = None
            
            # Validate that the product matches what we're looking for
            is_valid_product = True
            similarity = 0.0
            validation_message = ""
            
            if title:
                is_valid_product, similarity, validation_message = self.validate_product_match(product_name, title)
                self.log(f"Product validation: {validation_message}")
                
                if not is_valid_product:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'amazon',
                        'sku': product_sku,
                        'product_name': product_name,
                        'title': title,
                        'url': url,
                        'similarity_score': similarity,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': f'Product name mismatch: {validation_message}'
                    }
            
            # 2. Extract prices
            # Try different price selectors for Amazon
            price = None
            price_selectors = [
                "span.a-price-whole",
                "span#priceblock_ourprice",
                "span#priceblock_dealprice",
                "span.a-offscreen",
                "span.a-color-price",
                "#corePrice_feature_div .a-offscreen"
            ]
            
            for selector in price_selectors:
                try:
                    price_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for price_element in price_elements:
                        price_text = price_element.text.strip()
                        if price_text and ('₹' in price_text or 'Rs.' in price_text or 'INR' in price_text):
                            price = price_text
                            break
                    if price:
                        break
                except NoSuchElementException:
                    continue
            
            # If still no price, try JavaScript
            if not price:
                try:
                    price = self.driver.execute_script(
                        "return Array.from(document.querySelectorAll('span')).find(el => el.innerText && (el.innerText.includes('₹') || el.innerText.includes('Rs.'))).innerText"
                    )
                except:
                    price = None
            
            # Try to get original price (if there's a discount)
            original_price = None
            try:
                original_price_element = self.driver.find_element(By.CSS_SELECTOR, ".a-text-strike")
                original_price = original_price_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Check if out of stock
            stock_status = "Unknown"
            try:
                availability = self.driver.find_element(By.ID, "availability").text.strip()
                stock_status = "In Stock" if "in stock" in availability.lower() else "Out of Stock"
            except NoSuchElementException:
                try:
                    availability = self.driver.find_element(By.CSS_SELECTOR, "#availability span").text.strip()
                    stock_status = "In Stock" if "in stock" in availability.lower() else "Out of Stock"
                except NoSuchElementException:
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, ".a-color-price.a-text-bold")
                        stock_status = "Out of Stock"
                    except NoSuchElementException:
                        # If add to cart button exists, product is in stock
                        try:
                            self.driver.find_element(By.ID, "add-to-cart-button")
                            stock_status = "In Stock"
                        except NoSuchElementException:
                            pass
            
            # Get ratings if available
            rating = None
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                rating = rating_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Clean price data
            clean_price = self.extract_price_number(price)
            clean_original_price = self.extract_price_number(original_price)
            
            # Create data object
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'amazon',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'title': title,
                'current_price_inr': clean_price,
                'original_price_inr': clean_original_price,
                'rating': rating,
                'stock_status': stock_status,
                'status': 'success'
            }
            
            if self.debug_mode:
                data['debug_file'] = debug_file
            
            self.log(f"Amazon data extracted: {title} - ₹{clean_price}")
            return data
            
        except Exception as e:
            self.log(f"Error scraping Amazon {product_name}: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'amazon',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'status': 'error',
                'error': str(e)
            } 

    def scrape_myntra(self, product_name, product_sku, product_info, url=None):
        """Scrape product information from Myntra"""
        self.log(f"Scraping Myntra: {product_name} (SKU: {product_sku})")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("myntra", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'myntra',
                        'sku': product_sku,
                        'product_name': product_name,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': 'Could not find product'
                    }
            
            # Add random query parameters to avoid caching
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            full_url = url + (random_param if "?" not in url else f"&rand={random.randint(1000000, 9999999)}")
            
            # Open the product page
            self.log(f"Opening URL: {full_url}")
            self.driver.get(full_url)
            
            # Initial wait for page to load
            self.random_sleep(3, 5)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging if enabled
            debug_file = None
            if self.debug_mode:
                debug_file = self.save_debug_html("myntra", self.driver.page_source)
            
            # Check for login requirement - Myntra often requires login
            if "login" in self.driver.current_url.lower() or "Please Login to Continue" in self.driver.page_source:
                self.log("⚠️ Myntra requires login, cannot scrape product")
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'platform': 'myntra',
                    'sku': product_sku,
                    'product_name': product_name,
                    'master_price_eur': product_info.get('current_price_eur'),
                    'master_cost_eur': product_info.get('unit_cost_eur'),
                    'url': url,
                    'status': 'error',
                    'error': 'Login required'
                }
            
            # Extract product details
            # 1. Try to get product title
            title = None
            title_selectors = [
                "h1.pdp-title",
                "h1.pdp-name",
                ".pdp-price-info h1",
                ".title-container h1"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except NoSuchElementException:
                    continue
                    
            if not title:
                # Try JavaScript as a last resort
                try:
                    title = self.driver.execute_script("return document.querySelector('h1').innerText")
                except:
                    title = product_name  # Use default name if not found
                    
            # Validate that the product matches what we're looking for
            is_valid_product = True
            similarity = 0.0
            validation_message = ""
            
            if title and title != product_name:  # Only validate if we found a title and it's not just a copy of the search term
                is_valid_product, similarity, validation_message = self.validate_product_match(product_name, title)
                self.log(f"Product validation: {validation_message}")
                
                if not is_valid_product:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'myntra',
                        'sku': product_sku,
                        'product_name': product_name,
                        'title': title,
                        'url': url,
                        'similarity_score': similarity,
                        'master_price_eur': product_info.get('current_price_eur'),
                        'master_cost_eur': product_info.get('unit_cost_eur'),
                        'status': 'error',
                        'error': f'Product name mismatch: {validation_message}'
                    }
                    
            # Continue with extracting rest of the data...
            # ... [rest of the code remains the same]
            
            # Extract brand name
            brand = None
            try:
                brand_element = self.driver.find_element(By.CSS_SELECTOR, "h1.pdp-title, .pdp-brand-logo-container")
                brand = brand_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract price
            price = None
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, "span.pdp-price strong, div.pdp-price")
                price = price_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract original price
            original_price = None
            try:
                original_price_element = self.driver.find_element(By.CSS_SELECTOR, "span.pdp-mrp s")
                original_price = original_price_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Extract discount
            discount = None
            try:
                discount_element = self.driver.find_element(By.CSS_SELECTOR, "span.pdp-discount")
                discount = discount_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Check stock status
            stock_status = "In Stock"  # Default
            try:
                # Check for out of stock indicator
                self.driver.find_element(By.CSS_SELECTOR, "div.size-buttons-out-of-stock")
                stock_status = "Out of Stock"
            except NoSuchElementException:
                pass
            
            # Clean price data
            clean_price = self.extract_price_number(price)
            clean_original_price = self.extract_price_number(original_price)
            
            # Create data object
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'myntra',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'title': title,
                'brand': brand,
                'current_price_inr': clean_price,
                'original_price_inr': clean_original_price,
                'discount': discount,
                'stock_status': stock_status,
                'status': 'success'
            }
            
            if self.debug_mode:
                data['debug_file'] = debug_file
            
            self.log(f"Myntra data extracted: {title} - ₹{clean_price}")
            return data
            
        except Exception as e:
            self.log(f"Error scraping Myntra {product_name}: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'myntra',
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_product(self, platform, product_name, product_sku, product_info, url=None):
        """Scrape a product from a specific platform"""
        platform = platform.lower()
        
        # Choose the appropriate scraping method based on platform
        if platform == "flipkart":
            return self.scrape_flipkart(product_name, product_sku, product_info, url)
        elif platform == "amazon":
            return self.scrape_amazon(product_name, product_sku, product_info, url)
        elif platform == "myntra":
            return self.scrape_myntra(product_name, product_sku, product_info, url)
        else:
            self.log(f"Unsupported platform: {platform}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': platform,
                'sku': product_sku,
                'product_name': product_name,
                'master_price_eur': product_info.get('current_price_eur'),
                'master_cost_eur': product_info.get('unit_cost_eur'),
                'url': url,
                'status': 'error',
                'error': f"Unsupported platform: {platform}"
            }
    
    def read_master_products(self):
        """Read products from master CSV file"""
        self.log(f"Reading products from master CSV file: {self.master_csv_file}")
        products = []
        
        try:
            with open(self.master_csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check if required columns exist
                required_columns = ['name', 'sku']
                csv_columns = reader.fieldnames
                
                if not all(col in csv_columns for col in required_columns):
                    self.log(f"Error: CSV file must contain columns: {', '.join(required_columns)}")
                    return []
                
                # Read products from CSV
                for row in reader:
                    # Skip empty rows or rows without required fields
                    if not row['name'] or not row['sku']:
                        continue
                    
                    product = {
                        'sku': row['sku'].strip(),
                        'name': row['name'].strip(),
                        'current_price_eur': row.get('current_price_eur', '').strip() if row.get('current_price_eur') else None,
                        'unit_cost_eur': row.get('unit_cost_eur', '').strip() if row.get('unit_cost_eur') else None,
                        'ingested_at': row.get('ingested_at', '').strip() if row.get('ingested_at') else None
                    }
                    products.append(product)
        
        except Exception as e:
            self.log(f"Error reading CSV file: {e}")
            return []
        
        self.log(f"Found {len(products)} products in master CSV file")
        return products
    
    def scrape_all_products(self):
        """Scrape all products from the master CSV file across all platforms"""
        # Read products from CSV
        products = self.read_master_products()
        if not products:
            self.log("No products found in master CSV or CSV file could not be read")
            return False
        
        # Process each product
        results = []
        for index, product in enumerate(products):
            self.log(f"Processing product {index+1}/{len(products)}: {product['name']} (SKU: {product['sku']})")
            
            # Scrape the product from each platform
            for platform in self.platforms:
                self.log(f"Scraping {platform} for {product['name']}")
                
                # Add some randomization to avoid being flagged as a bot - reduced wait time
                self.random_sleep(1, 2)
                
                # Scrape the product
                result = self.scrape_product(
                    platform=platform,
                    product_name=product['name'],
                    product_sku=product['sku'],
                    product_info=product,
                    url=None  # No URLs in the master CSV, we'll search by name
                )
                
                # Add to results
                results.append(result)
                
                # Add a delay between products to avoid being blocked - reduced wait time
                delay = random.uniform(2, 5)
                self.log(f"Waiting {delay:.2f} seconds before processing next platform/product")
                time.sleep(delay)
        
        # Save results
        self.results = results
        output_file = self.save_results()
        
        # Create CSV output
        csv_output = self.save_results_to_csv()
        
        # Summary
        success_count = len([r for r in results if r.get('status') == 'success'])
        error_count = len([r for r in results if r.get('status') == 'error'])
        
        self.log(f"Scraping completed: {success_count} successes, {error_count} failures")
        self.log(f"Results saved to JSON: {output_file}")
        self.log(f"Results saved to CSV: {csv_output}")
        
        return success_count > 0
    
    def save_results(self):
        """Save results to JSON file"""
        # Generate filename with timestamp
        filename = f'data/raw/price_data_{self.timestamp}.json'
        
        # Save to JSON file
        try:
            # Sanitize results to handle encoding issues
            sanitized_results = []
            for result in self.results:
                sanitized_result = {}
                
                # Handle each field appropriately
                for key, value in result.items():
                    if isinstance(value, str):
                        # Replace rupee symbol with Rs.
                        if '\u20b9' in value or '₹' in value:
                            value = value.replace('\u20b9', 'Rs.').replace('₹', 'Rs.')
                            # Fix double 'Rs.' if it occurs
                            value = value.replace('Rs.Rs.', 'Rs.')
                    
                    sanitized_result[key] = value
                
                sanitized_results.append(sanitized_result)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(sanitized_results, f, indent=2, ensure_ascii=False)
            return filename
        except Exception as e:
            self.log(f"Error saving results to JSON: {e}")
            return None
    
    def save_results_to_csv(self):
        """Save results to CSV file"""
        # Generate filename with timestamp
        filename = f'data/processed/price_data_{self.timestamp}.csv'
        
        try:
            # Determine all possible fields from all results
            fieldnames = set()
            for result in self.results:
                fieldnames.update(result.keys())
            
            # Sort field names to ensure consistent order
            fieldnames = sorted(list(fieldnames))
            
            # Move certain important fields to the beginning
            key_fields = ['timestamp', 'platform', 'sku', 'product_name', 'title', 
                         'current_price_inr', 'original_price_inr', 'master_price_eur', 
                         'master_cost_eur', 'discount', 'stock_status', 'status', 'error']
            
            # Reorder fieldnames to put key fields first
            for field in reversed(key_fields):
                if field in fieldnames:
                    fieldnames.remove(field)
                    fieldnames.insert(0, field)
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.results:
                    # Ensure all fieldnames have a value (even if null)
                    row = {field: result.get(field, '') for field in fieldnames}
                    writer.writerow(row)
            
            return filename
        
        except Exception as e:
            self.log(f"Error saving results to CSV: {e}")
            return None
    
    def close(self):
        """Close the browser and clean up"""
        try:
            # Clean up debug files
            self.cleanup_debug_files()
            
            if hasattr(self, 'driver'):
                self.driver.quit()
                self.log("Browser closed successfully")
        except Exception as e:
            self.log(f"Error closing browser: {e}")

    def validate_product_match(self, target_name, scraped_name):
        """
        Validate if the scraped product name matches the target product name
        
        Args:
            target_name: The product name we're looking for 
            scraped_name: The product name found on the e-commerce site
            
        Returns:
            tuple: (is_valid, similarity_score, message)
        """
        if not scraped_name:
            return False, 0.0, "No product name found"
            
        if not self.product_matcher:
            # If no matcher available, accept all products
            return True, 1.0, "Product matcher not available, accepting all matches"
            
        # Use the product matcher to check validity
        is_valid, similarity = self.product_matcher.is_valid_match(target_name, scraped_name)
        
        if is_valid:
            return True, similarity, f"Valid match (similarity: {similarity:.2f})"
        else:
            return False, similarity, f"Invalid match (similarity: {similarity:.2f})"


def main(args=None):
    """Main function to run the scraper with command line arguments"""
    # Parse arguments if not provided
    if args is None:
        parser = argparse.ArgumentParser(description='Run the master CSV scraper')
        parser.add_argument('csv_file', nargs='?', default='products.csv', 
                            help='CSV file with products to scrape (default: products.csv)')
        parser.add_argument('--headless', action='store_true', default=True,
                            help='Run in headless mode (default: True)')
        parser.add_argument('--debug', action='store_true', default=True,
                            help='Enable debug mode (default: True)')
        parser.add_argument('--platforms', nargs='+', default=['amazon', 'flipkart', 'myntra'],
                            help='Platforms to scrape (default: amazon flipkart myntra)')
        parser.add_argument('--specialty-products-mode', action='store_true', default=False,
                            help='Enable specialty products mode for unique items')
        parser.add_argument('--similarity-threshold', type=float, default=0.7,
                            help='Threshold for product name similarity (0.0 to 1.0, default: 0.7)')
        args = parser.parse_args()
    
    print(f"Processing CSV file: {args.csv_file}")
    
    # Create and run the scraper
    try:
        # Print configuration
        print(f"Platforms to scrape: {args.platforms}")
        print(f"Headless mode: {'Enabled' if args.headless else 'Disabled'}")
        print(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
        print(f"Specialty products mode: {'Enabled' if args.specialty_products_mode else 'Disabled'}")
        print(f"Similarity threshold: {args.similarity_threshold}")
        
        # Initialize the scraper
        scraper = MasterProductScraper(
            master_csv_file=args.csv_file,
            headless=args.headless,
            debug_mode=args.debug,
            platforms=args.platforms,
            specialty_products_mode=args.specialty_products_mode,
            similarity_threshold=args.similarity_threshold
        )
        
        # Scrape all products
        success = scraper.scrape_all_products()
        
        # Close the scraper
        scraper.close()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 