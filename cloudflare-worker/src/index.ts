interface Env {
  DB?: D1Database;
  MAX_SIMULATIONS?: string;
  DEFAULT_SIMULATIONS?: string;
  DEFAULT_HORIZON?: string;
  DEFAULT_HORIZONS?: string;
  RATE_LIMIT_RUNS_PER_MINUTE?: string;
  RATE_LIMIT_WINDOW_SECONDS?: string;
  RENDER_API_BASE?: string;
}

interface RunRequest {
  asset?: string;
  horizon?: number;
  simulations?: number;
  model?: string;
}

interface MultiRunRequest {
  asset?: string;
  horizons?: number[];
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

interface MarketCandles {
  candles: Candle[];
  source: string;
  status: "real";
  warning?: string;
}

interface FundamentalSnapshot {
  values: Record<string, number | null>;
  sources: Record<string, string | null>;
  status: "partial_real_absent" | "absent";
  warnings: string[];
}

interface RateLimitResult {
  allowed: boolean;
  key: string;
  limit: number;
  remaining: number;
  reset_at: string;
  window_seconds: number;
}

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type, x-client-key"
};

const WORKER_VERSION = "1.15.0";
const SCHEMA_VERSION = "gpt_action_cloudflare_schema_v1.15.0";
const MODEL_VERSION = "cloudflare_render_bitget_bridge_v1";
const DEFAULT_RENDER_API_BASE = "https://quant-btc-model-api.onrender.com";
const DEFAULT_MULTI_HORIZONS = [7, 30, 90, 180, 365];
const SIMULATION_HARD_CAP = 10000;
const ANALYSIS_PRESETS: Record<string, { name: string; label: string; horizons: number[]; simulations: number; description: string }> = {
  "/run-quick": {
    name: "quick",
    label: "Quick multi-frame",
    horizons: [7, 30, 90, 180, 365],
    simulations: 2000,
    description: "Standard live GPT analysis with the established 7/30/90/180/365 frames."
  },
  "/run-tactical": {
    name: "tactical",
    label: "Tactical short-frame",
    horizons: [1, 3, 7, 14, 30],
    simulations: 5000,
    description: "Short-horizon analysis for 1/3/7/14/30 day risk, liquidity and regime sensitivity."
  },
  "/run-deep": {
    name: "deep",
    label: "Deep full-frame",
    horizons: [1, 3, 7, 14, 30, 90, 180, 365],
    simulations: 10000,
    description: "Higher-power full-frame analysis for detailed reports, Monte Carlo margins and long-horizon caveats."
  }
};
const USER_DISPLAY_TIMEZONE = "Europe/Paris";
const TIMEZONE_POLICY = "Source timestamps are UTC. User-facing GPT answers must show both UTC and Europe/Paris when citing report dates or spot timestamps.";
const rateLimitBuckets = new Map<string, number[]>();

