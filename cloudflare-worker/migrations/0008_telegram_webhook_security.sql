CREATE TABLE IF NOT EXISTS telegram_updates (
  update_id INTEGER PRIMARY KEY,
  received_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telegram_updates_received_at
  ON telegram_updates (received_at_utc DESC);
