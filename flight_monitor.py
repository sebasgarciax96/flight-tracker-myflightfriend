#!/usr/bin/env python3
"""
Flight Price Monitor
Built on top of google-flight-analysis

Monitors flight prices and sends notifications when prices change
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add the src directory to path
sys.path.append('src')

# Import the modern scraper
from modern_scraper import ModernFlightScraper

@dataclass
class PriceAlert:
    """Data class for price alerts"""
    flight_id: str
    old_price: float
    new_price: float
    change_percent: float
    timestamp: datetime
    alert_type: str  # 'decrease', 'increase', 'significant_change'

class FlightMonitor:
    """Main class for monitoring flight prices"""
    
    def __init__(self, config_file: str = "flight_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file {self.config_file}")
    
    def save_config(self):
        """Save configuration back to JSON file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['notification_settings']['console']['log_level'])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('flight_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_current_price(self, flight_config: Dict) -> Optional[float]:
        """Scrape current price for a flight using modern scraper"""
        try:
            self.logger.info(f"Scraping price for flight {flight_config['id']}")
            
            # Add delay to be respectful to Google
            time.sleep(self.config['scraping_settings']['delay_between_requests'])
            
            # Create modern scraper instance
            scraper = ModernFlightScraper(
                headless=self.config['scraping_settings']['headless'],
                timeout=self.config['scraping_settings']['timeout_seconds']
            )
            
            try:
                # Scrape based on flight type with Delta filtering
                if flight_config['type'] == 'round-trip':
                    price = scraper.scrape_flight_price(
                        origin=flight_config['origin'],
                        destination=flight_config['destination'],
                        outbound_date=flight_config['outbound_date'],
                        return_date=flight_config['return_date'],
                        outbound_time=flight_config.get('outbound_time'),
                        return_time=flight_config.get('return_time'),
                        flight_numbers=flight_config.get('flight_numbers'),
                        filter_delta=True,
                        filter_main_cabin=True
                    )
                else:  # one-way
                    price = scraper.scrape_flight_price(
                        origin=flight_config['origin'],
                        destination=flight_config['destination'],
                        outbound_date=flight_config['outbound_date'],
                        outbound_time=flight_config.get('outbound_time'),
                        flight_numbers=flight_config.get('flight_numbers'),
                        filter_delta=True,
                        filter_main_cabin=True
                    )
                
                if price:
                    self.logger.info(f"Found price: ${price}")
                    return float(price)
                else:
                    self.logger.warning(f"No price data found for flight {flight_config['id']} - this likely means your specific flights (DL1623 at 1:30 PM, DL2663 at 6:25 PM) are not available on the search dates")
                    return None
                    
            finally:
                scraper.close_driver()
                
        except Exception as e:
            self.logger.error(f"Error scraping price for flight {flight_config['id']}: {str(e)}")
            return None
    
    def calculate_price_change(self, old_price: float, new_price: float) -> Tuple[float, str]:
        """Calculate price change percentage and determine alert type"""
        if old_price == 0:
            return 0.0, 'no_change'
        
        change_percent = ((new_price - old_price) / old_price) * 100
        
        if change_percent <= -5:  # 5% or more decrease
            return change_percent, 'decrease'
        elif change_percent >= 10:  # 10% or more increase
            return change_percent, 'increase'
        elif abs(change_percent) >= 3:  # 3% or more change in either direction
            return change_percent, 'significant_change'
        else:
            return change_percent, 'no_change'
    
    def should_send_alert(self, flight_config: Dict, change_percent: float, alert_type: str) -> bool:
        """Determine if an alert should be sent based on thresholds"""
        notifications = flight_config.get('notifications', {})
        
        if alert_type == 'decrease':
            threshold = notifications.get('price_decrease_threshold', 0.05) * 100
            return abs(change_percent) >= threshold
        elif alert_type == 'increase':
            threshold = notifications.get('price_increase_threshold', 0.10) * 100
            return change_percent >= threshold
        elif alert_type == 'significant_change':
            return True
        
        return False
    
    def send_console_notification(self, alert: PriceAlert):
        """Send enhanced console notification with verification instructions"""
        if not self.config['notification_settings']['console']['enabled']:
            return
            
        flight = next((f for f in self.config['flights'] if f['id'] == alert.flight_id), None)
        if not flight:
            return
            
        symbol = "📉" if alert.alert_type == 'decrease' else "📈" if alert.alert_type == 'increase' else "🔔"
        
        message = f"""
{symbol} SMART FLIGHT PRICE ALERT {symbol}
Flight: {flight['description']}
Route: {flight['origin']} → {flight['destination']}
Date: {flight['outbound_date']} - {flight.get('return_date', 'N/A')}
Target Times: {flight.get('outbound_time', 'Any')} departure, {flight.get('return_time', 'Any')} return
Target Flights: {', '.join(flight.get('flight_numbers', []))}

DELTA MARKET PRICE CHANGE:
Original Price: ${flight['original_price']:.2f}
Previous Price: ${alert.old_price:.2f}
Current Price: ${alert.new_price:.2f}
Change: {alert.change_percent:+.1f}%
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if alert.alert_type == 'decrease':
            message += f"\n🎯 ACTION REQUIRED: Market dropped ${alert.old_price - alert.new_price:.2f}!\n"
            message += f"Your specific DL1623/DL2663 flights may also be cheaper.\n"
            message += f"Check these URLs immediately:\n"
        elif alert.alert_type == 'increase':
            message += f"\n⚠️  Market increased by ${alert.new_price - alert.old_price:.2f}\n"
            message += f"Your specific flights may be more expensive.\n"
            message += f"Monitor these URLs:\n"

        # Add verification URLs
        origin = flight['origin']
        destination = flight['destination']
        outbound_date = flight['outbound_date'] 
        return_date = flight.get('return_date')
        
        verification_urls = [
            f"1. Google Flights: https://www.google.com/travel/flights?hl=en-US&curr=USD#flt={origin}.{destination}.{outbound_date}*{destination}.{origin}.{return_date}",
            f"2. Delta.com: https://www.delta.com/flight-search/book-a-flight?tripType=roundTrip&fromAirportCode={origin}&toAirportCode={destination}&departureDate={outbound_date}&returnDate={return_date}&adultCount=1"
        ]
        
        for url in verification_urls:
            message += f"\n{url}"
            
        message += f"\n\n💡 Look specifically for DL1623 (1:30 PM) and DL2663 (6:25 PM)"
            
        print(message)
        self.logger.info(f"Enhanced console notification sent for flight {alert.flight_id}")
    
    def send_confirmation_email(self, flight_config: Dict):
        """Send confirmation email when flight is added for tracking"""
        email_config = self.config['notification_settings']['email']
        if not email_config['enabled']:
            return
        
        try:
            subject = f"✅ Flight Tracking Confirmed - {flight_config['origin']} to {flight_config['destination']}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">🎯 Flight Tracking Confirmed!</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">We're now monitoring your flight for price drops</p>
                    </div>
                    
                    <!-- Flight Details -->
                    <div style="padding: 30px;">
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                            <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">📋 Flight Details Being Monitored</h2>
                            <div style="color: #666; line-height: 1.8; font-size: 15px;">
                                <strong style="color: #333;">Route:</strong> {flight_config['origin']} → {flight_config['destination']}<br>
                                <strong style="color: #333;">Departure:</strong> {flight_config['outbound_date']}{' at ' + flight_config['outbound_time'] if flight_config.get('outbound_time') else ''}<br>
                                {f"<strong style='color: #333;'>Return:</strong> {flight_config['return_date']}{' at ' + flight_config['return_time'] if flight_config.get('return_time') else ''}<br>" if flight_config.get('return_date') else ''}
                                {f"<strong style='color: #333;'>Flight Numbers:</strong> {', '.join(flight_config['flight_numbers'])}<br>" if flight_config.get('flight_numbers') else ''}
                                <strong style="color: #333;">Original Price:</strong> <span style="font-size: 18px; color: #dc3545; font-weight: bold;">${flight_config['original_price']:.2f}</span>
                            </div>
                        </div>
                        
                        <!-- What Happens Next -->
                        <div style="background-color: #e3f2fd; border: 1px solid #90caf9; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                            <h2 style="color: #1565c0; margin: 0 0 15px 0; font-size: 18px;">🔄 What Happens Next</h2>
                            <ul style="color: #1565c0; margin: 0; padding-left: 20px; line-height: 1.6;">
                                <li>We'll check your flight price every 6 hours</li>
                                <li>You'll get an email alert if the price drops below ${flight_config['original_price']:.2f}</li>
                                <li>Each alert includes a ready-to-use message for claiming credits from Delta</li>
                                <li>After your flight date, we'll send a final summary</li>
                            </ul>
                        </div>
                        
                        <!-- Footer -->
                        <div style="border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #666; font-size: 12px;">
                            <p>Flight tracking started on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                            <p>Monitoring will continue until {flight_config.get('return_date', flight_config['outbound_date'])}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"Flight tracking confirmation email sent for flight {flight_config['id']}")
            
        except Exception as e:
            self.logger.error(f"Error sending confirmation email: {str(e)}")
    
    def send_email_notification(self, alert: PriceAlert):
        """Send email notification for price drops"""
        email_config = self.config['notification_settings']['email']
        if not email_config['enabled']:
            return
        
        # Only send emails for price decreases below original purchase
        if alert.alert_type != 'decrease' or alert.new_price >= alert.old_price:
            return
        
        # Get flight details
        flight_config = None
        for flight in self.config['flights']:
            if flight['id'] == alert.flight_id:
                flight_config = flight
                break
        
        if not flight_config:
            return
        
        try:
            # Create email content
            subject = f"✈️ Delta Price Drop Alert - Save ${(alert.old_price - alert.new_price):.2f}!"
            
            # Generate verification URL
            from modern_scraper import ModernFlightScraper
            scraper = ModernFlightScraper()
            verification_urls = scraper.generate_verification_urls(
                origin=flight_config['origin'],
                destination=flight_config['destination'],
                outbound_date=flight_config['outbound_date'],
                return_date=flight_config.get('return_date'),
                outbound_time=flight_config.get('outbound_time'),
                return_time=flight_config.get('return_time'),
                flight_numbers=flight_config.get('flight_numbers')
            )
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">🎉 Price Drop Alert!</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your Delta flight price has dropped below your original purchase price!</p>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="padding: 30px;">
                        
                        <!-- Flight Details -->
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                            <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">Flight Details</h2>
                            <div style="color: #666; line-height: 1.6;">
                                <strong style="color: #333;">Route:</strong> {flight_config['origin']} → {flight_config['destination']}<br>
                                <strong style="color: #333;">Departure:</strong> {flight_config['outbound_date']}{' at ' + flight_config['outbound_time'] if flight_config.get('outbound_time') else ''}<br>
                                {f"<strong style='color: #333;'>Return:</strong> {flight_config['return_date']}{' at ' + flight_config['return_time'] if flight_config.get('return_time') else ''}<br>" if flight_config.get('return_date') else ''}
                                {f"<strong style='color: #333;'>Flight Numbers:</strong> {', '.join(flight_config['flight_numbers'])}<br>" if flight_config.get('flight_numbers') else ''}
                            </div>
                        </div>
                        
                        <!-- Price Comparison -->
                        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin-bottom: 25px; text-align: center;">
                            <h2 style="color: #155724; margin: 0 0 15px 0; font-size: 18px;">💰 Price Comparison</h2>
                            <div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap;">
                                <div style="margin: 10px;">
                                    <div style="color: #666; font-size: 14px;">Original Purchase</div>
                                    <div style="color: #dc3545; font-size: 24px; font-weight: bold;">${alert.old_price:.2f}</div>
                                </div>
                                <div style="font-size: 30px; color: #28a745;">→</div>
                                <div style="margin: 10px;">
                                    <div style="color: #666; font-size: 14px;">Current Price</div>
                                    <div style="color: #28a745; font-size: 24px; font-weight: bold;">${alert.new_price:.2f}</div>
                                </div>
                            </div>
                            <div style="margin-top: 15px; padding: 10px; background-color: #fff; border-radius: 4px;">
                                <strong style="color: #28a745; font-size: 18px;">You can save ${(alert.old_price - alert.new_price):.2f}!</strong>
                            </div>
                        </div>
                        
                        <!-- Next Steps -->
                        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                            <h2 style="color: #856404; margin: 0 0 15px 0; font-size: 18px;">📞 Next Steps</h2>
                            <p style="color: #856404; margin: 0 0 15px 0;">Contact Delta now to claim your credit for the price difference:</p>
                            
                            <div style="background-color: white; border-radius: 4px; padding: 15px; margin-bottom: 15px;">
                                <strong style="color: #333;">Delta Customer Service:</strong><br>
                                <span style="font-size: 18px; color: #667eea; font-weight: bold;">📱 1-800-221-1212</span>
                            </div>
                            
                            <p style="color: #856404; margin: 0 0 10px 0;"><strong>Copy and paste this message to Delta:</strong></p>
                            <div style="background-color: #f8f9fa; border-left: 4px solid #667eea; padding: 15px; margin: 10px 0; font-family: monospace; font-size: 13px; line-height: 1.4; white-space: pre-line;">{self._generate_delta_message(flight_config, alert)}</div>
                            
                            <div style="margin-top: 15px; padding: 10px; background-color: #fff; border-radius: 4px; border: 1px solid #ffc107;">
                                <p style="margin: 0; color: #856404; font-size: 14px;">💡 <strong>Pro Tip:</strong> Call Delta within 24 hours of booking for the best chance of getting a credit for the difference!</p>
                            </div>
                        </div>
                        
                        <!-- Verification Links -->
                        <div style="margin-bottom: 25px;">
                            <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">🔗 Verify Current Prices</h2>
                            <p style="color: #666; margin: 0 0 15px 0;">Use these links to see current prices (flight details pre-populated):</p>
                            
                            {f'<div style="margin: 10px 0;"><a href="{verification_urls[0]}" style="display: inline-block; background-color: #4285f4; color: white; text-decoration: none; padding: 12px 20px; border-radius: 4px; font-weight: bold;">🌐 Check on Google Flights</a></div>' if verification_urls else ''}
                            
                            {f'<div style="margin: 10px 0;"><a href="{verification_urls[1]}" style="display: inline-block; background-color: #c41230; color: white; text-decoration: none; padding: 12px 20px; border-radius: 4px; font-weight: bold;">✈️ Check on Delta.com</a></div>' if len(verification_urls) > 1 else ''}
                        </div>
                        
                        <!-- Footer -->
                        <div style="border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #666; font-size: 12px;">
                            <p>This alert was sent by your Delta Flight Price Monitor</p>
                            <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            
            # Attach HTML version
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"Price drop email notification sent for flight {alert.flight_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {str(e)}")
            # Still log that we tried to send an email
            self.logger.info(f"Email notification attempted for flight {alert.flight_id} but failed: {str(e)}")
    
    def _generate_delta_message(self, flight_config: Dict, alert: PriceAlert) -> str:
        """Generate a dynamic Delta customer service message based on flight details"""
        try:
            import datetime
            
            # Parse dates
            outbound_date = datetime.datetime.strptime(flight_config['outbound_date'], '%Y-%m-%d')
            return_date = datetime.datetime.strptime(flight_config['return_date'], '%Y-%m-%d')
            
            # Format dates for Delta message
            outbound_day = outbound_date.strftime('%a, %d%b').replace(' 0', ' ')  # Remove leading zero
            return_day = return_date.strftime('%a, %d%b').replace(' 0', ' ')
            
            # Get flight details
            origin_code = flight_config['origin']
            dest_code = flight_config['destination']
            outbound_time = flight_config.get('outbound_time', 'TBD')
            return_time = flight_config.get('return_time', 'TBD')
            
            # Convert to airport names (common ones)
            airport_names = {
                'SLC': 'SALT LAKE CITY',
                'DEN': 'DENVER', 
                'SFO': 'SAN FRANCISCO',
                'LAX': 'LOS ANGELES',
                'ORD': 'CHICAGO',
                'ATL': 'ATLANTA',
                'JFK': 'NEW YORK',
                'LGA': 'NEW YORK',
                'EWR': 'NEWARK',
                'DFW': 'DALLAS',
                'IAH': 'HOUSTON',
                'PHX': 'PHOENIX',
                'LAS': 'LAS VEGAS',
                'SEA': 'SEATTLE',
                'MIA': 'MIAMI',
                'BOS': 'BOSTON',
                'MSP': 'MINNEAPOLIS'
            }
            
            origin_name = airport_names.get(origin_code, origin_code)
            dest_name = airport_names.get(dest_code, dest_code)
            
            # Get flight numbers (if available)
            flight_numbers = flight_config.get('flight_numbers', [])
            outbound_flight = flight_numbers[0] if flight_numbers else 'TBD'
            return_flight = flight_numbers[1] if len(flight_numbers) > 1 else 'TBD'
            
            # Format outbound/return times for Delta format
            def format_time_for_delta(time_str):
                try:
                    if 'PM' in time_str.upper():
                        time_part = time_str.upper().replace('PM', '').strip()
                        return f"{time_part}PM"
                    elif 'AM' in time_str.upper():
                        time_part = time_str.upper().replace('AM', '').strip()  
                        return f"{time_part}AM"
                    return time_str
                except:
                    return time_str
            
            outbound_time_formatted = format_time_for_delta(outbound_time)
            return_time_formatted = format_time_for_delta(return_time)
            
            # Generate message
            message = f"""I would like to receive credits from my Delta ticket purchase.

SkyMiles #: [YOUR_SKYMILES_NUMBER]

{outbound_day.upper()}
DEPART
{outbound_flight.replace('DL', 'DELTA ')}
Delta Main (Q)
{origin_name} to {dest_name}
{outbound_time_formatted}

{return_day.upper()}
DEPART
{return_flight.replace('DL', 'DELTA ')}
Delta Main (V)
{dest_name} to {origin_name}
{return_time_formatted}

- Original Price: ${alert.old_price:.2f}
- Current Price: ${alert.new_price:.2f}
- Booked directly with Delta

Please credit the difference to my account. Thanks!"""
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error generating Delta message: {e}")
            # Fallback to simple message
            return f"""I would like to receive credits from my Delta ticket purchase.

SkyMiles #: [YOUR_SKYMILES_NUMBER]

Flight: {flight_config['origin']} to {flight_config['destination']}
Date: {flight_config['outbound_date']} - {flight_config.get('return_date', 'N/A')}

- Original Price: ${alert.old_price:.2f}
- Current Price: ${alert.new_price:.2f}
- Booked directly with Delta

Please credit the difference to my account. Thanks!"""
    
    def send_post_flight_followup_email(self, flight_config: Dict):
        """Send follow-up email after flight date has passed"""
        email_config = self.config['notification_settings']['email']
        if not email_config['enabled']:
            return
        
        try:
            # Check if this is a round trip or one-way
            flight_date = flight_config.get('return_date', flight_config['outbound_date'])
            
            subject = f"🎉 Flight Complete - You Got the Best Price! Add Another Flight?"
            
            # Calculate savings if any price drops occurred
            price_history = flight_config['monitoring'].get('price_history', [])
            lowest_price = min([p['price'] for p in price_history], default=flight_config['original_price'])
            savings = flight_config['original_price'] - lowest_price if lowest_price < flight_config['original_price'] else 0
            
            # Prepare conditional HTML strings
            savings_div_style = 'background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin-bottom: 25px; text-align: center;' if savings > 0 else 'background-color: #e2e3e5; border: 1px solid #d6d8db; border-radius: 8px; padding: 20px; margin-bottom: 25px; text-align: center;'
            savings_header = '🎯 Congratulations! You Saved Money!' if savings > 0 else '📊 Price Analysis Complete'
            savings_header_color = '#155724' if savings > 0 else '#6c757d'
            
            savings_amount = f"<div style='font-size: 24px; font-weight: bold; color: #28a745;'>You saved ${savings:.2f}!</div>" if savings > 0 else "<div style='font-size: 18px; color: #6c757d;'>You got the best available price!</div>"
            price_drops_count = len([p for p in price_history if p['price'] < flight_config['original_price']])
            savings_details = f"<p style='color: #155724; margin: 10px 0 0 0;'>We found {price_drops_count} price drops during monitoring</p>" if savings > 0 else "<p style='color: #6c757d; margin: 10px 0 0 0;'>No lower prices were found during our monitoring period</p>"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">🛬 Hope You Had a Great Flight!</h1>
                        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your price monitoring has ended</p>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="padding: 30px;">
                        
                        <!-- Flight Summary -->
                        <div style="background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                            <h2 style="color: #333; margin: 0 0 15px 0; font-size: 18px;">✈️ Flight Summary</h2>
                            <div style="color: #666; line-height: 1.6;">
                                <strong style="color: #333;">Route:</strong> {flight_config['origin']} → {flight_config['destination']}<br>
                                <strong style="color: #333;">Travel Date:</strong> {flight_config['outbound_date']}{(" to " + flight_config['return_date']) if flight_config.get('return_date') else ""}<br>
                                <strong style="color: #333;">Original Price:</strong> ${flight_config['original_price']:.2f}<br>
                                <strong style="color: #333;">Lowest Price Found:</strong> ${lowest_price:.2f}
                            </div>
                        </div>
                        
                        <!-- Savings Result -->
                        <div style="{savings_div_style}">
                            <h2 style="color: {savings_header_color}; margin: 0 0 15px 0; font-size: 18px;">{savings_header}</h2>
                            
                            {savings_amount}
                            {savings_details}
                        </div>
                        
                        <!-- Add Another Flight CTA -->
                        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 25px; margin-bottom: 25px; text-align: center;">
                            <h2 style="color: #856404; margin: 0 0 15px 0; font-size: 20px;">✈️ Planning Another Trip?</h2>
                            <p style="color: #856404; margin: 0 0 20px 0; font-size: 16px;">Let us help you get the best price on your next flight too!</p>
                            
                            <a href="https://your-lovable-app.com/add-flight" style="display: inline-block; background-color: #007bff; color: white; text-decoration: none; padding: 15px 30px; border-radius: 6px; font-weight: bold; font-size: 16px; margin: 10px;">📊 Track Another Flight</a>
                        </div>
                        
                        <!-- Stats and Thank You -->
                        <div style="text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                            <h3 style="color: #333; margin: 0 0 10px 0;">Thank You for Using Flight Price Monitor! 🙏</h3>
                            <p style="color: #666; margin: 0; font-size: 14px;">
                                We checked your flight price {len(price_history)} times over {len(price_history) * 6} hours of monitoring
                            </p>
                            <p style="color: #666; margin: 5px 0 0 0; font-size: 12px;">
                                Flight monitoring ended on {datetime.now().strftime("%B %d, %Y")}
                            </p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create and send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg)
            
            self.logger.info(f"Post-flight follow-up email sent for flight {flight_config['id']}")
            
        except Exception as e:
            self.logger.error(f"Error sending post-flight follow-up email: {str(e)}")
    
    def check_for_completed_flights(self):
        """Check for flights that have passed their date and send follow-up emails"""
        current_date = datetime.now().date()
        
        for flight_config in self.config['flights']:
            # Get the end date (return date for round trip, outbound date for one-way)
            end_date_str = flight_config.get('return_date', flight_config['outbound_date'])
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Check if flight has ended and we haven't sent follow-up email yet
            if (current_date > end_date and 
                not flight_config['monitoring'].get('followup_email_sent', False)):
                
                # Send follow-up email
                self.send_post_flight_followup_email(flight_config)
                
                # Mark as sent and disable monitoring
                flight_config['monitoring']['followup_email_sent'] = True
                flight_config['monitoring']['enabled'] = False
                flight_config['monitoring']['completed_date'] = current_date.isoformat()
                
                self.logger.info(f"Flight {flight_config['id']} completed - follow-up email sent and monitoring disabled")
        
        # Save config with updates
        self.save_config()
    
    def update_price_history(self, flight_config: Dict, new_price: float):
        """Update price history for a flight"""
        if 'price_history' not in flight_config['monitoring']:
            flight_config['monitoring']['price_history'] = []
            
        flight_config['monitoring']['price_history'].append({
            'price': new_price,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 100 price points
        if len(flight_config['monitoring']['price_history']) > 100:
            flight_config['monitoring']['price_history'] = flight_config['monitoring']['price_history'][-100:]
        
        # Update current price and last checked time
        flight_config['current_price'] = new_price
        flight_config['monitoring']['last_checked'] = datetime.now().isoformat()
    
    def monitor_flight(self, flight_config: Dict) -> Optional[PriceAlert]:
        """Monitor a single flight and return alert if needed"""
        if not flight_config['monitoring']['enabled']:
            return None
            
        # Check if it's time to monitor this flight
        last_checked = flight_config['monitoring'].get('last_checked')
        if last_checked:
            last_checked_time = datetime.fromisoformat(last_checked)
            frequency_hours = flight_config['monitoring']['frequency_hours']
            if datetime.now() - last_checked_time < timedelta(hours=frequency_hours):
                return None
        
        # Get current price
        current_price = self.get_current_price(flight_config)
        if current_price is None:
            return None
            
        # Compare with previous price
        old_price = flight_config.get('current_price', flight_config['original_price'])
        change_percent, alert_type = self.calculate_price_change(old_price, current_price)
        
        # Update price history
        self.update_price_history(flight_config, current_price)
        
        # Check if we should send an alert
        if self.should_send_alert(flight_config, change_percent, alert_type):
            alert = PriceAlert(
                flight_id=flight_config['id'],
                old_price=old_price,
                new_price=current_price,
                change_percent=change_percent,
                timestamp=datetime.now(),
                alert_type=alert_type
            )
            return alert
            
        return None
    
    def monitor_all_flights(self):
        """Monitor all configured flights"""
        self.logger.info("Starting flight monitoring cycle")
        
        # Check for completed flights first
        self.check_for_completed_flights()
        
        alerts = []
        for flight_config in self.config['flights']:
            try:
                alert = self.monitor_flight(flight_config)
                if alert:
                    alerts.append(alert)
                    
                    # Send notifications
                    self.send_console_notification(alert)
                    self.send_email_notification(alert)
                    
            except Exception as e:
                self.logger.error(f"Error monitoring flight {flight_config['id']}: {str(e)}")
        
        # Save updated configuration
        self.save_config()
        
        self.logger.info(f"Monitoring cycle completed. {len(alerts)} alerts generated.")
        return alerts
    
    def run_once(self):
        """Run monitoring cycle once"""
        return self.monitor_all_flights()
    
    def run_continuous(self, interval_minutes: int = 60):
        """Run monitoring continuously"""
        self.logger.info(f"Starting continuous monitoring every {interval_minutes} minutes")
        
        while True:
            try:
                self.monitor_all_flights()
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous monitoring: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flight Price Monitor')
    parser.add_argument('--config', default='flight_config.json', help='Configuration file path')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in minutes for continuous mode')
    
    args = parser.parse_args()
    
    try:
        monitor = FlightMonitor(args.config)
        
        if args.once:
            alerts = monitor.run_once()
            print(f"Monitoring completed. {len(alerts)} alerts generated.")
        elif args.continuous:
            monitor.run_continuous(args.interval)
        else:
            # Default: run once
            alerts = monitor.run_once()
            print(f"Monitoring completed. {len(alerts)} alerts generated.")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()