export default {
  async scheduled(_controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(warmRenderBitgetBridge(env));
  },

  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: JSON_HEADERS });
    }

    try {
      if (url.pathname === "/health" && request.method === "GET") {
        const now = new Date();
        return json({
          status: "ok",
          service: "quant-btc-model-lite-worker",
          worker_version: WORKER_VERSION,
          mode: "render_bitget_bridge_probabilistic",
          timestamp: now.toISOString(),
          timestamp_utc: now.toISOString(),
          timestamp_paris: parisIso(now),
          user_display_timezone: USER_DISPLAY_TIMEZONE,
          timezone_policy: TIMEZONE_POLICY
        });
      }

      if (url.pathname === "/version" && request.method === "GET") {
        const now = new Date();
        return json({
          status: "ok",
          service: "quant-btc-model-lite-worker",
          worker_version: WORKER_VERSION,
          schema_version: SCHEMA_VERSION,
          model_version: MODEL_VERSION,
          runtime: "cloudflare_worker",
          bridge_target: getRenderApiBase(env),
          max_simulations: getMaxSimulations(env),
          default_simulations: clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, getMaxSimulations(env)),
          default_horizon: clampInt(parseNumber(env.DEFAULT_HORIZON, 365), 1, 3650),
          default_horizons: parseHorizons(env.DEFAULT_HORIZONS, DEFAULT_MULTI_HORIZONS),
          analysis_presets: publicAnalysisPresets(env),
          rate_limit_runs_per_minute: getRateLimit(env).limit,
          rate_limit_window_seconds: getRateLimit(env).windowSeconds,
          supported_diagnostics: [
            "data_freshness_gate",
            "monte_carlo_error_margins",
            "multi_seed_stability",
            "expanded_drawdown_metrics",
            "compare_runs",
            "alerts",
            "backtest_summary",
            "dashboard_redirect",
            "pdf_report_redirect",
            "client_keys_quotas_usage_logs",
            "billing_plans_checkout_bridge",
            "alert_subscriptions",
            "cloudflare_d1_free_durable_storage",
            "analysis_presets_quick_tactical_deep"
          ],
          user_display_timezone: USER_DISPLAY_TIMEZONE,
          timezone_policy: TIMEZONE_POLICY,
          analysis_consistency_policy: "One answer must use one fresh run/archive_id unless the user asks for a comparison.",
          timestamp: now.toISOString(),
          timestamp_utc: now.toISOString(),
          timestamp_paris: parisIso(now)
        });
      }

      if (url.pathname === "/status" && request.method === "GET") {
        const now = new Date();
        return json({
          status: "ok",
          service: "quant-btc-model-lite-worker",
          worker_version: WORKER_VERSION,
          always_awake_target: true,
          runtime: "cloudflare_worker_free_tier",
          endpoints: ["/health", "/version", "/status", "/audit", "/run", "/multi-run", "/multiRun", "/run-quick", "/run-tactical", "/run-deep", "/latest", "/history", "/compare-runs", "/alerts", "/alerts/subscribe", "/alerts/subscriptions", "/backtest-summary", "/billing/plans", "/billing/checkout", "/clients/register", "/clients/me", "/usage-summary", "/d1/status", "/dashboard", "/pdf-report"],
          runtime_controls: {
            max_simulations: getMaxSimulations(env),
            default_simulations: clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, getMaxSimulations(env)),
            default_horizon: clampInt(parseNumber(env.DEFAULT_HORIZON, 365), 1, 3650),
            default_horizons: parseHorizons(env.DEFAULT_HORIZONS, DEFAULT_MULTI_HORIZONS),
            analysis_presets: publicAnalysisPresets(env),
            rate_limit_runs_per_minute: getRateLimit(env).limit,
            rate_limit_window_seconds: getRateLimit(env).windowSeconds
          },
          data_sources: {
            primary_market_source: "bitget_via_render_full_engine",
            cloudflare_direct_bitget: "absent",
            fallback_market_sources: [],
            fundamental_features: "partial_real_absent_from_render_when_sources_are_reachable",
            partial_fundamental_sources: [
              "farside_bitcoin_etf_flow_total_usd_m",
              "bitget_current_fund_rate",
              "bitget_open_interest",
              "bitget_proof_of_reserves_btc_platform_assets",
              "blockchain_info_hash_rate_chart",
              "defillama_stablecoins_total_pegged_usd",
              "fred_dgs10_10y_treasury_rate",
              "treasury_daily_10y_yield_curve",
              "stooq_dx_f_quote",
              "stooq_ndx_quote"
            ],
            websocket_fundamental_sources: [
              "bitget_uta_liquidation_ws_btcusdt_quote_observed_window"
            ],
            corpus_knowledge_base: "absent"
          },
          durable_storage: {
            cloudflare_d1: env.DB ? "configured" : "absent",
            database_name: "quant-btc-model-lite-db",
            free_tier_role: "durable run, usage, client and alert metadata storage",
            render_runtime_storage: "secondary"
          },
          backend_routing: {
            cloudflare_default: "Use this Worker first for no-sleep fresh BTC analysis; it bridges requests to the Render Bitget full engine.",
            render_full_engine: "Render remains the Bitget-backed Python/numpy engine behind this Worker.",
            recommended_gpt_flow: "Call auditQuantBtcLiteSystem, then runQuantBtcMultiFrame for complete analysis or runQuantBtcModel for one explicit horizon."
          },
          user_display_timezone: USER_DISPLAY_TIMEZONE,
          timezone_policy: TIMEZONE_POLICY,
          analysis_consistency_policy: "Do not mix numeric outputs from different archive_id values in one analysis unless explicitly comparing runs.",
          limitations: [
            "Cloudflare routes GPT analysis to the Render Bitget full engine; direct Worker quant-lite code remains a backup implementation only.",
            "If the Render bridge is unavailable, live Bitget model output is absent rather than replaced by another exchange.",
            "Liquidations are real only when the Bitget public WebSocket emits a BTCUSDT liquidation push during the configured observation window; otherwise the field is absent.",
            "Outputs are probabilistic scenarios, not deterministic predictions.",
            "Public endpoint has a best-effort per-IP in-isolate rate limit and simulation caps.",
            "Every precise number must be cited with full model_run_id, report_date UTC, report_date Europe/Paris, reference_spot and data status.",
            "A user-facing answer must not truncate run_id values unless it also provides the full run_id in the provenance section.",
            "Spot freshness, Monte Carlo error, multi-seed stability, alerts and run comparison diagnostics must be surfaced when present."
          ],
          timestamp: now.toISOString(),
          timestamp_utc: now.toISOString(),
          timestamp_paris: parisIso(now)
        });
      }

      if (url.pathname === "/latest" && request.method === "GET") {
        const result = await proxyRenderGet("/latest", env, request);
        return json(withBridgeMetadata(result, "/latest", env));
      }

      if (url.pathname === "/audit" && request.method === "GET") {
        const result = await proxyRenderGet("/audit", env, request);
        return json(withBridgeMetadata(result, "/audit", env));
      }

      if (url.pathname === "/d1/status" && request.method === "GET") {
        return json(await d1Status(env));
      }

      if (["/history", "/compare-runs", "/alerts", "/alerts/subscriptions", "/backtest-summary", "/billing/plans", "/clients/me", "/usage-summary"].includes(url.pathname) && request.method === "GET") {
        const result = await proxyRenderGet(`${url.pathname}${url.search}`, env, request);
        const bridged = withBridgeMetadata(result, url.pathname, env);
        if (url.pathname === "/history") {
          bridged.cloudflare_d1 = await d1Status(env);
          bridged.d1_recent_runs = await listD1Runs(env, normalizeAsset(url.searchParams.get("asset") || "BTC"), clampInt(parseNumber(url.searchParams.get("limit"), 10), 1, 50));
        }
        return json(bridged);
      }

      if (["/clients/register", "/alerts/subscribe", "/billing/checkout"].includes(url.pathname) && request.method === "POST") {
        const result = await proxyRenderPost(url.pathname, await readJson(request), env, request);
        if (url.pathname === "/clients/register") {
          const queued = queueD1ClientPersist(result, env, ctx);
          result.cloudflare_d1 = queued;
        }
        if (url.pathname === "/alerts/subscribe") {
          const queued = queueD1AlertSubscriptionPersist(result, env, ctx);
          result.cloudflare_d1 = queued;
        }
        return json(result);
      }

      if (url.pathname === "/dashboard" && request.method === "GET") {
        return Response.redirect(renderUrl("/dashboard", env), 302);
      }

      if (url.pathname === "/pdf-report" && request.method === "GET") {
        return Response.redirect(renderUrl(`/pdf-report${url.search}`, env), 302);
      }

      if (ANALYSIS_PRESETS[url.pathname] && (request.method === "POST" || request.method === "GET")) {
        const rateLimit = checkRateLimit(request, env);
        if (!rateLimit.allowed) {
          return json(rateLimitResponse(rateLimit), 429);
        }
        const preset = ANALYSIS_PRESETS[url.pathname];
        const body = normalizeRenderPresetPayload(await readInput(request, url), env, preset);
        const result = await proxyRenderPost("/multi-run", body, env, request);
        result.analysis_preset = publicAnalysisPreset(url.pathname, env);
        result.cloudflare_bridge = {
          ...objectValue(result.cloudflare_bridge),
          operation_path: url.pathname,
          render_operation_path: "/multi-run",
          analysis_preset: preset.name
        };
        result.cloudflare_d1 = queueD1RunPersist(result, url.pathname, body, env, ctx);
        return json({ ...result, rate_limit: publicRateLimit(rateLimit) });
      }

      if (url.pathname === "/run" && (request.method === "POST" || request.method === "GET")) {
        const rateLimit = checkRateLimit(request, env);
        if (!rateLimit.allowed) {
          return json(rateLimitResponse(rateLimit), 429);
        }
        const input = await readInput(request, url);
        if (shouldRouteRunAsMultiFrame(input)) {
          const body = normalizeRenderMultiRunPayload(input, env);
          const result = await proxyRenderPost("/multi-run", body, env, request);
          result.cloudflare_d1 = queueD1RunPersist(result, "/multi-run", body, env, ctx);
          return json({ ...result, rate_limit: publicRateLimit(rateLimit) });
        }
        const body = normalizeRenderRunPayload(input, env);
        const result = await proxyRenderPost("/run", body, env, request);
        result.cloudflare_d1 = queueD1RunPersist(result, "/run", body, env, ctx);
        return json({ ...result, rate_limit: publicRateLimit(rateLimit) });
      }

      if ((url.pathname === "/multi-run" || url.pathname === "/multiRun") && (request.method === "POST" || request.method === "GET")) {
        const rateLimit = checkRateLimit(request, env);
        if (!rateLimit.allowed) {
          return json(rateLimitResponse(rateLimit), 429);
        }
        const body = normalizeRenderMultiRunPayload(await readInput(request, url), env);
        const result = await proxyRenderPost("/multi-run", body, env, request);
        result.cloudflare_d1 = queueD1RunPersist(result, "/multi-run", body, env, ctx);
        return json({ ...result, rate_limit: publicRateLimit(rateLimit) });
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

async function readJson(request: Request): Promise<Record<string, unknown>> {
  try {
    const parsed = await request.json();
    if (!parsed || typeof parsed !== "object") {
      return {};
    }
    return parsed as Record<string, unknown>;
  } catch {
    return {};
  }
}

async function readInput(request: Request, url: URL): Promise<Record<string, unknown>> {
  if (request.method !== "GET") {
    return await readJson(request);
  }
  const input: Record<string, unknown> = {};
  for (const [key, value] of url.searchParams.entries()) {
    if (key === "horizons") {
      input.horizons = value.split(",").map((item) => Number(item.trim())).filter(Number.isFinite);
    } else if (key === "horizon" || key === "simulations") {
      input[key] = Number(value);
    } else {
      input[key] = value;
    }
  }
  return input;
}

function getRenderApiBase(env: Env): string {
  return String(env.RENDER_API_BASE || DEFAULT_RENDER_API_BASE).replace(/\/+$/, "");
}

function renderUrl(path: string, env: Env): string {
  return `${getRenderApiBase(env)}${path.startsWith("/") ? path : `/${path}`}`;
}

function normalizeRenderRunPayload(input: Record<string, unknown>, env: Env): Record<string, unknown> {
  const maxSimulations = getMaxSimulations(env);
  const defaultSimulations = clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, maxSimulations);
  return {
    asset: normalizeAsset(input.asset),
    horizon: clampInt(parseNumber(input.horizon, parseNumber(env.DEFAULT_HORIZON, 365)), 1, 3650),
    simulations: Math.min(clampInt(parseNumber(input.simulations, defaultSimulations), 100, 250000), maxSimulations),
    model: normalizeRenderModel(input.model),
    skip_corpus: typeof input.skip_corpus === "boolean" ? input.skip_corpus : true,
    no_online: typeof input.no_online === "boolean" ? input.no_online : false
  };
}

