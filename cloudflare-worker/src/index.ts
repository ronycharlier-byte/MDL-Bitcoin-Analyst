interface Env {
  MAX_SIMULATIONS?: string;
  DEFAULT_SIMULATIONS?: string;
  DEFAULT_HORIZON?: string;
}

interface RunRequest {
  asset?: string;
  horizon?: number;
  simulations?: number;
  model?: string;
}

interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type"
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: JSON_HEADERS });
    }

    try {
      if (url.pathname === "/health" && request.method === "GET") {
        return json({
          status: "ok",
          service: "quant-btc-model-lite-worker",
          mode: "quant_lite_probabilistic",
          timestamp: new Date().toISOString()
        });
      }

      if (url.pathname === "/latest" && request.method === "GET") {
        return json({
          status: "available",
          service: "quant-btc-model-lite-worker",
          latest_report: null,
          dashboard_summary: null,
          message: "This Worker is stateless. Call POST /run for a fresh probabilistic quant-lite result.",
          data_status: {
            latest_report: "absent",
            dashboard_summary: "absent"
          }
        });
      }

      if (url.pathname === "/run" && request.method === "POST") {
        const body = await readJson(request);
        const result = await runQuantLite(body, env);
        return json(result);
      }

      return json({ error: "not_found", path: url.pathname }, 404);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return json({
        error: "quant_lite_run_failed",
        message,
        data_status: {
          model_output: "absent",
          market_data: "absent"
        },
        warning: "No deterministic prediction was produced."
      }, 500);
    }
  }
};

async function readJson(request: Request): Promise<RunRequest> {
  try {
    const parsed = await request.json();
    if (!parsed || typeof parsed !== "object") {
      return {};
    }
    return parsed as RunRequest;
  } catch {
    return {};
  }
}

