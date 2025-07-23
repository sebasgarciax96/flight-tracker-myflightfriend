-- Fix RLS Policies for Flights Table
-- Run this in Supabase SQL Editor AFTER running the user profile trigger

-- Drop existing policies (if they exist)
DROP POLICY IF EXISTS "Users can view own flights" ON public.flights;
DROP POLICY IF EXISTS "Users can insert own flights" ON public.flights;
DROP POLICY IF EXISTS "Users can update own flights" ON public.flights;
DROP POLICY IF EXISTS "Users can delete own flights" ON public.flights;

-- Create new, simpler RLS policies that work with auth.uid()
CREATE POLICY "Users can view own flights" ON public.flights
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own flights" ON public.flights
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own flights" ON public.flights
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own flights" ON public.flights
    FOR DELETE USING (auth.uid() = user_id);

-- Verify the flights table structure
-- Run this to check your table structure:
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'flights' AND table_schema = 'public';

-- If you need to add the user_id column (only run if it doesn't exist):
-- ALTER TABLE public.flights ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);