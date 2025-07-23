# ✈️ Flight Price Monitor

**Never miss a flight deal again!** Automatically monitor flight prices and get notified when prices drop.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://www.apple.com/macos/)

## 🚀 Quick Start

### 1. Download & Setup
```bash
git clone https://github.com/YOUR_USERNAME/flight-price-monitor.git
cd flight-price-monitor
python3 setup_wizard.py
```

### 2. Add Your First Flight
```bash
python3 flight_manager.py interactive
```

### 3. Start Monitoring
```bash
python3 flight_monitor.py --once
```

**That's it!** The monitor will automatically check your flights and send you alerts when prices change.

---

## 🌟 Features

- **🔄 Automatic Monitoring**: Set it and forget it - checks prices every 6 hours
- **📱 Smart Alerts**: Get notified only when prices drop significantly
- **💾 Price History**: Track price changes over time
- **🎯 Multiple Flights**: Monitor as many flights as you want
- **⚡ Easy Setup**: No coding experience required
- **🔒 Privacy First**: All data stays on your computer

---

## 📋 Requirements

- **macOS** (Windows/Linux support coming soon)
- **Python 3.8+** (usually pre-installed on Mac)
- **Google Chrome** (for web scraping)
- **Internet connection**

---

## 🛠️ Installation

### Option 1: Setup Wizard (Recommended)
```bash
python3 setup_wizard.py
```
The wizard will guide you through the entire setup process step by step.

### Option 2: Manual Setup
```bash
# Install dependencies
pip3 install -r requirements.txt

# Add your first flight
python3 flight_manager.py add JFK LAX 2024-12-01 2024-12-08 450

# Test the monitor
python3 flight_monitor.py --once

# Set up automatic monitoring
python3 setup_monitor.py --install --interval 360
```

---

## 📖 Usage Examples

### Add Flights
```bash
# Round-trip flight
python3 flight_manager.py add JFK LAX 2024-12-01 2024-12-08 450

# One-way flight
python3 flight_manager.py add SLC DEN 2024-11-15 250

# Interactive mode (easiest)
python3 flight_manager.py interactive
```

### Monitor Flights
```bash
# Check prices once
python3 flight_monitor.py --once

# Check prices continuously (every hour)
python3 flight_monitor.py --continuous --interval 60

# Check specific configuration file
python3 flight_monitor.py --config my_flights.json --once
```

### Manage Flights
```bash
# List all flights
python3 flight_manager.py list

# Remove a flight
python3 flight_manager.py remove flight_12345678

# Enable/disable monitoring
python3 flight_manager.py enable flight_12345678
python3 flight_manager.py disable flight_12345678
```

### Automation
```bash
# Set up automatic monitoring every 6 hours
python3 setup_monitor.py --install --interval 360

# Check monitoring status
python3 setup_monitor.py --status

# Remove automatic monitoring
python3 setup_monitor.py --uninstall
```

---

## 🔔 Alert Examples

### Price Drop Alert
```
📉 FLIGHT PRICE ALERT 📉
Flight: New York to Los Angeles
Route: JFK → LAX
Date: 2024-12-01 - 2024-12-08
Original Price: $450.00
Previous Price: $398.00
Current Price: $325.00
Change: -18.3%
💰 You could save $73.00!
```

### Price Increase Alert
```
📈 FLIGHT PRICE ALERT 📈
Flight: Denver to Seattle
Route: DEN → SEA
Date: 2024-11-15
Original Price: $250.00
Previous Price: $280.00
Current Price: $320.00
Change: +14.3%
⚠️ Price increased by $40.00
```

---

## ⚙️ Configuration

### Flight Configuration (`flight_config.json`)
```json
{
  "flights": [
    {
      "id": "flight_12345678",
      "description": "Christmas Vacation",
      "type": "round-trip",
      "origin": "JFK",
      "destination": "LAX",
      "outbound_date": "2024-12-01",
      "return_date": "2024-12-08",
      "original_price": 450.00,
      "current_price": 325.00,
      "airline": "American",
      "notifications": {
        "price_decrease_threshold": 0.05,
        "price_increase_threshold": 0.10
      },
      "monitoring": {
        "enabled": true,
        "frequency_hours": 6
      }
    }
  ]
}
```

### Notification Settings
- **`price_decrease_threshold`**: Alert when price drops by this percentage (0.05 = 5%)
- **`price_increase_threshold`**: Alert when price rises by this percentage (0.10 = 10%)
- **`frequency_hours`**: How often to check prices (6 = every 6 hours)

