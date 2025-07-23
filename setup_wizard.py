#!/usr/bin/env python3
"""
Setup Wizard for Flight Price Monitor
Easy setup for new users with no coding experience
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from flight_manager import FlightManager

def print_banner():
    """Print welcome banner"""
    print("✈️" * 30)
    print("   FLIGHT PRICE MONITOR SETUP")
    print("✈️" * 30)
    print()
    print("Welcome! This wizard will help you set up")
    print("your personal flight price monitor.")
    print()

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking Requirements...")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8+ required. Please upgrade Python.")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor} found")
    
    # Check Chrome
    chrome_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chrome.app/Contents/MacOS/Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser"
    ]
    
    chrome_found = any(os.path.exists(path) for path in chrome_paths)
    if not chrome_found:
        print("❌ Google Chrome not found. Please install Chrome from chrome.google.com")
        return False
    print("✅ Google Chrome found")
    
    # Check required Python packages
    required_packages = ['selenium', 'pandas', 'numpy', 'tqdm']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} not installed")
    
    if missing_packages:
        print(f"\n🔧 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, 
                          check=True, capture_output=True)
            print("✅ All packages installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False
    
    return True

def setup_first_flight():
    """Set up the first flight to monitor"""
    print("\n🛫 Let's add your first flight to monitor!")
    print("=" * 40)
    
    # Get flight details with helpful prompts
    print("Please enter your flight details:")
    print("(You can use 3-letter airport codes like JFK, LAX, SLC, DEN)")
    print()
    
    while True:
        origin = input("✈️  From (origin airport): ").strip().upper()
        if len(origin) == 3 and origin.isalpha():
            break
        print("   Please enter a 3-letter airport code (e.g., JFK, LAX)")
    
    while True:
        destination = input("🏁 To (destination airport): ").strip().upper()
        if len(destination) == 3 and destination.isalpha():
            break
        print("   Please enter a 3-letter airport code (e.g., DEN, NYC)")
    
    while True:
        outbound_date = input("📅 Departure date (YYYY-MM-DD): ").strip()
        try:
            from datetime import datetime
            datetime.strptime(outbound_date, '%Y-%m-%d')
            break
        except ValueError:
            print("   Please enter date in YYYY-MM-DD format (e.g., 2024-12-01)")
    
    return_date = input("🔄 Return date (YYYY-MM-DD, or press Enter for one-way): ").strip()
    if return_date:
        try:
            datetime.strptime(return_date, '%Y-%m-%d')
        except ValueError:
            print("   Invalid return date format, treating as one-way flight")
            return_date = None
    
    if not return_date:
        return_date = None
    
    # Optional details
    print("\nOptional details (press Enter to skip):")
    description = input("📝 Description (e.g., 'Christmas vacation'): ").strip()
    airline = input("🏢 Airline (e.g., Delta, American): ").strip()
    
    original_price = None
    price_input = input("💰 Current/original price ($): ").strip()
    if price_input:
        try:
            original_price = float(price_input)
        except ValueError:
            print("   Invalid price format, skipping")
    
    # Add the flight
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
    if return_date:
        print(f"   Dates: {outbound_date} → {return_date}")
    else:
        print(f"   Date: {outbound_date}")
    
    return flight_id

def setup_monitoring():
    """Set up monitoring preferences"""
    print("\n⚙️  Monitoring Setup")
    print("=" * 20)
    
    print("How often would you like to check for price changes?")
    print("1. Every 6 hours (recommended)")
    print("2. Every 12 hours")
    print("3. Once a day")
    print("4. Custom")
    
    while True:
        choice = input("Choose (1-4): ").strip()
        if choice == "1":
            frequency = 6
            break
        elif choice == "2":
            frequency = 12
            break
        elif choice == "3":
            frequency = 24
            break
        elif choice == "4":
            try:
                frequency = int(input("Enter hours between checks: "))
                if frequency < 1:
                    print("Please enter a positive number")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")
                continue
        else:
            print("Please choose 1, 2, 3, or 4")
    
    print(f"\n✅ Monitoring frequency set to every {frequency} hours")
    
    # Set up automatic monitoring
    setup_auto = input("\n🤖 Set up automatic monitoring? (y/n): ").strip().lower()
    if setup_auto in ['y', 'yes']:
        try:
            result = subprocess.run([
                sys.executable, 'setup_monitor.py', '--install', '--interval', str(frequency * 60)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Automatic monitoring set up successfully!")
                print(f"   Your flights will be checked every {frequency} hours")
            else:
                print("⚠️  Automatic setup failed, but you can set it up manually later")
                print("   Run: python3 setup_monitor.py --install")
        except Exception as e:
            print(f"⚠️  Automatic setup failed: {e}")
            print("   You can set it up manually later")
    
    return frequency

def setup_notifications():
    """Set up notification preferences"""
    print("\n📢 Notification Setup")
    print("=" * 20)
    
    print("When would you like to be notified?")
    print("1. When price drops by 5% or more (recommended)")
    print("2. When price drops by 10% or more")
    print("3. Any price change")
    print("4. Custom thresholds")
    
    while True:
        choice = input("Choose (1-4): ").strip()
        if choice == "1":
            decrease_threshold = 0.05
            increase_threshold = 0.10
            break
        elif choice == "2":
            decrease_threshold = 0.10
            increase_threshold = 0.15
            break
        elif choice == "3":
            decrease_threshold = 0.01
            increase_threshold = 0.01
            break
        elif choice == "4":
            try:
                decrease_threshold = float(input("Price decrease threshold (0.05 = 5%): "))
                increase_threshold = float(input("Price increase threshold (0.10 = 10%): "))
                break
            except ValueError:
                print("Please enter valid numbers")
                continue
        else:
            print("Please choose 1, 2, 3, or 4")
    
    print(f"\n✅ Notifications set up:")
    print(f"   Alert when price drops by {decrease_threshold*100:.0f}% or more")
    print(f"   Alert when price rises by {increase_threshold*100:.0f}% or more")
    
    return decrease_threshold, increase_threshold

def test_setup():
    """Test the setup by running a price check"""
    print("\n🧪 Testing Your Setup")
    print("=" * 20)
    
    test_now = input("Would you like to test the monitor now? (y/n): ").strip().lower()
    if test_now in ['y', 'yes']:
        print("\n⏳ Running test... This may take 30-60 seconds...")
        
        try:
            result = subprocess.run([
                sys.executable, 'flight_monitor.py', '--once'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print("✅ Test completed successfully!")
                print("\nTest output:")
                print("-" * 30)
                print(result.stdout)
                if result.stderr:
                    print("Warnings:")
                    print(result.stderr)
            else:
                print("❌ Test failed")
                print("Error output:")
                print(result.stderr)
        except subprocess.TimeoutExpired:
            print("⏰ Test timed out - this might be due to slow internet")
            print("   You can try running manually: python3 flight_monitor.py --once")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    return test_now in ['y', 'yes']

def show_next_steps():
    """Show what the user can do next"""
    print("\n🎉 Setup Complete!")
    print("=" * 20)
    print("Your flight price monitor is ready to use!")
    print()
    print("📋 Quick Commands:")
    print("   Check prices now:     python3 flight_monitor.py --once")
    print("   Add another flight:   python3 flight_manager.py interactive")
    print("   List all flights:     python3 flight_manager.py list")
    print("   Check monitor status: python3 setup_monitor.py --status")
    print()
    print("📚 Documentation:")
    print("   User Guide:     USER_GUIDE.md")
    print("   Quick Start:    QUICK_START.md")
    print()
    print("🔧 Advanced:")
    print("   Configure email alerts in flight_config.json")
    print("   Adjust monitoring frequency and thresholds")
    print("   View logs in flight_monitor.log")
    print()
    print("💡 Tip: Your flights will be monitored automatically!")
    print("   Check flight_monitor.log for monitoring activity.")

def main():
    """Run the setup wizard"""
    print_banner()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above and try again.")
        sys.exit(1)
    
    print("\n✅ All requirements met!")
    
    # Set up first flight
    flight_id = setup_first_flight()
    
    # Set up monitoring
    frequency = setup_monitoring()
    
    # Set up notifications
    decrease_threshold, increase_threshold = setup_notifications()
    
    # Test the setup
    test_successful = test_setup()
    
    # Show next steps
    show_next_steps()
    
    print("\n🚀 Ready to save money on flights!")

if __name__ == "__main__":
    main()