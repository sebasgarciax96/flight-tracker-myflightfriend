#!/usr/bin/env python3
"""
Flask API Server for Flight Price Monitor
Connects the backend to Lovable frontend
"""

import os
import json
import sys
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from typing import Dict, List, Optional

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flight_manager import FlightManager
from flight_monitor import FlightMonitor
from modern_scraper import ModernFlightScraper

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# Initialize managers
flight_manager = FlightManager()
flight_monitor = FlightMonitor()

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Returns the server health status, including current timestamp and API version.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/flights', methods=['GET'])
def get_flights():
    """
    Retrieve a list of all flights managed by the system.
    
    Returns:
        JSON response containing a success flag, the list of flights, and the total count. Returns an error message with HTTP 500 status if retrieval fails.
    """
    try:
        flights = flight_manager.list_flights()
        return jsonify({
            'success': True,
            'flights': flights,
            'count': len(flights)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights', methods=['POST'])
def add_flight():
    """
    Add a new flight to the system using data provided in the request body.
    
    Validates that 'origin', 'destination', and 'outbound_date' are present in the JSON payload. Optional fields such as return date, times, price, description, airline, flight numbers, monitoring status, and frequency can also be included. Returns the created flight's ID and details on success, or an error message if validation fails or an exception occurs.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['origin', 'destination', 'outbound_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Add the flight
        flight_id = flight_manager.add_flight(
            origin=data['origin'],
            destination=data['destination'],
            outbound_date=data['outbound_date'],
            return_date=data.get('return_date'),
            outbound_time=data.get('outbound_time'),
            return_time=data.get('return_time'),
            original_price=data.get('original_price'),
            description=data.get('description'),
            airline=data.get('airline', 'Delta'),
            flight_numbers=data.get('flight_numbers'),
            monitoring_enabled=data.get('monitoring_enabled', True),
            frequency_hours=data.get('frequency_hours', 6)
        )
        
        # Get the created flight
        flight = flight_manager.get_flight(flight_id)
        
        return jsonify({
            'success': True,
            'flight_id': flight_id,
            'flight': flight,
            'message': 'Flight added successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights/<flight_id>', methods=['GET'])
def get_flight(flight_id):
    """
    Retrieve details for a specific flight by its ID.
    
    Returns a JSON response containing the flight data if found, or a 404 error if the flight does not exist. On unexpected errors, returns a 500 error with an error message.
    """
    try:
        flight = flight_manager.get_flight(flight_id)
        if not flight:
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        return jsonify({
            'success': True,
            'flight': flight
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights/<flight_id>', methods=['DELETE'])
def delete_flight(flight_id):
    """
    Deletes a flight by its ID.
    
    If the flight does not exist, returns a 404 error response. On successful deletion, returns a confirmation message. Handles unexpected errors with a 500 error response.
    """
    try:
        success = flight_manager.remove_flight(flight_id)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Flight deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights/<flight_id>/toggle', methods=['POST'])
def toggle_flight_monitoring(flight_id):
    """
    Toggles the monitoring status (enabled/disabled) for a specific flight.
    
    If the flight is found, its monitoring status is switched to the opposite state and the new status is returned in the response. Returns a 404 error if the flight does not exist.
    """
    try:
        flight = flight_manager.get_flight(flight_id)
        if not flight:
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        # Toggle monitoring status
        current_status = flight['monitoring']['enabled']
        new_status = not current_status
        
        if new_status:
            flight_manager.enable_monitoring(flight_id)
        else:
            flight_manager.disable_monitoring(flight_id)
        
        return jsonify({
            'success': True,
            'monitoring_enabled': new_status,
            'message': f'Monitoring {"enabled" if new_status else "disabled"}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights/<flight_id>/check', methods=['POST'])
def check_flight_price(flight_id):
    """
    Checks and returns the current price for a specific flight, including price change percentage, alert type, and potential savings.
    
    Returns:
        A JSON response containing the current price, previous price, price change percent, alert type, and savings if applicable. Returns a 404 error if the flight is not found or a 500 error if the price cannot be retrieved.
    """
    try:
        flight = flight_manager.get_flight(flight_id)
        if not flight:
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        # Get current price using the monitor
        current_price = flight_monitor.get_current_price(flight)
        
        if current_price is None:
            return jsonify({
                'success': False,
                'error': 'Could not retrieve current price'
            }), 500
        
        # Calculate price change
        old_price = flight.get('current_price', flight.get('original_price', 0))
        change_percent, alert_type = flight_monitor.calculate_price_change(old_price, current_price)
        
        return jsonify({
            'success': True,
            'current_price': current_price,
            'previous_price': old_price,
            'price_change_percent': change_percent,
            'alert_type': alert_type,
            'savings': old_price - current_price if old_price > current_price else 0
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitor', methods=['POST'])
def run_monitor():
    """
    Trigger monitoring for all flights and return any generated alerts.
    
    Returns:
        JSON response containing a list of alerts generated during the monitoring process, including flight ID, old and new prices, price change percentage, alert type, and timestamp. On error, returns a JSON response with an error message and HTTP 500 status.
    """
    try:
        alerts = flight_monitor.monitor_all_flights()
        
        return jsonify({
            'success': True,
            'alerts_generated': len(alerts),
            'alerts': [
                {
                    'flight_id': alert.flight_id,
                    'old_price': alert.old_price,
                    'new_price': alert.new_price,
                    'change_percent': alert.change_percent,
                    'alert_type': alert.alert_type,
                    'timestamp': alert.timestamp.isoformat()
                } for alert in alerts
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitor/status', methods=['GET'])
def get_monitor_status():
    """
    Retrieve a summary of the current monitoring status for all flights.
    
    Returns:
        JSON response containing the total number of flights, counts of active and inactive flights, and a list of flight details including monitoring status, last checked time, and price information.
    """
    try:
        flights = flight_manager.list_flights()
        active_flights = [f for f in flights if f['monitoring']['enabled']]
        
        return jsonify({
            'success': True,
            'total_flights': len(flights),
            'active_flights': len(active_flights),
            'inactive_flights': len(flights) - len(active_flights),
            'flights': [{
                'id': f['id'],
                'description': f['description'],
                'route': f"{f['origin']} → {f['destination']}",
                'monitoring_enabled': f['monitoring']['enabled'],
                'last_checked': f['monitoring'].get('last_checked'),
                'current_price': f.get('current_price'),
                'original_price': f.get('original_price')
            } for f in flights]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/flights/<flight_id>/history', methods=['GET'])
def get_price_history(flight_id):
    """
    Retrieve the price history for a specific flight by its ID.
    
    Returns:
        A JSON response containing the flight ID, a list of historical prices, and the count of price records. Returns a 404 error if the flight is not found.
    """
    try:
        flight = flight_manager.get_flight(flight_id)
        if not flight:
            return jsonify({
                'success': False,
                'error': 'Flight not found'
            }), 404
        
        price_history = flight['monitoring'].get('price_history', [])
        
        return jsonify({
            'success': True,
            'flight_id': flight_id,
            'price_history': price_history,
            'count': len(price_history)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/')
def serve_frontend():
    """
    Serves the main frontend application page by returning the 'index.html' file from the 'frontend' directory.
    """
    return send_from_directory('frontend', 'index.html')

@app.route('/frontend/<path:filename>')
def serve_frontend_files(filename):
    """
    Serve a static file from the 'frontend' directory.
    
    Parameters:
        filename (str): The name of the file to serve.
    
    Returns:
        The requested file as a Flask response object.
    """
    return send_from_directory('frontend', filename)

@app.route('/api/test', methods=['POST'])
def test_scraper():
    """
    Tests the flight price scraper for Delta main cabin flights on a specified route and date.
    
    Expects a JSON payload with `origin`, `destination`, and `outbound_date`. Returns the found price for a Delta main cabin flight if available, or an error message if no matching flights are found.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['origin', 'destination', 'outbound_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Test scraping with Delta filtering
        scraper = ModernFlightScraper(headless=True)
        
        try:
            price = scraper.scrape_flight_price(
                origin=data['origin'],
                destination=data['destination'],
                outbound_date=data['outbound_date'],
                return_date=data.get('return_date'),
                filter_delta=True,
                filter_main_cabin=True
            )
            
            if price:
                return jsonify({
                    'success': True,
                    'price': price,
                    'message': 'Successfully found Delta flight price'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'No Delta flights found for the specified route'
                })
                
        finally:
            scraper.close_driver()
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Flight Price Monitor API Server")
    print("📡 API will be available at: http://localhost:5001")
    print("🔗 Frontend can connect to these endpoints:")
    print("   GET  /api/health - Health check")
    print("   GET  /api/flights - Get all flights")
    print("   POST /api/flights - Add new flight")
    print("   GET  /api/flights/<id> - Get specific flight")
    print("   DELETE /api/flights/<id> - Delete flight")
    print("   POST /api/flights/<id>/check - Check current price")
    print("   POST /api/flights/<id>/toggle - Toggle monitoring")
    print("   GET  /api/flights/<id>/history - Get price history")
    print("   POST /api/monitor - Run monitor for all flights")
    print("   GET  /api/monitor/status - Get monitoring status")
    print("   POST /api/test - Test Delta scraping")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=True)