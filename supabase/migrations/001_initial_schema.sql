-- Initial Schema for Flight Tracker
-- Create tables, RLS policies, and triggers

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Flights table
CREATE TABLE IF NOT EXISTS public.flights (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date DATE NOT NULL,
    return_date DATE,
    outbound_time TEXT,
    return_time TEXT,
    price_threshold DECIMAL(10,2) NOT NULL,
    current_price DECIMAL(10,2),
    lowest_price DECIMAL(10,2),
    original_price DECIMAL(10,2) DEFAULT 0,
    airline TEXT DEFAULT 'Delta',
    flight_numbers TEXT[],
    description TEXT,
    monitoring_enabled BOOLEAN DEFAULT true,
    notifications_enabled BOOLEAN DEFAULT true,
    price_decrease_threshold DECIMAL(3,2) DEFAULT 0.05,
    price_increase_threshold DECIMAL(3,2) DEFAULT 0.10,
    frequency_hours INTEGER DEFAULT 6,
    last_checked TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Price history table
CREATE TABLE IF NOT EXISTS public.price_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    flight_id UUID REFERENCES public.flights(id) ON DELETE CASCADE NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    airline TEXT,
    flight_numbers TEXT[],
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source TEXT DEFAULT 'google_flights'
);

-- Notifications log table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    flight_id UUID REFERENCES public.flights(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE NOT NULL,
    notification_type TEXT NOT NULL, -- 'price_drop', 'price_increase', 'tracking_started'
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    price_change_percent DECIMAL(5,2),
    message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_sent BOOLEAN DEFAULT false,
    email_sent_at TIMESTAMP WITH TIME ZONE
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.flights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- RLS Policies for flights table
CREATE POLICY "Users can view own flights" ON public.flights
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own flights" ON public.flights
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own flights" ON public.flights
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own flights" ON public.flights
    FOR DELETE USING (auth.uid() = user_id);

-- Service role can access all flights (for edge functions)
CREATE POLICY "Service role can access all flights" ON public.flights
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for price_history table
CREATE POLICY "Users can view price history of own flights" ON public.price_history
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.flights 
            WHERE flights.id = price_history.flight_id 
            AND flights.user_id = auth.uid()
        )
    );

CREATE POLICY "Service role can manage price history" ON public.price_history
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for notifications table
CREATE POLICY "Users can view own notifications" ON public.notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage notifications" ON public.notifications
    FOR ALL USING (auth.role() = 'service_role');

-- Triggers and Functions

-- Function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name'),
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON public.flights
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Function to calculate price change percentage
CREATE OR REPLACE FUNCTION public.calculate_price_change(old_price DECIMAL, new_price DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    IF old_price IS NULL OR old_price = 0 THEN
        RETURN 0;
    END IF;
    RETURN ROUND(((new_price - old_price) / old_price * 100), 2);
END;
$$ LANGUAGE plpgsql;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_flights_user_id ON public.flights(user_id);
CREATE INDEX IF NOT EXISTS idx_flights_monitoring ON public.flights(monitoring_enabled, last_checked);
CREATE INDEX IF NOT EXISTS idx_price_history_flight_id ON public.price_history(flight_id, scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id, sent_at DESC);