# Quick Start - Flight Price Monitor

## 3 Simple Steps to Get Started

### Step 1: Open Terminal
- Press `Cmd + Space` 
- Type "Terminal" and press Enter

### Step 2: Go to the Flight Monitor Folder
Copy and paste this command:
```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
```

### Step 3: Check Your Flight Price Now
Copy and paste this command:
```bash
python3 flight_monitor.py --once
```

**That's it!** The tool will automatically:
- Open Chrome in the background
- Check Google Flights for your Delta SLC-DEN flight
- Show you the current price
- Alert you if the price changed significantly

---

## Set Up Automatic Monitoring (Optional)

To check your flight price every 6 hours automatically:
```bash
python3 setup_monitor.py --install --interval 360
```

To check the status:
```bash
python3 setup_monitor.py --status
```

---

## What You'll See

### Price Drop Alert (Good News!)
```
📉 FLIGHT PRICE ALERT 📉
Flight: Delta SLC-DEN Round Trip August 2024
Current Price: $58.00
Change: -80.1%
💰 You could save $234.00!
```

### Price Increase Alert (Heads Up!)
```
📈 FLIGHT PRICE ALERT 📈
Current Price: $325.00
Change: +11.3%
⚠️ Price increased by $33.00
```

---

## That's All You Need to Know!

- **No coding required** - Just copy and paste the commands
- **Works automatically** - Set it once and forget it
- **Saves you money** - Get alerts when prices drop
- **Easy to use** - All commands are provided for you

**Questions?** Check the full USER_GUIDE.md for more details!