import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

// Check if credentials are properly configured
export const isSupabaseConfigured = 
  supabaseUrl.length > 0 && 
  !supabaseUrl.includes('example.supabase.co') && 
  supabaseAnonKey.length > 0 && 
  !supabaseAnonKey.includes('example-anon-key')

export const supabase = isSupabaseConfigured 
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null
