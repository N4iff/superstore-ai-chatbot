-- Create chatbot reader
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

-- Only allow SELECT on the restricted view
GRANT SELECT ON v_processed_superstore TO chatbot_reader;

-- Optional safety: prevent any accidental writes if grants change later
ALTER ROLE chatbot_reader SET default_transaction_read_only = on;
