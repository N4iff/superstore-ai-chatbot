-- Database Initialization Script
-- This script sets up the read-only chatbot user and the data view
-- Run this against your Project 1 database (superstore)

-- =============================================================================
-- STEP 1: Create Read-Only User
-- =============================================================================

-- Create a dedicated read-only user for the chatbot
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'chatbot_reader') THEN
    CREATE ROLE chatbot_reader LOGIN PASSWORD 'CHANGE_ME_STRONG';
  END IF;
END
$$;

-- Allow connection
GRANT CONNECT ON DATABASE superstore TO chatbot_reader;

-- Schema usage
GRANT USAGE ON SCHEMA public TO chatbot_reader;

-- =============================================================================
-- STEP 2: Create Restricted View
-- =============================================================================

-- Restrict chatbot access to processed data only
CREATE OR REPLACE VIEW v_processed_superstore AS
SELECT
  id,
  raw_id,
  ship_mode,
  segment,
  country,
  city,
  state,
  postal_code,
  region,
  category,
  sub_category,
  sales,
  quantity,
  discount,
  profit,
  profit_margin,
  processed_at
FROM processed_superstore;

-- =============================================================================
-- STEP 3: Grant Permissions
-- =============================================================================

-- Only allow SELECT on the restricted view
GRANT SELECT ON v_processed_superstore TO chatbot_reader;

-- Optional safety: prevent any accidental writes if grants change later
ALTER ROLE chatbot_reader SET default_transaction_read_only = on;

-- =============================================================================
-- Verification Queries (optional)
-- =============================================================================

-- Check that the user exists
SELECT rolname, rolcanlogin FROM pg_roles WHERE rolname = 'chatbot_reader';

-- Check view exists
SELECT table_name FROM information_schema.views WHERE table_name = 'v_processed_superstore';

-- Check permissions
SELECT grantee, privilege_type 
FROM information_schema.role_table_grants 
WHERE table_name = 'v_processed_superstore' AND grantee = 'chatbot_reader';

-- =============================================================================
-- Done!
-- =============================================================================