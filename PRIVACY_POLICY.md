# Privacy Policy

This GPT uses the Quant BTC Model API to run probabilistic Bitcoin analysis.

## Data Sent To The API

When a user requests an analysis, the GPT may send:

- asset symbol, normally BTC;
- requested horizon or timeframes;
- number of simulations;
- selected model name;
- runtime flags such as `skip_corpus` or `no_online`.

The GPT should not send personal information to the API. Telegram operation may process the configured owner chat ID, username, command text, callback data and update ID solely to authenticate, deduplicate and answer commands.

## Data Returned By The API

The API may return:

- market data status;
- probabilistic distributions;
- risk metrics;
- stress test outputs;
- model run metadata;
- version metadata;
- provenance fields.

## No Financial Advice

Outputs are probabilistic research information only. They are not financial advice, investment advice, or deterministic predictions.

## Data Retention

The API may generate logs and model run artifacts for debugging, provenance, and system reliability. These artifacts are not intended to contain personal data. Telegram update IDs used for replay protection should be removed after the configured retention window (recommended seven days); Telegram sessions and alert subscriptions should be deleted when disabled or after a verified deletion request. Analysis archives are retained according to the operator's documented policy, recommended no longer than 365 days absent a legal/audit need.

Secrets, full webhook URLs, raw client keys and unrelated Telegram message content must not be written to logs or archives. See `docs/SECURITY.md` for the deletion scope across SQLite, D1 and external mirrors.

## Third-Party Data Sources

The system may use public market/fundamental sources and service providers such as Bitget, Stooq, Cloudflare, Render, Telegram and configured alert/storage providers. Their own privacy policies apply.

## Contact

For questions about this project, contact the repository owner through GitHub.
