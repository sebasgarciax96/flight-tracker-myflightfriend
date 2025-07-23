# Flight Price Monitor

A custom monitoring system built on top of the google-flight-analysis package that tracks flight prices and sends notifications when prices change.

## Your Flight Configuration

Your Delta SLC-DEN round trip flight has been pre-configured:

- **Route**: Salt Lake City (SLC) ↔ Denver (DEN)
- **Dates**: August 4-5, 2024
- **Flights**: DL1623 (Q class), DL2663 (V class)
- **Original Price**: $328.97
- **Current Price**: $292.00
- **Savings**: $36.97 (11.2% decrease)

## Quick Start

### 1. Install Chrome (Required for Web Scraping)

The monitor needs Google Chrome to scrape flight prices. Install it from [chrome.google.com](https://chrome.google.com) if you don't have it.

### 2. Test the Monitor

```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
python3 flight_monitor.py --once
```

### 3. Set Up Automated Monitoring

```bash
# Install cron job to check every 6 hours
python3 setup_monitor.py --install --interval 360

# Check status
python3 setup_monitor.py --status

# Test the system
python3 setup_monitor.py --test
```

### 4. Manual Commands

```bash
# Run once and exit
python3 flight_monitor.py --once

# Run continuously (check every 60 minutes)
python3 flight_monitor.py --continuous --interval 60

# Run continuously with custom interval
python3 flight_monitor.py --continuous --interval 30  # every 30 minutes
```

## Features

### 🔔 Price Alerts
- **Decrease Alert**: When price drops by 5% or more
- **Increase Alert**: When price rises by 10% or more  
- **Significant Change**: Any change of 3% or more

### 📊 Price Tracking
- Historical price data stored in `flight_config.json`
- Tracks up to 100 price points per flight
- Automatic price history management

### 📧 Notifications
- **Console**: Immediate notifications with price details
- **Email**: Configurable SMTP notifications (setup required)
- **Logs**: Detailed logging in `flight_monitor.log`

## Configuration

Edit `flight_config.json` to:

### Add More Flights
```json
{
  "flights": [
    {
      "id": "my_new_flight",
      "description": "New York to Los Angeles",
      "type": "round-trip",
      "origin": "JFK",
      "destination": "LAX",
      "outbound_date": "2024-12-01",
      "return_date": "2024-12-08",
      "original_price": 450.00,
      "current_price": 450.00,
      "monitoring": {
        "enabled": true,
        "frequency_hours": 6
      }
    }
  ]
}
```

### Configure Email Notifications
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

### Adjust Alert Thresholds
```json
{
  "flights": [
    {
      "notifications": {
        "price_decrease_threshold": 0.03,  // 3% decrease
        "price_increase_threshold": 0.15   // 15% increase
      }
    }
  ]
}
```

## Automation Options

### Option 1: Cron Job (Recommended)
```bash
# Check every 6 hours
python3 setup_monitor.py --install --interval 360

# Remove cron job
python3 setup_monitor.py --uninstall
```

### Option 2: Continuous Mode
```bash
# Run in background
nohup python3 flight_monitor.py --continuous --interval 60 &

# Stop background process
pkill -f flight_monitor.py
```

### Option 3: Manual Scheduling
Add to your system's task scheduler or run manually when needed.

## Example Notifications

### Price Decrease Alert
```
📉 FLIGHT PRICE ALERT 📉
Flight: Delta SLC-DEN Round Trip August 2024
Route: SLC → DEN
Date: 2024-08-04 - 2024-08-05
Original Price: $328.97
Previous Price: $292.00
Current Price: $265.00
Change: -9.2%
💰 You could save $27.00!
```

### Price Increase Alert
```
📈 FLIGHT PRICE ALERT 📈
Flight: Delta SLC-DEN Round Trip August 2024
Route: SLC → DEN
Date: 2024-08-04 - 2024-08-05
Original Price: $328.97
Previous Price: $292.00
Current Price: $325.00
Change: +11.3%
⚠️ Price increased by $33.00
```

## Troubleshooting

### Chrome Not Found Error
```bash
# Install Chrome from chrome.google.com
# Or install via Homebrew
brew install --cask google-chrome
```

### Permission Errors
```bash
# Make scripts executable
chmod +x flight_monitor.py setup_monitor.py
```

### Cron Job Issues
```bash
# Check cron logs
grep CRON /var/log/system.log

# Check if cron is running
sudo launchctl list | grep cron
```

### Rate Limiting
If you get blocked by Google:
- Increase `delay_between_requests` in config
- Reduce monitoring frequency
- Use headless mode (already enabled)

## Files Created

- `flight_config.json` - Configuration and price history
- `flight_monitor.py` - Main monitoring script
- `setup_monitor.py` - Automation setup script
- `flight_monitor.log` - Detailed logs
- `flight_monitor_cron.log` - Cron job logs
- `README_MONITOR.md` - This documentation

## Next Steps

1. **Test the system**: Run `python3 setup_monitor.py --test`
2. **Set up automation**: Run `python3 setup_monitor.py --install`
3. **Monitor logs**: Check `flight_monitor.log` for activity
4. **Configure email**: Update email settings in config if desired
5. **Add more flights**: Edit `flight_config.json` to track additional routes

The system is now ready to monitor your Delta flight and notify you of price changes!