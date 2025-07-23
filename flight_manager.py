#!/usr/bin/env python3
"""
Flight Manager - Easy interface for adding/removing flights
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

class FlightManager:
    """Easy flight management interface"""
    
    def __init__(self, config_file: str = "flight_config.json"):
        self.config_file = config_file
        self.config = self.load_or_create_config()
    
    def load_or_create_config(self) -> Dict:
        """Load existing config or create new one"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Create default config
        return {
            "flights": [],
            "notification_settings": {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "",
                    "sender_password": "",
                    "recipient_email": ""
                },
                "console": {
                    "enabled": True,
                    "log_level": "INFO"
                }
            },
            "scraping_settings": {
                "headless": True,
                "timeout_seconds": 30,
                "retry_attempts": 3,
                "delay_between_requests": 2
            }
        }
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2, default=str)
    
    def add_flight(self, 
                   origin: str, 
                   destination: str, 
                   outbound_date: str,
                   return_date: str = None,
                   outbound_time: str = None,
                   return_time: str = None,
                   original_price: float = None,
                   description: str = None,
                   airline: str = None,
                   flight_numbers: List[str] = None,
                   monitoring_enabled: bool = True,
                   frequency_hours: int = 6) -> str:
        """Add a new flight to monitor"""
        
        # Generate unique ID
        flight_id = f"flight_{uuid.uuid4().hex[:8]}"
        
        # Determine flight type
        flight_type = "round-trip" if return_date else "one-way"
        
        # Generate description if not provided
        if not description:
            if return_date:
                outbound_desc = f"{outbound_date}"
                if outbound_time:
                    outbound_desc += f" at {outbound_time}"
                return_desc = f"{return_date}"
                if return_time:
                    return_desc += f" at {return_time}"
                description = f"{origin} to {destination} Round Trip ({outbound_desc} - {return_desc})"
            else:
                flight_desc = f"{outbound_date}"
                if outbound_time:
                    flight_desc += f" at {outbound_time}"
                description = f"{origin} to {destination} One Way ({flight_desc})"
        
        # Create flight object
        flight = {
            "id": flight_id,
            "description": description,
            "type": flight_type,
            "origin": origin,
            "destination": destination,
            "outbound_date": outbound_date,
            "original_price": original_price or 0.0,
            "current_price": original_price or 0.0,
            "notifications": {
                "email": True,
                "console": True,
                "price_decrease_threshold": 0.05,
                "price_increase_threshold": 0.10
            },
            "monitoring": {
                "enabled": monitoring_enabled,
                "frequency_hours": frequency_hours,
                "last_checked": None,
                "price_history": []
            }
        }
        
        # Add optional fields
        if return_date:
            flight["return_date"] = return_date
        if outbound_time:
            flight["outbound_time"] = outbound_time
        if return_time:
            flight["return_time"] = return_time
        if airline:
            flight["airline"] = airline
        if flight_numbers:
            flight["flight_numbers"] = flight_numbers
        
        # Add to config
        self.config["flights"].append(flight)
        self.save_config()
        
        # Send confirmation email
        try:
            from flight_monitor import FlightMonitor
            monitor = FlightMonitor(self.config_file)
            monitor.send_confirmation_email(flight)
        except Exception as e:
            print(f"Warning: Could not send confirmation email: {str(e)}")
        
        return flight_id
    
    def remove_flight(self, flight_id: str) -> bool:
        """Remove a flight from monitoring"""
        original_count = len(self.config["flights"])
        self.config["flights"] = [f for f in self.config["flights"] if f["id"] != flight_id]
        
        if len(self.config["flights"]) < original_count:
            self.save_config()
            return True
        return False
    
    def list_flights(self) -> List[Dict]:
        """List all flights"""
        return self.config["flights"]
    
    def get_flight(self, flight_id: str) -> Optional[Dict]:
        """Get a specific flight"""
        return next((f for f in self.config["flights"] if f["id"] == flight_id), None)
    
    def update_flight(self, flight_id: str, **kwargs) -> bool:
        """Update flight properties"""
        flight = self.get_flight(flight_id)
        if not flight:
            return False
        
        # Update allowed fields
        allowed_fields = [
            'description', 'original_price', 'current_price', 'airline', 
            'flight_numbers', 'monitoring', 'notifications'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                flight[key] = value
        
        self.save_config()
        return True
    
    def enable_monitoring(self, flight_id: str) -> bool:
        """Enable monitoring for a flight"""
        flight = self.get_flight(flight_id)
        if flight:
            flight["monitoring"]["enabled"] = True
            self.save_config()
            return True
        return False
    
    def disable_monitoring(self, flight_id: str) -> bool:
        """Disable monitoring for a flight"""
        flight = self.get_flight(flight_id)
        if flight:
            flight["monitoring"]["enabled"] = False
            self.save_config()
            return True
        return False
    
    def get_active_flights(self) -> List[Dict]:
        """Get all flights with monitoring enabled"""
        return [f for f in self.config["flights"] if f["monitoring"]["enabled"]]
    
    def print_flight_summary(self):
        """Print a summary of all flights"""
        flights = self.list_flights()
        
        if not flights:
            print("📋 No flights configured yet.")
            print("\nTo add a flight, use:")
            print("  python3 flight_manager.py add JFK LAX 2024-12-01 2024-12-08")
            return
        
        print(f"📋 Flight Monitor Summary ({len(flights)} flights)")
        print("=" * 60)
        
        for i, flight in enumerate(flights, 1):
            status = "🟢 Active" if flight["monitoring"]["enabled"] else "🔴 Disabled"
            
            print(f"\n{i}. {flight['description']}")
            print(f"   ID: {flight['id']}")
            print(f"   Route: {flight['origin']} → {flight['destination']}")
            print(f"   Date: {flight['outbound_date']}", end="")
            
            if flight.get('return_date'):
                print(f" → {flight['return_date']}")
            else:
                print()
            
            print(f"   Price: ${flight.get('original_price', 0):.2f} → ${flight.get('current_price', 0):.2f}")
            print(f"   Status: {status}")
            
            if flight["monitoring"]["last_checked"]:
                last_checked = datetime.fromisoformat(flight["monitoring"]["last_checked"])
                print(f"   Last Checked: {last_checked.strftime('%Y-%m-%d %H:%M:%S')}")
            
            price_history = flight["monitoring"].get("price_history", [])
            if price_history:
                print(f"   Price History: {len(price_history)} data points")

def interactive_add_flight():
    """Interactive flight addition"""
    print("✈️  Add New Flight to Monitor")
    print("=" * 30)
    
    # Get flight details
    origin = input("Origin airport (e.g., JFK, LAX, SLC): ").strip().upper()
    destination = input("Destination airport (e.g., DEN, NYC, SFO): ").strip().upper()
    outbound_date = input("Outbound date (YYYY-MM-DD): ").strip()
    
    return_date = input("Return date (YYYY-MM-DD, or press Enter for one-way): ").strip()
    if not return_date:
        return_date = None
    
    # Optional details
    print("\nOptional details (press Enter to skip):")
    description = input("Description: ").strip()
    airline = input("Airline (e.g., Delta, American): ").strip()
    
    try:
        original_price = input("Original price ($): ").strip()
        original_price = float(original_price) if original_price else None
    except ValueError:
        original_price = None
    
    # Add flight
    manager = FlightManager()
    flight_id = manager.add_flight(
        origin=origin,
        destination=destination,
        outbound_date=outbound_date,
        return_date=return_date,
        original_price=original_price,
        description=description if description else None,
        airline=airline if airline else None
    )
    
    print(f"\n✅ Flight added successfully!")
    print(f"   ID: {flight_id}")
    print(f"   Route: {origin} → {destination}")
    print(f"   Monitoring: Enabled")
    
    return flight_id

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flight Manager - Manage monitored flights')
    parser.add_argument('action', choices=['add', 'remove', 'list', 'enable', 'disable', 'interactive'], 
                       help='Action to perform')
    parser.add_argument('args', nargs='*', help='Action arguments')
    
    args = parser.parse_args()
    manager = FlightManager()
    
    if args.action == 'add':
        if len(args.args) < 3:
            print("❌ Usage: python3 flight_manager.py add ORIGIN DEST OUTBOUND_DATE [RETURN_DATE] [PRICE]")
            print("   Example: python3 flight_manager.py add JFK LAX 2024-12-01 2024-12-08 450")
            sys.exit(1)
        
        origin = args.args[0].upper()
        destination = args.args[1].upper()
        outbound_date = args.args[2]
        return_date = args.args[3] if len(args.args) > 3 else None
        
        try:
            original_price = float(args.args[4]) if len(args.args) > 4 else None
        except (ValueError, IndexError):
            original_price = None
        
        flight_id = manager.add_flight(
            origin=origin,
            destination=destination,
            outbound_date=outbound_date,
            return_date=return_date,
            original_price=original_price
        )
        
        print(f"✅ Flight added: {flight_id}")
        print(f"   Route: {origin} → {destination}")
        print(f"   Date: {outbound_date}" + (f" → {return_date}" if return_date else ""))
        
    elif args.action == 'remove':
        if len(args.args) < 1:
            print("❌ Usage: python3 flight_manager.py remove FLIGHT_ID")
            sys.exit(1)
        
        flight_id = args.args[0]
        if manager.remove_flight(flight_id):
            print(f"✅ Flight removed: {flight_id}")
        else:
            print(f"❌ Flight not found: {flight_id}")
    
    elif args.action == 'list':
        manager.print_flight_summary()
    
    elif args.action == 'enable':
        if len(args.args) < 1:
            print("❌ Usage: python3 flight_manager.py enable FLIGHT_ID")
            sys.exit(1)
        
        flight_id = args.args[0]
        if manager.enable_monitoring(flight_id):
            print(f"✅ Monitoring enabled for: {flight_id}")
        else:
            print(f"❌ Flight not found: {flight_id}")
    
    elif args.action == 'disable':
        if len(args.args) < 1:
            print("❌ Usage: python3 flight_manager.py disable FLIGHT_ID")
            sys.exit(1)
        
        flight_id = args.args[0]
        if manager.disable_monitoring(flight_id):
            print(f"✅ Monitoring disabled for: {flight_id}")
        else:
            print(f"❌ Flight not found: {flight_id}")
    
    elif args.action == 'interactive':
        interactive_add_flight()

if __name__ == "__main__":
    main()