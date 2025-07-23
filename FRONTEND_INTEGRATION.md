# 🔗 Frontend Integration Guide

## Connecting Your Lovable Frontend to the Flight Price Monitor

Your flight price monitor now includes **Delta-specific filtering** and a **REST API** for easy frontend integration.

---

## 🎯 **What's Ready:**

### ✅ **Delta Filtering Features:**
- **Airline Filter**: Only shows Delta flights
- **Main Cabin Filter**: Only shows Main cabin class
- **Automatic Filtering**: Applied to all price checks
- **Fallback Logic**: If no Delta flights found, shows all flights

### ✅ **API Endpoints:**
- **RESTful API** running on `http://localhost:5000`
- **CORS enabled** for frontend connections
- **JSON responses** for all endpoints
- **Error handling** with proper HTTP status codes

---

## 🚀 **Starting the API Server:**

### **Step 1: Start the Backend**
```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
python3 api_server.py
```

You'll see:
```
🚀 Starting Flight Price Monitor API Server
📡 API will be available at: http://localhost:5000
```

### **Step 2: Test the API**
```bash
curl http://localhost:5000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-15T14:51:21.419036",
  "version": "1.0.0"
}
```

---

## 📡 **API Endpoints for Your Frontend:**

### **1. Flight Management**

#### **Get All Flights**
```javascript
// GET /api/flights
fetch('http://localhost:5000/api/flights')
  .then(response => response.json())
  .then(data => {
    console.log(data.flights); // Array of flight objects
  });
```

#### **Add New Flight**
```javascript
// POST /api/flights
const newFlight = {
  origin: 'SLC',
  destination: 'DEN',
  outbound_date: '2025-02-15',
  return_date: '2025-02-20',
  original_price: 350,
  description: 'Valentine\'s Day Trip'
};

fetch('http://localhost:5000/api/flights', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(newFlight)
})
.then(response => response.json())
.then(data => {
  console.log('Flight added:', data.flight_id);
});
```

#### **Delete Flight**
```javascript
// DELETE /api/flights/{flight_id}
fetch(`http://localhost:5000/api/flights/${flightId}`, {
  method: 'DELETE'
})
.then(response => response.json())
.then(data => {
  console.log('Flight deleted:', data.message);
});
```

### **2. Price Monitoring**

#### **Check Current Price (with Delta filtering)**
```javascript
// POST /api/flights/{flight_id}/check
fetch(`http://localhost:5000/api/flights/${flightId}/check`, {
  method: 'POST'
})
.then(response => response.json())
.then(data => {
  console.log('Current price:', data.current_price);
  console.log('Price change:', data.price_change_percent);
  console.log('Savings:', data.savings);
});
```

#### **Run Monitor for All Flights**
```javascript
// POST /api/monitor
fetch('http://localhost:5000/api/monitor', {
  method: 'POST'
})
.then(response => response.json())
.then(data => {
  console.log('Alerts generated:', data.alerts_generated);
  console.log('Alerts:', data.alerts);
});
```

#### **Get Monitoring Status**
```javascript
// GET /api/monitor/status
fetch('http://localhost:5000/api/monitor/status')
  .then(response => response.json())
  .then(data => {
    console.log('Active flights:', data.active_flights);
    console.log('Flight details:', data.flights);
  });
```

### **3. Price History**

#### **Get Price History for a Flight**
```javascript
// GET /api/flights/{flight_id}/history
fetch(`http://localhost:5000/api/flights/${flightId}/history`)
  .then(response => response.json())
  .then(data => {
    console.log('Price history:', data.price_history);
    // Each entry has: { price: 350, timestamp: "2025-01-15T14:51:21.419036" }
  });
```

### **4. Testing & Debugging**

#### **Test Delta Scraping**
```javascript
// POST /api/test
const testFlight = {
  origin: 'SLC',
  destination: 'LAX',
  outbound_date: '2025-03-15',
  return_date: '2025-03-22'
};

fetch('http://localhost:5000/api/test', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(testFlight)
})
.then(response => response.json())
.then(data => {
  console.log('Test result:', data.price);
});
```

---

## 🎨 **Frontend Integration Examples:**

### **React Component Example**
```jsx
import React, { useState, useEffect } from 'react';

