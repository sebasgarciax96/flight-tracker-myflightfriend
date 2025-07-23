#!/usr/bin/env python3
"""
Test script to verify flight-analysis package installation
"""

import sys
import os

# Add the src directory to the path so we can import the package
sys.path.append('src')

try:
    from google_flight_analysis.scrape import *
    print("✅ Successfully imported flight-analysis package!")
    print("📦 Package is ready to use!")
    
    # Test creating a simple scrape object
    print("\n🧪 Testing basic functionality...")
    result = Scrape('JFK', 'LAX', '2024-01-15')
    print(f"✅ Created scrape object: {result}")
    print(f"   Origin: {result.origin}")
    print(f"   Destination: {result.dest}")
    print(f"   Date: {result.dates}")
    print(f"   Type: {result.type}")
    
    print("\n🎉 Installation successful! You can now use the flight-analysis package.")
    print("\n📚 Next steps:")
    print("   1. Check the README.md for usage examples")
    print("   2. Make sure you have Chrome/ChromeDriver installed for web scraping")
    print("   3. Try running: python3 -c \"from src.google_flight_analysis.scrape import *; print('Ready!')\"")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Try running: pip3 install -r requirements.txt")
except Exception as e:
    print(f"❌ Error: {e}")
    print("💡 Check the README.md for troubleshooting") 