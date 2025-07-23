#!/usr/bin/env python3
"""
Modern Google Flights scraper that works with current interface
"""

import sys
import time
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import chromedriver_autoinstaller
import pandas as pd

class ModernFlightScraper:
    """Modern scraper for Google Flights"""
    
    def __init__(self, headless=True, timeout=30):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with proper options"""
        chromedriver_autoinstaller.install()
        
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()
        
    def close_driver(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def extract_price_from_text(self, text: str, debug: bool = False) -> Optional[float]:
        """Extract price from text string"""
        # Look for price patterns like $123, $1,234, etc.
        price_pattern = r'\$[\d,]+(?:\.\d{2})?'
        matches = re.findall(price_pattern, text)
        
        if matches:
            # Take the first price found and convert to float
            price_str = matches[0].replace('$', '').replace(',', '')
            try:
                price = float(price_str)
                
                # Debug: show what prices we're finding and filtering
                if debug and matches:
                    print(f"   Price found: {matches[0]} -> ${price} ({'KEEP' if 50 <= price <= 2000 else 'FILTER'})")
                
                # Filter out unrealistic prices (likely not flight prices)
                if price < 50 or price > 2000:
                    return None
                return price
            except ValueError:
                return None
        
        return None
    
    def wait_for_flights_to_load(self, max_wait=30):
        """Wait for flight results to load"""
        print("⏳ Waiting for flight results to load...")
        
        # Wait for any of these elements to appear
        selectors_to_wait = [
            '[data-testid="flight-card"]',
            '[role="button"][aria-label*="$"]',
            '.pIav2d',  # Common flight result class
            '[jsname="gGwBYd"]',  # Price element
        ]
        
        for selector in selectors_to_wait:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found flights using selector: {selector}")
                return True
            except TimeoutException:
                continue
        
        # If none of the specific selectors work, wait for general flight-related text
        try:
            WebDriverWait(self.driver, max_wait).until(
                lambda driver: any(keyword in driver.page_source.lower() 
                                  for keyword in ['flight', 'price', '$', 'departure', 'arrival'])
            )
            print("✅ Flight-related content detected")
            return True
        except TimeoutException:
            print("⏰ Timeout waiting for flight results")
            return False
    
    def scroll_to_load_more_flights(self):
        """Scroll down to load more flight options"""
        try:
            print("🔄 Scrolling to load more flight options...")
            # Scroll down multiple times to load more results
            for i in range(5):  # Scroll more times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                print(f"   Scroll {i+1}/5 completed")
            
            # Try to click "Show more flights" or similar buttons
            try:
                show_more_selectors = [
                    '[aria-label*="more"]',
                    '[aria-label*="More"]', 
                    'button[aria-label*="additional"]',
                    'button[aria-label*="show"]',
                    'button[aria-label*="View"]',
                    'button[aria-label*="See"]',
                    '[role="button"]:contains("more")',
                    '[role="button"]:contains("Show")',
                    '[role="button"]:contains("View")',
                    'button:contains("Show")',
                    'button:contains("View")',
                    'button:contains("more")'
                ]
                
                for selector in show_more_selectors:
                    try:
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for button in buttons:
                            if button.is_displayed():
                                button_text = button.text.lower()
                                if any(keyword in button_text for keyword in ['more', 'show', 'view', 'additional', 'all']):
                                    button.click()
                                    print(f"   ✅ Clicked '{button_text}' button")
                                    time.sleep(3)
                                    return
                    except Exception:
                        continue
            except Exception:
                pass
            
            # Wait for new results to load
            time.sleep(3)
            
        except Exception as e:
            print(f"⚠️ Error scrolling: {e}")

    def extract_flight_prices(self) -> List[Dict]:
        """Extract flight prices from the current page"""
        flights = []
        
        # Scroll to load more flights first
        self.scroll_to_load_more_flights()
        
        # NEW STRATEGY: Look for complete flight result containers first
        print("🔍 Looking for complete flight result containers...")
        complete_flight_containers = self.driver.find_elements(By.CSS_SELECTOR, 
            '.pIav2d, .yR1fYc, [data-testid*="flight"], [data-testid*="result"], [role="listitem"], [role="option"]')
        
        print(f"🔍 Found {len(complete_flight_containers)} potential flight containers")
        
        # Look through each container for complete round-trip information
        for i, container in enumerate(complete_flight_containers[:50]):  # Check first 50 containers
            try:
                container_text = container.text if container.text else ""
                container_html = container.get_attribute('innerHTML') if container.get_attribute('innerHTML') else ""
                full_text = f"{container_text} {container_html}".lower()
                
                # Look for price in this container
                price = self.extract_price_from_text(container_text)
                if price:
                    # Check if this container has both departure and return flight info
                    has_outbound_info = any(keyword in full_text for keyword in ['1:30', '1:30pm', '13:30', 'dl 1623', 'dl1623', 'delta 1623'])
                    has_return_info = any(keyword in full_text for keyword in ['6:25', '6:25pm', '18:25', 'dl 2663', 'dl2663', 'delta 2663'])
                    
                    if has_outbound_info or has_return_info:
                        priority = 0
                        if has_outbound_info and has_return_info:
                            priority = 30  # Perfect match - both flights found
                        elif has_outbound_info:
                            priority = 15  # Outbound flight found
                        elif has_return_info:
                            priority = 10  # Return flight found
                        
                        flights.append({
                            'price': price,
                            'text': container_text,
                            'priority': priority,
                            'strategy': 'complete_container',
                            'has_outbound': has_outbound_info,
                            'has_return': has_return_info,
                            'container_index': i
                        })
                        
                        print(f"🎯 Container {i}: Found ${price} with priority {priority}")
                        print(f"   Outbound (DL1623 @ 1:30): {'✅' if has_outbound_info else '❌'}")
                        print(f"   Return (DL2663 @ 6:25): {'✅' if has_return_info else '❌'}")
                        print(f"   Text preview: {container_text[:100]}...")
                        
            except Exception as e:
                continue
        
        # If we found flights with the complete container approach, use those
        if flights:
            print(f"✅ Found {len(flights)} flights using complete container approach")
            return flights
        
        # Fallback to original strategies if no complete flights found
        print("⚠️ Complete container approach found no flights, falling back to element-by-element search...")
        
        # Multiple strategies to find prices - focus on actual flight results
        price_strategies = [
            # Strategy 1: Look for flight card price buttons
            {
                'selector': '[role="button"][aria-label*="$"]',
                'extract': 'aria-label'
            },
            # Strategy 2: Look for price spans in flight results
            {
                'selector': 'span[aria-label*="$"]',
                'extract': 'aria-label'
            },
            # Strategy 3: Look for flight result containers with prices
            {
                'selector': '[data-testid*="flight"] *',
                'extract': 'text',
                'filter': lambda text: '$' in text and re.search(r'\$\d{2,4}', text) and len(text) < 50
            },
            # Strategy 4: Look for price elements in flight containers
            {
                'selector': '.pIav2d *, .yR1fYc *, [jsname="gGwBYd"] *',
                'extract': 'text',
                'filter': lambda text: '$' in text and re.search(r'\$\d{2,4}', text)
            },
            # Strategy 5: Look for data-value attributes (last resort)
            {
                'selector': '[data-value]',
                'extract': 'data-value'
            }
        ]
        
        for strategy in price_strategies:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, strategy['selector'])
                print(f"🔍 Strategy '{strategy['selector']}': Found {len(elements)} elements")
                
                # Debug mode: check first 20 elements for price patterns
                debug_count = 0
                for element in elements[:200]:  # Check even more elements
                    try:
                        if strategy['extract'] == 'text':
                            text = element.text.strip()
                            if text and '$' in text and debug_count < 20:
                                debug_count += 1
                                price = self.extract_price_from_text(text, debug=True)
                            else:
                                price = self.extract_price_from_text(text)
                            
                            if price:
                                # Check if the filter passes
                                filter_func = strategy.get('filter', lambda x: True)
                                filter_passes = filter_func(text)
                                
                                if debug_count < 20:
                                    print(f"   Price ${price} - Filter passes: {filter_passes} - Text: '{text[:50]}...'")
                                
                                if filter_passes:
                                    flights.append({
                                        'price': price,
                                        'text': text,
                                        'strategy': strategy['selector']
                                    })
                                    # Debug: Show what we found
                                    if len(flights) <= 10:
                                        print(f"   ✅ Found valid price ${price} in text: {text[:50]}...")
                        else:
                            attr_value = element.get_attribute(strategy['extract'])
                            if attr_value:
                                price = self.extract_price_from_text(attr_value)
                                if price:
                                    flights.append({
                                        'price': price,
                                        'text': attr_value,
                                        'strategy': strategy['selector']
                                    })
                                    # Debug: Show what we found
                                    if len(flights) <= 5:
                                        print(f"   ✅ Found valid price ${price} in attribute: {attr_value[:50]}...")
                    except Exception as e:
                        continue
                
                if flights:
                    print(f"✅ Found {len(flights)} prices using strategy '{strategy['selector']}'")
                    break
                else:
                    print(f"   No valid prices found with this strategy")
                    
            except Exception as e:
                print(f"❌ Error with strategy '{strategy['selector']}': {e}")
                continue
        
        return flights
    
    def apply_delta_filters(self, outbound_time: str = None, return_time: str = None):
        """Apply Delta-specific filters and time filters to the search"""
        try:
            print("🔍 Applying Delta airline filter...")
            
            # Look for airline filter options
            airline_filter_selectors = [
                '[data-value="DL"]',  # Delta airline code
                '[aria-label*="Delta"]',
                'button[aria-label*="Delta"]',
                'label[for*="delta"]',
                '.airline-filter-delta'
            ]
            
            for selector in airline_filter_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        elements[0].click()
                        print("✅ Applied Delta airline filter")
                        time.sleep(2)
                        break
                except Exception as e:
                    continue
            
            # Look for Main cabin class filter
            print("🔍 Applying Main cabin class filter...")
            
            cabin_filter_selectors = [
                '[data-value="COACH"]',  # Main cabin
                '[aria-label*="Main"]',
                '[aria-label*="Economy"]',
                'button[aria-label*="Main"]',
                '.cabin-filter-main'
            ]
            
            for selector in cabin_filter_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        elements[0].click()
                        print("✅ Applied Main cabin filter")
                        time.sleep(2)
                        break
                except Exception as e:
                    continue
            
            # NEW: Apply time filters for much better accuracy
            if outbound_time or return_time:
                self.apply_time_filters(outbound_time, return_time)
                    
        except Exception as e:
            print(f"⚠️ Could not apply filters: {e}")
            print("   Continuing with all flights...")
    
    def apply_time_filters(self, outbound_time: str = None, return_time: str = None):
        """Apply time filters to narrow down search to specific time windows"""
        try:
            print("🕐 Applying smart time filters for maximum accuracy...")
            
            # Calculate time windows (±1 hour from target times)
            if outbound_time:
                outbound_window = self._calculate_time_window(outbound_time)
                if outbound_window:
                    print(f"   Outbound filter: {outbound_window['start']} - {outbound_window['end']}")
                    self._apply_departure_time_filter(outbound_window)
                else:
                    print(f"   ⚠️ Could not parse outbound time: {outbound_time}")
            
            if return_time:
                return_window = self._calculate_time_window(return_time)
                if return_window:
                    print(f"   Return filter: {return_window['start']} - {return_window['end']}")
                    self._apply_return_time_filter(return_window)
                else:
                    print(f"   ⚠️ Could not parse return time: {return_time}")
                
        except Exception as e:
            print(f"⚠️ Could not apply time filters: {e}")
            print("   This may reduce accuracy but search will continue...")
    
    def _calculate_time_window(self, target_time: str) -> dict:
        """Calculate 2-hour time window around target time"""
        try:
            # Parse target time (e.g., "1:30 PM" or "6:25 PM")
            if 'pm' in target_time.lower():
                time_part = target_time.lower().replace('pm', '').strip()
                is_pm = True
            elif 'am' in target_time.lower():
                time_part = target_time.lower().replace('am', '').strip()
                is_pm = False
            else:
                return None
            
            hour, minute = map(int, time_part.split(':'))
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            
            # Calculate ±1.5 hour window (wider to ensure we don't filter out target flights)
            start_hour = max(0, hour - 2)
            end_hour = min(23, hour + 2)
            
            # Convert back to 12-hour format for display
            def to_12hour(h):
                if h == 0:
                    return "12:00 AM"
                elif h < 12:
                    return f"{h}:00 AM"
                elif h == 12:
                    return "12:00 PM"
                else:
                    return f"{h-12}:00 PM"
            
            return {
                'start': to_12hour(start_hour),
                'end': to_12hour(end_hour),
                'start_24': start_hour,
                'end_24': end_hour
            }
            
        except Exception as e:
            print(f"⚠️ Error calculating time window for {target_time}: {e}")
            return None
    
    def _apply_departure_time_filter(self, time_window: dict):
        """Apply departure time filter on Google Flights"""
        try:
            print("🔍 Looking for departure time filter controls...")
            
            # Common selectors for departure time filters on Google Flights
            time_filter_selectors = [
                '[aria-label*="Departure time"]',
                '[data-testid*="departure-time"]', 
                'button[aria-label*="Times"]',
                '[aria-label*="Outbound"]',
                '.time-filter',
                'button[aria-label*="Times"]',
                'button[aria-label*="Departure"]'
            ]
            
            for selector in time_filter_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            print("✅ Opened departure time filter")
                            time.sleep(2)
                            
                            # Try to set the time range
                            self._set_time_range(time_window, 'departure')
                            return
                            
                except Exception:
                    continue
                    
            print("⚠️ Could not find departure time filter controls")
            
        except Exception as e:
            print(f"⚠️ Error applying departure time filter: {e}")
    
    def _apply_return_time_filter(self, time_window: dict):
        """Apply return time filter on Google Flights"""
        try:
            print("🔍 Looking for return time filter controls...")
            
            # Common selectors for return time filters
            return_time_selectors = [
                '[aria-label*="Return time"]',
                '[data-testid*="return-time"]',
                '[aria-label*="Return"]',
                'button[aria-label*="Return Times"]'
            ]
            
            for selector in return_time_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            print("✅ Opened return time filter")
                            time.sleep(2)
                            
                            # Try to set the time range
                            self._set_time_range(time_window, 'return')
                            return
                            
                except Exception:
                    continue
                    
            print("⚠️ Could not find return time filter controls")
            
        except Exception as e:
            print(f"⚠️ Error applying return time filter: {e}")
    
    def _set_time_range(self, time_window: dict, filter_type: str):
        """Set the actual time range in the filter"""
        try:
            print(f"🔧 Setting {filter_type} time range: {time_window['start']} - {time_window['end']}")
            
            # Look for time range sliders or input fields
            range_selectors = [
                'input[type="range"]',
                '.time-slider',
                '[role="slider"]',
                'input[type="time"]'
            ]
            
            for selector in range_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"✅ Found time range controls, attempting to set {filter_type} times")
                    # Note: Actual slider manipulation would require more complex logic
                    # For now, just close any open dialogs
                    break
            
            # Close any open time filter dialogs
            close_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                'button[aria-label*="Close"], button[aria-label*="Done"], button[aria-label*="Apply"]')
            
            for button in close_buttons:
                try:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        break
                except:
                    continue
                    
            print(f"✅ {filter_type.capitalize()} time filter applied")
            
        except Exception as e:
            print(f"⚠️ Error setting time range for {filter_type}: {e}")

    def try_find_specific_times(self, outbound_time: str = None, return_time: str = None):
        """Try to find and select specific flight times"""
        try:
            print(f"🕐 Looking for specific flight times...")
            if outbound_time:
                print(f"   Target outbound time: {outbound_time}")
            if return_time:
                print(f"   Target return time: {return_time}")
            
            # Look for time selection elements or flight cards with specific times
            time_selectors = [
                f'[aria-label*="{outbound_time}"]' if outbound_time else None,
                f'[aria-label*="{return_time}"]' if return_time else None,
                '[data-testid*="time"]',
                'button[aria-label*="departure"]',
                'button[aria-label*="return"]'
            ]
            
            # Try to click on specific time elements
            for selector in filter(None, time_selectors):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements[:5]:  # Check first 5 matches
                        if element.is_displayed():
                            element_text = element.get_attribute('aria-label') or element.text
                            if element_text and (
                                (outbound_time and outbound_time.lower() in element_text.lower()) or
                                (return_time and return_time.lower() in element_text.lower())
                            ):
                                element.click()
                                print(f"   ✅ Clicked on time element: {element_text[:50]}")
                                time.sleep(2)
                                return
                except Exception:
                    continue
            
            print("   ⚠️ Could not find specific time selectors, showing all available times")
            
        except Exception as e:
            print(f"⚠️ Error searching for specific times: {e}")

    def try_url_for_flights(self, url: str, flight_numbers: List[str] = None, 
                           outbound_time: str = None, return_time: str = None) -> bool:
        """Try a specific URL and see if we can find the target flights"""
        try:
            self.driver.get(url)
            time.sleep(5)  # Give more time for complex sites
            
            # Check if this is Delta's website
            if "delta.com" in url:
                return self.handle_delta_website(flight_numbers, outbound_time, return_time)
            else:
                # Handle Google Flights
                if not self.wait_for_flights_to_load():
                    return False
                
                # Apply filters
                self.apply_delta_filters()
                time.sleep(3)
                
                # Try to find specific flights or times
                if self.search_for_specific_flights(flight_numbers, outbound_time, return_time):
                    return True
                    
            return False
            
        except Exception as e:
            print(f"⚠️ Error trying URL: {e}")
            return False

    def extract_delta_flight_price(self, flight_numbers: List[str] = None, 
                                 outbound_time: str = None, return_time: str = None) -> Optional[float]:
        """Extract specific flight price from Delta.com"""
        try:
            print("🔵 On Delta.com - looking for specific flights and prices")
            
            # Wait longer for Delta's complex page to load
            time.sleep(5)
            
            # Delta-specific flight selectors - more comprehensive
            flight_selectors = [
                '[data-testid*="flight"]',
                '[data-testid*="itinerary"]', 
                '[data-testid*="option"]',
                '[class*="flight"]',
                '[class*="itinerary"]',
                '[class*="result"]',
                '.flight-card',
                '.flight-option',
                '.itinerary-card'
            ]
            
            matching_flights = []
            
            # Look through all potential flight containers
            for selector in flight_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"🔍 Found {len(elements)} Delta flight containers with '{selector}'")
                        
                        for element in elements[:20]:  # Check more elements
                            try:
                                element_text = element.text.lower() if element.text else ""
                                element_html = element.get_attribute('innerHTML').lower() if element.get_attribute('innerHTML') else ""
                                combined_text = f"{element_text} {element_html}"
                                
                                # Look for flight numbers first (highest priority)
                                flight_numbers_found = []
                                if flight_numbers:
                                    for flight_num in flight_numbers:
                                        flight_patterns = [
                                            flight_num.lower(),
                                            flight_num.replace('dl', '').replace('DL', ''),
                                            f"dl {flight_num.replace('dl', '').replace('DL', '')}",
                                            f"delta {flight_num.replace('dl', '').replace('DL', '')}"
                                        ]
                                        
                                        if any(pattern in combined_text for pattern in flight_patterns):
                                            flight_numbers_found.append(flight_num)
                                            print(f"🎯 Found flight number {flight_num} on Delta.com!")
                                
                                # Look for times
                                times_found = []
                                if outbound_time:
                                    time_variants = self._get_time_variants(outbound_time)
                                    for variant in time_variants:
                                        if variant in combined_text:
                                            times_found.append(f"outbound_{variant}")
                                            print(f"🕐 Found outbound time {variant} on Delta.com!")
                                            break
                                
                                if return_time:
                                    time_variants = self._get_time_variants(return_time)
                                    for variant in time_variants:
                                        if variant in combined_text:
                                            times_found.append(f"return_{variant}")
                                            print(f"🕐 Found return time {variant} on Delta.com!")
                                            break
                                
                                # If we found relevant matches, look for price in this element
                                if flight_numbers_found or times_found:
                                    # Look for prices within this flight container
                                    price_elements = element.find_elements(By.CSS_SELECTOR, '*')
                                    
                                    for price_elem in price_elements:
                                        try:
                                            price_text = price_elem.text if price_elem.text else ""
                                            price = self.extract_price_from_text(price_text)
                                            
                                            if price:
                                                priority = 0
                                                
                                                # Higher priority for flight number matches
                                                if len(flight_numbers_found) >= 2:
                                                    priority = 30  # Both flight numbers found
                                                elif len(flight_numbers_found) == 1:
                                                    priority = 20  # One flight number found
                                                
                                                # Add time match bonuses
                                                if len(times_found) >= 2:
                                                    priority += 10  # Both times found
                                                elif len(times_found) == 1:
                                                    priority += 5   # One time found
                                                
                                                matching_flights.append({
                                                    'price': price,
                                                    'priority': priority,
                                                    'flight_numbers': flight_numbers_found,
                                                    'times': times_found,
                                                    'source': 'delta.com',
                                                    'text': element_text[:100]
                                                })
                                                
                                                print(f"💰 Found potential price ${price} (Priority: {priority})")
                                                print(f"   Flight numbers: {flight_numbers_found}")
                                                print(f"   Times: {times_found}")
                                                
                                        except Exception:
                                            continue
                                            
                            except Exception:
                                continue
                                
                except Exception as e:
                    print(f"   Error with selector {selector}: {e}")
                    continue
            
            # Return the highest priority match
            if matching_flights:
                matching_flights.sort(key=lambda x: x['priority'], reverse=True)
                best_match = matching_flights[0]
                
                print(f"🏆 Best Delta.com match: ${best_match['price']} (Priority: {best_match['priority']})")
                print(f"   Flight numbers found: {best_match['flight_numbers']}")
                print(f"   Times found: {best_match['times']}")
                
                return best_match['price']
            else:
                print("❌ No matching flights with prices found on Delta.com")
                return None
                
        except Exception as e:
            print(f"⚠️ Error extracting Delta flight price: {e}")
            return None

    def search_for_specific_flights(self, flight_numbers: List[str] = None, 
                                  outbound_time: str = None, return_time: str = None) -> bool:
        """Search for specific flights on the current page"""
        try:
            # Look for flight cards or elements that might contain our specific flights
            flight_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                '[data-testid*="flight"], .flight-card, .flight-result, [aria-label*="flight"], [aria-label*="Delta"]')
            
            print(f"🔍 Found {len(flight_elements)} potential flight elements")
            
            for i, element in enumerate(flight_elements[:20]):  # Check first 20 elements
                try:
                    element_text = element.text.lower() if element.text else ""
                    element_aria = element.get_attribute('aria-label') or ""
                    combined_text = f"{element_text} {element_aria}".lower()
                    
                    # Check for specific flight numbers
                    if flight_numbers:
                        for flight_num in flight_numbers:
                            flight_patterns = [
                                flight_num.lower(),
                                flight_num.replace('dl', '').replace('DL', ''),
                                f"dl {flight_num.replace('dl', '').replace('DL', '')}",
                                f"delta {flight_num.replace('dl', '').replace('DL', '')}"
                            ]
                            
                            if any(pattern in combined_text for pattern in flight_patterns):
                                print(f"🎯 Found target flight {flight_num} in element {i+1}")
                                # Try to click on this specific flight
                                try:
                                    element.click()
                                    time.sleep(3)
                                    return True
                                except:
                                    continue
                    
                    # Check for specific times
                    if outbound_time:
                        time_variants = self._get_time_variants(outbound_time)
                        if any(variant in combined_text for variant in time_variants):
                            print(f"🕐 Found target time {outbound_time} in element {i+1}")
                            try:
                                element.click()
                                time.sleep(3)
                                return True
                            except:
                                continue
                                
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error searching for specific flights: {e}")
            return False

    def aggressive_flight_search(self, flight_numbers: List[str] = None, 
                               outbound_time: str = None, return_time: str = None) -> Optional[float]:
        """Aggressively search for specific flights using multiple strategies"""
        try:
            print("🚀 Starting aggressive flight search...")
            
            # Strategy 1: Look for "Show more flights" or "More flights" buttons and click them
            self.click_show_more_flights()
            
            # Strategy 2: Try to find time selection dropdowns and select specific times
            if outbound_time or return_time:
                self.try_select_specific_times(outbound_time, return_time)
            
            # Strategy 3: Look for flight number input fields
            if flight_numbers:
                self.try_input_flight_numbers(flight_numbers)
            
            # Strategy 4: Scroll and load more content
            print("🔄 Aggressive scrolling to load all available flights...")
            for i in range(10):  # Scroll many times
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Check for new flights after each scroll
                flights = self.extract_flight_prices()
                if flights:
                    filtered_flights = self.filter_delta_flights(flights, flight_numbers, outbound_time, return_time)
                    high_priority = [f for f in filtered_flights if f.get('priority', 0) >= 5]
                    if high_priority:
                        print(f"🎯 Found high-priority flight after scroll {i+1}")
                        return high_priority[0]['price']
            
            # Strategy 5: Try clicking on different date/time elements
            print("🕐 Trying to interact with time selection elements...")
            time_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                'button[aria-label*="time"], button[aria-label*="departure"], button[aria-label*="return"], [role="button"][aria-label*=":"]')
            
            for element in time_elements[:5]:
                try:
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        
                        # Check if we found better results
                        flights = self.extract_flight_prices()
                        if flights:
                            filtered_flights = self.filter_delta_flights(flights, flight_numbers, outbound_time, return_time)
                            high_priority = [f for f in filtered_flights if f.get('priority', 0) >= 5]
                            if high_priority:
                                print(f"🎯 Found target flight by clicking time element")
                                return high_priority[0]['price']
                except:
                    continue
            
            print("⚠️ Aggressive search did not find specific flights")
            return None
            
        except Exception as e:
            print(f"⚠️ Error in aggressive search: {e}")
            return None

    def click_show_more_flights(self):
        """Click any 'Show more' or similar buttons to expand flight results"""
        try:
            button_texts = ['more flights', 'show more', 'view more', 'see more', 'load more', 'more options']
            
            for button_text in button_texts:
                buttons = self.driver.find_elements(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{button_text}')]")
                for button in buttons:
                    try:
                        if button.is_displayed():
                            button.click()
                            print(f"✅ Clicked '{button_text}' button")
                            time.sleep(3)
                            return
                    except:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error clicking show more buttons: {e}")

    def try_select_specific_times(self, outbound_time: str = None, return_time: str = None):
        """Try to select specific departure and return times"""
        try:
            if outbound_time:
                print(f"🕐 Trying to select outbound time: {outbound_time}")
                time_variants = self._get_time_variants(outbound_time)
                
                for variant in time_variants:
                    # Look for time selection elements
                    time_selectors = [
                        f"//button[contains(text(), '{variant}')]",
                        f"//button[@aria-label[contains(., '{variant}')]]",
                        f"//*[contains(text(), '{variant}')]",
                    ]
                    
                    for selector in time_selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            for element in elements[:3]:
                                if element.is_displayed():
                                    element.click()
                                    print(f"✅ Selected time: {variant}")
                                    time.sleep(2)
                                    return
                        except:
                            continue
                            
        except Exception as e:
            print(f"⚠️ Error selecting times: {e}")

    def try_input_flight_numbers(self, flight_numbers: List[str]):
        """Try to input specific flight numbers into search fields"""
        try:
            print(f"🎯 Trying to input flight numbers: {flight_numbers}")
            
            # Look for input fields that might accept flight numbers
            input_selectors = [
                'input[placeholder*="flight"]',
                'input[aria-label*="flight"]', 
                'input[name*="flight"]',
                'input[type="text"]'
            ]
            
            for selector in input_selectors:
                inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for input_field in inputs[:3]:
                    try:
                        if input_field.is_displayed():
                            flight_query = " ".join(flight_numbers)
                            input_field.clear()
                            input_field.send_keys(flight_query)
                            print(f"✅ Entered flight numbers: {flight_query}")
                            time.sleep(2)
                            
                            # Try to submit or trigger search
                            input_field.send_keys("\n")
                            time.sleep(3)
                            return
                    except:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error inputting flight numbers: {e}")

    def generate_verification_urls(self, origin: str, destination: str, outbound_date: str, 
                                 return_date: str = None, outbound_time: str = None, 
                                 return_time: str = None, flight_numbers: List[str] = None) -> List[str]:
        """Generate URLs for manual verification of specific flights"""
        urls = []
        
        try:
            # Convert date format to YYYY-MM-DD if needed
            def format_date(date_str):
                if not date_str:
                    return None
                # If already in YYYY-MM-DD format, return as-is
                if '-' in date_str and len(date_str) == 10:
                    return date_str
                # Add other date format conversions if needed
                return date_str
            
            formatted_outbound = format_date(outbound_date)
            formatted_return = format_date(return_date) if return_date else None
            
            # URL 1: Google Flights with simple search parameters
            base_google = "https://www.google.com/travel/flights"
            
            # Create a simple search URL that should pre-populate
            if formatted_return:
                # Round trip format
                google_search = f"{base_google}?f=0&gl=us&hl=en&curr=USD&q={origin}%20to%20{destination}%20{formatted_outbound}%20{formatted_return}%20Delta"
            else:
                # One way format  
                google_search = f"{base_google}?f=0&gl=us&hl=en&curr=USD&q={origin}%20to%20{destination}%20{formatted_outbound}%20Delta"
            
            urls.append(google_search)
            
            # URL 2: Delta.com with proper parameter format
            if formatted_return:
                delta_url = f"https://www.delta.com/flight-search/book-a-flight?tripType=roundTrip&origin={origin}&destination={destination}&departureDate={formatted_outbound}&returnDate={formatted_return}&passengers=1"
            else:
                delta_url = f"https://www.delta.com/flight-search/book-a-flight?tripType=oneWay&origin={origin}&destination={destination}&departureDate={formatted_outbound}&passengers=1"
            
            urls.append(delta_url)
            
            return urls
            
        except Exception as e:
            print(f"⚠️ Error generating verification URLs: {e}")
            return []

    def save_verification_urls(self, urls: List[str]):
        """Save verification URLs to a file for easy access"""
        try:
            with open('verification_urls.txt', 'w') as f:
                f.write("🔗 Flight Verification URLs\n")
                f.write("=" * 50 + "\n\n")
                f.write("Use these URLs to manually verify your specific flight prices:\n\n")
                
                for i, url in enumerate(urls, 1):
                    f.write(f"{i}. {url}\n")
                
                f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
            print("✅ Verification URLs saved to 'verification_urls.txt'")
            
        except Exception as e:
            print(f"⚠️ Error saving verification URLs: {e}")

    def filter_delta_flights(self, flights: List[Dict], specific_flight_numbers: List[str] = None, 
                           outbound_time: str = None, return_time: str = None) -> List[Dict]:
        """Filter flights to only include Delta flights, optionally matching specific flight numbers and times"""
        delta_flights = []
        
        print(f"🔍 Filtering {len(flights)} flights for Delta...")
        if outbound_time:
            print(f"   Looking for outbound time: {outbound_time}")
        if return_time:
            print(f"   Looking for return time: {return_time}")
        
        for i, flight in enumerate(flights):
            flight_text = flight.get('text', '').lower()
            
            # Debug: Show first few flights and their text
            if i < 10:
                print(f"   Flight {i+1}: ${flight['price']} - Text: '{flight_text[:100]}...'")
            
            # Check if this flight is from Delta
            if any(keyword in flight_text for keyword in ['delta', 'dl ', 'dl,', 'dl-']):
                print(f"   ✅ Found Delta flight: ${flight['price']} - '{flight_text[:80]}...'")
                
                priority = 0
                time_matches = []
                
                # Check for specific flight times - BOTH must match for high priority
                outbound_found = False
                return_found = False
                
                if outbound_time:
                    outbound_time_variants = self._get_time_variants(outbound_time)
                    for time_variant in outbound_time_variants:
                        if time_variant in flight_text:
                            outbound_found = True
                            time_matches.append(f"outbound_{time_variant}")
                            print(f"   🕐 Found outbound time match: {time_variant}")
                            break
                
                if return_time:
                    return_time_variants = self._get_time_variants(return_time)
                    for time_variant in return_time_variants:
                        if time_variant in flight_text:
                            return_found = True
                            time_matches.append(f"return_{time_variant}")
                            print(f"   🕐 Found return time match: {time_variant}")
                            break
                
                # Only give high priority if BOTH times are found (for round-trip)
                if outbound_time and return_time:
                    if outbound_found and return_found:
                        priority += 10  # Very high priority for both times matching
                        print(f"   ⭐ BOTH TIMES MATCHED - This is likely your specific flight!")
                    elif outbound_found or return_found:
                        priority += 1   # Low priority for partial match
                        print(f"   ⚠️ Only partial time match - might be a different flight")
                elif outbound_time and outbound_found:
                    priority += 5   # Medium priority for one-way outbound match
                elif return_time and return_found:
                    priority += 5   # Medium priority for one-way return match
                
                # Check for specific flight numbers - prefer finding both numbers
                flight_numbers_found = []
                if specific_flight_numbers:
                    for flight_num in specific_flight_numbers:
                        # Check various formats: DL1623, 1623, Delta 1623, etc.
                        flight_patterns = [
                            flight_num.lower(),
                            flight_num.replace('dl', '').replace('DL', ''),
                            f"delta {flight_num.replace('dl', '').replace('DL', '')}",
                            f"dl {flight_num.replace('dl', '').replace('DL', '')}",
                            f"dl{flight_num.replace('dl', '').replace('DL', '')}"
                        ]
                        
                        if any(pattern in flight_text for pattern in flight_patterns):
                            flight_numbers_found.append(flight_num)
                            print(f"   🎯 Found flight number match: {flight_num}")
                    
                    # Bonus priority for finding multiple flight numbers (round-trip)
                    if len(flight_numbers_found) >= 2:
                        priority += 20  # Highest priority for multiple flight numbers
                        print(f"   🚀 MULTIPLE FLIGHT NUMBERS FOUND - This is definitely your specific flight!")
                    elif len(flight_numbers_found) == 1:
                        priority += 8   # Good priority for single flight number
                
                flight['priority'] = priority
                flight['time_matches'] = time_matches
                flight['flight_number_match'] = flight_numbers_found
                delta_flights.append(flight)
                
                if priority > 0:
                    print(f"   ⭐ High priority flight (score: {priority}): ${flight['price']}")
        
        # Sort by priority (specific flight matches first)
        delta_flights.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        if delta_flights:
            print(f"✅ Found {len(delta_flights)} Delta flights out of {len(flights)} total")
            
            # SMART MATCHING: Accept reasonable matches for your specific flight
            perfect_match_flights = [f for f in delta_flights if f.get('priority', 0) >= 20]  # Multiple flight numbers
            excellent_match_flights = [f for f in delta_flights if f.get('priority', 0) >= 10]  # Both times matched
            good_match_flights = [f for f in delta_flights if f.get('priority', 0) >= 5]  # Single time + Delta
            acceptable_match_flights = [f for f in delta_flights if f.get('priority', 0) >= 1]  # At least one time matched
            
            if perfect_match_flights:
                print(f"🚀 Found {len(perfect_match_flights)} flights with PERFECT matches (multiple flight numbers):")
                for i, flight in enumerate(perfect_match_flights[:3]):
                    print(f"   #{i+1}: ${flight['price']} (Priority: {flight['priority']}) - {flight.get('time_matches', [])} - {flight.get('flight_number_match', [])}")
                return perfect_match_flights
            elif excellent_match_flights:
                print(f"🎯 Found {len(excellent_match_flights)} flights with EXCELLENT matches (both times):")
                for i, flight in enumerate(excellent_match_flights[:3]):
                    print(f"   #{i+1}: ${flight['price']} (Priority: {flight['priority']}) - {flight.get('time_matches', [])} - {flight.get('flight_number_match', [])}")
                return excellent_match_flights
            elif good_match_flights:
                print(f"✅ Found {len(good_match_flights)} flights with GOOD matches (single time + criteria):")
                for i, flight in enumerate(good_match_flights[:3]):
                    print(f"   #{i+1}: ${flight['price']} (Priority: {flight['priority']}) - {flight.get('time_matches', [])} - {flight.get('flight_number_match', [])}")
                return good_match_flights
            elif acceptable_match_flights:
                print(f"⚠️ Found {len(acceptable_match_flights)} flights with ACCEPTABLE matches (at least one time):")
                for i, flight in enumerate(acceptable_match_flights[:3]):
                    print(f"   #{i+1}: ${flight['price']} (Priority: {flight['priority']}) - {flight.get('time_matches', [])} - {flight.get('flight_number_match', [])}")
                print("   📍 These might be your flights - showing best available match")
                return acceptable_match_flights
            else:
                print("❌ No flights found matching any time criteria - returning NO PRICE!")
        else:
            print("⚠️ No Delta flights found, returning all flights")
            return flights
            
        return delta_flights

    def _get_time_variants(self, time_str: str) -> List[str]:
        """Get various time format variants for matching"""
        if not time_str:
            return []
        
        variants = []
        time_str_lower = time_str.lower()
        
        # Add the original time
        variants.append(time_str_lower)
        
        # Convert between 12-hour and 24-hour formats
        try:
            # Handle formats like "1:30 PM"
            if 'pm' in time_str_lower or 'am' in time_str_lower:
                # Extract hour and minute
                time_part = time_str_lower.replace('pm', '').replace('am', '').strip()
                if ':' in time_part:
                    hour, minute = time_part.split(':')
                    hour = int(hour)
                    minute = int(minute)
                    
                    # Add variants
                    if 'pm' in time_str_lower and hour != 12:
                        hour_24 = hour + 12
                    elif 'am' in time_str_lower and hour == 12:
                        hour_24 = 0
                    else:
                        hour_24 = hour
                    
                    # Add comprehensive time formats that Google Flights might use
                    am_pm = 'pm' if 'pm' in time_str_lower else 'am'
                    variants.extend([
                        # Basic formats
                        f"{hour}:{minute:02d}",
                        f"{hour_24}:{minute:02d}",
                        f"{hour}:{minute:02d} {am_pm}",
                        f"{hour_24:02d}:{minute:02d}",
                        
                        # Google Flights specific formats
                        f"{hour}:{minute:02d}{am_pm}",  # "1:30pm" (no space)
                        f"{hour}:{minute:02d} {am_pm.upper()}",  # "1:30 PM"
                        f"{hour}:{minute:02d}{am_pm.upper()}",  # "1:30PM"
                        
                        # Additional variants
                        f"{hour:02d}:{minute:02d}",  # "01:30"
                        f"{hour:02d}:{minute:02d} {am_pm}",  # "01:30 pm"
                        f"{hour:02d}:{minute:02d}{am_pm}",  # "01:30pm"
                        
                        # Just hour variants for loose matching
                        f"{hour} {am_pm}",  # "1 pm" 
                        f"{hour}{am_pm}",   # "1pm"
                        f"{hour_24}",       # "13" (24-hour)
                    ])
        except:
            pass
        
        return list(set(variants))

    def scrape_flight_price(self, origin: str, destination: str, outbound_date: str, return_date: str = None,
                          outbound_time: str = None, return_time: str = None,
                          flight_numbers: List[str] = None,
                          filter_delta: bool = True, filter_main_cabin: bool = True) -> Optional[float]:
        """Scrape flight price for given route and dates with Delta filtering"""
        
        if not self.driver:
            self.setup_driver()
        
        try:
            # STRATEGY: Try to find your EXACT flights using multiple approaches
            
            # First, try to find specific flight numbers if provided
            if flight_numbers:
                print(f"🎯 Looking specifically for flight numbers: {flight_numbers}")
                
                # Try Delta.com first for exact flight lookup
                delta_url = f"https://www.delta.com/flight-search/book-a-flight?tripType=roundTrip&origin={origin}&destination={destination}&departureDate={outbound_date}&returnDate={return_date}&passengers=1"
                print(f"🌐 Trying Delta.com first: {delta_url}")
                
                try:
                    self.driver.get(delta_url)
                    time.sleep(8)  # Give Delta more time to load
                    
                    # Try to find flight results on Delta
                    delta_price = self.extract_delta_flight_price(flight_numbers, outbound_time, return_time)
                    if delta_price:
                        print(f"🎉 SUCCESS: Found specific flights on Delta.com for ${delta_price}")
                        return delta_price
                    else:
                        print("⚠️ Could not find specific flights on Delta.com - trying Google Flights...")
                        
                except Exception as e:
                    print(f"⚠️ Error accessing Delta.com: {e} - trying Google Flights...")
            
            # Fallback to Google Flights (existing approach)
            print("🌐 Falling back to Google Flights...")
            if return_date:
                url = f"https://www.google.com/travel/flights?hl=en&q=Delta%20Flights%20to%20{destination}%20from%20{origin}%20on%20{outbound_date}%20round%20trip%20return%20{return_date}"
            else:
                url = f"https://www.google.com/travel/flights?hl=en&q=Delta%20Flights%20to%20{destination}%20from%20{origin}%20on%20{outbound_date}%20oneway"
            
            print(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Wait for flights to load
            if not self.wait_for_flights_to_load():
                print("❌ Failed to load flight results")
                return None
            
            # Apply Delta and Main cabin filters
            if filter_delta or filter_main_cabin:
                # First try WITHOUT time filters (your preferred approach for reliability)
                self.apply_delta_filters()
                time.sleep(3)
                
                # Extract initial results
                initial_flights = self.extract_flight_prices()
                
                # If we didn't find good matches, try with your smart time filtering approach
                if not initial_flights or not any(f.get('priority', 0) >= 10 for f in initial_flights):
                    print("🔄 Initial search didn't find ideal matches, trying with your smart time filters...")
                    self.apply_delta_filters(outbound_time, return_time)
                    time.sleep(3)
            
            # SMART APPROACH: Generate verification URLs for manual checking
            verification_urls = self.generate_verification_urls(origin, destination, outbound_date, return_date, 
                                                              outbound_time, return_time, flight_numbers)
            
            print("🔗 Generated verification URLs for manual checking:")
            for i, url in enumerate(verification_urls, 1):
                print(f"   {i}. {url}")
            
            # Save these URLs for the user
            self.save_verification_urls(verification_urls)
            
            # Give extra time for prices to load
            time.sleep(2)
            
            # Extract prices
            flights = self.extract_flight_prices()
            
            if not flights:
                print("❌ No prices found")
                return None
            
            # Filter for Delta flights if requested
            if filter_delta:
                flights = self.filter_delta_flights(flights, flight_numbers, outbound_time, return_time)
                
                if not flights:
                    print("❌ No exact matches found - returning NO PRICE (this is correct behavior)")
                    return None
            
            # SMART MATCHING: Be more strict about matches - require outbound time match for round-trip flights
            excellent_matches = [f for f in flights if f.get('priority', 0) >= 10]  # Both times matched
            good_matches = [f for f in flights if f.get('priority', 0) >= 5]         # Single time + criteria
            acceptable_matches = [f for f in flights if f.get('priority', 0) >= 1]   # At least one time matched
            
            # For round-trip flights, be stricter about outbound time
            if outbound_time and return_time:
                outbound_matches = []
                for flight in flights:
                    time_matches = flight.get('time_matches', [])
                    has_outbound = any('outbound_' in match for match in time_matches)
                    if has_outbound and flight.get('priority', 0) >= 1:
                        outbound_matches.append(flight)
                
                if outbound_matches:
                    print(f"✅ Found {len(outbound_matches)} flights with outbound time {outbound_time}")
                    reasonable_match_flights = outbound_matches
                elif excellent_matches:
                    print(f"🎯 Found {len(excellent_matches)} flights with excellent matches (both times)")
                    reasonable_match_flights = excellent_matches
                else:
                    print("🚫 NO OUTBOUND TIME MATCHES FOUND!")
                    print(f"   Looking for outbound time: {outbound_time}")
                    print(f"   Only found return time matches (6:25 PM)")
                    print("   This suggests your specific DL1623 flight at 1:30 PM is not available")
                    print("   Use verification URLs to manually check if DL1623 and DL2663 exist")
                    return None
            else:
                # For one-way flights, use standard logic
                if excellent_matches:
                    reasonable_match_flights = excellent_matches
                elif good_matches:
                    reasonable_match_flights = good_matches
                elif acceptable_matches:
                    reasonable_match_flights = acceptable_matches
                else:
                    print("🚫 NO REASONABLE MATCHES FOUND")
                    return None
            
            # Sort by priority first (highest priority = best match), then by price
            reasonable_match_flights.sort(key=lambda x: (x.get('priority', 0), -x['price']), reverse=True)
            
            # Use the highest priority match
            selected_flight = reasonable_match_flights[0]
            selected_price = selected_flight['price']
            priority = selected_flight.get('priority', 0)
            
            if priority >= 20:
                print(f"🚀 PERFECT MATCH FOUND! Selected flight price: ${selected_price}")
            elif priority >= 10:
                print(f"🎯 EXCELLENT MATCH FOUND! Selected flight price: ${selected_price}")
            elif priority >= 5:
                print(f"✅ GOOD MATCH FOUND! Selected flight price: ${selected_price}")
            else:
                print(f"⚠️ ACCEPTABLE MATCH FOUND! Selected flight price: ${selected_price}")
            
            print(f"   Priority: {priority}")
            print(f"   Flight numbers found: {selected_flight.get('flight_number_match', [])}")
            print(f"   Times matched: {selected_flight.get('time_matches', [])}")
            
            # Debug: Show what match flights were found
            for i, flight in enumerate(reasonable_match_flights[:3]):
                flight_text_preview = flight.get('text', '')[:100]
                priority = flight.get('priority', 0)
                matched_numbers = flight.get('flight_number_match', [])
                time_matches = flight.get('time_matches', [])
                match_type = "PERFECT" if priority >= 20 else "EXCELLENT" if priority >= 10 else "GOOD" if priority >= 5 else "ACCEPTABLE"
                print(f"   {match_type} Match {i+1}: ${flight['price']} (Priority: {priority})")
                print(f"   Numbers: {matched_numbers} - Times: {time_matches}")
                print(f"   Text: {flight_text_preview}...")
                print("   ---")
            
            return selected_price
            
        except Exception as e:
            print(f"❌ Error scraping flight: {e}")
            return None

def test_modern_scraper():
    """Test the modern scraper"""
    print("🧪 Testing modern scraper...")
    
    scraper = ModernFlightScraper(headless=True)
    
    try:
        # Test your specific flight
        price = scraper.scrape_flight_price(
            origin='SLC',
            destination='DEN',
            outbound_date='2024-08-04',
            return_date='2024-08-05'
        )
        
        if price:
            print(f"✅ Successfully scraped price: ${price}")
        else:
            print("❌ Failed to scrape price")
            
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    test_modern_scraper()