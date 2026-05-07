CREATE TABLE IF NOT EXISTS strategy_performance_snapshots (
  signal_id TEXT NOT NULL,
  horizon_days INTEGER NOT NULL,
  asset TEXT NOT NULL,
  action TEXT NOT NULL,
  entry_price REAL,
  mark_price REAL,
  return_pct REAL,
  outcome_label TEXT,
  archive_id TEXT,
  run_id TEXT,
  signal_created_at_utc TEXT,
  evaluated_at_utc TEXT NOT NULL,
  PRIMARY KEY (signal_id, horizon_days)
);

CREATE INDEX IF NOT EXISTS idx_strategy_perf_asset_time ON strategy_performance_snapshots (asset, evaluated_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_perf_horizon_outcome ON strategy_performance_snapshots (horizon_days, outcome_label);

CREATE TABLE IF NOT EXISTS virtual_portfolio_ledger (
  event_id TEXT PRIMARY KEY,
  asset TEXT NOT NULL,
  kind TEXT NOT NULL,
  side TEXT,
  quantity REAL,
  price REAL,
  notional_usdt REAL,
  source_order_id TEXT,
  payload_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_virtual_portfolio_asset_time ON virtual_portfolio_ledger (asset, created_at_utc DESC);