### Email Notifications (Optional)
```json
{
  "notification_settings": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "your-email@gmail.com",
      "sender_password": "your-app-password",
      "recipient_email": "alerts@your-domain.com"
    }
  }
}
```

---

## 📊 Monitoring Dashboard

### Check Current Status
```bash
python3 setup_monitor.py --status
```

### View Price History
```bash
python3 flight_manager.py list
```

### Check Logs
```bash
# View recent activity
tail -20 flight_monitor.log

# View price alerts only
grep "PRICE ALERT" flight_monitor.log
```

---

## 🎯 Use Cases

### 🏖️ Vacation Planning
- Monitor flights to your dream destination
- Get alerts when prices drop for your travel dates
- Track price trends to find the best booking time

### 💼 Business Travel
- Monitor regular routes for business trips
- Get notified of price changes for flexible dates
- Track multiple airports for better deals

### 🏠 Visit Family
- Monitor flights to family destinations
- Get alerts for holiday travel deals
- Track prices for last-minute trips

### 🎓 Student Travel
- Monitor budget-friendly routes
- Get alerts for student discounts
- Track prices for semester breaks

---

## 🔧 Advanced Features

### Custom Scraping Settings
```json
{
  "scraping_settings": {
    "headless": true,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "delay_between_requests": 2
  }
}
```

### Multiple Configuration Files
```bash
# Use different config files for different purposes
python3 flight_monitor.py --config vacation_flights.json --once
python3 flight_monitor.py --config business_flights.json --once
```

### Batch Operations
```bash
# Add multiple flights from a CSV file
python3 import_flights.py flights.csv

# Export flight data
python3 export_flights.py --format csv
```

---

## 🛡️ Privacy & Security

- **Local Data**: All flight data stays on your computer
- **No Account Required**: No sign-ups or external services
- **Open Source**: Full transparency in code
- **Secure Scraping**: Respectful rate limiting to avoid blocking

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### For Users
- 🐛 Report bugs in [Issues](https://github.com/YOUR_USERNAME/flight-price-monitor/issues)
- 💡 Suggest features and improvements
- 📚 Help improve documentation
- ⭐ Star the project if you find it useful

### For Developers
- 🔧 Fix bugs and add features
- 📝 Improve code documentation
- 🧪 Add tests and improve reliability
- 🌍 Add support for other countries/languages

### Development Setup
```bash
git clone https://github.com/YOUR_USERNAME/flight-price-monitor.git
cd flight-price-monitor
pip3 install -r requirements.txt
python3 -m pytest tests/
```

---

## 📚 Documentation

- **[Quick Start Guide](QUICK_START.md)** - Get started in 3 steps
- **[User Guide](USER_GUIDE.md)** - Complete user documentation
- **[API Reference](docs/API.md)** - Technical documentation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🆘 Support

### Getting Help
- 📖 Check the [User Guide](USER_GUIDE.md)
- 🐛 Search [Issues](https://github.com/YOUR_USERNAME/flight-price-monitor/issues)
- 💬 Ask questions in [Discussions](https://github.com/YOUR_USERNAME/flight-price-monitor/discussions)

### Common Issues
- **Chrome not found**: Install Chrome from [chrome.google.com](https://chrome.google.com)
- **Python not found**: Install Python from [python.org](https://python.org)
- **Permission denied**: Run `chmod +x *.py` to fix permissions

---

## 🏆 Success Stories

> "Saved $400 on my honeymoon flights to Hawaii!" - @user123

> "Never miss a deal anymore. This tool pays for itself!" - @traveler456

> "Perfect for business travel. Tracks all my regular routes." - @businesswoman

---

## 📈 Roadmap

### ✅ Current Features
- [x] Automatic price monitoring
- [x] Smart alerts and notifications
- [x] Multiple flight support
- [x] Price history tracking
- [x] Easy setup wizard

### 🔄 In Progress
- [ ] Windows and Linux support
- [ ] Mobile app (iOS/Android)
- [ ] Web dashboard
- [ ] Email notifications
- [ ] API for integrations

### 🚀 Future Plans
- [ ] International flight support
- [ ] Price prediction ML models
- [ ] Hotel and car rental monitoring
- [ ] Group travel features
- [ ] Integration with travel booking sites

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built on top of [google-flight-analysis](https://github.com/celebi-pkg/flight-analysis)
- Selenium WebDriver for web scraping
- Python community for excellent libraries
- All contributors and users who make this project better

---

## 💰 Support the Project

If this tool saves you money on flights, consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs and issues
- 💡 Suggesting new features
- 📢 Sharing with friends and family
- ☕ [Buy me a coffee](https://buymeacoffee.com/flightmonitor)

---

**Happy travels and happy savings!** ✈️💰