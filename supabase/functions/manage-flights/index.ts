import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface FlightData {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  departure_time?: string;
  return_time?: string;
  price_threshold: number;
  original_price?: number;
  description?: string;
  airline?: string;
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const url = new URL(req.url)
    const segments = url.pathname.split('/').filter(Boolean)
    const method = req.method
    
    // Extract flight ID from URL path - handle both /manage-flights and /manage-flights/{id}
    let flightId = null
    const lastSegment = segments[segments.length - 1]
    
    // If last segment is not 'manage-flights', it's probably the flight ID
    if (lastSegment !== 'manage-flights' && lastSegment.length > 10) {
      flightId = lastSegment
    }

    // Get user from Authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response('Unauthorized', { 
        status: 401, 
        headers: corsHeaders 
      })
    }

    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)
    
    if (authError || !user) {
      return new Response('Unauthorized', { 
        status: 401, 
        headers: corsHeaders 
      })
    }

    switch (method) {
      case 'GET':
        // Get all flights for user - simplified without price_history for now
        const { data: flights, error: fetchError } = await supabase
          .from('flights')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })

        if (fetchError) {
          return new Response(JSON.stringify({ error: fetchError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ 
          success: true, 
          flights: flights || [],
          count: flights?.length || 0
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })

      case 'POST':
        // Add new flight
        const flightData: FlightData = await req.json()
        
        // Validate required fields
        if (!flightData.origin || !flightData.destination || !flightData.departure_date || (!flightData.price_threshold && !flightData.original_price)) {
          return new Response(JSON.stringify({ 
            error: 'Missing required fields: origin, destination, departure_date, and either price_threshold or original_price' 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Validate flight data
        const validation = validateFlightData(flightData)
        if (!validation.isValid) {
          return new Response(JSON.stringify({ 
            error: 'Validation failed: ' + validation.errors.join(', ')
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Map frontend field names to database column names
        const priceValue = flightData.price_threshold || flightData.original_price
        
        // Insert flight using correct database column names
        const { data: newFlight, error: insertError } = await supabase
          .from('flights')
          .insert([{
            user_id: user.id,
            departure_airport: flightData.origin.toUpperCase(),
            arrival_airport: flightData.destination.toUpperCase(),
            departure_date: flightData.departure_date,
            return_date: flightData.return_date || null,
            departure_time: flightData.departure_time || null,
            return_time: flightData.return_time || null,
            original_price: priceValue,
            current_price: priceValue,
            description: flightData.description || `${flightData.origin} to ${flightData.destination}`,
            airline: flightData.airline || 'Delta',
            monitoring_enabled: true,
            email_notifications_enabled: true
          }])
          .select()
          .single()

        if (insertError) {
          return new Response(JSON.stringify({ error: insertError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        // Send confirmation notification
        await supabase
          .from('notifications')
          .insert([{
            flight_id: newFlight.id,
            user_id: user.id,
            notification_type: 'tracking_started',
            message: `Flight tracking started for ${newFlight.origin} → ${newFlight.destination}`,
            new_price: newFlight.price_threshold
          }])

        // Trigger price check for new flight (async)
        fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/check-flight-price`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${Deno.env.get('SUPABASE_ANON_KEY')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ flight_id: newFlight.id })
        }).catch(console.error) // Don't await, run in background

        return new Response(JSON.stringify({ 
          success: true, 
          flight: newFlight,
          message: 'Flight added successfully and monitoring started'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })

      case 'DELETE':
        // Delete flight - flightId should be extracted from URL path
        if (!flightId) {
          return new Response(JSON.stringify({ 
            error: 'Flight ID required in URL path: /manage-flights/{flight-id}' 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        console.log(`Attempting to delete flight ${flightId} for user ${user.id}`)

        const { error: deleteError } = await supabase
          .from('flights')
          .delete()
          .eq('id', flightId)
          .eq('user_id', user.id)

        if (deleteError) {
          return new Response(JSON.stringify({ error: deleteError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ 
          success: true, 
          message: 'Flight deleted successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })

      case 'PATCH':
        // Update flight
        if (!flightId) {
          return new Response(JSON.stringify({ 
            error: 'Flight ID required in URL path: /manage-flights/{flight-id}' 
          }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        const updateData = await req.json()
        
        const { data: updatedFlight, error: updateError } = await supabase
          .from('flights')
          .update(updateData)
          .eq('id', flightId)
          .eq('user_id', user.id)
          .select()
          .single()

        if (updateError) {
          return new Response(JSON.stringify({ error: updateError.message }), {
            status: 400,
            headers: { ...corsHeaders, 'Content-Type': 'application/json' }
          })
        }

        return new Response(JSON.stringify({ 
          success: true, 
          flight: updatedFlight,
          message: 'Flight updated successfully'
        }), {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })

      default:
        return new Response('Method not allowed', { 
          status: 405, 
          headers: corsHeaders 
        })
    }

  } catch (error) {
    console.error('Function error:', error)
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

function validateFlightData(data: FlightData) {
  const errors: string[] = []

  // Validate airport codes
  if (data.origin && (!data.origin.match(/^[A-Z]{3}$/) || data.origin.length !== 3)) {
    errors.push('Origin must be a valid 3-letter airport code')
  }
  
  if (data.destination && (!data.destination.match(/^[A-Z]{3}$/) || data.destination.length !== 3)) {
    errors.push('Destination must be a valid 3-letter airport code')
  }

  if (data.origin && data.destination && data.origin === data.destination) {
    errors.push('Origin and destination cannot be the same')
  }

  // Validate dates
  if (data.departure_date) {
    const departureDate = new Date(data.departure_date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    if (departureDate < today) {
      errors.push('Departure date cannot be in the past')
    }

    // Check if departure is too far in future (1 year)
    const oneYearFromNow = new Date()
    oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1)
    if (departureDate > oneYearFromNow) {
      errors.push('Departure date cannot be more than 1 year in the future')
    }

    // Validate return date if provided
    if (data.return_date) {
      const returnDate = new Date(data.return_date)
      
      if (returnDate <= departureDate) {
        errors.push('Return date must be after departure date')
      }

      const oneYearFromDep = new Date(departureDate)
      oneYearFromDep.setFullYear(oneYearFromDep.getFullYear() + 1)
      if (returnDate > oneYearFromDep) {
        errors.push('Return date cannot be more than 1 year after departure')
      }
    }
  }

  // Validate price (either price_threshold or original_price)
  const price = data.price_threshold || data.original_price
  if (price !== undefined) {
    if (typeof price !== 'number' || price <= 0) {
      errors.push('Price must be a positive number')
    } else if (price < 50) {
      errors.push('Price must be at least $50')
    } else if (price > 10000) {
      errors.push('Price cannot exceed $10,000')
    }
  }

  return {
    isValid: errors.length === 0,
    errors: errors
  }
}