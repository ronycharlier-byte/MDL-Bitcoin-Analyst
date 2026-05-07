#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash install_systemd_ubuntu.sh" >&2
  exit 1
fi

WORKER_URL="${WORKER_URL:-https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev}"
MIN_INTERVAL_SECONDS="${MIN_INTERVAL_SECONDS:-15}"

if [[ -z "${REALTIME_INGEST_SECRET:-}" ]]; then
  echo "REALTIME_INGEST_SECRET is required." >&2
  echo "Example: sudo REALTIME_INGEST_SECRET=xxx bash install_systemd_ubuntu.sh" >&2
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip ca-certificates

id -u quantbtc >/dev/null 2>&1 || useradd --system --home /opt/quant-btc-bitget-collector --shell /usr/sbin/nologin quantbtc

install -d -o quantbtc -g quantbtc /opt/quant-btc-bitget-collector
cp collector.py requirements.txt /opt/quant-btc-bitget-collector/
chown -R quantbtc:quantbtc /opt/quant-btc-bitget-collector

python3 -m venv /opt/quant-btc-bitget-collector/.venv
/opt/quant-btc-bitget-collector/.venv/bin/pip install --upgrade pip
/opt/quant-btc-bitget-collector/.venv/bin/pip install -r /opt/quant-btc-bitget-collector/requirements.txt
chown -R quantbtc:quantbtc /opt/quant-btc-bitget-collector/.venv

cat >/etc/quant-btc-bitget-collector.env <<EOF
WORKER_URL=${WORKER_URL}
REALTIME_INGEST_SECRET=${REALTIME_INGEST_SECRET}
MIN_INTERVAL_SECONDS=${MIN_INTERVAL_SECONDS}
EOF
chmod 600 /etc/quant-btc-bitget-collector.env

cp quant-btc-bitget-collector.service /etc/systemd/system/quant-btc-bitget-collector.service
systemctl daemon-reload
systemctl enable quant-btc-bitget-collector
systemctl restart quant-btc-bitget-collector

systemctl --no-pager --full status quant-btc-bitget-collector || true

echo "Installed. Logs:"
echo "journalctl -u quant-btc-bitget-collector -f"
