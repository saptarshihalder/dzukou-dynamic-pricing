import json
import os
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EcommerceScraper")

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

# Enhanced User agents list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203"
]

# Define proxy options - you would replace these with your actual proxies
PROXIES = [
    # Format: "ip:port" or "username:password@ip:port"
    # Leave empty if not using proxies
]


class EcommerceScraper:
    def __init__(self, use_proxies: bool = False, debug_mode: bool = True):
        """
        Initialize the scraper with configurable options
        
        Args:
            use_proxies: Whether to use proxy rotation
            debug_mode: Whether to save debug files
        """
        self.use_proxies = use_proxies
        self.debug_mode = debug_mode
        self.results = []
        self.setup_driver()
        
    def setup_driver(self):
        """Set up the Selenium WebDriver with enhanced anti-detection measures"""
        chrome_options = Options()
        
        # Decide whether to run headless based on environment
        # In production, you might want to run headless
        chrome_options.add_argument("--headless=new")  # New headless mode for Chrome
        
        # Basic Chrome options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Enhanced anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Add browser fingerprint randomization
        chrome_options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        
        # Browser language and locale settings
        languages = ["en-US,en;q=0.9", "en-GB,en;q=0.9", "en-IN,en;q=0.9"]
        chrome_options.add_argument(f"--lang={random.choice(languages)}")
        
        # Proxy rotation (if enabled and proxies are available)
        if self.use_proxies and PROXIES:
            proxy = random.choice(PROXIES)
            chrome_options.add_argument(f'--proxy-server={proxy}')
            logger.info(f"Using proxy: {proxy}")
        
        # Add extensions for additional anti-detection (if needed)
        # chrome_options.add_extension('path/to/extension.crx')
        
        # Install and setup Chrome driver
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            
            # Additional anti-detection measures via JavaScript
            self.driver.execute_script("""
                // Overwrite the 'webdriver' property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Overwrite the plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Overwrite the languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'es']
                });
            """)
            
            # Set timeouts
            self.driver.set_page_load_timeout(30)
            self.wait = WebDriverWait(self.driver, 15)
            
            logger.info("WebDriver setup complete")
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            raise
    
    def random_sleep(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """Sleep for a random duration to mimic human behavior"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    def simulate_human_behavior(self) -> None:
        """Simulate realistic human-like browsing behavior"""
        try:
            # Random number of scroll actions
            num_scrolls = random.randint(3, 7)
            for i in range(num_scrolls):
                # Random scroll distance
                scroll_distance = random.randint(100, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance})")
                self.random_sleep(0.5, 1.5)
            
            # Sometimes move the mouse randomly (using ActionChains)
            if random.random() > 0.5:
                actions = ActionChains(self.driver)
                for _ in range(random.randint(2, 5)):
                    x_offset = random.randint(10, 500)
                    y_offset = random.randint(10, 500)
                    actions.move_by_offset(x_offset, y_offset)
                    actions.perform()
                    self.random_sleep(0.2, 1.0)
            
            # Sometimes scroll back up
            if random.random() > 0.7:
                self.driver.execute_script("window.scrollTo(0, 0)")
                self.random_sleep(0.5, 1.0)
                
            logger.debug("Human behavior simulation complete")
        except Exception as e:
            logger.warning(f"Error during human behavior simulation: {e}")
    
    def extract_with_retry(self, strategies: List[Dict[str, Any]], max_retries: int = 3) -> Optional[str]:
        """
        Extract data using multiple strategies with retry logic
        
        Args:
            strategies: List of extraction strategies
            max_retries: Maximum number of retry attempts
            
        Returns:
            Extracted data or None if all strategies fail
        """
        for strategy in strategies:
            for attempt in range(max_retries):
                try:
                    if strategy.get("type") == "css":
                        element = self.driver.find_element(By.CSS_SELECTOR, strategy["selector"])
                        return element.text if element else None
                    elif strategy.get("type") == "xpath":
                        element = self.driver.find_element(By.XPATH, strategy["selector"])
                        return element.text if element else None
                    elif strategy.get("type") == "id":
                        element = self.driver.find_element(By.ID, strategy["selector"])
                        return element.text if element else None
                    elif strategy.get("type") == "js":
                        return self.driver.execute_script(strategy["script"])
                except (NoSuchElementException, StaleElementReferenceException, TimeoutException) as e:
                    if attempt == max_retries - 1:
                        logger.debug(f"Strategy failed after {max_retries} attempts: {strategy}")
                    self.random_sleep(0.5, 1.0)
                except Exception as e:
                    logger.debug(f"Unexpected error in extraction strategy: {e}")
                    break
        
        return None
    
    def clean_price(self, price_text: Optional[str]) -> Optional[str]:
        """
        Clean price text by removing currency symbols and formatting
        
        Args:
            price_text: Raw price text
            
        Returns:
            Cleaned price or None
        """
        if not price_text:
            return None
            
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[^\d.]', '', price_text)
        
        # Handle case where price might have multiple decimal points
        parts = cleaned.split('.')
        if len(parts) > 2:
            cleaned = parts[0] + '.' + parts[1]
            
        return cleaned.strip() if cleaned else None
    
    def save_debug_file(self, platform: str) -> str:
        """
        Save page source to debug file
        
        Args:
            platform: Platform name for the debug file
            
        Returns:
            Debug file path
        """
        if not self.debug_mode:
            return ""
            
        # Ensure debug directory exists
        os.makedirs('debug', exist_ok=True)
        
        # Generate unique filename with timestamp
        debug_file = f"debug/{platform}_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        try:
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            logger.debug(f"Saved debug file: {debug_file}")
            return debug_file
        except Exception as e:
            logger.error(f"Failed to save debug file: {e}")
            return ""
    
    def scrape_flipkart(self, product: Dict[str, str]) -> Dict[str, Any]:
        """
        Scrape product information from Flipkart
        
        Args:
            product: Product information dictionary
            
        Returns:
            Scraped product data
        """
        logger.info(f"Scraping Flipkart: {product['name']}")
        
        try:
            # Add random query parameters and referrer to avoid detection
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.execute_script("window.localStorage.clear();")
            
            # Set a realistic referrer
            referrers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.flipkart.com/",
                "https://www.flipkart.com/search?q=bamboo+toothbrush"
            ]
            self.driver.execute_script(f"window.document.referrer = '{random.choice(referrers)}';")
            
            # Navigate to URL
            self.driver.get(product["url"] + random_param)
            self.random_sleep(3, 6)
            
            # Simulate human-like behavior
            self.simulate_human_behavior()
            
            # Save debug file
            debug_file = self.save_debug_file("flipkart")
            
            # Title extraction strategies
            title_strategies = [
                {"type": "css", "selector": "span.B_NuCI"},
                {"type": "css", "selector": "h1.yhB1nd"},
                {"type": "css", "selector": ".B_NuCI"},
                {"type": "js", "script": "return document.querySelector('h1') ? document.querySelector('h1').innerText : null;"},
                {"type": "js", "script": "return document.title.split('-')[0].trim();"}
            ]
            
            title = self.extract_with_retry(title_strategies) or product["name"]
            
            # Price extraction strategies
            price_strategies = [
                {"type": "css", "selector": "div._30jeq3._16Jk6d"},
                {"type": "css", "selector": "div._30jeq3"},
                {"type": "css", "selector": ".CEmiEU div._16Jk6d"},
                {"type": "css", "selector": ".CEmiEU ._30jeq3"},
                {"type": "css", "selector": "div[data-price]"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('div')).find(el => el.innerText && el.innerText.includes('₹') && !el.innerText.includes('off'))?.innerText;"}
            ]
            
            price = self.extract_with_retry(price_strategies)
            clean_price = self.clean_price(price)
            
            # Original price extraction strategies
            original_price_strategies = [
                {"type": "css", "selector": "div._3I9_wc._2p6lqe"},
                {"type": "css", "selector": "div._3I9_wc"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('div')).find(el => el.innerText && el.innerText.includes('₹') && el.innerText.includes('MRP'))?.innerText;"}
            ]
            
            original_price = self.extract_with_retry(original_price_strategies)
            clean_original_price = self.clean_price(original_price)
            
            # Discount extraction strategies
            discount_strategies = [
                {"type": "css", "selector": "div._3Ay6Sb._31Dcoz"},
                {"type": "css", "selector": "div._3Ay6Sb"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('div')).find(el => el.innerText && el.innerText.includes('% off'))?.innerText;"}
            ]
            
            discount = self.extract_with_retry(discount_strategies)
            
            # Stock status extraction strategies
            try:
                stock_status_element = self.driver.find_element(By.CSS_SELECTOR, "div._16FRp0")
                stock_status = "Out of Stock"
            except NoSuchElementException:
                # Check for "ADD TO CART" button
                try:
                    self.driver.find_element(By.CSS_SELECTOR, "button._2KpZ6l._2U9uOA._3v1-ww")
                    stock_status = "In Stock"
                except NoSuchElementException:
                    stock_status = "Unknown"
            
            # Extract ratings if available
            rating_strategies = [
                {"type": "css", "selector": "div._3LWZlK"},
                {"type": "js", "script": "return document.querySelector('[id*=\"productRating\"]')?.innerText;"}
            ]
            
            rating = self.extract_with_retry(rating_strategies)
            
            # Extract number of reviews if available
            reviews_strategies = [
                {"type": "css", "selector": "span._2_R_DZ"},
                {"type": "js", "script": "return document.querySelector('[id*=\"productReviews\"]')?.innerText;"}
            ]
            
            reviews = self.extract_with_retry(reviews_strategies)
            
            # Create data object with all extracted information
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'flipkart',
                'product_name': product["name"],
                'url': product["url"],
                'title': title,
                'current_price': clean_price,
                'original_price': clean_original_price,
                'discount': discount,
                'stock_status': stock_status,
                'rating': rating,
                'reviews': reviews
            }
            
            # Add debug file if available
            if debug_file:
                data['debug_file'] = debug_file
            
            logger.info(f"Successfully scraped Flipkart: {product['name']}")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping Flipkart {product['name']}: {e}", exc_info=True)
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'flipkart',
                'product_name': product["name"],
                'url': product["url"],
                'error': str(e)
            }
    
    def scrape_amazon(self, product: Dict[str, str]) -> Dict[str, Any]:
        """
        Scrape product information from Amazon
        
        Args:
            product: Product information dictionary
            
        Returns:
            Scraped product data
        """
        logger.info(f"Scraping Amazon: {product['name']}")
        
        try:
            # Add random query parameters and clear storage
            random_param = f"?rand={random.randint(1000000, 9999999)}"
            self.driver.execute_script("window.sessionStorage.clear();")
            self.driver.execute_script("window.localStorage.clear();")
            
            # Set a realistic referrer
            referrers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.amazon.in/",
                "https://www.amazon.in/s?k=bamboo+toothbrush"
            ]
            self.driver.execute_script(f"window.document.referrer = '{random.choice(referrers)}';")
            
            # Navigate to URL
            self.driver.get(product["url"] + random_param)
            self.random_sleep(3, 6)
            
            # Handle cookie consent if it appears
            try:
                cookie_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[id*='accept'], button[id*='accept']")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self.random_sleep(1, 2)
            except Exception:
                pass
            
            # Simulate human-like behavior
            self.simulate_human_behavior()
            
            # Save debug file
            debug_file = self.save_debug_file("amazon")
            
            # Title extraction strategies
            title_strategies = [
                {"type": "id", "selector": "productTitle"},
                {"type": "css", "selector": "#productTitle"},
                {"type": "js", "script": "return document.getElementById('productTitle')?.innerText;"},
                {"type": "js", "script": "return document.querySelector('h1')?.innerText;"}
            ]
            
            title = self.extract_with_retry(title_strategies) or product["name"]
            
            # Price extraction strategies - Amazon often has complex price structures
            price_strategies = [
                {"type": "css", "selector": "#priceblock_ourprice"},
                {"type": "css", "selector": "#priceblock_dealprice"},
                {"type": "css", "selector": "#priceblock_saleprice"}, 
                {"type": "css", "selector": ".a-price .a-offscreen"},
                {"type": "css", "selector": ".a-price-whole"},
                {"type": "css", "selector": "#corePrice_feature_div .a-offscreen"},
                {"type": "css", "selector": ".a-price"},
                {"type": "js", "script": "return document.querySelector('[data-asin-price]')?.getAttribute('data-asin-price');"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('span')).find(el => el.innerText && el.innerText.includes('₹'))?.innerText;"}
            ]
            
            price = self.extract_with_retry(price_strategies)
            clean_price = self.clean_price(price)
            
            # Availability strategies
            availability_strategies = [
                {"type": "id", "selector": "availability"},
                {"type": "css", "selector": "#availability span"},
                {"type": "css", "selector": ".a-color-success"},
                {"type": "js", "script": "return document.getElementById('availability')?.innerText;"},
                {"type": "js", "script": "return document.querySelector('[id*=\"availability\"]')?.innerText;"}
            ]
            
            availability = self.extract_with_retry(availability_strategies)
            
            # Determine stock status
            if availability:
                stock_status = "In Stock" if "in stock" in availability.lower() else "Out of Stock"
            else:
                # If availability text is not found, check for add to cart button
                try:
                    add_to_cart = self.driver.find_element(By.ID, "add-to-cart-button")
                    stock_status = "In Stock"
                except NoSuchElementException:
                    stock_status = "Unknown"
            
            # Extract original price (usually displayed as strike-through)
            original_price_strategies = [
                {"type": "css", "selector": ".a-text-strike"},
                {"type": "css", "selector": "#listPrice"},
                {"type": "css", "selector": "#priceBlockStrikePriceString"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('span')).find(el => el.innerText && el.innerText.includes('₹') && el.style.textDecoration && el.style.textDecoration.includes('line-through'))?.innerText;"}
            ]
            
            original_price = self.extract_with_retry(original_price_strategies)
            clean_original_price = self.clean_price(original_price)
            
            # Extract ratings
            rating_strategies = [
                {"type": "css", "selector": ".a-icon-star .a-icon-alt"},
                {"type": "css", "selector": "#acrPopover .a-icon-alt"},
                {"type": "id", "selector": "acrCustomerReviewText"},
                {"type": "js", "script": "return document.querySelector('.a-icon-star')?.getAttribute('title');"}
            ]
            
            rating = self.extract_with_retry(rating_strategies)
            
            # Create data object with all extracted information
            data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'amazon',
                'product_name': product["name"],
                'url': product["url"],
                'title': title,
                'current_price': clean_price,
                'original_price': clean_original_price,
                'stock_status': stock_status,
                'rating': rating
            }
            
            # Add debug file if available
            if debug_file:
                data['debug_file'] = debug_file
            
            logger.info(f"Successfully scraped Amazon: {product['name']}")
            return data
            
        except Exception as e:
            logger.error(f"Error scraping Amazon {product['name']}: {e}", exc_info=True)
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'platform': 'amazon',
                'product_name': product["name"],
                'url': product["url"],
                'error': str(e)
            } 

    def scrape_product(self, product: Dict[str, str]) -> Dict[str, Any]:
        """
        Scrape a product based on its platform with retry logic
        
        Args:
            product: Product information dictionary
            
        Returns:
            Scraped product data
        """
        # Initialize retry counter
        retries = 3
        
        while retries > 0:
            try:
                if product["platform"] == "flipkart":
                    return self.scrape_flipkart(product)
                elif product["platform"] == "amazon":
                    return self.scrape_amazon(product)
                else:
                    logger.warning(f"Unsupported platform: {product['platform']}")
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': product["platform"],
                        'product_name': product["name"],
                        'url': product["url"],
                        'error': f"Unsupported platform: {product['platform']}"
                    }
            except Exception as e:
                retries -= 1
                logger.warning(f"Retry {3-retries}/3 for {product['name']} due to: {e}")
                
                if retries > 0:
                    # Reset browser state before retry
                    self.driver.delete_all_cookies()
                    self.driver.execute_script("window.sessionStorage.clear();")
                    self.driver.execute_script("window.localStorage.clear();")
                    self.random_sleep(5, 10)  # Longer delay before retry
                else:
                    logger.error(f"Failed to scrape {product['name']} after 3 attempts")
                    return {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'platform': product["platform"],
                        'product_name': product["name"],
                        'url': product["url"],
                        'error': f"Failed after 3 retries: {str(e)}"
                    }
    
    def scrape_all(self) -> List[Dict[str, Any]]:
        """
        Scrape all products with randomized order
        
        Returns:
            List of scraped product data
        """
        # Randomize product order to make bot detection harder
        products_to_scrape = PRODUCTS.copy()
        random.shuffle(products_to_scrape)
        
        for product in products_to_scrape:
            try:
                result = self.scrape_product(product)
                self.results.append(result)
                
                # Add a random delay between requests with more variability
                delay = random.uniform(8, 15) if random.random() > 0.7 else random.uniform(5, 10)
                logger.info(f"Waiting {delay:.2f} seconds before next request")
                time.sleep(delay)
                
                # Occasionally reset the browser state
                if random.random() > 0.7:
                    logger.info("Resetting browser state")
                    self.driver.delete_all_cookies()
                    self.driver.execute_script("window.sessionStorage.clear();")
                    self.driver.execute_script("window.localStorage.clear();")
            except Exception as e:
                logger.error(f"Error processing product {product['name']}: {e}", exc_info=True)
        
        return self.results
    
    def save_results(self) -> str:
        """
        Save results to JSON file with proper directory structure
        
        Returns:
            Path to saved file
        """
        # Create data directory structure if it doesn't exist
        os.makedirs('data/raw', exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'data/raw/prices_{timestamp}.json'
        
        # Save to JSON file with proper formatting
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving results: {e}", exc_info=True)
            return ""
    
    def close(self) -> None:
        """Close the WebDriver gracefully"""
        if hasattr(self, 'driver'):
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")


def main():
    """
    Main function to run the scraper with proper error handling and reporting
    """
    logger.info("Starting E-commerce Scraper")
    
    # Initialize scraper
    scraper = None
    
    try:
        # Create scraper instance with configurable options
        scraper = EcommerceScraper(
            use_proxies=False,  # Set to True if you want to use proxies
            debug_mode=True     # Save HTML debug files
        )
        
        # Run the scraper and get results
        results = scraper.scrape_all()
        
        # Save results to file
        output_file = scraper.save_results()
        
        # Print summary
        success_count = len([r for r in results if 'error' not in r])
        error_count = len([r for r in results if 'error' in r])
        
        logger.info(f"Scraping completed: {success_count} successes, {error_count} failures")
        logger.info(f"Results saved to {output_file}")
        
        # Return success status
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Scraper failed with error: {e}", exc_info=True)
        return False
        
    finally:
        # Always close the scraper properly
        if scraper:
            scraper.close()
            
    logger.info("E-commerce Scraper finished")


class FlipkartScraper(EcommerceScraper):
    """
    Specialized scraper for Flipkart - allows for platform-specific customization
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = "flipkart"
    
    def scrape_product(self, product):
        """Override to add Flipkart-specific scraping logic"""
        return self.scrape_flipkart(product)
        
    def extract_product_highlights(self, product_url):
        """Extract product highlights from Flipkart product page"""
        try:
            self.driver.get(product_url)
            self.random_sleep(3, 5)
            
            highlight_strategies = [
                {"type": "css", "selector": "div._2cM9lP"},
                {"type": "css", "selector": "div._3xWLK0"},
                {"type": "js", "script": "return Array.from(document.querySelectorAll('div._2cM9lP')).map(el => el.innerText);"}
            ]
            
            highlights = self.extract_with_retry(highlight_strategies)
            return highlights
        except Exception as e:
            logger.error(f"Error extracting highlights: {e}")
            return None


class AmazonScraper(EcommerceScraper):
    """
    Specialized scraper for Amazon - allows for platform-specific customization
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = "amazon"
    
    def scrape_product(self, product):
        """Override to add Amazon-specific scraping logic"""
        return self.scrape_amazon(product)
        
    def extract_product_specifications(self, product_url):
        """Extract product specifications from Amazon product page"""
        try:
            self.driver.get(product_url)
            self.random_sleep(3, 5)
            
            # Look for technical details section
            spec_strategies = [
                {"type": "id", "selector": "productDetails_techSpec_section_1"},
                {"type": "id", "selector": "productDetails_detailBullets_sections1"},
                {"type": "css", "selector": "table.a-keyvalue"}
            ]
            
            specs = self.extract_with_retry(spec_strategies)
            return specs
        except Exception as e:
            logger.error(f"Error extracting specifications: {e}")
            return None


def run_batch_scraping(product_list, output_dir="data/raw", headless=True):
    """
    Run batch scraping for a list of products with advanced options
    
    Args:
        product_list: List of product dictionaries
        output_dir: Directory to save results
        headless: Whether to run browser in headless mode
    
    Returns:
        Path to saved results file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create scraper instance
    scraper = EcommerceScraper(debug_mode=True)
    
    try:
        results = []
        
        # Process each product with retry mechanism
        for product in product_list:
            try:
                # Process product with retry
                result = scraper.scrape_product(product)
                results.append(result)
                
                # Add random delay
                delay = random.uniform(5, 15)
                logger.info(f"Waiting {delay:.2f} seconds before next request")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to scrape {product['name']}: {e}")
                results.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'platform': product.get('platform', 'unknown'),
                    'product_name': product.get('name', 'unknown'),
                    'url': product.get('url', ''),
                    'error': str(e)
                })
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'{output_dir}/batch_results_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch results saved to {filename}")
        return filename
        
    finally:
        # Clean up resources
        scraper.close()