async function runQuantLite(input: RunRequest, env: Env): Promise<Record<string, unknown>> {
  const asset = normalizeAsset(input.asset);
  if (asset !== "BTC") {
    throw new Error("Only BTC is supported by the quant-lite Worker.");
  }

  const maxSimulations = clampInt(parseNumber(env.MAX_SIMULATIONS, 5000), 100, 5000);
  const defaultSimulations = clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, maxSimulations);
  const defaultHorizon = clampInt(parseNumber(env.DEFAULT_HORIZON, 365), 1, 3650);
  const requestedSimulations = clampInt(parseNumber(input.simulations, defaultSimulations), 100, 250000);
  const simulations = Math.min(requestedSimulations, maxSimulations);
  const horizon = clampInt(parseNumber(input.horizon, defaultHorizon), 1, 3650);
  const requestedModel = String(input.model || "quant_lite");
  const model = requestedModel === "ensemble" ? "quant_lite" : "quant_lite";

  const runStartedAt = new Date();
  const modelRunId = `cfql_${runStartedAt.toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}_${randomRunSuffix()}`;

  const candles = await fetchBitgetCandles();
  if (candles.length < 30) {
    throw new Error("Insufficient Bitget market history for quant-lite run.");
  }

  const sorted = candles.sort((a, b) => a.timestamp - b.timestamp);
  const closes = sorted.map((candle) => candle.close).filter((value) => Number.isFinite(value) && value > 0);
  const returns = logReturns(closes);
  const spot = closes[closes.length - 1];
  const calibration = calibrateReturns(returns);
  const seed = hashString(`${modelRunId}:${spot}:${horizon}:${simulations}`);
  const simulatedReturns = simulateTerminalReturns(calibration, horizon, simulations, seed);
  const sortedReturns = [...simulatedReturns].sort((a, b) => a - b);
  const terminalPrices = sortedReturns.map((value) => spot * Math.exp(value));
  const simpleReturns = sortedReturns.map((value) => Math.exp(value) - 1);

  const distribution = {
    p10_return: quantile(simpleReturns, 0.10),
    median_return: quantile(simpleReturns, 0.50),
    p90_return: quantile(simpleReturns, 0.90),
    p10_price: quantile(terminalPrices, 0.10),
    median_price: quantile(terminalPrices, 0.50),
    p90_price: quantile(terminalPrices, 0.90),
    probability_positive_return: meanIndicator(simpleReturns, (value) => value > 0),
    probability_loss_10_or_more: meanIndicator(simpleReturns, (value) => value <= -0.10),
    probability_loss_30_or_more: meanIndicator(simpleReturns, (value) => value <= -0.30),
    probability_gain_30_or_more: meanIndicator(simpleReturns, (value) => value >= 0.30)
  };

  const bull = meanIndicator(simpleReturns, (value) => value >= 0.20);
  const bear = meanIndicator(simpleReturns, (value) => value <= -0.20);
  const range = meanIndicator(simpleReturns, (value) => value > -0.10 && value < 0.10);
  const regimeSum = bull + bear + range;
  const nonClassified = Math.max(0, 1 - regimeSum);
  const regimeDistribution = {
    bull,
    bear,
    range,
    non_classified_transition: nonClassified,
    sum_without_residual: regimeSum,
    sum_with_residual: regimeSum + nonClassified,
    is_complete: Math.abs((regimeSum + nonClassified) - 1) <= 0.01,
    note: nonClassified > 0.01
      ? "A residual bucket is shown because bull/bear/range do not cover every simulated trajectory."
      : "Bull/bear/range plus residual total approximately 100%."
  };

  const risk = calculateRisk(simpleReturns, returns);
  const stress = calculateStressScenarios(spot);
  const confidence = calculateConfidence(candles.length, simulations, calibration, requestedSimulations > simulations);
  const runCompletedAt = new Date();

  const warnings = [
    "Probabilistic infrastructure only; not financial advice.",
    "Cloudflare Worker quant-lite is a lightweight runtime, not the full Python/numpy engine.",
    "Fundamental variables are absent in this Worker result unless supplied by a future connected store.",
    "Precise numbers are valid only for this response and must be cited with model_run_id, report_date, reference_spot and status.",
    "VaR/CVaR are expressed as simulated returns, so negative values represent losses."
  ];
  if (requestedSimulations > simulations) {
    warnings.push(`Requested simulations capped from ${requestedSimulations} to ${simulations} to protect the free Worker runtime.`);
  }

  return {
    status: "ok",
    service: "quant-btc-model-lite-worker",
    asset,
    horizon,
    simulations,
    requested_simulations: requestedSimulations,
    model,
    model_version: "cloudflare_quant_lite_v1",
    model_run_id: modelRunId,
    report_date: runCompletedAt.toISOString(),
    provenance: {
      source_report: "runtime_response",
      report_date: runCompletedAt.toISOString(),
      run_started_at: runStartedAt.toISOString(),
      run_completed_at: runCompletedAt.toISOString(),
      model_run_id: modelRunId,
      model_version: "cloudflare_quant_lite_v1",
      reference_spot: spot,
      reference_spot_source: "bitget_btcusdt_spot_candles",
      reference_spot_timestamp: new Date(sorted[sorted.length - 1].timestamp).toISOString(),
      calculation_origin: "cloudflare_worker_quant_lite_runtime",
      status: "mixed"
    },
    data_status: {
      market_prices: "real",
      market_source: "bitget_btcusdt_spot_candles",
      simulation_results: "inferred",
      risk_metrics: "inferred",
      stress_tests: "inferred",
      fundamental_features: "absent",
      corpus_knowledge_base: "absent",
      full_python_engine: "absent"
    },
    calibration: {
      daily_observations: returns.length,
      annualized_drift: calibration.mean * 365,
      annualized_volatility: calibration.std * Math.sqrt(365),
      jump_probability_daily: calibration.jumpProbability,
      jump_mean_log_return: calibration.jumpMean,
      jump_std_log_return: calibration.jumpStd
    },
    distribution,
    regime_distribution: regimeDistribution,
    risk_metrics: risk,
    stress_tests: stress,
    confidence_score: confidence,
    assumptions: [
      "Historical daily Bitget BTCUSDT spot candles are used as the real market input.",
      "Terminal distribution is inferred from a heavy-tail jump approximation calibrated on recent log returns.",
      "No ETF flow, DXY, rates, Nasdaq, funding, open interest, liquidation, hash rate, exchange reserve or stablecoin fields are connected in the Worker.",
      "The result is a scenario distribution, not a deterministic forecast."
    ],
    governance: {
      allowed_language: [
        "Le modele indique une distribution probabiliste sous hypotheses.",
        "Le biais est probabiliste et fragile si le confidence score est inferieur a 50/100.",
        "Cette VaR est exprimee comme un rendement simule negatif."
      ],
      forbidden_language: [
        "Bitcoin va atteindre ce prix.",
        "Prediction certaine.",
        "Objectif garanti."
      ],
      numeric_traceability_required: true,
      no_hidden_extrapolation: true
    },
    warnings
  };
}

