# Model governance

## Intended use

The engine produces conditional BTC distributions for research, model-risk review and educational analysis. It is not a deterministic forecaster, portfolio optimizer, suitability engine, trading recommendation or execution system.

## Reproducibility

Seeds are derived with SHA-256 rather than Python's process-randomized `hash()`. A production run should persist input hashes, seeds, dependency versions, git/model/schema versions, time bounds, shared spot snapshot, simulations per model, runtime and warnings. The current response contains most but not all of this run manifest; completion is P1 in the migration plan.

## Ensemble policy

The ensemble scores models from walk-forward Brier score, calibration error and P10/P90 coverage. Scores are shrunk 20% toward equal weighting and capped at 35% per component. When out-of-sample evidence is absent, weights are equal and marked absent rather than presented as learned.

Weights are descriptive model-combination parameters, not evidence of causal truth. Weight diagnostics, observations and fallbacks must be archived.

## Backtesting

Backtests are strict chronological walk-forward evaluations with a rolling training window. Report period, observations, hit rate, Brier score, log loss, expected calibration error, calibration bins, P10/P90 coverage, VaR 95/99 breach rates, bootstrap confidence interval and a zero-drift random-walk benchmark.

Known limitations: there is no fully isolated train/validation/test orchestration across every model, no multiple-testing correction, and no implemented Kupiec/Christoffersen test yet. These are not silently replaced with proxy metrics.

## Risk definitions

VaR and CVaR are positive simulated loss magnitudes, not guaranteed maximum losses. Drawdown from paths is preferred; terminal-return fallback is labeled. Stress scenarios are inferred counterfactuals, never observed outcomes. Position-sizing outputs remain internal/information-only and must not be phrased as allocations.

## Confidence

Confidence is a vector: data quality, Monte Carlo sampling error, multi-seed stability, model disagreement, regime ambiguity, backtest calibration/coverage and sample size. Data quality separately exposes freshness, completeness, consistency, source integrity and temporal alignment. The scalar 0–100 score is only a weighted display summary. Any blocker or score below 50 requires weak/fragile language.

## Review and release gates

A model change requires: contract tests, invariant tests, temporal leakage review, comparison with baseline, documented evaluation period, reproducible seed, artifact/version update and human review. No metric threshold automatically deploys or authorizes financial action.

## Drift and incidents

Monitor source freshness, missingness, spot discrepancies, calibration, coverage, breach rates, ensemble concentration, schema failures and archive failures. A critical drift alert blocks claims of readiness; it does not trigger trading. Incident records must identify affected archives and versions without storing secrets.
