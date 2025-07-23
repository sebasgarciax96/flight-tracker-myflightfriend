#!/usr/bin/env python3
"""
Test script to debug the scraping issue
"""

import sys
sys.path.append('src')

from google_flight_analysis.scrape import Scrape, ScrapeObjects
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller
import time

def test_manual_scrape():
    """Test manual scraping approach"""
    print("🔍 Testing manual scraping approach...")
    
    # Install ChromeDriver
    chromedriver_autoinstaller.install()
    
    # Set up Chrome options
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to Google Flights for your specific route
        url = "https://www.google.com/travel/flights?hl=en&q=Flights%20to%20DEN%20from%20SLC%20on%202024-08-04%20round%20trip%20return%202024-08-05"
        print(f"🌐 Navigating to: {url}")
        
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)
        
        # Try to find price elements
        print("🔍 Looking for price elements...")
        
        # Common price selectors for Google Flights
        price_selectors = [
            '[data-value]',  # Price data attribute
            '[role="button"] span[aria-label*="dollar"]',  # Price buttons
            '.gws-flights-results__price',  # Price class
            '.OgQvJf',  # Common price class
            'span[data-gs*="price"]',  # Price data attribute
            'span[aria-label*="$"]',  # Aria label with dollar sign
        ]
        
        prices_found = []
        
        for selector in price_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  Found {len(elements)} elements with selector: {selector}")
                
                for element in elements[:5]:  # Check first 5 elements
                    try:
                        text = element.text.strip()
                        if text and ('$' in text or text.isdigit()):
                            prices_found.append(text)
                            print(f"    Price text: {text}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"  Error with selector {selector}: {e}")
        
        # Print page source snippet for debugging
        print("\n📄 Page source snippet:")
        page_source = driver.page_source
        if "Sort by:" in page_source:
            print("  ✅ 'Sort by:' found in page source")
        else:
            print("  ❌ 'Sort by:' NOT found in page source")
            
        if "$" in page_source:
            print("  ✅ '$' found in page source")
        else:
            print("  ❌ '$' NOT found in page source")
        
        # Look for common flight-related text
        flight_keywords = ["flight", "price", "delta", "departure", "arrival"]
        for keyword in flight_keywords:
            if keyword.lower() in page_source.lower():
                print(f"  ✅ '{keyword}' found in page source")
        
        print(f"\n💰 Prices found: {list(set(prices_found))}")
        
        # Save page source for debugging
        with open('debug_page_source.html', 'w') as f:
            f.write(driver.page_source)
        print("💾 Page source saved to debug_page_source.html")
        
    finally:
        driver.quit()

def test_original_scrape():
    """Test the original scraping method"""
    print("\n🧪 Testing original scraping method...")
    
    try:
        # Your flight details
        result = Scrape('SLC', 'DEN', '2024-08-04', '2024-08-05')
        print(f"✅ Created scrape object: {result}")
        
        # Try to scrape
        ScrapeObjects(result)
        
        if not result.data.empty:
            print("✅ Data scraped successfully!")
            print(result.data.head())
            
            if 'price' in result.data.columns:
                min_price = result.data['price'].min()
                print(f"💰 Minimum price found: ${min_price}")
            else:
                print("❌ No price column found")
                print(f"Columns: {result.data.columns.tolist()}")
        else:
            print("❌ No data scraped")
            
    except Exception as e:
        print(f"❌ Error in original scrape: {e}")

if __name__ == "__main__":
    print("🚀 Starting scraping tests...")
    
    # Test manual approach first
    test_manual_scrape()
    
    # Test original approach
    test_original_scrape()
    
    print("\n✅ Tests completed!")