const FlightMonitor = () => {
  const [flights, setFlights] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load flights on component mount
  useEffect(() => {
    fetchFlights();
  }, []);

  const fetchFlights = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/flights');
      const data = await response.json();
      setFlights(data.flights);
    } catch (error) {
      console.error('Error fetching flights:', error);
    }
  };

  const addFlight = async (flightData) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/flights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(flightData)
      });
      const data = await response.json();
      if (data.success) {
        fetchFlights(); // Refresh the list
      }
    } catch (error) {
      console.error('Error adding flight:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkPrice = async (flightId) => {
    setLoading(true);
    try {
      const response = await fetch(`http://localhost:5000/api/flights/${flightId}/check`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        alert(`Current price: $${data.current_price}`);
        fetchFlights(); // Refresh to show updated price
      }
    } catch (error) {
      console.error('Error checking price:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Flight Price Monitor</h1>
      <button onClick={() => addFlight({
        origin: 'SLC',
        destination: 'DEN',
        outbound_date: '2025-02-15',
        return_date: '2025-02-20',
        original_price: 350
      })}>
        Add Test Flight
      </button>
      
      {flights.map(flight => (
        <div key={flight.id} className="flight-card">
          <h3>{flight.description}</h3>
          <p>Route: {flight.origin} → {flight.destination}</p>
          <p>Price: ${flight.original_price} → ${flight.current_price}</p>
          <button onClick={() => checkPrice(flight.id)} disabled={loading}>
            Check Current Price
          </button>
        </div>
      ))}
    </div>
  );
};

export default FlightMonitor;
```

### **Vue.js Component Example**
```vue
<template>
  <div>
    <h1>Flight Price Monitor</h1>
    <button @click="addFlight">Add Test Flight</button>
    
    <div v-for="flight in flights" :key="flight.id" class="flight-card">
      <h3>{{ flight.description }}</h3>
      <p>Route: {{ flight.origin }} → {{ flight.destination }}</p>
      <p>Price: ${{ flight.original_price }} → ${{ flight.current_price }}</p>
      <button @click="checkPrice(flight.id)" :disabled="loading">
        Check Current Price
      </button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      flights: [],
      loading: false
    };
  },
  
  mounted() {
    this.fetchFlights();
  },
  
  methods: {
    async fetchFlights() {
      try {
        const response = await fetch('http://localhost:5000/api/flights');
        const data = await response.json();
        this.flights = data.flights;
      } catch (error) {
        console.error('Error fetching flights:', error);
      }
    },
    
    async addFlight() {
      this.loading = true;
      try {
        const response = await fetch('http://localhost:5000/api/flights', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            origin: 'SLC',
            destination: 'DEN',
            outbound_date: '2025-02-15',
            return_date: '2025-02-20',
            original_price: 350
          })
        });
        const data = await response.json();
        if (data.success) {
          this.fetchFlights();
        }
      } catch (error) {
        console.error('Error adding flight:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async checkPrice(flightId) {
      this.loading = true;
      try {
        const response = await fetch(`http://localhost:5000/api/flights/${flightId}/check`, {
          method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
          alert(`Current price: $${data.current_price}`);
          this.fetchFlights();
        }
      } catch (error) {
        console.error('Error checking price:', error);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

---

## 🔧 **API Response Formats:**

### **Flight Object**
```json
{
  "id": "flight_bb227b56",
  "description": "SLC to DEN Round Trip (2025-01-15 - 2025-01-20)",
  "type": "round-trip",
  "origin": "SLC",
  "destination": "DEN",
  "outbound_date": "2025-01-15",
  "return_date": "2025-01-20",
  "original_price": 300.0,
  "current_price": 58.0,
  "airline": "Delta",
  "notifications": {
    "email": true,
    "console": true,
    "price_decrease_threshold": 0.05,
    "price_increase_threshold": 0.1
  },
  "monitoring": {
    "enabled": true,
    "frequency_hours": 6,
    "last_checked": "2025-07-15T14:51:21.419036",
    "price_history": [
      {
        "price": 58.0,
        "timestamp": "2025-07-15T14:51:21.418988"
      }
    ]
  }
}
```

### **Price Check Response**
```json
{
  "success": true,
  "current_price": 58.0,
  "previous_price": 300.0,
  "price_change_percent": -80.7,
  "alert_type": "decrease",
  "savings": 242.0
}
```

### **Monitor Status Response**
```json
{
  "success": true,
  "total_flights": 5,
  "active_flights": 4,
  "inactive_flights": 1,
  "flights": [
    {
      "id": "flight_bb227b56",
      "description": "SLC to DEN Round Trip",
      "route": "SLC → DEN",
      "monitoring_enabled": true,
      "last_checked": "2025-07-15T14:51:21.419036",
      "current_price": 58.0,
      "original_price": 300.0
    }
  ]
}
```

---

## 🛠️ **Development Setup:**

### **1. Start Backend**
```bash
cd "/Users/sebastiangarcia/cursor/Flight Tracker Delta/flight-analysis"
python3 api_server.py
```

### **2. Test API Endpoints**
```bash
# Health check
curl http://localhost:5000/api/health

# Get flights
curl http://localhost:5000/api/flights

# Add flight
curl -X POST http://localhost:5000/api/flights \
  -H "Content-Type: application/json" \
  -d '{"origin":"SLC","destination":"LAX","outbound_date":"2025-03-15","return_date":"2025-03-22","original_price":450}'
```

### **3. Connect Your Frontend**
- Point your Lovable frontend to `http://localhost:5000`
- Use the API endpoints documented above
- Handle loading states and errors appropriately

---

## 🎯 **Key Features for Frontend:**

### **Delta-Specific Features:**
- All price checks automatically filter for Delta flights
- Main cabin class filtering is applied
- Clear messaging when no Delta flights are found

### **Real-Time Updates:**
- Check prices on-demand with `/api/flights/{id}/check`
- Monitor all flights with `/api/monitor`
- Get updated flight lists with `/api/flights`

### **User Experience:**
- Loading states during price checks (can take 30-60 seconds)
- Error handling for failed requests
- Success messages for completed actions
- Price history visualization

---

## 🔐 **Security & Performance:**

### **CORS Configuration:**
- Currently allows all origins for development
- Restrict to your frontend domain in production

### **Rate Limiting:**
- Built-in delays between requests (2 seconds)
- Respectful to Google Flights
- Avoid excessive API calls

### **Error Handling:**
- Proper HTTP status codes
- Descriptive error messages
- Fallback behavior when scraping fails

---

## 🎉 **Ready to Connect!**

Your flight price monitor is now ready to connect to your Lovable frontend with:

✅ **Delta filtering** for airline-specific results  
✅ **Main cabin filtering** for class-specific results  
✅ **RESTful API** for easy integration  
✅ **Real-time price checking** with live scraping  
✅ **Price history tracking** for trend analysis  
✅ **Error handling** for robust operation  

**Next Steps:**
1. Start the API server: `python3 api_server.py`
2. Test the endpoints with your frontend
3. Implement the UI components using the examples above
4. Add error handling and loading states
5. Style the components to match your design

**Happy coding!** 🚀✈️