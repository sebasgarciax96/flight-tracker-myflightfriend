# Flight Price Monitor - User Guide
## No Coding Experience Required!

This guide will walk you through using the flight price monitor step by step, with no coding knowledge needed.

---

## 📋 What You Need Before Starting

1. **A Mac computer** (this tool is set up for Mac)
2. **Google Chrome browser** (download from chrome.google.com if you don't have it)
3. **Terminal app** (already on your Mac - we'll show you how to find it)

---

## 🚀 Step-by-Step Instructions

### Step 1: Open Terminal
1. Press `Cmd + Space` to open Spotlight search
2. Type "Terminal" and press Enter
3. A black window will open - this is your terminal

### Step 2: Navigate to the Flight Monitor
Copy and paste this command into Terminal, then press Enter:
```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
```

### Step 3: Test the Monitor (Check Your Flight Price Right Now)
Copy and paste this command and press Enter:
```bash
python3 flight_monitor.py --once
```

**What happens:**
- Chrome will open automatically (you might see it briefly)
- The tool will check Google Flights for your SLC-DEN flight
- You'll see a price alert if the price changed
- It takes about 30 seconds to complete

---

## 🔔 Understanding the Price Alert

When you see an alert like this:
```
📉 FLIGHT PRICE ALERT 📉
Flight: Delta SLC-DEN Round Trip August 2024
Route: SLC → DEN
Date: 2024-08-04 - 2024-08-05
Original Price: $328.97
Previous Price: $292.00
Current Price: $58.00
Change: -80.1%
💰 You could save $234.00!
```

**This means:**
- 📉 = Price went DOWN (good news!)
- 📈 = Price went UP (heads up!)
- The tool found your flight for $58 (much cheaper than before!)
- You could save $234 compared to the last price check

---

## ⚙️ Setting Up Automatic Monitoring

### Option 1: Automatic Checks Every 6 Hours (Recommended)
Copy and paste this command:
```bash
python3 setup_monitor.py --install --interval 360
```

**What this does:**
- Checks your flight price every 6 hours automatically
- Runs even when your computer is asleep
- Saves alerts to a log file you can check later

### Option 2: Check Status of Automatic Monitoring
```bash
python3 setup_monitor.py --status
```

### Option 3: Stop Automatic Monitoring
```bash
python3 setup_monitor.py --uninstall
```

---

## 🎯 Common Commands (Copy & Paste These)

### Check Price Right Now
```bash
python3 flight_monitor.py --once
```

### Check Price Every Hour (Runs Until You Stop It)
```bash
python3 flight_monitor.py --continuous --interval 60
```
*Press Ctrl+C to stop it*

### Check Price Every 30 Minutes
```bash
python3 flight_monitor.py --continuous --interval 30
```

### See All Available Commands
```bash
python3 flight_monitor.py --help
```

---

## 📂 Files You'll See

After running the monitor, you'll see these files in your folder:

- **flight_config.json** - Your flight details and price history
- **flight_monitor.log** - Detailed log of all price checks
- **flight_monitor_cron.log** - Log of automatic checks
- **USER_GUIDE.md** - This guide

---

## 🔧 Adding More Flights to Monitor

If you want to monitor additional flights:

1. Open the `flight_config.json` file with TextEdit
2. Look for the section with your current flight
3. Add a new flight section following the same format

**Example of adding a new flight:**
```json
{
  "id": "my_vacation_flight",
  "description": "Vacation to Hawaii",
  "type": "round-trip",
  "origin": "SLC",
  "destination": "HNL",
  "outbound_date": "2024-12-01",
  "return_date": "2024-12-08",
  "original_price": 650.00,
  "current_price": 650.00,
  "monitoring": {
    "enabled": true,
    "frequency_hours": 6
  }
}
```

---

## 🆘 Troubleshooting

### "Command not found" error
Make sure you're in the right folder:
```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
```

### Chrome opens but no prices found
- Make sure Chrome is updated to the latest version
- Try running the command again (sometimes Google Flights loads slowly)
- Check that your internet connection is working

### "Permission denied" error
Run this command to fix permissions:
```bash
chmod +x flight_monitor.py setup_monitor.py
```

### Getting too many alerts
Edit the `flight_config.json` file and change these numbers:
- `"price_decrease_threshold": 0.05` (only alert for 5% or more decrease)
- `"price_increase_threshold": 0.10` (only alert for 10% or more increase)

---

## 📊 Reading the Log Files

### Check Recent Activity
```bash
tail -20 flight_monitor.log
```

### See All Price History
```bash
cat flight_monitor.log | grep "Found price"
```

---

## 🎯 Quick Start Summary

1. **Open Terminal** (Cmd+Space, type "Terminal")
2. **Go to folder:** `cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"`
3. **Check price now:** `python3 flight_monitor.py --once`
4. **Set up automatic checks:** `python3 setup_monitor.py --install --interval 360`
5. **Check status:** `python3 setup_monitor.py --status`

---

## 💡 Pro Tips

- **Check manually before big trips** - Run the price check a few days before you travel
- **Don't check too frequently** - Every 6 hours is plenty to catch good deals
- **Watch for patterns** - Prices often drop on Tuesday/Wednesday
- **Set reasonable thresholds** - 5% decrease alerts are good for most flights

---

## 🎉 You're All Set!

You now have a personal flight price monitor that will:
- ✅ Check your flight prices automatically
- ✅ Send you alerts when prices change significantly  
- ✅ Keep a history of all price changes
- ✅ Help you save money on flights

**Need help?** Just run any command from this guide - they're all copy-and-paste ready!