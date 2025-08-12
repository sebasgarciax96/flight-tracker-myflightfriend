import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'
import { scrapeFlightPrice, FlightSearchParams } from '../_shared/flight-scraper.ts'

interface PriceCheckRequest {
  flight_id?: string;
  check_all?: boolean;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { flight_id, check_all }: PriceCheckRequest = await req.json()

    let flights: any[] = []

    if (flight_id) {
      // Check specific flight
      const { data, error } = await supabase
        .from('flights')
        .select('*')
        .eq('id', flight_id)
        .eq('monitoring_enabled', true)
        .single()

      if (error || !data) {
        return new Response(JSON.stringify({ error: 'Flight not found or monitoring disabled' }), {
          status: 404,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }
      flights = [data]
    } else if (check_all) {
      // Check all active flights
      const { data, error } = await supabase
        .from('flights')
        .select('*')
        .eq('monitoring_enabled', true)
        .lt('last_checked', new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()) // Not checked in last 6 hours
        .limit(10) // Process max 10 flights per invocation

      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        })
      }
      flights = data || []
    } else {
      return new Response(JSON.stringify({ error: 'Either flight_id or check_all must be specified' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const results = []

    for (const flight of flights) {
      try {
        // Update last_checked timestamp
        await supabase
          .from('flights')
          .update({ last_checked: new Date().toISOString() })
          .eq('id', flight.id)

        // Prepare search parameters
        const searchParams: FlightSearchParams = {
          origin: flight.departure_airport,
          destination: flight.arrival_airport,
          departureDate: flight.departure_date,
          returnDate: flight.return_date,
          airline: flight.airline || 'Delta'
        }

        console.log(`Checking price for flight ${flight.id}: ${flight.departure_airport} → ${flight.arrival_airport}`)

        // Scrape current price
        const scrapeResult = await scrapeFlightPrice(searchParams)

        if (scrapeResult.success && scrapeResult.price) {
          const newPrice = scrapeResult.price
          const oldPrice = flight.current_price || flight.original_price
          const priceChange = ((newPrice - oldPrice) / oldPrice) * 100

          // Update flight with new price
          const updateData: any = {
            current_price: newPrice,
            last_checked: new Date().toISOString()
          }

          // Update lowest price if this is lower
          if (!flight.lowest_price || newPrice < flight.lowest_price) {
            updateData.lowest_price = newPrice
          }

          await supabase
            .from('flights')
            .update(updateData)
            .eq('id', flight.id)

          // Add to price history
          await supabase
            .from('price_history')
            .insert([{
              flight_id: flight.id,
              price: newPrice,
              airline: scrapeResult.airline || flight.airline,
              flight_numbers: scrapeResult.flight_numbers || [],
              scraped_at: new Date().toISOString()
            }])

          // Check if notification should be sent
          const notificationsEnabled = flight.email_notifications_enabled ?? flight.notifications_enabled ?? true
          const decreaseThreshold = flight.price_decrease_threshold ?? 0.05 // Default 5%
          const increaseThreshold = flight.price_increase_threshold ?? 0.10 // Default 10%
          
          const shouldNotify = notificationsEnabled && (
            (priceChange <= -decreaseThreshold * 100) || // Price decrease
            (priceChange >= increaseThreshold * 100)     // Price increase
          )

          if (shouldNotify) {
            const notificationType = priceChange < 0 ? 'price_drop' : 'price_increase'
            const savings = oldPrice - newPrice
            
            // Create notification record
            const { data: notification } = await supabase
              .from('notifications')
              .insert([{
                flight_id: flight.id,
                user_id: flight.user_id,
                notification_type: notificationType,
                old_price: oldPrice,
                new_price: newPrice,
                price_change_percent: priceChange,
                message: `Flight ${flight.departure_airport} → ${flight.arrival_airport}: Price ${priceChange < 0 ? 'dropped' : 'increased'} by ${Math.abs(priceChange).toFixed(1)}% to $${newPrice}${savings > 0 ? ` (Save $${savings.toFixed(2)})` : ''}`
              }])
              .select()
              .single()

            // Send email notification (async)
            if (notification) {
              fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/send-notification`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${Deno.env.get('SUPABASE_ANON_KEY')}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notification_id: notification.id })
              }).catch(console.error)
            }
          }

          results.push({
            flight_id: flight.id,
            route: `${flight.departure_airport} → ${flight.arrival_airport}`,
            old_price: oldPrice,
            new_price: newPrice,
            price_change: priceChange,
            notification_sent: shouldNotify,
            success: true
          })

        } else {
          console.error(`Failed to scrape price for flight ${flight.id}:`, scrapeResult.error)
          results.push({
            flight_id: flight.id,
            route: `${flight.departure_airport} → ${flight.arrival_airport}`,
            success: false,
            error: scrapeResult.error || 'Failed to scrape price'
          })
        }

      } catch (error) {
        console.error(`Error processing flight ${flight.id}:`, error)
        results.push({
          flight_id: flight.id,
          route: `${flight.departure_airport} → ${flight.arrival_airport}`,
          success: false,
          error: error.message
        })
      }

      // Add small delay between requests to be respectful
      await new Promise(resolve => setTimeout(resolve, 2000))
    }

    return new Response(JSON.stringify({
      success: true,
      flights_checked: flights.length,
      results: results,
      timestamp: new Date().toISOString()
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Price check function error:', error)
    return new Response(JSON.stringify({ 
      error: 'Internal server error',
      details: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})