# Quant BTC Model

Autonomous probabilistic quantitative engine for Bitcoin inside this corpus.

The system produces probabilities, distributions, and risk measures. It never emits certainty or a deterministic price prediction.

## Created structure

```text
quant_btc_model/
  data/
    raw/
    processed/
    features/
    backtests/
    simulations/
    quant_model.db
  knowledge_base/
    corpus_raw/
    corpus_chunks/
    metadata/
    claims/
  models/
  reports/
    latest_report.md
    dashboard_summary.md
  logs/
    system.log
  src/
  README.md
```

## Quick start

From `C:\Users\ronyc\Desktop\Corpus\quant_btc_model`:

```powershell
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble
```

Useful options:

```powershell
python src/main.py --asset BTC --horizon 90 --simulations 50000 --model garch
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble --no-online
python src/main.py --asset BTC --horizon 365 --simulations 200000 --model ensemble --skip-corpus
```

## Data policy

- No source file outside `quant_btc_model` is modified.
- Corpus integration copies relevant files into `knowledge_base/corpus_raw`.
- Market loading uses local CSV first, then public online candles (`Bitget`, then `CoinGecko`) unless `--no-online` is set.
- If real market data are unavailable, the engine generates synthetic prices tagged `mock` and logs `MOCK`.
- Missing fundamental fields remain SQL `NULL` and are logged in `logs/system.log`.
- SQLite tables include `timestamp`, `source`, and `statut` (`real`, `mock`, or `missing`).

## Optional input files

Place audited CSV files in `data/raw`.

Market prices:

```csv
timestamp,open,high,low,close,volume
2024-01-01,42000,43000,41000,42500,123456789
```

Supported names:

- `BTC_prices.csv`
- `btc_prices.csv`
- `market_prices.csv`

Fundamentals:

```csv
timestamp,etf_flows,funding_rate,open_interest,liquidations,hash_rate,exchange_reserves,stablecoins_supply,dxy,us_rates,nasdaq
2024-01-01,,,,,,,,,,
```

Supported names:

- `BTC_fundamentals.csv`
- `btc_fundamentals.csv`
- `fundamental_features.csv`

## SQLite tables

- `market_prices`
- `technical_features`
- `fundamental_features`
- `risk_metrics`
- `model_runs`
- `simulation_results`
- `backtest_results`

Database path:

```text
data/quant_model.db
```

## Models

Implemented in `src`:

- `monte_carlo.py`: lognormal Monte Carlo from historical daily returns.
- `student_t_model.py`: heavy-tailed Student-t simulation.
- `jump_diffusion.py`: jump diffusion with historical tail calibration.
- `garch_model.py`: GARCH-like conditional variance simulation.
- `regime_switching.py`: calm/stress state simulation.
- `liquidation_model.py`: downside cascade shock model.
- `correlation_model.py`: macro-sensitive correlation model with NULL-safe fundamentals.
- `ensemble_model.py`: dynamic weighting by performance, error, and calibration inputs.

## Risk metrics

Implemented in `src/risk_metrics.py`:

- VaR 95 and 99
- CVaR 95 and 99
- skewness
- kurtosis
- max drawdown
- conditional volatility

## Corpus pipeline

`src/corpus_pipeline.py`:

1. Scans the existing corpus for relevant text files.
2. Copies relevant files into `knowledge_base/corpus_raw`.
3. Writes provenance into `knowledge_base/metadata/corpus_copy_manifest.jsonl`.
4. Chunks documents into 500-1000 token JSON chunks.
5. Extracts claims into `knowledge_base/claims/claims.jsonl`.

Claim categories:

- marche
- macro
- volatilite
- risques
- hypotheses

Default reliability is `unknown`.

## Reports

The run creates:

- `reports/latest_report.md`
- `reports/dashboard_summary.md`
- `data/simulations/<run_id>_summary.json`

Reports include data used, missing data, assumptions, model weights, P10/median/P90 distribution, threshold probabilities, VaR/CVaR, stress tests, drawdown, bull/bear/range probabilities, confidence score, backtest results, and explicit limits.

## Quality rules

- The engine is modular and NULL-safe.
- Data quality status is explicit.
- Mock data are never presented as real data.
- Exceptions are caught, logged, and written to `data/last_error.json`.
- This is research infrastructure, not financial advice.