function normalizeRenderMultiRunPayload(input: Record<string, unknown>, env: Env): Record<string, unknown> {
  const maxSimulations = getMaxSimulations(env);
  const defaultSimulations = clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, maxSimulations);
  return {
    asset: normalizeAsset(input.asset),
    horizons: parseHorizons(input.horizons, parseHorizons(env.DEFAULT_HORIZONS, DEFAULT_MULTI_HORIZONS)),
    simulations: Math.min(clampInt(parseNumber(input.simulations, defaultSimulations), 100, 250000), maxSimulations),
    model: normalizeRenderModel(input.model),
    skip_corpus: typeof input.skip_corpus === "boolean" ? input.skip_corpus : true,
    no_online: typeof input.no_online === "boolean" ? input.no_online : false
  };
}

function normalizeRenderPresetPayload(
  input: Record<string, unknown>,
  env: Env,
  preset: { name: string; horizons: number[]; simulations: number }
): Record<string, unknown> {
  const max = getMaxSimulations(env);
  return {
    asset: normalizeAsset(input.asset),
    horizons: preset.horizons,
    simulations: Math.min(preset.simulations, max),
    model: normalizeRenderModel(input.model),
    skip_corpus: typeof input.skip_corpus === "boolean" ? input.skip_corpus : true,
    no_online: typeof input.no_online === "boolean" ? input.no_online : false
  };
}

function getMaxSimulations(env: Env): number {
  return clampInt(parseNumber(env.MAX_SIMULATIONS, SIMULATION_HARD_CAP), 100, SIMULATION_HARD_CAP);
}

function publicAnalysisPreset(path: string, env: Env): Record<string, unknown> {
  const preset = ANALYSIS_PRESETS[path];
  const simulations = Math.min(preset.simulations, getMaxSimulations(env));
  return {
    name: preset.name,
    label: preset.label,
    endpoint: path,
    horizons: preset.horizons,
    simulations_per_horizon: simulations,
    model: "ensemble",
    description: preset.description,
    status: simulations < preset.simulations ? "capped_by_runtime" : "ok"
  };
}

function publicAnalysisPresets(env: Env): Record<string, unknown>[] {
  return Object.keys(ANALYSIS_PRESETS).map((path) => publicAnalysisPreset(path, env));
}

function normalizeRenderModel(value: unknown): string {
  const model = String(value || "ensemble");
  const allowed = new Set([
    "ensemble",
    "monte_carlo",
    "student_t",
    "student_t_model",
    "jump_diffusion",
    "garch",
    "garch_model",
    "regime_switching",
    "liquidation",
    "liquidation_model",
    "correlation",
    "correlation_model"
  ]);
  return allowed.has(model) ? model : "ensemble";
}

function shouldRouteRunAsMultiFrame(input: Record<string, unknown>): boolean {
  if (Array.isArray(input.horizons)) {
    return true;
  }
  if (input.horizon === undefined || input.horizon === null || input.horizon === "") {
    return true;
  }
  return false;
}

function renderProxyHeaders(request?: Request, includeJson = false): HeadersInit {
  const headers: Record<string, string> = {
    "accept": "application/json",
    "user-agent": "quant-btc-model-cloudflare-bitget-bridge/1.0"
  };
  if (includeJson) {
    headers["content-type"] = "application/json";
  }
  const clientKey = request?.headers.get("x-client-key");
  if (clientKey) {
    headers["x-client-key"] = clientKey;
  }
  return headers;
}

async function proxyRenderGet(path: string, env: Env, request?: Request): Promise<Record<string, unknown>> {
  const response = await fetch(renderUrl(path, env), {
    method: "GET",
    headers: renderProxyHeaders(request),
    cf: { cacheTtl: 0, cacheEverything: false }
  });
  return await parseRenderResponse(response, path);
}

async function proxyRenderPost(path: string, payload: Record<string, unknown>, env: Env, request?: Request): Promise<Record<string, unknown>> {
  const response = await fetch(renderUrl(path, env), {
    method: "POST",
    headers: renderProxyHeaders(request, true),
    body: JSON.stringify(payload),
    cf: { cacheTtl: 0, cacheEverything: false }
  });
  const result = await parseRenderResponse(response, path);
  return withBridgeMetadata(result, path, env);
}

async function parseRenderResponse(response: Response, path: string): Promise<Record<string, unknown>> {
  const text = await response.text();
  let parsed: unknown = {};
  try {
    parsed = text ? JSON.parse(text) : {};
  } catch {
    parsed = { raw_response: text.slice(0, 1000) };
  }
  if (!response.ok) {
    return {
      error: "render_bitget_bridge_failed",
      message: `Render Bitget bridge ${path} failed with HTTP ${response.status}.`,
      render_status: response.status,
      render_response: parsed,
      data_status: {
        market_prices: "absent",
        simulation_results: "absent",
        risk_metrics: "absent",
        fundamental_features: "absent"
      },
      warning: "No deterministic prediction was produced and no non-Bitget fallback was used."
    };
  }
  return objectValue(parsed);
}

