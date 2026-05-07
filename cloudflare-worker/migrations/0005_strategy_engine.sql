CREATE TABLE IF NOT EXISTS strategy_signals (
  signal_id TEXT PRIMARY KEY,
  asset TEXT NOT NULL,
  preset TEXT NOT NULL,
  horizon INTEGER NOT NULL,
  ensemble_score REAL,
  ensemble_action TEXT,
  agreement REAL,
  confidence REAL,
  archive_id TEXT,
  run_id TEXT,
  payload_json TEXT NOT NULL,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_strategy_signals_asset_time ON strategy_signals (asset, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_signals_action_time ON strategy_signals (ensemble_action, created_at_utc DESC);
