-- Create views
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