async function fetchBitgetCandles(): Promise<Candle[]> {
  const candles: Candle[] = [];
  let endTime = Date.now();

  for (let page = 0; page < 8; page += 1) {
    const url = new URL("https://api.bitget.com/api/v2/spot/market/history-candles");
    url.searchParams.set("symbol", "BTCUSDT");
    url.searchParams.set("granularity", "1Dutc");
    url.searchParams.set("endTime", String(endTime));
    url.searchParams.set("limit", "200");

    const response = await fetch(url.toString(), {
      headers: {
        "accept": "application/json"
      }
    });

    if (!response.ok) {
      throw new Error(`Bitget candles request failed with HTTP ${response.status}.`);
    }

    const payload = await response.json() as { data?: unknown };
    const rows = Array.isArray(payload.data) ? payload.data : [];
    if (rows.length === 0) {
      break;
    }

    for (const row of rows) {
      if (!Array.isArray(row) || row.length < 6) {
        continue;
      }
      const timestamp = Number(row[0]);
      const open = Number(row[1]);
      const high = Number(row[2]);
      const low = Number(row[3]);
      const close = Number(row[4]);
      const volume = Number(row[5]);
      if ([timestamp, open, high, low, close].every(Number.isFinite) && close > 0) {
        candles.push({ timestamp, open, high, low, close, volume });
      }
    }

    const oldest = Math.min(...candles.map((candle) => candle.timestamp));
    if (!Number.isFinite(oldest) || candles.length >= 1000) {
      break;
    }
    endTime = oldest - 1;
  }

  const unique = new Map<number, Candle>();
  for (const candle of candles) {
    unique.set(candle.timestamp, candle);
  }
  return Array.from(unique.values());
}

function normalizeAsset(asset: unknown): string {
  return String(asset || "BTC").trim().toUpperCase();
}

