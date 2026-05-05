CREATE TABLE IF NOT EXISTS quant_runs (
  archive_id TEXT PRIMARY KEY,
  asset TEXT,
  model TEXT,
  horizons_json TEXT,
  run_ids_json TEXT,
  report_date_utc TEXT,
  reference_spot TEXT,
  status TEXT,
  api_version TEXT,
  worker_version TEXT,
  render_git_commit TEXT,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quant_runs_created_at ON quant_runs (created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_quant_runs_asset_created_at ON quant_runs (asset, created_at_utc DESC);

CREATE TABLE IF NOT EXISTS usage_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id TEXT,
  endpoint TEXT NOT NULL,
  asset TEXT,
  model TEXT,
  horizons_json TEXT,
  simulations INTEGER,
  archive_id TEXT,
  status TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_usage_events_client_time ON usage_events (client_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_usage_events_archive ON usage_events (archive_id);

CREATE TABLE IF NOT EXISTS api_clients (
  client_id TEXT PRIMARY KEY,
  email TEXT,
  plan TEXT,
  quota_runs_per_month INTEGER,
  status TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_api_clients_plan ON api_clients (plan);

CREATE TABLE IF NOT EXISTS alert_subscriptions (
  subscription_id TEXT PRIMARY KEY,
  client_id TEXT,
  channel TEXT NOT NULL,
  target TEXT NOT NULL,
  min_level TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_client ON alert_subscriptions (client_id, status);
