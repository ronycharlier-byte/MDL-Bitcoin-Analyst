export const DATA_STATUSES = [
  "real",
  "inferred",
  "absent",
  "mock",
  "mock_paper",
  "unknown",
  "stale",
  "ambiguous_status"
] as const;

export type DataStatus = (typeof DATA_STATUSES)[number];

export const ERROR_CODES = [
  "INVALID_REQUEST",
  "UNSUPPORTED_ASSET",
  "BITGET_UNAVAILABLE",
  "SPOT_MISSING",
  "SPOT_STALE",
  "MARKET_HISTORY_INSUFFICIENT",
  "FUNDAMENTAL_SOURCE_UNAVAILABLE",
  "ARCHIVE_NOT_FOUND",
  "ARCHIVE_MISMATCH",
  "SPOT_SNAPSHOT_MISMATCH",
  "FRAME_COUNT_MISMATCH",
  "QUANTILE_ORDER_INVALID",
  "PROBABILITY_OUT_OF_RANGE",
  "REGIME_SUM_INVALID",
  "RISK_METRIC_INCONSISTENT",
  "BACKTEST_UNAVAILABLE",
  "CACHE_STALE",
  "RATE_LIMITED",
  "STORAGE_UNAVAILABLE",
  "MODEL_EXECUTION_FAILED",
  "SCHEMA_VALIDATION_FAILED",
  "METHOD_NOT_ALLOWED",
  "AUTHENTICATION_REQUIRED",
  "EXECUTION_FORBIDDEN",
  "INTERNAL_ERROR"
] as const;

export type ErrorCode = (typeof ERROR_CODES)[number];

export interface StableError {
  status: "error";
  error_code: ErrorCode;
  message: string;
  retryable: boolean;
  details: Record<string, unknown>;
  request_id: string;
}

