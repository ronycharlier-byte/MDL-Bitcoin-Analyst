# Claims Registry

## Purpose

This registry is a compact GPT Custom Knowledge version of extracted claims and governance claims. It intentionally avoids dumping the full raw claim JSONL and excludes massive raw data.

## Extraction Summary

- Copied documents reviewed: 100.
- Chunks created: 165.
- Extracted claims: 39.
- Default reliability: unknown.
- Original corpus files modified: false.

## Reliability Rule

All extracted corpus claims have reliability `unknown` unless independently verified. The GPT must not treat unknown claims as facts without qualification.

## Core Governance Claims

| ID | Claim | Category | Reliability | Status |
|---|---|---|---|---|
| G-001 | The BTC engine must output probabilities, distributions, and risk measures, not certainty. | model_governance | high | inferred from system rules |
| G-002 | The stored latest market data source is Bitget BTCUSDT spot candles; live API runs also append the Bitget BTCUSDT spot ticker. | data_source | high | real |
| G-003 | Fundamental features are absent in the latest export. | data_quality | high | absent |
| G-004 | The latest confidence score is 42/100. | model_output | high | inferred |
| G-005 | Stress tests are hypothetical shocks, not predictions. | risk | high | inferred |
| G-006 | Backtests are empirical diagnostics, not proof of future performance. | validation | high | inferred |
| G-007 | The GPT must distinguish real, mock, absent, and inferred information. | governance | high | inferred |
| G-008 | The GPT must not give buy/sell instructions. | governance | high | inferred |
| G-009 | Every precise quantitative figure must carry source, report date, run ID, reference spot when relevant, and status. | governance | high | inferred |
| G-010 | Bull, bear, and range probabilities must be checked for completeness; residual probability must be shown as non-classified / transition. | governance | high | inferred |
| G-011 | VaR/CVaR must be described as simulated loss measures with explicit sign convention. | risk | high | inferred |
| G-012 | If confidence score is below 50/100, directional language must be weak or fragile. | governance | high | inferred |

## Extracted Corpus Claim Themes

The extraction pipeline found claims around:

- market prudence;
- volatility and temporal validity;
- risk of overclaiming;
- distinction between doctrine, proof, hypothesis, implementation, and monitoring;
- need to revalidate volatile objects;
- explicit handling of assumptions.

These corpus-derived claims are useful for governance tone, but reliability remains `unknown`.

## Representative Extracted Claims

| Claim ID | Summary | Category | Reliability |
|---|---|---|---|
| claim_000002 | Hypotheses, limits, and non-established information should be explicitly signalled. | hypotheses | unknown |
| claim_000003 | Distinction should be explicit between doctrine, proof, implementation, monitoring, and hypothesis. | hypotheses | unknown |
| claim_000004 | Reduction of hallucination risk should be claimed with prudence. | risks | unknown |
| claim_000005 | Separate primary source, secondary source, and volatile source. | volatility | unknown |
| claim_000006 | Prices, quotas, and vendor data should be revalidated before current use. | market | unknown |
| claim_000009 | Market demand, pricing, traction, independent validation, and benchmarked performance are non-established unless proven. | market | unknown |
| claim_000012 | Volatile objects require freshness, expiration, and usage policy. | volatility | unknown |
| claim_000014 | Evidence registers and prudent public positioning reduce overclaiming risk. | risks | unknown |
| claim_000017 | Volatile objects should be revalidated periodically. | volatility | unknown |

## Usage Rules For GPT

- Treat this registry as governance support, not market data.
- Do not quote raw JSON/package-lock claims as financial evidence.
- If a claim is `unknown`, say it is unverified or corpus-derived.
- Prefer the latest report for numeric model outputs.
- Prefer governance rules for answer behavior.