function parseNumber(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clampInt(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function logReturns(closes: number[]): number[] {
  const values: number[] = [];
  for (let index = 1; index < closes.length; index += 1) {
    const previous = closes[index - 1];
    const current = closes[index];
    if (previous > 0 && current > 0) {
      values.push(Math.log(current / previous));
    }
  }
  return values;
}

function calibrateReturns(returns: number[]) {
  const meanValue = mean(returns);
  const stdValue = std(returns, meanValue) || 0.01;
  const sorted = [...returns].sort((a, b) => a - b);
  const lowerTailCutoff = quantile(sorted, 0.05);
  const tail = sorted.filter((value) => value <= lowerTailCutoff);
  const jumpProbability = clamp(tail.length / Math.max(1, returns.length), 0.01, 0.12);
  const jumpMean = tail.length > 0 ? mean(tail) : -2 * stdValue;
  const jumpStd = tail.length > 1 ? std(tail, jumpMean) || stdValue : stdValue;
  const cappedMean = clamp(meanValue, -0.01, 0.01);
  const cappedStd = clamp(stdValue, 0.005, 0.12);

  return {
    mean: cappedMean,
    std: cappedStd,
    jumpProbability,
    jumpMean: clamp(jumpMean, -0.30, -0.01),
    jumpStd: clamp(jumpStd, 0.005, 0.15)
  };
}

function simulateTerminalReturns(
  calibration: ReturnType<typeof calibrateReturns>,
  horizon: number,
  simulations: number,
  seed: number
): number[] {
  const rng = mulberry32(seed);
  const results: number[] = [];
  const drift = (calibration.mean - 0.5 * calibration.std * calibration.std) * horizon;
  const diffusionScale = calibration.std * Math.sqrt(horizon);
  const expectedJumps = calibration.jumpProbability * horizon;

  for (let index = 0; index < simulations; index += 1) {
    const diffusion = diffusionScale * randomNormal(rng);
    const jumpCount = samplePoisson(expectedJumps, rng);
    let jumpReturn = 0;
    for (let jump = 0; jump < jumpCount; jump += 1) {
      jumpReturn += calibration.jumpMean + calibration.jumpStd * randomNormal(rng);
    }
    results.push(drift + diffusion + jumpReturn);
  }
  return results;
}

function samplePoisson(lambda: number, rng: () => number): number {
  if (lambda <= 0) {
    return 0;
  }
  if (lambda > 30) {
    return Math.max(0, Math.round(lambda + Math.sqrt(lambda) * randomNormal(rng)));
  }
  const limit = Math.exp(-lambda);
  let product = 1;
  let count = 0;
  do {
    count += 1;
    product *= rng();
  } while (product > limit);
  return count - 1;
}

function calculateRisk(simpleReturns: number[], dailyReturns: number[]) {
  const sorted = [...simpleReturns].sort((a, b) => a - b);
  const var95 = quantile(sorted, 0.05);
  const var99 = quantile(sorted, 0.01);
  const tail95 = sorted.filter((value) => value <= var95);
  const tail99 = sorted.filter((value) => value <= var99);
  const meanValue = mean(simpleReturns);
  const stdValue = std(simpleReturns, meanValue);
  const historicalConditionalVol = std(dailyReturns.slice(-60), mean(dailyReturns.slice(-60))) * Math.sqrt(365);

  return {
    var_95_return: var95,
    var_99_return: var99,
    cvar_95_return: tail95.length > 0 ? mean(tail95) : var95,
    cvar_99_return: tail99.length > 0 ? mean(tail99) : var99,
    var_95_interpretation: "VaR 95 du rendement simule: les 5% pires scenarios commencent autour de cette perte ou pire.",
    cvar_95_interpretation: "CVaR 95 du rendement simule: perte moyenne estimee dans les scenarios pires que la VaR 95.",
    skewness: skewness(simpleReturns, meanValue, stdValue),
    kurtosis: kurtosis(simpleReturns, meanValue, stdValue),
    historical_max_drawdown: maxDrawdownFromReturns(dailyReturns),
    conditional_volatility: Number.isFinite(historicalConditionalVol) ? historicalConditionalVol : null
  };
}

function calculateStressScenarios(spot: number) {
  const scenarios = [
    ["crash_30", -0.30],
    ["crash_50", -0.50],
    ["massive_etf_outflow", -0.18],
    ["dxy_spike", -0.12],
    ["us_rates_spike", -0.15],
    ["nasdaq_drop", -0.20],
    ["liquidation_cascade", -0.35]
  ] as const;

  return scenarios.map(([name, shock]) => ({
    scenario: name,
    shock_return: shock,
    stressed_price: spot * (1 + shock),
    status: "inferred",
    source: "deterministic stress shock library in Worker runtime"
  }));
}

function calculateConfidence(
  candleCount: number,
  simulations: number,
  calibration: ReturnType<typeof calibrateReturns>,
  capped: boolean
) {
  let score = 35;
  score += Math.min(25, candleCount / 40);
  score += Math.min(15, simulations / 500);
  score += calibration.std > 0 && calibration.std < 0.08 ? 10 : 3;
  score -= capped ? 8 : 0;
  score -= 15;
  const rounded = Math.round(clamp(score, 0, 100));
  return {
    score: rounded,
    level: rounded < 50 ? "low_to_moderate_fragile" : rounded < 70 ? "moderate" : "high",
    drivers: {
      market_price_quality: "real_bitget_spot_candles",
      model_stability: "simplified_terminal_distribution",
      backtest_performance: "absent",
      uncertainty: "elevated_due_to_missing_fundamentals_and_worker_runtime_cap"
    }
  };
}

function mean(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function std(values: number[], meanValue = mean(values)): number {
  if (values.length < 2) {
    return 0;
  }
  const variance = values.reduce((sum, value) => sum + (value - meanValue) ** 2, 0) / (values.length - 1);
  return Math.sqrt(Math.max(0, variance));
}

function quantile(sortedOrValues: number[], q: number): number {
  if (sortedOrValues.length === 0) {
    return 0;
  }
  const sorted = isSorted(sortedOrValues) ? sortedOrValues : [...sortedOrValues].sort((a, b) => a - b);
  const position = (sorted.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) {
    return sorted[lower];
  }
  const weight = position - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

function isSorted(values: number[]): boolean {
  for (let index = 1; index < values.length; index += 1) {
    if (values[index] < values[index - 1]) {
      return false;
    }
  }
  return true;
}

function meanIndicator(values: number[], predicate: (value: number) => boolean): number {
  if (values.length === 0) {
    return 0;
  }
  let count = 0;
  for (const value of values) {
    if (predicate(value)) {
      count += 1;
    }
  }
  return count / values.length;
}

function skewness(values: number[], meanValue: number, stdValue: number): number {
  if (values.length === 0 || stdValue === 0) {
    return 0;
  }
  return mean(values.map((value) => ((value - meanValue) / stdValue) ** 3));
}

function kurtosis(values: number[], meanValue: number, stdValue: number): number {
  if (values.length === 0 || stdValue === 0) {
    return 0;
  }
  return mean(values.map((value) => ((value - meanValue) / stdValue) ** 4));
}

function maxDrawdownFromReturns(dailyReturns: number[]): number {
  let equity = 1;
  let peak = 1;
  let maxDrawdown = 0;

  for (const value of dailyReturns) {
    equity *= Math.exp(value);
    peak = Math.max(peak, equity);
    const drawdown = equity / peak - 1;
    maxDrawdown = Math.min(maxDrawdown, drawdown);
  }

  return maxDrawdown;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function randomNormal(rng: () => number): number {
  const u1 = Math.max(Number.EPSILON, rng());
  const u2 = Math.max(Number.EPSILON, rng());
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

function mulberry32(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6D2B79F5;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function hashString(value: string): number {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function randomRunSuffix(): string {
  const bytes = new Uint8Array(4);
  crypto.getRandomValues(bytes);
  return Array.from(bytes).map((value) => value.toString(16).padStart(2, "0")).join("");
}

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: JSON_HEADERS
  });
}
