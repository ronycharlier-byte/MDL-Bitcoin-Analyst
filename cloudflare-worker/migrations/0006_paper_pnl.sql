CREATE TABLE IF NOT EXISTS paper_pnl_snapshots (
  order_id TEXT NOT NULL,
  horizon_days INTEGER NOT NULL,
  asset TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price REAL,
  mark_price REAL,
  size_base REAL,
  size_usdt REAL,
  pnl_usdt REAL,
  pnl_pct REAL,
  created_at_utc TEXT NOT NULL,
  PRIMARY KEY (order_id, horizon_days)
);

CREATE INDEX IF NOT EXISTS idx_paper_pnl_asset_time ON paper_pnl_snapshots (asset, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_paper_pnl_horizon_time ON paper_pnl_snapshots (horizon_days, created_at_utc DESC);
