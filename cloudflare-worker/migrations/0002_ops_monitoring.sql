CREATE TABLE IF NOT EXISTS ops_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  payload_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ops_events_fingerprint_time ON ops_events (fingerprint, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_ops_events_status_time ON ops_events (status, created_at_utc DESC);
