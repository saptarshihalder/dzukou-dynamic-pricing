import json
import os
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Product URLs to scrape
PRODUCTS = [
    # Flipkart products
    {
        "platform": "flipkart",
        "url": "https://www.flipkart.com/awenest-bamboo-charcoal-activated-bristles-treated-neem-oil-extra-soft-toothbrush/p/itm5a51260c0237e",
        "name": "Awenest Bamboo Toothbrush"
    },
    {
        "platform": "flipkart",
        "url": "https://www.flipkart.com/mouth-company-gentlebrush-flat-premium-bamboo-toothbrush-charcoal-activated-bristles-ultra-soft/p/itm7073cf6b7addf",
        "name": "The Mouth Company Bamboo Toothbrush"
    },
    {
        "platform": "flipkart",
        "url": "https://www.flipkart.com/greenlife-bamboo-charcoal-toothbrush-natural-wooden-eco-friendly-soft-medium-bristles-pack-4/p/itm6c0cb25db6cb9",
        "name": "GreenLife Bamboo Toothbrush"
    },
    # Amazon products
    {
        "platform": "amazon",
        "url": "https://www.amazon.in/Bamboo-India-Toothbrush-Pack-Brown/dp/B07JMZYJVZ/",
        "name": "Bamboo India Toothbrush"
    },
    {
        "platform": "amazon",
        "url": "https://www.amazon.in/Ecofriendly-Biodegradable-Toothbrush-Individually-Numbered/dp/B07WGPN9F4/",
        "name": "Bamboo Toothbrush Biodegradable"
    }
]

# User agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15"
]

