-- Set up automated cron jobs for flight price checking
-- This requires the pg_cron extension

-- Enable pg_cron extension (run this as superuser in production)
-- CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule price checking every 6 hours
-- This will call the check-flight-price Edge Function
SELECT cron.schedule(
    'check-flight-prices-every-6-hours',
    '0 */6 * * *', -- Every 6 hours at minute 0
    $$
    SELECT
        net.http_post(
            url := 'https://wacrvpraqzvpbsbzvlxp.supabase.co/functions/v1/check-flight-price',
            headers := jsonb_build_object(
                'Content-Type', 'application/json',
                'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key', true)
            ),
            body := jsonb_build_object(
                'check_all', true
            )
        ) as request_id;
    $$
);

-- Schedule cleanup of old price history (keep last 30 days)
SELECT cron.schedule(
    'cleanup-old-price-history',
    '0 2 * * *', -- Daily at 2 AM
    $$
    DELETE FROM public.price_history 
    WHERE scraped_at < NOW() - INTERVAL '30 days';
    $$
);

-- Schedule cleanup of old notifications (keep last 90 days)
SELECT cron.schedule(
    'cleanup-old-notifications',
    '0 3 * * *', -- Daily at 3 AM
    $$
    DELETE FROM public.notifications 
    WHERE sent_at < NOW() - INTERVAL '90 days';
    $$
);

-- View all scheduled jobs
-- SELECT * FROM cron.job;

-- To unschedule a job (if needed):
-- SELECT cron.unschedule('check-flight-prices-every-6-hours');