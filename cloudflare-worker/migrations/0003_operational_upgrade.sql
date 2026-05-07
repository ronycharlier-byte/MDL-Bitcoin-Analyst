CREATE TABLE IF NOT EXISTS system_locks (
  name TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  acquired_at_utc TEXT NOT NULL,
  expires_at_utc TEXT NOT NULL,
  metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_system_locks_expires ON system_locks (expires_at_utc);

CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  asset TEXT NOT NULL,
  source TEXT NOT NULL,
  kind TEXT NOT NULL,
  price REAL,
  bid REAL,
  ask REAL,
  spread_bps REAL,
  funding_rate REAL,
  open_interest REAL,
  liquidations_status TEXT,
  payload_json TEXT,
  observed_at_utc TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_asset_time ON market_snapshots (asset, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_market_snapshots_kind_time ON market_snapshots (kind, created_at_utc DESC);

CREATE TABLE IF NOT EXISTS deep_jobs (
  job_id TEXT PRIMARY KEY,
  asset TEXT NOT NULL,
  preset TEXT NOT NULL,
  status TEXT NOT NULL,
  request_json TEXT,
  result_archive_id TEXT,
  error TEXT,
  notify_channel TEXT,
  notify_target TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  completed_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_deep_jobs_status_time ON deep_jobs (status, created_at_utc ASC);

CREATE TABLE IF NOT EXISTS user_alert_rules (
  rule_id TEXT PRIMARY KEY,
  client_id TEXT,
  chat_id TEXT,
  asset TEXT NOT NULL,
  metric TEXT NOT NULL,
  operator TEXT NOT NULL,
  threshold REAL NOT NULL,
  horizon INTEGER,
  status TEXT NOT NULL,
  cooldown_seconds INTEGER NOT NULL DEFAULT 1800,
  last_triggered_at_utc TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_alert_rules_status_asset ON user_alert_rules (status, asset);
CREATE INDEX IF NOT EXISTS idx_user_alert_rules_chat ON user_alert_rules (chat_id, status);

CREATE TABLE IF NOT EXISTS telegram_sessions (
  chat_id TEXT PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_command TEXT,
  muted_until_utc TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL
);