export function stableError(
  errorCode: ErrorCode,
  message: string,
  requestId: string,
  retryable = false,
  details: Record<string, unknown> = {}
): StableError {
  return {
    status: "error",
    error_code: errorCode,
    message,
    retryable,
    details,
    request_id: requestId
  };
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function numberValue(value: unknown): number | null {
  if (value === null || value === undefined || typeof value === "boolean") return null;
  const normalized = typeof value === "string" ? value.replace(/[$,]/g, "").trim() : value;
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

function firstNumber(value: Record<string, unknown>, keys: string[]): number | null {
  for (const key of keys) {
    const number = numberValue(value[key]);
    if (number !== null) return number;
  }
  return null;
}

export function normalizeDataStatus(value: unknown, fallback: DataStatus = "unknown"): DataStatus {
  const text = String(value || "").toLowerCase();
  if ((DATA_STATUSES as readonly string[]).includes(text)) return text as DataStatus;
  const aliases: Record<string, DataStatus> = {
    missing: "absent",
    modelled_stress: "inferred",
    partial_real_absent: "ambiguous_status",
    mock_or_missing: "ambiguous_status",
    real_or_mock_per_frame: "ambiguous_status",
    absent_unless_supplied: "absent"
  };
  return aliases[text] || fallback;
}

export function canonicalFrame(frameValue: unknown, fallbackModel = "ensemble"): Record<string, unknown> {
  const frame = objectValue(frameValue);
  const distribution = objectValue(frame.distribution);
  const quantiles = objectValue(frame.quantiles);
  const legacyRegime = objectValue(frame.regime_distribution || frame.regimes);
  const risk = objectValue(frame.risk_metrics || frame.risk);
  const confidence = objectValue(frame.confidence);
  const transition = firstNumber(legacyRegime, ["transition", "non_classified_transition"]) ?? 0;
  return {
    ...frame,
    horizon_days: Number(frame.horizon_days || frame.horizon || 0),
    run_id: String(frame.run_id || ""),
    model_name: String(frame.model_name || frame.model || fallbackModel),
    model_version: String(frame.model_version || objectValue(frame.version).model_version || "unknown"),
    simulation_count: Number(frame.simulation_count || frame.simulations || 0),
    probability_up: firstNumber(frame, ["probability_up"]) ?? firstNumber(distribution, ["probability_up", "prob_up"]),
    quantiles: {
      p10: firstNumber(quantiles, ["p10"]) ?? firstNumber(distribution, ["p10", "p10_return"]),
      median: firstNumber(quantiles, ["median"]) ?? firstNumber(distribution, ["median", "median_return"]),
      p90: firstNumber(quantiles, ["p90"]) ?? firstNumber(distribution, ["p90", "p90_return"])
    },
    regimes: {
      bull: firstNumber(legacyRegime, ["bull"]) ?? 0,
      bear: firstNumber(legacyRegime, ["bear"]) ?? 0,
      range: firstNumber(legacyRegime, ["range"]) ?? 0,
      transition
    },
    risk: {
      ...risk,
      var95_loss: firstNumber(risk, ["var95_loss", "var_95"]),
      cvar95_loss: firstNumber(risk, ["cvar95_loss", "cvar_95"]),
      var99_loss: firstNumber(risk, ["var99_loss", "var_99"]),
      cvar99_loss: firstNumber(risk, ["cvar99_loss", "cvar_99"]),
      loss_sign_convention: "positive_loss",
      status: "inferred"
    },
    confidence,
    monte_carlo: objectValue(frame.monte_carlo || frame.monte_carlo_error),
    stability: objectValue(frame.stability || frame.multi_seed_stability),
    warnings: Array.isArray(frame.warnings) ? frame.warnings.map(String) : frame.warning ? [String(frame.warning)] : [],
    status: normalizeDataStatus(objectValue(frame.data_status).simulation_outputs || frame.status, "inferred")
  };
}

function dataInventory(payload: Record<string, unknown>): Record<string, unknown>[] {
  return Object.entries(objectValue(payload.data_status)).map(([field, value]) => ({
    field,
    value: null,
    status: normalizeDataStatus(value),
    source: null,
    observed_at_utc: null,
    unit: null,
    limitations: []
  }));
}

export function canonicalizeAnalysis(payloadValue: Record<string, unknown>): Record<string, unknown> {
  const payload = { ...payloadValue };
  const legacyProvenance = objectValue(payload.provenance);
  const versions = objectValue(payload.versions || payload.version);
  const cache = objectValue(payload.cache || legacyProvenance.cache);
  const canonicalSpot = objectValue(legacyProvenance.spot);
  const frames = Array.isArray(payload.frames)
    ? payload.frames.map((frame) => canonicalFrame(frame, String(payload.model || "ensemble")))
    : [];
  const firstFrame = objectValue(frames[0]);
  const firstFrameProvenance = objectValue(firstFrame.provenance);
  const archiveId = String(payload.archive_id || legacyProvenance.archive_id || "");
  const ageSeconds = numberValue(cache.age_seconds) ?? 0;
  const maxAgeSeconds = numberValue(cache.max_age_seconds || cache.ttl_seconds) ?? 0;
  const responseType = String(payload.response_type || "");
  const presetName = String(objectValue(payload.analysis_preset).name || "").toLowerCase();
  const canonicalResponseType = ["standard", "quick", "deep"].includes(responseType)
    ? responseType
    : presetName === "deep"
      ? "deep"
      : ["quick", "tactical"].includes(presetName)
        ? "quick"
        : "standard";
  const referenceSpot = numberValue(
    payload.reference_spot || legacyProvenance.reference_spot || canonicalSpot.value || firstFrame.reference_spot
  );
  const referenceSpotSource =
    payload.reference_spot_source ||
    legacyProvenance.reference_spot_source ||
    canonicalSpot.source ||
    firstFrame.reference_spot_source ||
    null;
  const referenceSpotTimestampUtc =
    payload.reference_spot_timestamp_utc ||
    legacyProvenance.reference_spot_timestamp_utc ||
    canonicalSpot.observed_at_utc ||
    firstFrame.reference_spot_timestamp_utc ||
    null;
  const warnings = [payload.warning, ...(Array.isArray(payload.warnings) ? payload.warnings : [])]
    .filter((item) => item !== null && item !== undefined && String(item).length > 0)
    .map(String);
  return {
    ...payload,
    legacy_response_type: responseType || null,
    status: payload.status === "partial" ? "partial" : "ok",
    asset: "BTC",
    response_type: canonicalResponseType,
    archive_id: archiveId,
    analysis_id: archiveId,
    provenance: {
      ...legacyProvenance,
      report_generated_at_utc:
        payload.report_date_utc || legacyProvenance.report_date_utc || firstFrameProvenance.report_date_utc || null,
      report_generated_at_local:
        payload.report_date_paris ||
        legacyProvenance.report_date_paris ||
        firstFrameProvenance.report_date_paris ||
        null,
      timezone: "Europe/Paris",
      archive_created_at_utc: legacyProvenance.archive_created_at_utc || null,
      api_version: versions.render_api_version || versions.api_version || legacyProvenance.api_version || null,
      worker_version: versions.worker_version || legacyProvenance.worker_version || null,
      model_version: versions.render_model_version || versions.model_version || legacyProvenance.model_version || null,
      schema_version:
        versions.worker_schema_version || versions.schema_version || legacyProvenance.schema_version || null,
      git_commit: versions.render_git_commit || versions.git_commit || legacyProvenance.git_commit || null,
      runtime: legacyProvenance.runtime || "cloudflare_worker",
      cache: {
        status: cache.status === "hit" ? "hit" : "miss",
        age_seconds: ageSeconds,
        freshness_threshold_seconds: maxAgeSeconds,
        freshness_class: String(cache.freshness_label || (ageSeconds <= maxAgeSeconds ? "recent" : "unknown"))
      },
      spot: {
        value: referenceSpot,
        currency: canonicalSpot.currency || "USDT",
        source: referenceSpotSource,
        observed_at_utc: referenceSpotTimestampUtc,
        observed_at_local:
          payload.reference_spot_timestamp_paris ||
          legacyProvenance.reference_spot_timestamp_paris ||
          canonicalSpot.observed_at_local ||
          firstFrame.reference_spot_timestamp_paris ||
          null,
        age_seconds: numberValue(canonicalSpot.age_seconds),
        status: normalizeDataStatus(
          canonicalSpot.status,
          referenceSpot !== null && referenceSpotSource && referenceSpotTimestampUtc ? "real" : "absent"
        )
      }
    },
    data_inventory: Array.isArray(payload.data_inventory) ? payload.data_inventory : dataInventory(payload),
    frames,
    backtests: payload.backtests || payload.backtest_diagnostics || {},
    alerts: Array.isArray(payload.alerts) ? payload.alerts : [],
    warnings: [...new Set(warnings)],
    limitations: [
      ...new Set([
        ...(Array.isArray(payload.limitations) ? payload.limitations.map(String) : []),
        "Probabilistic research output only; no deterministic prediction.",
        "Financial advice and buy/sell recommendations are forbidden.",
        "Execution authority is none; paper trading is mock-only."
      ])
    ],
    policy: {
      user_effect: "information_only",
      execution_authority: "none",
      financial_advice: false,
      paper_trading: "mock_only",
      live_trading: "blocked"
    },
    contract: {
      schema: "contracts/analysis.schema.json",
      schema_version: "2.0.0"
    }
  };
}

export function validateCanonicalAnalysis(payloadValue: Record<string, unknown>): string[] {
  const issues: string[] = [];
  const payload = payloadValue;
  if (payload.asset !== "BTC") issues.push("UNSUPPORTED_ASSET");
  if (!String(payload.archive_id || "")) issues.push("ARCHIVE_NOT_FOUND");
  const spot = objectValue(objectValue(payload.provenance).spot);
  if ((numberValue(spot.value) ?? 0) <= 0 || !String(spot.source || "") || !String(spot.observed_at_utc || "")) {
    issues.push("SPOT_MISSING");
  }
  const frames = Array.isArray(payload.frames) ? payload.frames : [];
  if (!frames.length) issues.push("FRAME_COUNT_MISMATCH");
  frames.forEach((frameValue, index) => {
    const frame = objectValue(frameValue);
    if ((numberValue(frame.horizon_days) ?? 0) <= 0 || (numberValue(frame.simulation_count) ?? 0) <= 0) {
      issues.push(`SCHEMA_VALIDATION_FAILED:frames[${index}].dimensions`);
    }
    if (!String(frame.run_id || "")) issues.push(`SCHEMA_VALIDATION_FAILED:frames[${index}].run_id`);
    const probability = numberValue(frame.probability_up);
    if (probability === null || probability < 0 || probability > 1)
      issues.push(`PROBABILITY_OUT_OF_RANGE:frames[${index}]`);
    const quantiles = objectValue(frame.quantiles);
    const p10 = numberValue(quantiles.p10);
    const median = numberValue(quantiles.median);
    const p90 = numberValue(quantiles.p90);
    if (p10 === null || median === null || p90 === null || p10 > median || median > p90)
      issues.push(`QUANTILE_ORDER_INVALID:frames[${index}]`);
    const regimes = objectValue(frame.regimes);
    const regimeValues = ["bull", "bear", "range", "transition"].map((key) => numberValue(regimes[key]));
    if (regimeValues.some((value) => value === null || value < 0 || value > 1)) {
      issues.push(`PROBABILITY_OUT_OF_RANGE:frames[${index}].regimes`);
    } else {
      const sum = (regimeValues as number[]).reduce((total, value) => total + value, 0);
      if (Math.abs(sum - 1) > 0.015) issues.push(`REGIME_SUM_INVALID:frames[${index}]`);
    }
    const risk = objectValue(frame.risk);
    const [var95, cvar95, var99, cvar99] = ["var95_loss", "cvar95_loss", "var99_loss", "cvar99_loss"].map((key) =>
      numberValue(risk[key])
    );
    if (
      [var95, cvar95, var99, cvar99].every((value) => value !== null) &&
      !(
        (var99 as number) >= (var95 as number) &&
        (cvar95 as number) >= (var95 as number) &&
        (cvar99 as number) >= (var99 as number) &&
        (cvar99 as number) >= (cvar95 as number)
      )
    ) {
      issues.push(`RISK_METRIC_INCONSISTENT:frames[${index}]`);
    }
  });
  return issues;
}
