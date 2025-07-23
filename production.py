#!/usr/bin/env python3
"""
Production configuration for Flight Price Monitor API
For deployment to cloud platforms (Railway, Heroku, etc.)
"""

import os
from api_server import app

# Production settings
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Flight Price Monitor API Server (Production)")
    print(f"📡 Server will run on port: {port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )