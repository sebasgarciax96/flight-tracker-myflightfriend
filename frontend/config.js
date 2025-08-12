// Flight Tracker Configuration
// This file should be generated dynamically in production

class FlightTrackerConfig {
  constructor() {
    // Detect environment
    this.isDevelopment = window.location.hostname === 'localhost' || 
                        window.location.hostname === '127.0.0.1' ||
                        window.location.port === '8000'
    
    // Set configuration - use development keys for now since we're testing locally
    this.supabaseUrl = 'https://wacrvpraqzvpbsbzvlxp.supabase.co'
    this.supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndhY3J2cHJhcXp2cGJzYnp2bHhwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTMxNTA1MDUsImV4cCI6MjA2ODcyNjUwNX0.uPK81YZyUYFfwViIMT4LHE4Xz6aP_0pCQuLIERgVl0M'
    
    // For production deployment, you would use environment-based configuration:
    // if (!this.isDevelopment) {
    //   this.supabaseUrl = this.getConfigValue('SUPABASE_URL') || this.supabaseUrl
    //   this.supabaseAnonKey = this.getConfigValue('SUPABASE_ANON_KEY')
    // }

    // API endpoints
    this.apiBaseUrl = this.supabaseUrl + '/functions/v1'
    
    // Feature flags
    this.features = {
      emailNotifications: true,
      priceHistory: true,
      bulkOperations: false,
      realTimeUpdates: true
    }
  }

  getConfigValue(key) {
    // Try to get from meta tags first (server-rendered)
    const metaTag = document.querySelector(`meta[name="config-${key.toLowerCase()}"]`)
    if (metaTag) {
      return metaTag.getAttribute('content')
    }

    // Try to get from window config object
    if (window.FLIGHT_TRACKER_CONFIG && window.FLIGHT_TRACKER_CONFIG[key]) {
      return window.FLIGHT_TRACKER_CONFIG[key]
    }

    // Return empty string if not found (will cause authentication errors)
    return ''
  }

  validateConfig() {
    const errors = []
    
    if (!this.supabaseUrl) {
      errors.push('Supabase URL is required')
    }
    
    if (!this.supabaseAnonKey) {
      errors.push('Supabase anonymous key is required')
    }
    
    if (!this.supabaseUrl.startsWith('https://')) {
      errors.push('Supabase URL must use HTTPS')
    }

    return {
      isValid: errors.length === 0,
      errors: errors
    }
  }

  // Get API endpoint URLs
  getEndpoint(name) {
    const endpoints = {
      manageFlights: `${this.apiBaseUrl}/manage-flights`,
      checkPrices: `${this.apiBaseUrl}/check-flight-price`,
      sendNotification: `${this.apiBaseUrl}/send-notification`
    }
    
    return endpoints[name] || null
  }

  // Log configuration (for debugging - removes sensitive data)
  logConfig() {
    console.log('Flight Tracker Config:', {
      environment: this.isDevelopment ? 'development' : 'production',
      supabaseUrl: this.supabaseUrl,
      supabaseAnonKey: this.supabaseAnonKey ? '[CONFIGURED]' : '[MISSING]',
      apiBaseUrl: this.apiBaseUrl,
      features: this.features
    })
  }
}

// Create global config instance
window.FlightTrackerConfig = new FlightTrackerConfig()

// Validate configuration on load
const validation = window.FlightTrackerConfig.validateConfig()
if (!validation.isValid) {
  console.error('Flight Tracker Configuration Errors:', validation.errors)
  
  // Show user-friendly error message
  document.addEventListener('DOMContentLoaded', function() {
    const errorDiv = document.createElement('div')
    errorDiv.innerHTML = `
      <div style="background: #fee; border: 2px solid #f00; padding: 20px; margin: 20px; border-radius: 8px;">
        <h3 style="color: #d00;">Configuration Error</h3>
        <p>The application is not properly configured. Please contact support.</p>
        <details>
          <summary>Technical Details</summary>
          <ul style="margin-top: 10px;">
            ${validation.errors.map(error => `<li>${error}</li>`).join('')}
          </ul>
        </details>
      </div>
    `
    document.body.insertBefore(errorDiv, document.body.firstChild)
  })
}

// Log configuration in development
if (window.FlightTrackerConfig.isDevelopment) {
  window.FlightTrackerConfig.logConfig()
}

// Debug log to ensure config loads
console.log('Flight Tracker Config loaded:', window.FlightTrackerConfig)