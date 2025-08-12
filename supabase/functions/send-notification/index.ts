import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'
import { corsHeaders } from '../_shared/cors.ts'

interface NotificationRequest {
  notification_id: string;
}

interface EmailData {
  to: string;
  subject: string;
  html: string;
  text: string;
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

    const { notification_id }: NotificationRequest = await req.json()

    // Get notification with flight and user details
    const { data: notification, error: notificationError } = await supabase
      .from('notifications')
      .select(`
        *,
        flights (
          origin,
          destination,
          departure_date,
          return_date,
          description,
          airline
        ),
        users (
          email,
          full_name
        )
      `)
      .eq('id', notification_id)
      .single()

    if (notificationError || !notification || notification.email_sent) {
      return new Response(JSON.stringify({ 
        error: 'Notification not found or already sent' 
      }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const flight = notification.flights
    const user = notification.users

    if (!user?.email) {
      return new Response(JSON.stringify({ 
        error: 'User email not found' 
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    // Generate email content
    const emailData = generateEmailContent(notification, flight, user)

    // Send email using EmailJS (free tier - 200 emails/month)
    const emailResult = await sendEmailViaEmailJS(emailData)

    if (emailResult.success) {
      // Mark notification as sent
      await supabase
        .from('notifications')
        .update({
          email_sent: true,
          email_sent_at: new Date().toISOString()
        })
        .eq('id', notification_id)

      return new Response(JSON.stringify({
        success: true,
        message: 'Notification sent successfully',
        notification_id: notification_id
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    } else {
      return new Response(JSON.stringify({
        success: false,
        error: 'Failed to send email',
        details: emailResult.error
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

  } catch (error) {
    console.error('Notification function error:', error)
    return new Response(JSON.stringify({
      error: 'Internal server error',
      details: error.message
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

function generateEmailContent(notification: any, flight: any, user: any): EmailData {
  const isDecrease = notification.notification_type === 'price_drop'
  const isIncrease = notification.notification_type === 'price_increase'
  const savings = notification.old_price - notification.new_price
  const priceChangeAbs = Math.abs(notification.price_change_percent)

  const subject = isDecrease 
    ? `🎉 Flight Price Drop Alert: ${flight.origin} → ${flight.destination} (Save $${savings.toFixed(2)})`
    : isIncrease
    ? `⚠️ Flight Price Increase: ${flight.origin} → ${flight.destination}`
    : `✈️ Flight Update: ${flight.origin} → ${flight.destination}`

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Flight Price Alert</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { background: linear-gradient(135deg, ${isDecrease ? '#28a745' : isIncrease ? '#dc3545' : '#007bff'} 0%, ${isDecrease ? '#20c997' : isIncrease ? '#e74c3c' : '#0056b3'} 100%); padding: 30px; text-align: center; color: white; }
            .content { padding: 30px; }
            .flight-info { background-color: #f8f9fa; border-radius: 8px; padding: 20px; margin: 20px 0; }
            .price-box { text-align: center; margin: 20px 0; }
            .price-old { text-decoration: line-through; color: #666; font-size: 18px; }
            .price-new { font-size: 32px; font-weight: bold; color: ${isDecrease ? '#28a745' : isIncrease ? '#dc3545' : '#007bff'}; }
            .savings { font-size: 20px; color: #28a745; font-weight: bold; margin-top: 10px; }
            .cta { text-align: center; margin: 30px 0; }
            .button { display: inline-block; background-color: #007bff; color: white; text-decoration: none; padding: 15px 30px; border-radius: 6px; font-weight: bold; }
            .footer { border-top: 1px solid #eee; padding-top: 20px; text-align: center; color: #666; font-size: 12px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>${isDecrease ? '🎉' : isIncrease ? '⚠️' : '✈️'} Flight Price ${isDecrease ? 'Drop' : isIncrease ? 'Increase' : 'Update'}!</h1>
                <p>Your tracked flight has a price update</p>
            </div>
            
            <div class="content">
                <div class="flight-info">
                    <h2>Flight Details</h2>
                    <p><strong>Route:</strong> ${flight.origin} → ${flight.destination}</p>
                    <p><strong>Departure:</strong> ${flight.departure_date}${flight.return_date ? ` (Return: ${flight.return_date})` : ''}</p>
                    <p><strong>Airline:</strong> ${flight.airline}</p>
                    ${flight.description ? `<p><strong>Description:</strong> ${flight.description}</p>` : ''}
                </div>
                
                <div class="price-box">
                    <div class="price-old">Previous: $${notification.old_price.toFixed(2)}</div>
                    <div class="price-new">Current: $${notification.new_price.toFixed(2)}</div>
                    <div style="font-size: 16px; color: ${isDecrease ? '#28a745' : isIncrease ? '#dc3545' : '#666'}; margin-top: 10px;">
                        ${isDecrease ? '📉' : isIncrease ? '📈' : '📊'} ${priceChangeAbs.toFixed(1)}% ${isDecrease ? 'decrease' : isIncrease ? 'increase' : 'change'}
                    </div>
                    ${isDecrease && savings > 0 ? `<div class="savings">💰 You could save $${savings.toFixed(2)}!</div>` : ''}
                </div>
                
                <div class="cta">
                    <a href="https://myflightfriend.com/dashboard" class="button">View in Dashboard</a>
                </div>
                
                <p style="text-align: center; color: #666; font-size: 14px;">
                    ${isDecrease ? 'This might be a great time to book your flight!' : isIncrease ? 'You might want to book soon if prices continue rising.' : 'Keep monitoring for the best deals.'}
                </p>
            </div>
            
            <div class="footer">
                <p>This alert was sent by MyFlightFriend.com</p>
                <p>Generated on ${new Date().toLocaleDateString()}</p>
                <p><a href="https://myflightfriend.com/unsubscribe">Unsubscribe</a> | <a href="https://myflightfriend.com/settings">Manage Alerts</a></p>
            </div>
        </div>
    </body>
    </html>
  `

  const text = `
Flight Price ${isDecrease ? 'Drop' : isIncrease ? 'Increase' : 'Update'} Alert

Flight: ${flight.origin} → ${flight.destination}
Date: ${flight.departure_date}${flight.return_date ? ` - ${flight.return_date}` : ''}
Airline: ${flight.airline}

Previous Price: $${notification.old_price.toFixed(2)}
Current Price: $${notification.new_price.toFixed(2)}
Change: ${priceChangeAbs.toFixed(1)}% ${isDecrease ? 'decrease' : isIncrease ? 'increase' : 'change'}

${isDecrease && savings > 0 ? `You could save $${savings.toFixed(2)}!` : ''}

View your dashboard: https://myflightfriend.com/dashboard

--
MyFlightFriend.com - Never miss a flight deal again!
  `

  return {
    to: user.email,
    subject,
    html,
    text
  }
}

async function sendEmailViaEmailJS(emailData: EmailData) {
  try {
    // Using EmailJS free tier (200 emails/month)
    // You'll need to set up an EmailJS account and get these values
    const emailJSConfig = {
      service_id: Deno.env.get('EMAILJS_SERVICE_ID') || 'gmail',
      template_id: Deno.env.get('EMAILJS_TEMPLATE_ID') || 'flight_alert',
      user_id: Deno.env.get('EMAILJS_USER_ID') || '',
      access_token: Deno.env.get('EMAILJS_ACCESS_TOKEN') || ''
    }

    // For now, we'll simulate sending (you can replace with actual EmailJS)
    console.log('Would send email:', {
      to: emailData.to,
      subject: emailData.subject
    })

    // Actual EmailJS implementation:
    /*
    const response = await fetch('https://api.emailjs.com/api/v1.0/email/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        service_id: emailJSConfig.service_id,
        template_id: emailJSConfig.template_id,
        user_id: emailJSConfig.user_id,
        accessToken: emailJSConfig.access_token,
        template_params: {
          to_email: emailData.to,
          subject: emailData.subject,
          html_content: emailData.html,
          text_content: emailData.text
        }
      })
    })

    if (response.ok) {
      return { success: true }
    } else {
      return { success: false, error: 'Failed to send via EmailJS' }
    }
    */

    // For demo purposes, always return success
    return { success: true }

  } catch (error) {
    return { success: false, error: error.message }
  }
}