class EcommerceScraper:
    def __init__(self):
        self.setup_driver()
        self.results = []
        
    def setup_driver(self):
        """Set up the Selenium WebDriver with Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Randomize user agent to avoid detection
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        # Additional options to avoid detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Install and setup Chrome driver
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Modify navigator.webdriver flag to prevent detection
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 15)  # 15 seconds timeout
    
    def random_sleep(self, min_seconds=2, max_seconds=5):
        """Sleep for a random amount of time to mimic human behavior"""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def simulate_human_behavior(self):
        """Simulate human-like behavior to avoid detection"""
        # Scroll down slowly
        for i in range(5):
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(100, 500)})")
            self.random_sleep(0.5, 1.5)
        
        # Scroll back up
        self.driver.execute_script("window.scrollTo(0, 0)")
        self.random_sleep()
    
    def scrape_flipkart(self, product):
        """Scrape product information from Flipkart"""
        print(f"Scraping Flipkart: {product['name']}")
        
        try:
            # Add random query parameters to avoid caching
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            self.driver.get(product["url"] + random_param)
            
            # Initial wait for page to load
            self.random_sleep(3, 6)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging
            debug_file = f"flipkart_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Extract product details using multiple strategies
            # Strategy 1: Standard selectors
            try:
                title_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.B_NuCI")))
                title = title_element.text
            except (TimeoutException, NoSuchElementException):
                # Strategy 2: Try JavaScript to extract title
                try:
                    title = self.driver.execute_script("return document.querySelector('h1').innerText")
                except:
                    title = product["name"]  # Use default name if not found
            
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
            try:
                original_price_element = self.driver.find_element(By.CSS_SELECTOR, "div._3I9_wc._2p6lqe, div._3I9_wc")
                original_price = original_price_element.text
            except NoSuchElementException:
                original_price = None
                
            try:
                discount_element = self.driver.find_element(By.CSS_SELECTOR, "div._3Ay6Sb._31Dcoz, div._3Ay6Sb")
                discount = discount_element.text
            except NoSuchElementException:
                discount = None
            
            # Check if out of stock
            try:
                self.driver.find_element(By.CSS_SELECTOR, "div._16FRp0")
                stock_status = "Out of Stock"
            except NoSuchElementException:
                stock_status = "In Stock"
            
            # Clean price data
            if price:
                clean_price = price.replace('₹', '').replace(',', '').strip()
            else:
                clean_price = None
                
            if original_price:
                clean_original_price = original_price.replace('₹', '').replace(',', '').strip()
            else:
                clean_original_price = None
            
            # Create data object
            data = {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'platform': 'flipkart',
                'product_name': product["name"],
                'url': product["url"],
                'title': title,
                'current_price': clean_price,
                'original_price': clean_original_price,
                'discount': discount,
                'stock_status': stock_status,
                'debug_file': debug_file
            }
            
            print(f"Extracted data: {data}")
            return data
            
        except Exception as e:
            print(f"Error scraping Flipkart {product['name']}: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'platform': 'flipkart',
                'product_name': product["name"],
                'url': product["url"],
                'error': str(e)
            }
    
    def scrape_amazon(self, product):
        """Scrape product information from Amazon"""
        print(f"Scraping Amazon: {product['name']}")
        
        try:
            # Add random query parameters to avoid caching
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            self.driver.get(product["url"] + random_param)
            
            # Initial wait for page to load
            self.random_sleep(3, 6)
            
            # Simulate human behavior
            self.simulate_human_behavior()
            
            # Save page source for debugging
            debug_file = f"amazon_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            
            # Extract product details
            try:
                title_element = self.wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
                title = title_element.text
            except (TimeoutException, NoSuchElementException):
                # Try JavaScript to extract title
                try:
                    title = self.driver.execute_script("return document.getElementById('productTitle').innerText")
                except:
                    title = product["name"]  # Use default name if not found
            
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
                        price = price_element.text
                        if price and '₹' in price:
                            break
                    if price and '₹' in price:
                        break
                except NoSuchElementException:
                    continue
            
            # If still no price, try JavaScript
            if not price or '₹' not in price:
                try:
                    price = self.driver.execute_script(
                        "return Array.from(document.querySelectorAll('span')).find(el => el.innerText && el.innerText.includes('₹')).innerText"
                    )
                except:
                    price = None
            
            # Check if out of stock
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
                        stock_status = "Unknown"
            
            # Clean price data
            if price:
                clean_price = price.replace('₹', '').replace(',', '').replace('.00', '').strip()
            else:
                clean_price = None
            
            # Create data object
            data = {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'platform': 'amazon',
                'product_name': product["name"],
                'url': product["url"],
                'title': title,
                'current_price': clean_price,
                'stock_status': stock_status,
                'debug_file': debug_file
            }
            
            print(f"Extracted data: {data}")
            return data
            
        except Exception as e:
            print(f"Error scraping Amazon {product['name']}: {e}")
            return {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'platform': 'amazon',
                'product_name': product["name"],
                'url': product["url"],
                'error': str(e)
            }
    
    def scrape_product(self, product):
        """Scrape a product based on its platform"""
        if product["platform"] == "flipkart":
            return self.scrape_flipkart(product)
        elif product["platform"] == "amazon":
            return self.scrape_amazon(product)
        else:
            return {
                'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'platform': product["platform"],
                'product_name': product["name"],
                'url': product["url"],
                'error': f"Unsupported platform: {product['platform']}"
            }
    
    def scrape_all(self):
        """Scrape all products"""
        for product in PRODUCTS:
            result = self.scrape_product(product)
            self.results.append(result)
            # Add a random delay between requests to avoid detection
            self.random_sleep(5, 10)
        
        return self.results
    
    def save_results(self):
        """Save results to JSON file"""
        # Create data directory if it doesn't exist
        os.makedirs('data/raw', exist_ok=True)
        
        # Generate filename with timestamp
        filename = f'data/raw/prices_{datetime.now().strftime("%Y%m%d_%H")}.json'
        
        # Save to JSON file
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Data saved to {filename}")
    
    def close(self):
        """Close the WebDriver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

def main():
    scraper = EcommerceScraper()
    try:
        scraper.scrape_all()
        scraper.save_results()
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 