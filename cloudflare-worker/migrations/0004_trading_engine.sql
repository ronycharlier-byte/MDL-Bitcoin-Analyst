CREATE TABLE IF NOT EXISTS trade_orders (
  order_id TEXT PRIMARY KEY,
  asset TEXT NOT NULL,
  symbol TEXT NOT NULL,
  mode TEXT NOT NULL,
  status TEXT NOT NULL,
  side TEXT NOT NULL,
  order_type TEXT NOT NULL,
  size_usdt REAL,
  size_base REAL,
  limit_price REAL,
  filled_price REAL,
  exchange_order_id TEXT,
  client_oid TEXT,
  archive_id TEXT,
  run_id TEXT,
  proposal_json TEXT,
  execution_json TEXT,
  error TEXT,
  created_by TEXT,
  approved_by TEXT,
  created_at_utc TEXT NOT NULL,
  updated_at_utc TEXT NOT NULL,
  approved_at_utc TEXT,
  executed_at_utc TEXT
);

CREATE INDEX IF NOT EXISTS idx_trade_orders_status_time ON trade_orders (status, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_trade_orders_asset_time ON trade_orders (asset, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_trade_orders_client_oid ON trade_orders (client_oid);

CREATE TABLE IF NOT EXISTS trade_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT,
  kind TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT NOT NULL,
  payload_json TEXT,
  created_at_utc TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_events_order_time ON trade_events (order_id, created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_trade_events_kind_time ON trade_events (kind, created_at_utc DESC);
