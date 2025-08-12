import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { corsHeaders } from '../_shared/cors.ts'

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    console.log('Cron job triggered: Starting automated price check')

    // Call the check-flight-price function to check all flights
    const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/check-flight-price`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        check_all: true
      })
    })

    const data = await response.json()
    console.log('Cron price check result:', data)

    if (data.success) {
      return new Response(JSON.stringify({
        success: true,
        message: `Automated price check completed successfully`,
        flights_checked: data.flights_checked,
        results: data.results,
        timestamp: new Date().toISOString()
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    } else {
      console.error('Cron price check failed:', data.error)
      return new Response(JSON.stringify({
        success: false,
        error: data.error,
        timestamp: new Date().toISOString()
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

  } catch (error) {
    console.error('Cron job error:', error)
    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})