#!/bin/bash

# Flight Price Monitor Installation Script
# This script sets up the Flight Price Monitor for new users

set -e  # Exit on any error

echo "✈️ Flight Price Monitor Installation"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# print_status prints a status message in green with a checkmark icon.
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

# print_warning prints a warning message in yellow with a warning icon.
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# print_error prints an error message in red with a cross icon to stderr.
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# print_info prints an informational message in blue with a magnifying glass icon.
print_info() {
    echo -e "${BLUE}🔍 $1${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer currently only supports macOS"
    print_info "Windows and Linux support coming soon!"
    exit 1
fi

print_status "Running on macOS"

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.8+ required. Found $PYTHON_VERSION"
        print_info "Install Python from https://python.org"
        exit 1
    fi
else
    print_error "Python 3 not found"
    print_info "Install Python from https://python.org"
    exit 1
fi

# Check if Google Chrome is installed
print_info "Checking for Google Chrome..."
if [ -d "/Applications/Google Chrome.app" ]; then
    print_status "Google Chrome found"
else
    print_error "Google Chrome not found"
    print_info "Install Chrome from https://chrome.google.com"
    exit 1
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    print_info "Try running: pip3 install selenium pandas numpy tqdm chromedriver-autoinstaller"
    exit 1
fi

# Make scripts executable
print_info "Setting up permissions..."
chmod +x *.py
print_status "Permissions set"

# Create default config if it doesn't exist
if [ ! -f "flight_config.json" ]; then
    print_info "Creating default configuration..."
    cat > flight_config.json << EOF
{
  "flights": [],
  "notification_settings": {
    "email": {
      "enabled": false,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "",
      "sender_password": "",
      "recipient_email": ""
    },
    "console": {
      "enabled": true,
      "log_level": "INFO"
    }
  },
  "scraping_settings": {
    "headless": true,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "delay_between_requests": 2
  }
}
EOF
    print_status "Default configuration created"
fi

# Test the installation
print_info "Testing installation..."
if python3 -c "import selenium, pandas, numpy, tqdm; print('All imports successful')"; then
    print_status "Installation test passed"
else
    print_error "Installation test failed"
    exit 1
fi

# Success message
echo ""
print_status "Installation completed successfully!"
echo ""
echo "🚀 Next Steps:"
echo "1. Run the setup wizard: python3 setup_wizard.py"
echo "2. Or add a flight manually: python3 flight_manager.py interactive"
echo "3. Test the monitor: python3 flight_monitor.py --once"
echo ""
echo "📚 Documentation:"
echo "- Quick Start: QUICK_START.md"
echo "- User Guide: USER_GUIDE.md"
echo "- Full README: README.md"
echo ""
echo "🎉 Happy flight monitoring!"