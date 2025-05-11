import json
import os
import time
import random
import csv
import re
import argparse
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
import sys

class CSVEcommerceScraper:
    def __init__(self, csv_file, headless=True, debug_mode=True):
        """
        Initialize the scraper with configurable options
        
        Args:
            csv_file: Path to CSV file with products to scrape
            headless: Whether to run browser in headless mode
            debug_mode: Whether to save debug files
        """
        self.csv_file = csv_file
        self.setup_driver(headless)
        self.results = []
        self.debug_mode = debug_mode
        self.debug_files = []  # Track debug files created
        self.max_debug_files = 2  # Maximum number of debug files to keep per platform
        
        # Create data directories if they don't exist
        os.makedirs('data/raw', exist_ok=True)
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Setup logging
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = f'logs/scraper_log_{self.timestamp}.txt'
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"CSVEcommerceScraper initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except UnicodeEncodeError:
            with open(self.log_file, 'w', encoding='ascii', errors='replace') as f:
                f.write(f"CSVEcommerceScraper initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Validate CSV file exists
        if not os.path.exists(csv_file):
            self.log(f"Error: CSV file '{csv_file}' not found")
            raise FileNotFoundError(f"CSV file '{csv_file}' not found")
    
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
            
    def scrape_flipkart(self, product_name, url=None):
        """Scrape product information from Flipkart"""
        self.log(f"Scraping Flipkart: {product_name}")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("flipkart", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'flipkart',
                        'product_name': product_name,
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
            self.random_sleep(3, 6)
            
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
                'product_name': product_name,
                'url': url,
                'title': title,
                'current_price': clean_price,
                'original_price': clean_original_price,
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
                'product_name': product_name,
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_amazon(self, product_name, url=None):
        """Scrape product information from Amazon"""
        self.log(f"Scraping Amazon: {product_name}")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("amazon", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'amazon',
                        'product_name': product_name,
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
            self.random_sleep(3, 6)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging if enabled
            debug_file = None
            if self.debug_mode:
                debug_file = self.save_debug_html("amazon", self.driver.page_source)
            
            # Check if we're blocked or encountering a CAPTCHA
            if "Sorry, we just need to make sure you're not a robot" in self.driver.page_source:
                self.log(f"⚠️ Amazon CAPTCHA detected for {product_name}")
                return {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'platform': 'amazon',
                    'product_name': product_name,
                    'url': url,
                    'status': 'error',
                    'error': 'CAPTCHA encountered'
                }
            
            # Extract product details
            title = None
            try:
                title_element = self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                title = title_element.text.strip()
            except (TimeoutException, NoSuchElementException):
                # Try JavaScript to extract title
                try:
                    title = self.driver.execute_script("return document.getElementById('productTitle').innerText")
                except:
                    title = product_name  # Use default name if not found
            
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
                'product_name': product_name,
                'url': url,
                'title': title,
                'current_price': clean_price,
                'original_price': clean_original_price,
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
                'product_name': product_name,
                'url': url,
                'status': 'error',
                'error': str(e)
            } 

    def scrape_myntra(self, product_name, url=None):
        """Scrape product information from Myntra"""
        self.log(f"Scraping Myntra: {product_name}")
        
        try:
            # If no URL provided, search for the product
            if not url:
                url = self.search_for_product("myntra", product_name)
                if not url:
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': 'myntra',
                        'product_name': product_name,
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
            self.random_sleep(3, 6)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging if enabled
            debug_file = None
            if self.debug_mode:
                debug_file = self.save_debug_html("myntra", self.driver.page_source)
            
            # Extract product details
            title = None
            try:
                title_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1.pdp-name")))
                title = title_element.text.strip()
            except (TimeoutException, NoSuchElementException):
                title = product_name  # Use default name if not found
            
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
                'product_name': product_name,
                'url': url,
                'title': title,
                'brand': brand,
                'current_price': clean_price,
                'original_price': clean_original_price,
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
                'product_name': product_name,
                'url': url,
                'status': 'error',
                'error': str(e)
            }
    
    def scrape_product(self, platform, product_name, url=None):
        """Scrape a product from a specific platform"""
        platform = platform.lower()
        
        # Choose the appropriate scraping method based on platform
        if platform == "flipkart":
            return self.scrape_flipkart(product_name, url)
        elif platform == "amazon":
            return self.scrape_amazon(product_name, url)
        elif platform == "myntra":
            return self.scrape_myntra(product_name, url)
        else:
            self.log(f"Unsupported platform: {platform}")
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': platform,
                'product_name': product_name,
                'url': url,
                'status': 'error',
                'error': f"Unsupported platform: {platform}"
            }
    
    def read_csv_products(self):
        """Read products from CSV file"""
        self.log(f"Reading products from CSV file: {self.csv_file}")
        products = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Check if required columns exist
                required_columns = ['platform', 'product_name']
                csv_columns = reader.fieldnames
                
                if not all(col in csv_columns for col in required_columns):
                    self.log(f"Error: CSV file must contain columns: {', '.join(required_columns)}")
                    return []
                
                # Read products from CSV
                for row in reader:
                    # Skip empty rows or rows without required fields
                    if not row['platform'] or not row['product_name']:
                        continue
                    
                    product = {
                        'platform': row['platform'].strip(),
                        'product_name': row['product_name'].strip(),
                        'url': row.get('url', '').strip() if row.get('url') else None
                    }
                    products.append(product)
        
        except Exception as e:
            self.log(f"Error reading CSV file: {e}")
            return []
        
        self.log(f"Found {len(products)} products in CSV file")
        return products
    
    def scrape_all_products(self):
        """Scrape all products from the CSV file"""
        # Read products from CSV
        products = self.read_csv_products()
        if not products:
            self.log("No products found in CSV or CSV file could not be read")
            return False
        
        # Process each product
        results = []
        for index, product in enumerate(products):
            self.log(f"Processing product {index+1}/{len(products)}: {product['product_name']} ({product['platform']})")
            
            # Add some randomization to avoid being flagged as a bot - but shorter wait
            self.random_sleep(1, 2)
            
            # Scrape the product
            result = self.scrape_product(
                platform=product['platform'],
                product_name=product['product_name'],
                url=product.get('url')
            )
            
            # Add to results
            results.append(result)
            
            # Add a delay between products to avoid being blocked - but shorter wait
            if index < len(products) - 1:  # Don't delay after the last product
                delay = random.uniform(2, 5)
                self.log(f"Waiting {delay:.2f} seconds before processing next product")
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
            key_fields = ['timestamp', 'platform', 'product_name', 'title', 'current_price', 
                         'original_price', 'discount', 'stock_status', 'status', 'error']
            
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


def main(args=None):
    """Run the scraper with command line arguments"""
    if args is None:
        # Parse command line arguments if not provided
        parser = argparse.ArgumentParser(description='CSV-based e-commerce scraper')
        parser.add_argument('csv_file', help='CSV file with products to scrape')
        parser.add_argument('--headless', action='store_true', default=True,
                            help='Run in headless mode')
        parser.add_argument('--debug', action='store_true', default=True,
                            help='Enable debug mode')
        args = parser.parse_args()
    
    scraper = CSVEcommerceScraper(args.csv_file, args.headless, args.debug)
    
    try:
        scraper.log(f"Starting scraper with file: {args.csv_file}")
        scraper.scrape_all_products()
        scraper.save_results()
        scraper.save_results_to_csv()
        scraper.close()
        return 0
    except Exception as e:
        scraper.log(f"Error in main execution: {e}")
        scraper.close()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 