function withBridgeMetadata(result: Record<string, unknown>, path: string, env: Env): Record<string, unknown> {
  const now = new Date();
  const bridge = {
    worker_version: WORKER_VERSION,
    schema_version: SCHEMA_VERSION,
    model_version: MODEL_VERSION,
    mode: "cloudflare_to_render_bitget_bridge",
    operation_path: path,
    render_api_base: getRenderApiBase(env),
    source_policy: "bitget_required_no_exchange_fallback",
    cloudflare_direct_bitget: "absent",
    user_display_timezone: USER_DISPLAY_TIMEZONE,
    timezone_policy: TIMEZONE_POLICY,
    analysis_consistency_policy: "Use one fresh archive_id/run response per analysis; compare runs only when explicitly requested.",
    bridge_timestamp_utc: now.toISOString(),
    bridge_timestamp_paris: parisIso(now)
  };
  const existingDataStatus = objectValue(result.data_status);
  return {
    ...result,
    cloudflare_bridge: bridge,
    data_status: {
      ...existingDataStatus,
      bitget_required: "real",
      cloudflare_direct_bitget: "absent",
      non_bitget_market_fallback: "absent"
    }
  };
}

function queueD1RunPersist(
  result: Record<string, unknown>,
  endpoint: string,
  requestBody: Record<string, unknown>,
  env: Env,
  ctx: ExecutionContext
): Record<string, unknown> {
  if (!env.DB) {
    return { status: "absent", target: "cloudflare_d1", reason: "DB binding is not configured" };
  }
  const archiveId = archiveIdFromPayload(result);
  ctx.waitUntil(persistRunToD1(result, endpoint, requestBody, env));
  ctx.waitUntil(persistUsageToD1(result, endpoint, requestBody, env));
  return {
    status: "queued",
    target: "cloudflare_d1",
    database_name: "quant-btc-model-lite-db",
    archive_id: archiveId,
    note: "Compact run and usage metadata are written asynchronously to D1."
  };
}

function queueD1ClientPersist(result: Record<string, unknown>, env: Env, ctx: ExecutionContext): Record<string, unknown> {
  if (!env.DB) {
    return { status: "absent", target: "cloudflare_d1", reason: "DB binding is not configured" };
  }
  ctx.waitUntil(persistClientToD1(result, env));
  return {
    status: "queued",
    target: "cloudflare_d1",
    database_name: "quant-btc-model-lite-db",
    client_id: typeof result.client_id === "string" ? result.client_id : null
  };
}

function queueD1AlertSubscriptionPersist(result: Record<string, unknown>, env: Env, ctx: ExecutionContext): Record<string, unknown> {
  if (!env.DB) {
    return { status: "absent", target: "cloudflare_d1", reason: "DB binding is not configured" };
  }
  ctx.waitUntil(persistAlertSubscriptionToD1(result, env));
  return {
    status: "queued",
    target: "cloudflare_d1",
    database_name: "quant-btc-model-lite-db",
    subscription_id: typeof result.subscription_id === "string" ? result.subscription_id : null
  };
}

