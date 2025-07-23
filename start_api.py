#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api_server import app

if __name__ == "__main__":
    print("🚀 Starting Flight Price Monitor API Server")
    print("📡 API will be available at: http://localhost:5001")
    app.run(host="0.0.0.0", port=5001, debug=True)