def add_new_products(products_file="products.json", new_products=None):
    """
    Add new products to the products list
    
    Args:
        products_file: Path to products JSON file
        new_products: List of new product dictionaries to add
    
    Returns:
        Number of products added
    """
    if not new_products:
        return 0
        
    try:
        # Load existing products
        if os.path.exists(products_file):
            with open(products_file, 'r', encoding='utf-8') as f:
                existing_products = json.load(f)
        else:
            existing_products = []
        
        # Track added products
        added_count = 0
        
        # Add new products if they don't exist
        for product in new_products:
            if product not in existing_products:
                existing_products.append(product)
                added_count += 1
        
        # Save updated products list
        with open(products_file, 'w', encoding='utf-8') as f:
            json.dump(existing_products, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Added {added_count} new products to {products_file}")
        return added_count
        
    except Exception as e:
        logger.error(f"Error adding new products: {e}")
        return 0


def price_history_analysis(data_directory="data/raw", product_name=None):
    """
    Analyze price history for a specific product
    
    Args:
        data_directory: Directory containing JSON price data files
        product_name: Name of product to analyze
    
    Returns:
        Dictionary with price history analysis
    """
    if not os.path.exists(data_directory):
        logger.error(f"Data directory {data_directory} does not exist")
        return None
    
    try:
        # Get all JSON files in directory
        json_files = [f for f in os.listdir(data_directory) if f.endswith('.json')]
        
        if not json_files:
            logger.warning(f"No JSON files found in {data_directory}")
            return None
        
        # Collect price data from all files
        price_data = []
        
        for file in json_files:
            file_path = os.path.join(data_directory, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract data for specific product if provided
                    if product_name:
                        data = [d for d in data if d.get('product_name') == product_name]
                    
                    if data:
                        # Extract timestamp from filename if not in data
                        if 'timestamp' not in data[0]:
                            # Extract timestamp from filename (e.g., prices_20220101_120000.json)
                            timestamp_str = file.split('_')[1:3]
                            if len(timestamp_str) >= 2:
                                timestamp = f"{timestamp_str[0]}_{timestamp_str[1].split('.')[0]}"
                                for d in data:
                                    d['timestamp'] = timestamp
                        
                        price_data.extend(data)
            except Exception as e:
                logger.error(f"Error processing file {file}: {e}")
        
        if not price_data:
            logger.warning(f"No price data found for {product_name or 'any product'}")
            return None
        
        # Analyze price data
        analysis = {
            'product_name': product_name if product_name else "All Products",
            'data_points': len(price_data),
            'platforms': list(set(d.get('platform') for d in price_data if 'platform' in d)),
            'price_history': []
        }
        
        # Group by product and sort by timestamp
        products = {}
        for d in price_data:
            if 'product_name' in d and 'current_price' in d and d['current_price']:
                product = d['product_name']
                if product not in products:
                    products[product] = []
                products[product].append(d)
        
        # Sort by timestamp and create price history
        for product, data in products.items():
            data.sort(key=lambda x: x.get('timestamp', ''))
            
            product_history = {
                'product': product,
                'price_points': []
            }
            
            for d in data:
                if 'current_price' in d and d['current_price']:
                    try:
                        price_point = {
                            'timestamp': d.get('timestamp', ''),
                            'platform': d.get('platform', ''),
                            'price': float(d['current_price'])
                        }
                        product_history['price_points'].append(price_point)
                    except (ValueError, TypeError):
                        pass
            
            if product_history['price_points']:
                # Calculate statistics
                prices = [p['price'] for p in product_history['price_points']]
                product_history['min_price'] = min(prices)
                product_history['max_price'] = max(prices)
                product_history['avg_price'] = sum(prices) / len(prices)
                product_history['price_change'] = prices[-1] - prices[0] if len(prices) > 1 else 0
                product_history['price_change_percent'] = (product_history['price_change'] / prices[0] * 100) if len(prices) > 1 and prices[0] > 0 else 0
                
                analysis['price_history'].append(product_history)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing price history: {e}")
        return None


if __name__ == "__main__":
    main() 