async function persistRunToD1(
  result: Record<string, unknown>,
  endpoint: string,
  requestBody: Record<string, unknown>,
  env: Env
): Promise<void> {
  if (!env.DB) {
    return;
  }
  const compact = compactRunPayload(result);
  const archiveId = compact.archive_id || `${new Date().toISOString()}_${randomRunSuffix()}`;
  const version = objectValue(result.version);
  await env.DB.prepare(`
    INSERT OR REPLACE INTO quant_runs (
      archive_id, asset, model, horizons_json, run_ids_json, report_date_utc,
      reference_spot, status, api_version, worker_version, render_git_commit,
      payload_json, created_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    String(archiveId),
    stringOrNull(result.asset) || normalizeAsset(requestBody.asset),
    stringOrNull(result.model) || stringOrNull(requestBody.model),
    JSON.stringify(compact.horizons || []),
    JSON.stringify(compact.run_ids || []),
    compact.report_date_utc || new Date().toISOString(),
    compact.reference_spot,
    stringOrNull(result.status) || "ok",
    stringOrNull(version.api_version),
    WORKER_VERSION,
    stringOrNull(version.git_commit),
    JSON.stringify(compact),
    new Date().toISOString()
  ).run();
}

async function persistUsageToD1(
  result: Record<string, unknown>,
  endpoint: string,
  requestBody: Record<string, unknown>,
  env: Env
): Promise<void> {
  if (!env.DB) {
    return;
  }
  const clientUsage = objectValue(result.client_usage);
  const horizons = Array.isArray(result.horizons)
    ? result.horizons
    : Array.isArray(requestBody.horizons)
      ? requestBody.horizons
      : requestBody.horizon ? [requestBody.horizon] : [];
  await env.DB.prepare(`
    INSERT INTO usage_events (
      client_id, endpoint, asset, model, horizons_json, simulations,
      archive_id, status, created_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    stringOrNull(clientUsage.client_id),
    endpoint,
    stringOrNull(result.asset) || normalizeAsset(requestBody.asset),
    stringOrNull(result.model) || stringOrNull(requestBody.model),
    JSON.stringify(horizons),
    numberOrNull(result.simulations_per_horizon) || numberOrNull(result.simulations) || numberOrNull(requestBody.simulations),
    archiveIdFromPayload(result),
    stringOrNull(result.status) || "ok",
    new Date().toISOString()
  ).run();
}

async function persistClientToD1(result: Record<string, unknown>, env: Env): Promise<void> {
  if (!env.DB || typeof result.client_id !== "string") {
    return;
  }
  await env.DB.prepare(`
    INSERT OR REPLACE INTO api_clients (
      client_id, email, plan, quota_runs_per_month, status,
      created_at_utc, updated_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    result.client_id,
    stringOrNull(result.email),
    stringOrNull(result.plan),
    numberOrNull(result.quota_runs_per_month),
    stringOrNull(result.status) || "ok",
    stringOrNull(result.created_at_utc) || new Date().toISOString(),
    new Date().toISOString()
  ).run();
}

async function persistAlertSubscriptionToD1(result: Record<string, unknown>, env: Env): Promise<void> {
  if (!env.DB || typeof result.subscription_id !== "string") {
    return;
  }
  await env.DB.prepare(`
    INSERT OR REPLACE INTO alert_subscriptions (
      subscription_id, client_id, channel, target, min_level, status, created_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    result.subscription_id,
    stringOrNull(result.client_id),
    stringOrNull(result.channel) || "webhook",
    stringOrNull(result.target) || "absent",
    stringOrNull(result.min_level) || "warning",
    stringOrNull(result.status) || "ok",
    stringOrNull(result.created_at_utc) || new Date().toISOString()
  ).run();
}

async function d1Status(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", target: "cloudflare_d1", reason: "DB binding is not configured" };
  }
  try {
    const [runs, usage, clients, subscriptions] = await env.DB.batch([
      env.DB.prepare("SELECT COUNT(*) AS count FROM quant_runs"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM usage_events"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM api_clients"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM alert_subscriptions")
    ]);
    return {
      status: "ok",
      target: "cloudflare_d1",
      database_name: "quant-btc-model-lite-db",
      binding: "DB",
      counts: {
        runs: countFromD1(runs),
        usage_events: countFromD1(usage),
        clients: countFromD1(clients),
        alert_subscriptions: countFromD1(subscriptions)
      },
      free_tier_role: "durable metadata storage for run archives, usage logs, clients and alert subscriptions",
      checked_at_utc: new Date().toISOString(),
      checked_at_paris: parisIso(new Date())
    };
  } catch (error) {
    return {
      status: "error",
      target: "cloudflare_d1",
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function listD1Runs(env: Env, asset: string, limit: number): Promise<Record<string, unknown>[]> {
  if (!env.DB) {
    return [];
  }
  try {
    const { results } = await env.DB.prepare(`
      SELECT archive_id, asset, model, horizons_json, report_date_utc,
             reference_spot, status, api_version, worker_version,
             render_git_commit, created_at_utc
      FROM quant_runs
      WHERE asset = ?
      ORDER BY created_at_utc DESC
      LIMIT ?
    `).bind(asset, limit).all();
    return (results || []).map((row) => ({
      archive_id: row.archive_id,
      asset: row.asset,
      model: row.model,
      horizons: parseStoredJsonArray(row.horizons_json),
      report_date_utc: row.report_date_utc,
      report_date_paris: typeof row.report_date_utc === "string" ? parisIso(new Date(row.report_date_utc)) : null,
      reference_spot: row.reference_spot,
      status: row.status,
      api_version: row.api_version,
      worker_version: row.worker_version,
      render_git_commit: row.render_git_commit,
      created_at_utc: row.created_at_utc,
      created_at_paris: typeof row.created_at_utc === "string" ? parisIso(new Date(row.created_at_utc)) : null
    }));
  } catch {
    return [];
  }
}

function compactRunPayload(result: Record<string, unknown>): Record<string, unknown> {
  const archive = objectValue(result.archive);
  const provenance = objectValue(result.provenance_summary);
  const referenceSpots = Array.isArray(provenance.reference_spots) ? provenance.reference_spots : [];
  const frames = Array.isArray(result.frames) ? result.frames.map((item) => {
    const frame = objectValue(item);
    return {
      horizon: frame.horizon,
      run_id: frame.run_id,
      distribution: frame.distribution,
      regime_distribution: frame.regime_distribution,
      risk_metrics: frame.risk_metrics,
      confidence: frame.confidence,
      monte_carlo_error: compactMonteCarloError(objectValue(frame.monte_carlo_error)),
      multi_seed_stability: compactStability(objectValue(frame.multi_seed_stability))
    };
  }) : [];
  return {
    schema: "cloudflare_d1_quant_btc_run_v1",
    archive_id: stringOrNull(archive.archive_id) || stringOrNull(provenance.archive_id),
    asset: result.asset,
    model: result.model,
    horizons: Array.isArray(result.horizons) ? result.horizons : frames.map((frame) => frame.horizon),
    run_ids: frames.map((frame) => frame.run_id).filter(Boolean),
    report_date_utc: stringOrNull(provenance.report_date_utc) || stringOrNull(provenance.report_date),
    report_date_paris: stringOrNull(provenance.report_date_paris),
    reference_spot: referenceSpots.length ? referenceSpots[0] : null,
    data_status: result.data_status,
    alerts: result.alerts,
    version: result.version,
    cloudflare_bridge: result.cloudflare_bridge,
    frames,
    stored_at_utc: new Date().toISOString(),
    storage_policy: "Compact D1 record; raw simulation paths and massive payloads are excluded."
  };
}

function compactMonteCarloError(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    method: value.method,
    tail_counts: value.tail_counts,
    warnings: value.warnings
  };
}

function compactStability(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    seed_runs: value.seed_runs,
    simulations_per_seed: value.simulations_per_seed,
    directional_stability: value.directional_stability,
    bias_stability_label: value.bias_stability_label
  };
}

function archiveIdFromPayload(payload: Record<string, unknown>): string | null {
  const archive = objectValue(payload.archive);
  const provenance = objectValue(payload.provenance_summary);
  return stringOrNull(archive.archive_id) || stringOrNull(provenance.archive_id);
}

function countFromD1(result: D1Result<unknown>): number {
  const first = objectValue(result.results?.[0]);
  return Number(first.count || 0);
}

function parseStoredJsonArray(value: unknown): unknown[] {
  if (typeof value !== "string") {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function numberOrNull(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

async function warmRenderBitgetBridge(env: Env): Promise<void> {
  try {
    await fetch(renderUrl("/health", env), {
      method: "GET",
      headers: {
        "accept": "application/json",
        "user-agent": "quant-btc-model-cloudflare-render-warmer/1.0"
      },
      cf: { cacheTtl: 0, cacheEverything: false }
    });
  } catch {
    // Scheduled warmup is best-effort only; request handlers still report bridge failures explicitly.
  }
}

function getRateLimit(env: Env) {
  return {
    limit: clampInt(parseNumber(env.RATE_LIMIT_RUNS_PER_MINUTE, 20), 1, 120),
    windowSeconds: clampInt(parseNumber(env.RATE_LIMIT_WINDOW_SECONDS, 60), 10, 3600)
  };
}

function checkRateLimit(request: Request, env: Env): RateLimitResult {
  const { limit, windowSeconds } = getRateLimit(env);
  const now = Date.now();
  const windowMs = windowSeconds * 1000;
  const key = request.headers.get("cf-connecting-ip")
    || request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || "unknown-client";
  const existing = rateLimitBuckets.get(key) || [];
  const recent = existing.filter((timestamp) => now - timestamp < windowMs);
  const allowed = recent.length < limit;
  if (allowed) {
    recent.push(now);
    rateLimitBuckets.set(key, recent);
  } else {
    rateLimitBuckets.set(key, recent);
  }
  for (const [bucketKey, timestamps] of rateLimitBuckets) {
    const fresh = timestamps.filter((timestamp) => now - timestamp < windowMs);
    if (fresh.length === 0) {
      rateLimitBuckets.delete(bucketKey);
    } else if (fresh.length !== timestamps.length) {
      rateLimitBuckets.set(bucketKey, fresh);
    }
  }
  const oldest = recent[0] || now;
  return {
    allowed,
    key,
    limit,
    remaining: allowed ? Math.max(0, limit - recent.length) : 0,
    reset_at: new Date(oldest + windowMs).toISOString(),
    window_seconds: windowSeconds
  };
}

function publicRateLimit(rateLimit: RateLimitResult) {
  return {
    limit: rateLimit.limit,
    remaining: rateLimit.remaining,
    reset_at: rateLimit.reset_at,
    window_seconds: rateLimit.window_seconds,
    scope: "best_effort_per_ip_in_worker_isolate"
  };
}

function rateLimitResponse(rateLimit: RateLimitResult) {
  return {
    error: "rate_limited",
    message: "Public Cloudflare Worker run limit reached. Wait before calling the endpoint again.",
    rate_limit: publicRateLimit(rateLimit),
    data_status: {
      model_output: "absent",
      market_data: "absent"
    },
    warning: "No deterministic prediction was produced."
  };
}

async function runQuantLite(
  input: RunRequest,
  env: Env,
  shared?: { market?: MarketCandles; fundamentals?: FundamentalSnapshot; groupRunId?: string }
): Promise<Record<string, unknown>> {
  const asset = normalizeAsset(input.asset);
  if (asset !== "BTC") {
    throw new Error("Only BTC is supported by the quant-lite Worker.");
  }

  const maxSimulations = getMaxSimulations(env);
  const defaultSimulations = clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, maxSimulations);
  const defaultHorizon = clampInt(parseNumber(env.DEFAULT_HORIZON, 365), 1, 3650);
  const requestedSimulations = clampInt(parseNumber(input.simulations, defaultSimulations), 100, 250000);
  const simulations = Math.min(requestedSimulations, maxSimulations);
  const horizon = clampInt(parseNumber(input.horizon, defaultHorizon), 1, 3650);
  const requestedModel = String(input.model || "quant_lite");
  const model = requestedModel === "ensemble" ? "quant_lite" : "quant_lite";

  const runStartedAt = new Date();
  const baseRunId = shared?.groupRunId || `cfql_${runStartedAt.toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}_${randomRunSuffix()}`;
  const modelRunId = shared?.groupRunId ? `${baseRunId}_h${horizon}` : baseRunId;

  const market = shared?.market || await fetchMarketCandles();
  const fundamentals = shared?.fundamentals || await fetchFundamentalSnapshot();
  const candles = market.candles;
  if (candles.length < 30) {
    throw new Error("Insufficient real market history for quant-lite run.");
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
  const confidence = calculateConfidence(
    candles.length,
    simulations,
    calibration,
    requestedSimulations > simulations,
    market.source,
    fundamentals.status
  );
  const runCompletedAt = new Date();
  const referenceSpotTimestamp = new Date(sorted[sorted.length - 1].timestamp);

  const warnings = [
    "Probabilistic infrastructure only; not financial advice.",
    "Cloudflare Worker quant-lite is a lightweight runtime, not the full Python/numpy engine.",
    "Fundamental variables are absent in this Worker result unless supplied by a future connected store.",
    "Precise numbers are valid only for this response and must be cited with model_run_id, report_date_utc, report_date_paris, reference_spot and status.",
    "VaR/CVaR are expressed as simulated returns, so negative values represent losses."
  ];
  if (requestedSimulations > simulations) {
    warnings.push(`Requested simulations capped from ${requestedSimulations} to ${simulations} to protect the free Worker runtime.`);
  }
  if (market.warning) {
    warnings.push(market.warning);
  }
  warnings.push(...fundamentals.warnings);

  return {
    status: "ok",
    service: "quant-btc-model-lite-worker",
    asset,
    horizon,
    simulations,
    requested_simulations: requestedSimulations,
    model,
    model_version: MODEL_VERSION,
    model_run_id: modelRunId,
    report_date: runCompletedAt.toISOString(),
    report_date_utc: runCompletedAt.toISOString(),
    report_date_paris: parisIso(runCompletedAt),
    provenance: {
      source_report: "runtime_response",
      report_date: runCompletedAt.toISOString(),
      report_date_utc: runCompletedAt.toISOString(),
      report_date_paris: parisIso(runCompletedAt),
      run_started_at: runStartedAt.toISOString(),
      run_started_at_utc: runStartedAt.toISOString(),
      run_started_at_paris: parisIso(runStartedAt),
      run_completed_at: runCompletedAt.toISOString(),
      run_completed_at_utc: runCompletedAt.toISOString(),
      run_completed_at_paris: parisIso(runCompletedAt),
      model_run_id: modelRunId,
      model_version: MODEL_VERSION,
      reference_spot: spot,
      reference_spot_source: market.source,
      reference_spot_timestamp: referenceSpotTimestamp.toISOString(),
      reference_spot_timestamp_utc: referenceSpotTimestamp.toISOString(),
      reference_spot_timestamp_paris: parisIso(referenceSpotTimestamp),
      calculation_origin: "cloudflare_worker_quant_lite_runtime",
      timezone_policy: TIMEZONE_POLICY,
      status: "mixed"
    },
    data_status: {
      market_prices: "real",
      market_source: market.source,
      bitget_market_prices: market.source.startsWith("bitget") ? "real" : "absent",
      fallback_market_prices: market.source.startsWith("bitget") ? "absent" : "real",
      simulation_results: "inferred",
      risk_metrics: "inferred",
      stress_tests: "inferred",
      fundamental_features: fundamentals.status,
      fundamental_sources: fundamentals.sources,
      corpus_knowledge_base: "absent",
      full_python_engine: "absent"
    },
    fundamental_features: fundamentals.values,
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
      `${market.source} is used as the real market input for this run.`,
      "Terminal distribution is inferred from a heavy-tail jump approximation calibrated on recent log returns.",
      "Worker fundamental variables are partial and must be read from fundamental_features plus data_status.fundamental_sources.",
      "ETF flow, liquidations, hash rate, exchange reserves, stablecoin supply and US rates remain absent unless a future connected source provides them.",
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

async function runQuantLiteMultiFrame(input: MultiRunRequest, env: Env): Promise<Record<string, unknown>> {
  const asset = normalizeAsset(input.asset);
  if (asset !== "BTC") {
    throw new Error("Only BTC is supported by the quant-lite Worker.");
  }

  const maxSimulations = getMaxSimulations(env);
  const defaultSimulations = clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, maxSimulations);
  const requestedSimulations = clampInt(parseNumber(input.simulations, defaultSimulations), 100, 250000);
  const simulations = Math.min(requestedSimulations, maxSimulations);
  const horizons = parseHorizons(input.horizons, parseHorizons(env.DEFAULT_HORIZONS, DEFAULT_MULTI_HORIZONS));
  const model = String(input.model || "quant_lite");
  const runStartedAt = new Date();
  const groupRunId = `cfqlmf_${runStartedAt.toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}_${randomRunSuffix()}`;

  const market = await fetchMarketCandles();
  const fundamentals = await fetchFundamentalSnapshot();
  const sharedSpotSnapshot = getMarketSpotSnapshot(market);
  const frameResults: Record<string, unknown>[] = [];

  for (const horizon of horizons) {
    const frame = await runQuantLite(
      { asset, horizon, simulations, model },
      env,
      { market, fundamentals, groupRunId }
    );
    frameResults.push(frame);
  }

  const frameSummaries = frameResults.map(summarizeFrameResult);
  const runCompletedAt = new Date();
  const warnings = uniqueStrings([
    "Cloudflare multi-run is quant-lite and optimized for no-sleep GPT latency, not the full Python/numpy engine.",
    "All frames share one market snapshot and one fundamental snapshot for coherent comparison.",
    ...frameResults.flatMap((frame) => {
      const values = objectValue(frame).warnings;
      return Array.isArray(values) ? values.map(String) : [];
    })
  ]);

  return {
    status: "ok",
    service: "quant-btc-model-lite-worker",
    asset,
    horizons,
    simulations,
    requested_simulations: requestedSimulations,
    model: model === "ensemble" ? "quant_lite" : "quant_lite",
    model_version: MODEL_VERSION,
    model_run_id: groupRunId,
    report_date: runCompletedAt.toISOString(),
    report_date_utc: runCompletedAt.toISOString(),
    report_date_paris: parisIso(runCompletedAt),
    runtime: "cloudflare_worker_quant_lite_multi_frame",
    provenance_summary: {
      source_report: "runtime_response",
      report_date: runCompletedAt.toISOString(),
      report_date_utc: runCompletedAt.toISOString(),
      report_date_paris: parisIso(runCompletedAt),
      run_started_at: runStartedAt.toISOString(),
      run_started_at_utc: runStartedAt.toISOString(),
      run_started_at_paris: parisIso(runStartedAt),
      run_completed_at: runCompletedAt.toISOString(),
      run_completed_at_utc: runCompletedAt.toISOString(),
      run_completed_at_paris: parisIso(runCompletedAt),
      model_run_id: groupRunId,
      model_version: MODEL_VERSION,
      shared_spot_snapshot: sharedSpotSnapshot,
      calculation_origin: "cloudflare_worker_quant_lite_multi_frame_runtime",
      timezone_policy: TIMEZONE_POLICY,
      analysis_consistency_policy: "Use this multi-frame response as one analysis unit; do not mix with another run unless explicitly comparing.",
      status: "mixed"
    },
    data_status: {
      market_prices: "real",
      market_source: market.source,
      bitget_market_prices: market.source.startsWith("bitget") ? "real" : "absent",
      fallback_market_prices: market.source.startsWith("bitget") ? "absent" : "real",
      simulation_results: "inferred",
      risk_metrics: "inferred",
      stress_tests: "inferred",
      fundamental_features: fundamentals.status,
      fundamental_sources: fundamentals.sources,
      corpus_knowledge_base: "absent",
      full_python_engine: "absent"
    },
    fundamental_features: fundamentals.values,
    frame_summaries: frameSummaries,
    aggregate: buildMultiFrameAggregate(frameSummaries),
    frames: frameResults,
    governance: {
      numeric_traceability_required: true,
      no_hidden_extrapolation: true,
      required_citation_fields: [
        "model_run_id",
        "report_date_utc",
        "report_date_paris",
        "provenance_summary.shared_spot_snapshot.price",
        "provenance_summary.shared_spot_snapshot.source",
        "data_status"
      ],
      required_language: "Probabilistic scenario distribution; never a deterministic prediction."
    },
    warnings
  };
}

async function fetchMarketCandles(): Promise<MarketCandles> {
  try {
    return {
      candles: await fetchBitgetCandles(),
      source: "bitget_btcusdt_spot_candles",
      status: "real"
    };
  } catch (error) {
    const bitgetMessage = error instanceof Error ? error.message : String(error);
    throw new Error(`Bitget market data unavailable. No non-Bitget exchange fallback is allowed. Bitget error: ${bitgetMessage}.`);
  }
}

async function fetchFundamentalSnapshot(): Promise<FundamentalSnapshot> {
  const values: Record<string, number | null> = {
    funding_rate: null,
    open_interest: null,
    dxy: null,
    nasdaq: null,
    etf_flows: null,
    liquidations: null,
    hash_rate: null,
    exchange_reserves: null,
    stablecoins_supply: null,
    us_rates: null
  };
  const sources: Record<string, string | null> = {};
  const warnings: string[] = [];

  const fundingRate = await fetchBitgetFundingRate();
  if (fundingRate.value !== null) {
    values.funding_rate = fundingRate.value;
    sources.funding_rate = fundingRate.source;
  } else {
    sources.funding_rate = null;
    warnings.push(`funding_rate absent in Worker runtime: ${fundingRate.warning}`);
  }

  const openInterest = await fetchBitgetOpenInterest();
  if (openInterest.value !== null) {
    values.open_interest = openInterest.value;
    sources.open_interest = openInterest.source;
  } else {
    sources.open_interest = null;
    warnings.push(`open_interest absent in Worker runtime: ${openInterest.warning}`);
  }

  const dxy = await fetchStooqQuote("dx.f", "stooq_dx_f_quote");
  if (dxy.value !== null) {
    values.dxy = dxy.value;
    sources.dxy = dxy.source;
  } else {
    sources.dxy = null;
    warnings.push(`dxy absent in Worker runtime: ${dxy.warning}`);
  }

  const nasdaq = await fetchStooqQuote("^ndx", "stooq_ndx_quote");
  if (nasdaq.value !== null) {
    values.nasdaq = nasdaq.value;
    sources.nasdaq = nasdaq.source;
  } else {
    sources.nasdaq = null;
    warnings.push(`nasdaq absent in Worker runtime: ${nasdaq.warning}`);
  }

  for (const field of ["etf_flows", "liquidations", "hash_rate", "exchange_reserves", "stablecoins_supply", "us_rates"]) {
    sources[field] = null;
  }

  const hasRealFundamentals = Object.values(sources).some((source) => source !== null);
  return {
    values,
    sources,
    status: hasRealFundamentals ? "partial_real_absent" : "absent",
    warnings: [
      ...warnings,
      "ETF flows, liquidations, hash rate, exchange reserves, stablecoin supply and US rates are absent in the Cloudflare Worker."
    ]
  };
}

async function fetchBitgetFundingRate(): Promise<{ value: number | null; source: string | null; warning: string }> {
  const url = "https://api.bitget.com/api/v2/mix/market/current-fund-rate?symbol=BTCUSDT&productType=usdt-futures";
  try {
    const response = await fetch(url, { headers: { "accept": "application/json" } });
    if (!response.ok) {
      return { value: null, source: null, warning: `HTTP ${response.status}` };
    }
    const payload = await response.json() as { code?: string; data?: unknown; msg?: string };
    if (payload.code !== "00000") {
      return { value: null, source: null, warning: payload.msg || `code ${payload.code || "unknown"}` };
    }
    const data = Array.isArray(payload.data) ? payload.data[0] : payload.data;
    const record = objectValue(data);
    const value = parseNullableNumber(record.fundingRate);
    return value === null
      ? { value: null, source: null, warning: "fundingRate missing" }
      : { value, source: "bitget_current_fund_rate", warning: "" };
  } catch (error) {
    return { value: null, source: null, warning: error instanceof Error ? error.message : String(error) };
  }
}

async function fetchBitgetOpenInterest(): Promise<{ value: number | null; source: string | null; warning: string }> {
  const url = "https://api.bitget.com/api/v2/mix/market/open-interest?symbol=BTCUSDT&productType=usdt-futures";
  try {
    const response = await fetch(url, { headers: { "accept": "application/json" } });
    if (!response.ok) {
      return { value: null, source: null, warning: `HTTP ${response.status}` };
    }
    const payload = await response.json() as { code?: string; data?: unknown; msg?: string };
    if (payload.code !== "00000") {
      return { value: null, source: null, warning: payload.msg || `code ${payload.code || "unknown"}` };
    }
    const data = objectValue(payload.data);
    const list = Array.isArray(data.openInterestList) ? data.openInterestList : [];
    const first = objectValue(list[0]);
    const value = parseNullableNumber(first.size ?? first.openInterest);
    return value === null
      ? { value: null, source: null, warning: "openInterestList size missing" }
      : { value, source: "bitget_open_interest", warning: "" };
  } catch (error) {
    return { value: null, source: null, warning: error instanceof Error ? error.message : String(error) };
  }
}

async function fetchStooqQuote(symbol: string, source: string): Promise<{ value: number | null; source: string | null; warning: string }> {
  const url = `https://stooq.com/q/l/?s=${encodeURIComponent(symbol)}&i=d`;
  try {
    const response = await fetch(url, {
      headers: {
        "accept": "text/plain,text/csv,*/*",
        "user-agent": "quant-btc-model-lite-worker/1.0"
      }
    });
    if (!response.ok) {
      return { value: null, source: null, warning: `HTTP ${response.status}` };
    }
    const text = await response.text();
    const lines = text.trim().split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) {
      return { value: null, source: null, warning: "empty Stooq response" };
    }
    const headers = lines[0].split(",").map((item) => item.trim().toLowerCase());
    const values = lines[1].split(",").map((item) => item.trim());
    const closeIndex = headers.indexOf("close");
    const value = closeIndex >= 0 ? parseNullableNumber(values[closeIndex]) : null;
    return value === null
      ? { value: null, source: null, warning: "close missing in Stooq response" }
      : { value, source, warning: "" };
  } catch (error) {
    return { value: null, source: null, warning: error instanceof Error ? error.message : String(error) };
  }
}

async function fetchBitgetCandles(): Promise<Candle[]> {
  const candles: Candle[] = [];
  let endTime = Date.now();

  for (let page = 0; page < 8; page += 1) {
    const url = new URL("https://api.bitget.com/api/v2/spot/market/candles");
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

function parseHorizons(value: unknown, fallback: number[]): number[] {
  const raw = Array.isArray(value)
    ? value
    : typeof value === "string"
      ? value.split(",")
      : [];
  const parsed = raw
    .map((item) => clampInt(parseNumber(item, NaN), 1, 3650))
    .filter((item) => Number.isFinite(item));
  const unique = Array.from(new Set(parsed));
  const horizons = unique.length > 0 ? unique : fallback;
  return horizons.slice(0, 8);
}

function parseNumber(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseNullableNumber(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function clampInt(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function numberField(value: unknown, key: string): number | null {
  const parsed = parseNullableNumber(objectValue(value)[key]);
  return parsed;
}

function stringField(value: unknown, key: string): string | null {
  const raw = objectValue(value)[key];
  return typeof raw === "string" ? raw : null;
}

function getMarketSpotSnapshot(market: MarketCandles) {
  const sorted = [...market.candles].sort((a, b) => a.timestamp - b.timestamp);
  const latest = sorted[sorted.length - 1];
  const timestamp = latest ? new Date(latest.timestamp) : null;
  return {
    price: latest?.close || null,
    timestamp: timestamp ? timestamp.toISOString() : null,
    timestamp_utc: timestamp ? timestamp.toISOString() : null,
    timestamp_paris: timestamp ? parisIso(timestamp) : null,
    source: market.source,
    status: "real"
  };
}

function summarizeFrameResult(frame: Record<string, unknown>) {
  const distribution = objectValue(frame.distribution);
  const risk = objectValue(frame.risk_metrics);
  const confidence = objectValue(frame.confidence_score);
  const regime = objectValue(frame.regime_distribution);
  return {
    horizon: numberField(frame, "horizon"),
    model_run_id: stringField(frame, "model_run_id"),
    report_date: stringField(frame, "report_date"),
    report_date_utc: stringField(frame, "report_date_utc"),
    report_date_paris: stringField(frame, "report_date_paris"),
    reference_spot: numberField(objectValue(frame.provenance), "reference_spot"),
    p10_return: numberField(distribution, "p10_return"),
    median_return: numberField(distribution, "median_return"),
    p90_return: numberField(distribution, "p90_return"),
    probability_positive_return: numberField(distribution, "probability_positive_return"),
    var_95_return: numberField(risk, "var_95_return"),
    cvar_95_return: numberField(risk, "cvar_95_return"),
    confidence_score: numberField(confidence, "score"),
    regime_sum_with_residual: numberField(regime, "sum_with_residual"),
    dominant_regime: dominantRegime(regime)
  };
}

function dominantRegime(regime: Record<string, unknown>): string {
  const entries = [
    ["bull", numberField(regime, "bull") || 0],
    ["bear", numberField(regime, "bear") || 0],
    ["range", numberField(regime, "range") || 0],
    ["non_classified_transition", numberField(regime, "non_classified_transition") || 0]
  ] as const;
  return [...entries].sort((a, b) => b[1] - a[1])[0][0];
}

function buildMultiFrameAggregate(frameSummaries: Record<string, unknown>[]) {
  const valid = frameSummaries.filter((frame) => numberField(frame, "horizon") !== null);
  const byMedian = [...valid].sort((a, b) => (numberField(b, "median_return") || -Infinity) - (numberField(a, "median_return") || -Infinity));
  const byRisk = [...valid].sort((a, b) => (numberField(a, "cvar_95_return") || Infinity) - (numberField(b, "cvar_95_return") || Infinity));
  const confidenceValues = valid.map((frame) => numberField(frame, "confidence_score")).filter((value): value is number => value !== null);
  return {
    strongest_median_return_horizon: numberField(byMedian[0], "horizon"),
    weakest_median_return_horizon: numberField(byMedian[byMedian.length - 1], "horizon"),
    most_severe_cvar_95_horizon: numberField(byRisk[0], "horizon"),
    average_confidence_score: confidenceValues.length > 0 ? mean(confidenceValues) : null,
    directional_note: "Compare horizons probabilistically; do not collapse them into one deterministic BTC prediction."
  };
}

function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
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
  capped: boolean,
  marketSource = "unknown",
  fundamentalStatus: FundamentalSnapshot["status"] = "absent"
) {
  let score = 35;
  score += Math.min(25, candleCount / 40);
  score += Math.min(15, simulations / 500);
  score += calibration.std > 0 && calibration.std < 0.08 ? 10 : 3;
  score -= capped ? 8 : 0;
  score -= fundamentalStatus === "partial_real_absent" ? 8 : 15;
  const rounded = Math.round(clamp(score, 0, 100));
  return {
    score: rounded,
    level: rounded < 50 ? "low_to_moderate_fragile" : rounded < 70 ? "moderate" : "high",
    drivers: {
      market_price_quality: `real_${marketSource}`,
      model_stability: "simplified_terminal_distribution",
      backtest_performance: "absent",
      uncertainty: fundamentalStatus === "partial_real_absent"
        ? "elevated_due_to_partial_fundamentals_and_worker_runtime_cap"
        : "elevated_due_to_missing_fundamentals_and_worker_runtime_cap"
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

function parisIso(date: Date): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: USER_DISPLAY_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23"
  }).formatToParts(date);
  const item = (type: string) => parts.find((part) => part.type === type)?.value || "00";
  const year = Number(item("year"));
  const month = Number(item("month"));
  const day = Number(item("day"));
  const hour = Number(item("hour"));
  const minute = Number(item("minute"));
  const second = Number(item("second"));
  const parisAsUtc = Date.UTC(year, month - 1, day, hour, minute, second);
  const offsetMinutes = Math.round((parisAsUtc - date.getTime()) / 60000);
  const sign = offsetMinutes >= 0 ? "+" : "-";
  const absolute = Math.abs(offsetMinutes);
  const offsetHours = String(Math.floor(absolute / 60)).padStart(2, "0");
  const offsetRemainder = String(absolute % 60).padStart(2, "0");
  return `${item("year")}-${item("month")}-${item("day")}T${item("hour")}:${item("minute")}:${item("second")}${sign}${offsetHours}:${offsetRemainder}`;
}

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: JSON_HEADERS
  });
}
