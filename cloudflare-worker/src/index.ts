interface Env {
  DB?: D1Database;
  WORKER_SERVICE_NAME?: string;
  MAX_SIMULATIONS?: string;
  DEFAULT_SIMULATIONS?: string;
  DEFAULT_HORIZON?: string;
  DEFAULT_HORIZONS?: string;
  RATE_LIMIT_RUNS_PER_MINUTE?: string;
  RATE_LIMIT_WINDOW_SECONDS?: string;
  RENDER_API_BASE?: string;
  DEEP_RATE_LIMIT_RUNS_PER_MINUTE?: string;
  DEEP_RATE_LIMIT_WINDOW_SECONDS?: string;
  QUICK_CACHE_MAX_SECONDS?: string;
  STALE_CACHE_MAX_SECONDS?: string;
  OPS_ALERT_WEBHOOK_URL?: string;
  DISCORD_WEBHOOK_URL?: string;
  TELEGRAM_BOT_TOKEN?: string;
  TELEGRAM_CHAT_ID?: string;
  OPS_MONITOR_ALERT_COOLDOWN_SECONDS?: string;
  OPS_DAILY_SUMMARY_PARIS_HOUR?: string;
  MODEL_ALERT_VAR95_THRESHOLD?: string;
  MODEL_ALERT_CONFIDENCE_THRESHOLD?: string;
  MODEL_ALERT_TRANSITION_THRESHOLD?: string;
  MODEL_ALERT_BIAS_DELTA_THRESHOLD?: string;
  MODEL_ALERT_COOLDOWN_SECONDS?: string;
  MODEL_ALERT_QUICK_REFRESH_SECONDS?: string;
  MODEL_ALERT_DEEP_REFRESH_SECONDS?: string;
  TRADING_MODE?: string;
  TRADING_DEFAULT_NOTIONAL_USDT?: string;
  TRADING_MAX_NOTIONAL_USDT?: string;
  TRADING_MIN_CONFIDENCE?: string;
  TRADING_MAX_VAR95?: string;
  TRADING_MAX_TRANSITION?: string;
  TRADING_BUY_PROB_UP?: string;
  TRADING_SELL_PROB_UP?: string;
  TRADING_MAX_SPOT_AGE_SECONDS?: string;
  TRADING_LIVE_CONFIRMATION?: string;
  TRADING_TELEGRAM_APPROVAL_ENABLED?: string;
  BITGET_API_KEY?: string;
  BITGET_API_SECRET?: string;
  BITGET_API_PASSPHRASE?: string;
  STRATEGY_MIN_ENSEMBLE_SCORE?: string;
  STRATEGY_MIN_AGREEMENT?: string;
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

const WORKER_VERSION = "1.29.0";
const SCHEMA_VERSION = "gpt_action_cloudflare_schema_v1.29.0";
const MODEL_VERSION = "cloudflare_render_bitget_bridge_v1";
const DEFAULT_WORKER_SERVICE_NAME = "quant-btc-model-lite-worker";
const DEFAULT_RENDER_API_BASE = "https://quant-btc-model-api.onrender.com";
const DEFAULT_MULTI_HORIZONS = [7, 30, 90, 180, 365];
const SIMULATION_HARD_CAP = 10000;
const QUICK_CACHE_MAX_SECONDS_DEFAULT = 10 * 60;
const STALE_CACHE_MAX_SECONDS_DEFAULT = 60 * 60;
const OPS_MONITOR_ALERT_COOLDOWN_SECONDS_DEFAULT = 15 * 60;
const OPS_DAILY_SUMMARY_PARIS_HOUR_DEFAULT = 9;
const MODEL_ALERT_VAR95_THRESHOLD_DEFAULT = 0.30;
const MODEL_ALERT_CONFIDENCE_THRESHOLD_DEFAULT = 50;
const MODEL_ALERT_TRANSITION_THRESHOLD_DEFAULT = 0.25;
const MODEL_ALERT_BIAS_DELTA_THRESHOLD_DEFAULT = 0.10;
const MODEL_ALERT_COOLDOWN_SECONDS_DEFAULT = 30 * 60;
const MODEL_ALERT_QUICK_REFRESH_SECONDS_DEFAULT = 5 * 60;
const MODEL_ALERT_DEEP_REFRESH_SECONDS_DEFAULT = 30 * 60;
const LOCK_TTL_SECONDS_DEFAULT = 4 * 60;
const REALTIME_SNAPSHOT_MAX_SECONDS = 6 * 60;
const TRADING_DEFAULT_NOTIONAL_USDT_DEFAULT = 10;
const TRADING_MAX_NOTIONAL_USDT_DEFAULT = 25;
const TRADING_MIN_CONFIDENCE_DEFAULT = 55;
const TRADING_MAX_VAR95_DEFAULT = 0.25;
const TRADING_MAX_TRANSITION_DEFAULT = 0.30;
const TRADING_BUY_PROB_UP_DEFAULT = 0.58;
const TRADING_SELL_PROB_UP_DEFAULT = 0.42;
const TRADING_MAX_SPOT_AGE_SECONDS_DEFAULT = 180;
const BITGET_SPOT_PLACE_ORDER_PATH = "/api/v2/spot/trade/place-order";
const STRATEGY_MIN_ENSEMBLE_SCORE_DEFAULT = 25;
const STRATEGY_MIN_AGREEMENT_DEFAULT = 0.55;
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
  },
  "/quick": {
    name: "quick",
    label: "Quick multi-frame",
    horizons: [7, 30, 90, 180, 365],
    simulations: 2000,
    description: "Short alias for the standard 7/30/90/180/365 GPT analysis."
  },
  "/tactical": {
    name: "tactical",
    label: "Tactical short-frame",
    horizons: [1, 3, 7, 14, 30],
    simulations: 5000,
    description: "Short alias for the 1/3/7/14/30 day tactical GPT analysis."
  },
  "/deep": {
    name: "deep",
    label: "Deep full-frame",
    horizons: [1, 3, 7, 14, 30, 90, 180, 365],
    simulations: 10000,
    description: "Short alias for the high-power full-frame GPT analysis."
  }
};
const USER_DISPLAY_TIMEZONE = "Europe/Paris";
const TIMEZONE_POLICY = "Source timestamps are UTC. User-facing GPT answers must show both UTC and Europe/Paris when citing report dates or spot timestamps.";
const rateLimitBuckets = new Map<string, number[]>();

export default {
  async scheduled(_controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(warmRenderBitgetBridge(env));
    ctx.waitUntil(collectRealtimeMarketSnapshot(env, "scheduled"));
    ctx.waitUntil(runOperationalMonitor(env));
    ctx.waitUntil(runModelAlertMonitor(env, false, true));
    ctx.waitUntil(processDeepJobQueue(env));
    ctx.waitUntil(evaluateCustomAlertRules(env));
    ctx.waitUntil(sendDailyOpsSummaryIfDue(env));
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
          service: workerServiceName(env),
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
          service: workerServiceName(env),
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
            "analysis_presets_quick_tactical_deep",
            "dedicated_cached_deep_action",
            "ops_monitoring",
            "strict_cache_policy",
            "deep_compute_quota",
            "optional_webhook_alerting",
            "telegram_ops_alerting",
            "telegram_daily_ops_summary",
            "telegram_model_alerts",
            "telegram_model_alert_real_time_refresh",
            "telegram_french_notifications",
            "d1_refresh_locks",
            "telegram_interactive_commands",
            "custom_alert_rules",
            "deep_job_queue",
            "realtime_bitget_polling_snapshots",
            "local_dashboard",
            "visible_backtest_report",
            "legal_pages",
            "paper_trading_engine",
            "gpt_trade_proposals",
            "telegram_trade_approval",
            "bitget_live_trading_guarded_disabled_by_default",
            "quant_strategy_engine_v1",
            "strategy_ensemble_scoring",
            "strategy_signal_persistence",
            "strategy_paper_trading"
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
          service: workerServiceName(env),
          worker_version: WORKER_VERSION,
          always_awake_target: true,
          runtime: "cloudflare_worker_free_tier",
          endpoints: ["/health", "/version", "/status", "/audit", "/ops/status", "/ops/monitor", "/ops/test-alert", "/ops/test-summary", "/model-alerts/status", "/model-alerts/test", "/realtime/status", "/realtime/collect", "/telegram/webhook", "/telegram/setup-webhook", "/alert-rules", "/alert-rules/evaluate", "/deep-jobs", "/trading/status", "/trading/signal", "/trading/orders", "/trading/paper-order", "/trading/propose", "/trading/approve", "/trading/paper-pnl", "/trading/paper-portfolio", "/trading/cleanup-paper-tests", "/strategies/status", "/strategies/deep-summary", "/strategies/deep-signal", "/strategies/deep-paper-order", "/strategies/signal", "/strategies/ensemble", "/strategies/signals", "/strategies/paper-order", "/strategies/propose-trade", "/backtests", "/legal", "/legal/privacy", "/legal/terms", "/legal/disclaimer", "/legal/refund", "/run", "/multi-run", "/multiRun", "/run-quick", "/run-tactical", "/run-deep", "/quick", "/tactical", "/deep", "/analyze", "/analyze-deep", "/latest", "/history", "/compare-runs", "/alerts", "/alerts/subscribe", "/alerts/subscriptions", "/backtest-summary", "/billing/plans", "/billing/checkout", "/clients/register", "/clients/me", "/usage-summary", "/d1/status", "/dashboard", "/pdf-report"],
          runtime_controls: {
            max_simulations: getMaxSimulations(env),
            default_simulations: clampInt(parseNumber(env.DEFAULT_SIMULATIONS, 2000), 100, getMaxSimulations(env)),
            default_horizon: clampInt(parseNumber(env.DEFAULT_HORIZON, 365), 1, 3650),
            default_horizons: parseHorizons(env.DEFAULT_HORIZONS, DEFAULT_MULTI_HORIZONS),
            analysis_presets: publicAnalysisPresets(env),
            rate_limit_runs_per_minute: getRateLimit(env).limit,
            rate_limit_window_seconds: getRateLimit(env).windowSeconds,
            deep_compute_rate_limit_runs_per_minute: getDeepRateLimit(env).limit,
            deep_compute_rate_limit_window_seconds: getDeepRateLimit(env).windowSeconds,
            cache_policy: cachePolicy(env)
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
            free_tier_role: "durable run, usage, client, alert and ops metadata storage",
            render_runtime_storage: "secondary"
          },
          ops_monitoring: {
            scheduled_check: "every_5_minutes",
            alert_channels: getOpsAlertChannels(env),
            cache_policy: cachePolicy(env),
            deep_compute_quota: getDeepRateLimit(env),
            daily_summary_paris_hour: getDailySummaryParisHour(env),
            model_alerts: getModelAlertConfig(env)
          },
          trading: tradingPublicStatus(env),
          strategies: strategyPublicStatus(env),
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
            "Spot freshness, Monte Carlo error, multi-seed stability, alerts and run comparison diagnostics must be surfaced when present.",
            "Cloudflare Workers free tier cannot keep a permanent Bitget WebSocket collector alive; realtime snapshots are collected by scheduled polling and explicit /realtime/collect calls.",
            "Trading is paper-only unless TRADING_MODE=live, Bitget trade secrets are configured, and an explicit owner approval/confirmation is supplied."
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

      if (url.pathname === "/ops/status" && request.method === "GET") {
        return json(await buildOpsStatus(env));
      }

      if (url.pathname === "/ops/monitor" && request.method === "GET") {
        const status = await runOperationalMonitor(env, true);
        return json(status, status.status === "ok" ? 200 : 503);
      }

      if (url.pathname === "/ops/test-alert" && request.method === "GET") {
        return json(await sendOpsTestAlert(env));
      }

      if (url.pathname === "/ops/test-summary" && request.method === "GET") {
        return json(await sendDailyOpsSummary(env, true));
      }

      if (url.pathname === "/realtime/status" && request.method === "GET") {
        return json(await realtimeStatus(env));
      }

      if (url.pathname === "/realtime/collect" && request.method === "GET") {
        return json(await collectRealtimeMarketSnapshot(env, "manual"));
      }

      if (url.pathname === "/model-alerts/status" && request.method === "GET") {
        const input = await readInput(request, url);
        const refreshStatus = wantsFreshRun(input)
          ? await refreshModelAlertRunsIfNeeded(env, true)
          : { status: "not_requested", reason: "status endpoint is cache-only unless fresh=true is provided" };
        return json(await evaluateLatestModelAlerts(env, refreshStatus));
      }

      if (url.pathname === "/model-alerts/test" && request.method === "GET") {
        const input = await readInput(request, url);
        return json(await runModelAlertMonitor(env, true, true, wantsFreshRun(input)));
      }

      if (url.pathname === "/telegram/webhook" && request.method === "POST") {
        return json(await handleTelegramWebhook(env, await readJson(request)));
      }

      if (url.pathname === "/telegram/setup-webhook" && request.method === "GET") {
        return json(await setupTelegramWebhook(env, request));
      }

      if (url.pathname === "/alert-rules" && request.method === "GET") {
        return json(await listCustomAlertRules(env, url.searchParams.get("chat_id") || undefined));
      }

      if (url.pathname === "/alert-rules" && request.method === "POST") {
        return json(await createCustomAlertRule(env, await readJson(request)));
      }

      if (url.pathname === "/alert-rules/evaluate" && request.method === "GET") {
        return json(await evaluateCustomAlertRules(env));
      }

      if (url.pathname === "/deep-jobs" && request.method === "GET") {
        return json(await listDeepJobs(env, clampInt(parseNumber(url.searchParams.get("limit"), 10), 1, 50)));
      }

      if (url.pathname === "/deep-jobs" && request.method === "POST") {
        return json(await createDeepJob(env, await readJson(request)));
      }

      if (url.pathname === "/deep-jobs/process" && request.method === "GET") {
        return json(await processDeepJobQueue(env));
      }

      if (url.pathname === "/trading/status" && request.method === "GET") {
        return json(await tradingStatus(env));
      }

      if (url.pathname === "/trading/signal" && request.method === "GET") {
        return json(await buildTradingSignal(env, await readInput(request, url)));
      }

      if (url.pathname === "/trading/orders" && request.method === "GET") {
        return json(await listTradeOrders(env, clampInt(parseNumber(url.searchParams.get("limit"), 10), 1, 50)));
      }

      if (url.pathname === "/trading/paper-pnl" && request.method === "GET") {
        return json(await paperTradingPnl(env));
      }

      if (url.pathname === "/trading/paper-portfolio" && request.method === "GET") {
        return json(await paperPortfolioState(env));
      }

      if (url.pathname === "/trading/cleanup-paper-tests" && request.method === "GET") {
        return json(await cleanupPaperTestOrders(env, await readInput(request, url)));
      }

      if (url.pathname === "/trading/paper-order" && (request.method === "POST" || request.method === "GET")) {
        return json(await createPaperTradeOrder(env, await readInput(request, url), "gpt_action"));
      }

      if (url.pathname === "/trading/propose" && (request.method === "POST" || request.method === "GET")) {
        return json(await proposeTradeOrder(env, await readInput(request, url), "gpt_action"));
      }

      if (url.pathname === "/trading/approve" && (request.method === "POST" || request.method === "GET")) {
        return json(await approveTradeOrder(env, await readInput(request, url), "gpt_action"));
      }

      if (url.pathname === "/strategies/status" && request.method === "GET") {
        return json(await strategyStatus(env));
      }

      if (url.pathname === "/strategies/deep-summary" && request.method === "GET") {
        return json(await buildStrategySummary(env));
      }

      if (url.pathname === "/strategies/deep-signal" && request.method === "GET") {
        return json(await buildStrategySignal(env, { asset: "BTC", preset: "deep", horizon: 30 }));
      }

      if (url.pathname === "/strategies/deep-paper-order" && request.method === "GET") {
        return json(await createStrategyPaperOrder(env, { asset: "BTC", preset: "deep", horizon: 30 }, "gpt_strategy_action"));
      }

      if ((url.pathname === "/strategies/signal" || url.pathname === "/strategies/ensemble") && request.method === "GET") {
        return json(await buildStrategySignal(env, await readInput(request, url)));
      }

      if (url.pathname === "/strategies/signals" && request.method === "GET") {
        return json(await listStrategySignals(env, clampInt(parseNumber(url.searchParams.get("limit"), 10), 1, 50)));
      }

      if (url.pathname === "/strategies/paper-order" && (request.method === "POST" || request.method === "GET")) {
        return json(await createStrategyPaperOrder(env, await readInput(request, url), "gpt_strategy_action"));
      }

      if (url.pathname === "/strategies/propose-trade" && (request.method === "POST" || request.method === "GET")) {
        return json(await proposeStrategyTradeOrder(env, await readInput(request, url), "gpt_strategy_action"));
      }

      if (url.pathname === "/backtests" && request.method === "GET") {
        return json(await visibleBacktestReport(env));
      }

      if (url.pathname === "/legal" && request.method === "GET") {
        return html(legalIndexHtml());
      }

      if (url.pathname.startsWith("/legal/") && request.method === "GET") {
        return html(legalPageHtml(url.pathname));
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

      if (url.pathname === "/dashboard" && request.method === "HEAD") {
        return new Response(null, {
          status: 200,
          headers: {
            "content-type": "text/html; charset=utf-8",
            "access-control-allow-origin": "*"
          }
        });
      }

      if (url.pathname === "/dashboard" && request.method === "GET") {
        return html(await dashboardHtml(env));
      }

      if (url.pathname === "/pdf-report" && request.method === "GET") {
        return Response.redirect(renderUrl(`/pdf-report${url.search}`, env), 302);
      }

      if (url.pathname === "/analyze-deep" && (request.method === "POST" || request.method === "GET")) {
        const rateLimit = checkRateLimit(request, env);
        if (!rateLimit.allowed) {
          return json(rateLimitResponse(rateLimit), 429);
        }
        const input = await readInput(request, url);
        const presetPath = "/deep";
        const preset = ANALYSIS_PRESETS[presetPath];
        const body = normalizeRenderPresetPayload(input, env, preset);
        if (!wantsFreshRun(input)) {
          const cached = await latestCachedAnalyzeResponse(env, body, presetPath, publicRateLimit(rateLimit), cachePolicy(env).fresh_seconds, "hit", "/analyze-deep");
          if (cached) {
            return json(cached);
          }
        }
        const deepRateLimit = checkDeepRateLimit(request, env);
        if (!deepRateLimit.allowed) {
          const staleCached = await latestCachedAnalyzeResponse(env, body, presetPath, publicRateLimit(rateLimit), cachePolicy(env).warning_seconds, "stale_fallback", "/analyze-deep");
          if (staleCached) {
            staleCached.warning = "Deep compute quota is exhausted, so a warning-age D1 cache fallback is returned. Do not present it as a fresh live run.";
            staleCached.deep_compute_rate_limit = publicRateLimit(deepRateLimit);
            return json(staleCached);
          }
          return json(deepRateLimitResponse(deepRateLimit), 429);
        }
        const result = await proxyRenderPost("/multi-run", body, env, request);
        result.analysis_preset = {
          ...publicAnalysisPreset(presetPath, env),
          requested_endpoint: "/analyze-deep",
          requested_preset: preset.name
        };
        result.cloudflare_bridge = {
          ...objectValue(result.cloudflare_bridge),
          operation_path: "/analyze-deep",
          render_operation_path: "/multi-run",
          analysis_preset: preset.name
        };
        if (result.error) {
          const staleCached = await latestCachedAnalyzeResponse(env, body, presetPath, publicRateLimit(rateLimit), cachePolicy(env).warning_seconds, "stale_fallback", "/analyze-deep");
          if (staleCached) {
            staleCached.warning = "Render returned an error, so a warning-age D1 deep cache fallback is returned. Do not present it as a fresh live run.";
            staleCached.render_error = {
              error: result.error,
              message: result.message,
              render_status: result.render_status
            };
            return json(staleCached);
          }
        }
        result.cloudflare_d1 = result.error
          ? { status: "skipped", target: "cloudflare_d1", reason: "engine_error_or_absent_live_output" }
          : queueD1RunPersist(result, "/analyze-deep", body, env, ctx);
        return json(compactAnalyzeResponse(result, publicRateLimit(rateLimit), env));
      }

      if (url.pathname === "/analyze" && (request.method === "POST" || request.method === "GET")) {
        const rateLimit = checkRateLimit(request, env);
        if (!rateLimit.allowed) {
          return json(rateLimitResponse(rateLimit), 429);
        }
        const input = await readInput(request, url);
        const presetPath = analysisPresetPathFromInput(input);
        const preset = ANALYSIS_PRESETS[presetPath];
        const body = normalizeRenderPresetPayload(input, env, preset);
        if (!wantsFreshRun(input)) {
          const cached = await latestCachedAnalyzeResponse(env, body, presetPath, publicRateLimit(rateLimit), cachePolicy(env).fresh_seconds);
          if (cached) {
            return json(cached);
          }
        }
        const result = await proxyRenderPost("/multi-run", body, env, request);
        result.analysis_preset = {
          ...publicAnalysisPreset(presetPath, env),
          requested_endpoint: "/analyze",
          requested_preset: preset.name
        };
        result.cloudflare_bridge = {
          ...objectValue(result.cloudflare_bridge),
          operation_path: "/analyze",
          render_operation_path: "/multi-run",
          analysis_preset: preset.name
        };
        if (result.error) {
          const staleCached = await latestCachedAnalyzeResponse(env, body, presetPath, publicRateLimit(rateLimit), cachePolicy(env).warning_seconds, "stale_fallback");
          if (staleCached) {
            staleCached.warning = "Render returned an error, so a warning-age D1 cache fallback is returned. Do not present it as a fresh live run.";
            staleCached.render_error = {
              error: result.error,
              message: result.message,
              render_status: result.render_status
            };
            return json(staleCached);
          }
        }
        result.cloudflare_d1 = result.error
          ? { status: "skipped", target: "cloudflare_d1", reason: "engine_error_or_absent_live_output" }
          : queueD1RunPersist(result, "/analyze", body, env, ctx);
        return json(compactAnalyzeResponse(result, publicRateLimit(rateLimit), env));
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

function cachePolicy(env: Env): Record<string, number> {
  const freshSeconds = clampInt(parseNumber(env.QUICK_CACHE_MAX_SECONDS, QUICK_CACHE_MAX_SECONDS_DEFAULT), 60, 3600);
  const warningSeconds = clampInt(parseNumber(env.STALE_CACHE_MAX_SECONDS, STALE_CACHE_MAX_SECONDS_DEFAULT), freshSeconds, 24 * 60 * 60);
  return {
    fresh_seconds: freshSeconds,
    warning_seconds: warningSeconds,
    hard_block_after_seconds: warningSeconds
  };
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

function analysisPresetPathFromInput(input: Record<string, unknown>): string {
  const preset = String(input.preset || input.mode || "quick").trim().toLowerCase();
  if (preset === "quick" || preset === "standard" || preset === "default") {
    return "/quick";
  }
  if (preset === "tactical" || preset === "short" || preset === "short_term") {
    return "/tactical";
  }
  return "/deep";
}

function wantsFreshRun(input: Record<string, unknown>): boolean {
  const value = input.fresh ?? input.live ?? input.force_fresh;
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    return ["1", "true", "yes", "fresh", "live"].includes(value.trim().toLowerCase());
  }
  return false;
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
    const [runs, usage, clients, subscriptions, ops, locks, snapshots, jobs, rules, tradeOrders, tradeEvents] = await env.DB.batch([
      env.DB.prepare("SELECT COUNT(*) AS count FROM quant_runs"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM usage_events"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM api_clients"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM alert_subscriptions"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM ops_events"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM system_locks"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM market_snapshots"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM deep_jobs"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM user_alert_rules"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM trade_orders"),
      env.DB.prepare("SELECT COUNT(*) AS count FROM trade_events")
    ]);
    const strategySignals = await optionalD1Count(env, "strategy_signals");
    const paperPnlSnapshots = await optionalD1Count(env, "paper_pnl_snapshots");
    return {
      status: "ok",
      target: "cloudflare_d1",
      database_name: "quant-btc-model-lite-db",
      binding: "DB",
      counts: {
        runs: countFromD1(runs),
        usage_events: countFromD1(usage),
        clients: countFromD1(clients),
        alert_subscriptions: countFromD1(subscriptions),
        ops_events: countFromD1(ops),
        system_locks: countFromD1(locks),
        market_snapshots: countFromD1(snapshots),
        deep_jobs: countFromD1(jobs),
        user_alert_rules: countFromD1(rules),
        trade_orders: countFromD1(tradeOrders),
        trade_events: countFromD1(tradeEvents),
        strategy_signals: strategySignals,
        paper_pnl_snapshots: paperPnlSnapshots
      },
      free_tier_role: "durable metadata storage for run archives, usage logs, clients, locks, realtime snapshots, alert rules, queued deep jobs, strategy signals, paper PnL and trading journals",
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

async function optionalD1Count(env: Env, tableName: string): Promise<number | string> {
  if (!env.DB || !/^[a-z_]+$/i.test(tableName)) {
    return "absent";
  }
  try {
    const result = await env.DB.prepare(`SELECT COUNT(*) AS count FROM ${tableName}`).first();
    return numberOrNull(objectValue(result).count) ?? 0;
  } catch {
    return "migration_pending";
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

async function buildOpsStatus(env: Env): Promise<Record<string, unknown>> {
  const now = new Date();
  const policy = cachePolicy(env);
  const [renderHealth, d1, quickCache, deepCache] = await Promise.all([
    checkRenderHealth(env),
    d1Status(env),
    latestD1CacheSummary(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons),
    latestD1CacheSummary(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons)
  ]);
  const quickCheck = classifyCacheSummary(quickCache, policy);
  const deepCheck = classifyCacheSummary(deepCache, policy);
  const warnings: string[] = [];
  const blockers: string[] = [];

  if (renderHealth.status !== "ok") {
    blockers.push(`Render health ${renderHealth.status}`);
  }
  if (d1.status !== "ok") {
    blockers.push(`Cloudflare D1 ${d1.status}`);
  }
  collectOpsIssue(quickCheck, "quick cache", warnings, blockers);
  collectOpsIssue(deepCheck, "deep cache", warnings, blockers);

  const status = blockers.length > 0 ? "degraded" : warnings.length > 0 ? "warning" : "ok";
  return {
    status,
    service: workerServiceName(env),
    worker_version: WORKER_VERSION,
    schema_version: SCHEMA_VERSION,
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now),
    checks: {
      worker: {
        status: "ok",
        quick_domain: "https://quant-btc-model-lite.mdl-bitcoin-analyst.workers.dev",
        deep_domain: "https://quant-btc-model-deep.mdl-bitcoin-analyst.workers.dev"
      },
      render_health: renderHealth,
      cloudflare_d1: d1,
      quick_cache: quickCheck,
      deep_cache: deepCheck
    },
    cache_policy: policy,
    deep_compute_quota: getDeepRateLimit(env),
    alerting: {
      channels: getOpsAlertChannels(env),
      cooldown_seconds: clampInt(parseNumber(env.OPS_MONITOR_ALERT_COOLDOWN_SECONDS, OPS_MONITOR_ALERT_COOLDOWN_SECONDS_DEFAULT), 60, 24 * 60 * 60),
      daily_summary_paris_hour: getDailySummaryParisHour(env)
    },
    warnings,
    blockers,
    operational_policy: [
      "Cache age <= fresh_seconds: analysis allowed as recent cache.",
      "Cache age <= warning_seconds after Render failure or quota exhaustion: analysis allowed only with explicit warning-age fallback.",
      "Cache age > warning_seconds: analysis blocked; do not present stale numbers.",
      "Deep live computation has a separate quota; cache is preferred before compute."
    ]
  };
}

async function runOperationalMonitor(env: Env, manual = false): Promise<Record<string, unknown>> {
  const status = await buildOpsStatus(env);
  if (status.status !== "ok") {
    const warnings = Array.isArray(status.warnings) ? status.warnings.join("; ") : "";
    const blockers = Array.isArray(status.blockers) ? status.blockers.join("; ") : "";
    const message = blockers || warnings || "Quant BTC operational monitor detected a degraded state.";
    const fingerprint = `ops:${status.status}:${message}`;
    await sendOpsAlertIfNeeded(env, fingerprint, message, status);
    await persistOpsEventToD1(env, {
      kind: manual ? "manual_monitor" : "scheduled_monitor",
      status: String(status.status),
      severity: String(status.status) === "degraded" ? "critical" : "warning",
      message,
      fingerprint,
      payload: status
    });
  }
  return status;
}

async function sendDailyOpsSummaryIfDue(env: Env): Promise<Record<string, unknown>> {
  const now = new Date();
  const paris = parisIso(now);
  const hour = Number(paris.slice(11, 13));
  const minute = Number(paris.slice(14, 16));
  const targetHour = getDailySummaryParisHour(env);
  if (hour !== targetHour || minute >= 10) {
    return {
      status: "skipped",
      reason: "outside_daily_summary_window",
      target_paris_hour: targetHour,
      checked_at_utc: now.toISOString(),
      checked_at_paris: paris
    };
  }
  return await sendDailyOpsSummary(env, false);
}

async function sendDailyOpsSummary(env: Env, manual: boolean): Promise<Record<string, unknown>> {
  const channels = getOpsAlertChannels(env);
  if (channels.telegram !== "configured" && channels.discord_webhook !== "configured") {
    return {
      status: "not_configured",
      channels,
      message: "No alert channel is configured."
    };
  }
  const now = new Date();
  const dateKey = parisIso(now).slice(0, 10);
  const fingerprint = manual
    ? `ops:daily-summary-test:${now.toISOString()}`
    : `ops:daily-summary:${dateKey}`;
  if (!manual && !(await shouldSendOpsAlert(env, fingerprint, 36 * 60 * 60))) {
    return {
      status: "skipped",
      reason: "daily_summary_already_sent",
      date_paris: dateKey
    };
  }
  const status = await buildOpsStatus(env);
  const text = formatDailySummaryText(status, manual);
  const [discord, telegram] = await Promise.all([
    sendDiscordOpsAlert(env, manual ? "Quant BTC daily summary TEST" : "Quant BTC daily summary", text, status),
    sendTelegramOpsAlert(env, text)
  ]);
  const sent = [discord, telegram].some((item) => objectValue(item).status === "sent");
  await persistOpsEventToD1(env, {
    kind: manual ? "manual_daily_summary" : "daily_summary",
    status: sent ? "sent" : "error",
    severity: "info",
    message: manual ? "Manual daily summary test" : `Daily ops summary ${dateKey}`,
    fingerprint,
    payload: {
      status,
      delivery: { discord, telegram }
    }
  });
  return {
    status: sent ? "sent" : "error",
    channels,
    delivery: { discord, telegram },
    date_paris: dateKey,
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now)
  };
}

function collectOpsIssue(check: Record<string, unknown>, label: string, warnings: string[], blockers: string[]): void {
  const status = stringOrNull(check.status) || "unknown";
  if (status === "error" || status === "blocked" || status === "absent") {
    blockers.push(`${label}: ${stringOrNull(check.message) || status}`);
  } else if (status === "warning") {
    warnings.push(`${label}: ${stringOrNull(check.message) || status}`);
  }
}

async function acquireD1Lock(
  env: Env,
  name: string,
  ttlSeconds = LOCK_TTL_SECONDS_DEFAULT,
  metadata: Record<string, unknown> = {}
): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { acquired: true, status: "no_d1_lock", name, owner: "no-d1" };
  }
  const now = new Date();
  const expires = new Date(now.getTime() + ttlSeconds * 1000);
  const owner = `${WORKER_VERSION}-${randomRunSuffix()}`;
  try {
    await env.DB.prepare("DELETE FROM system_locks WHERE name = ? AND expires_at_utc <= ?").bind(name, now.toISOString()).run();
    await env.DB.prepare(`
      INSERT INTO system_locks (name, owner, acquired_at_utc, expires_at_utc, metadata_json)
      VALUES (?, ?, ?, ?, ?)
    `).bind(name, owner, now.toISOString(), expires.toISOString(), JSON.stringify(metadata)).run();
    return {
      acquired: true,
      status: "locked",
      name,
      owner,
      acquired_at_utc: now.toISOString(),
      expires_at_utc: expires.toISOString()
    };
  } catch {
    const existing = await env.DB.prepare("SELECT name, owner, acquired_at_utc, expires_at_utc FROM system_locks WHERE name = ?").bind(name).first();
    return {
      acquired: false,
      status: "busy",
      name,
      owner: objectValue(existing).owner,
      acquired_at_utc: objectValue(existing).acquired_at_utc,
      expires_at_utc: objectValue(existing).expires_at_utc
    };
  }
}

async function releaseD1Lock(env: Env, name: string, owner: string): Promise<void> {
  if (!env.DB || !name || !owner || owner === "no-d1") {
    return;
  }
  try {
    await env.DB.prepare("DELETE FROM system_locks WHERE name = ? AND owner = ?").bind(name, owner).run();
  } catch {
    // Lock release is best-effort; expired locks are removed by the next acquisition.
  }
}

async function collectRealtimeMarketSnapshot(env: Env, trigger: string): Promise<Record<string, unknown>> {
  const lock = await acquireD1Lock(env, "realtime-market-collector", 90, { trigger, worker_version: WORKER_VERSION });
  if (!lock.acquired) {
    return { status: "skipped", reason: "lock_active", lock };
  }
  const now = new Date();
  try {
    const snapshot = await fetchRealtimeSnapshot(env);
    const price = numberOrNull(snapshot.price);
    const bid = numberOrNull(snapshot.bid);
    const ask = numberOrNull(snapshot.ask);
    const spreadBps = numberOrNull(snapshot.spread_bps);
    const observedAt = stringOrNull(snapshot.observed_at_utc) || now.toISOString();
    const payload = { ...snapshot, trigger };
    if (env.DB) {
      await env.DB.prepare(`
        INSERT INTO market_snapshots (
          asset, source, kind, price, bid, ask, spread_bps, funding_rate, open_interest,
          liquidations_status, payload_json, observed_at_utc, created_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        "BTC",
        "bitget_polling_snapshot",
        "spot_orderbook_derivatives",
        price,
        bid,
        ask,
        spreadBps,
        snapshot.funding_rate,
        snapshot.open_interest,
        stringOrNull(snapshot.liquidations_status) || "absent",
        JSON.stringify(payload),
        observedAt,
        now.toISOString()
      ).run();
    }
    return {
      status: "ok",
      mode: "near_realtime_polling",
      trigger,
      asset: "BTC",
      source: snapshot.source,
      limitation: "Not a permanent WebSocket stream on the free Worker tier.",
      price,
      bid,
      ask,
      spread_bps: spreadBps,
      funding_rate: snapshot.funding_rate,
      open_interest: snapshot.open_interest,
      liquidations_status: snapshot.liquidations_status || "absent",
      observed_at_utc: observedAt,
      observed_at_paris: parisIso(new Date(observedAt)),
      created_at_utc: now.toISOString(),
      created_at_paris: parisIso(now)
    };
  } catch (error) {
    return {
      status: "error",
      trigger,
      message: error instanceof Error ? error.message : String(error),
      data_status: {
        bitget_spot: "absent",
        orderbook: "absent",
        funding_rate: "absent",
        open_interest: "absent",
        liquidations: "absent"
      },
      checked_at_utc: now.toISOString(),
      checked_at_paris: parisIso(now)
    };
  } finally {
    await releaseD1Lock(env, String(lock.name), String(lock.owner));
  }
}

async function realtimeStatus(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", reason: "D1 binding is not configured" };
  }
  try {
    const row = await env.DB.prepare(`
      SELECT asset, source, kind, price, bid, ask, spread_bps, funding_rate, open_interest,
             liquidations_status, observed_at_utc, created_at_utc, payload_json
      FROM market_snapshots
      WHERE asset = ?
      ORDER BY created_at_utc DESC
      LIMIT 1
    `).bind("BTC").first();
    if (!row) {
      return {
        status: "absent",
        recommendation: "Call /realtime/collect or wait for the next scheduled collection.",
        checked_at_utc: new Date().toISOString(),
        checked_at_paris: parisIso(new Date())
      };
    }
    const createdAt = stringOrNull(objectValue(row).created_at_utc);
    const age = createdAt ? Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 1000)) : null;
    return {
      status: age !== null && age <= REALTIME_SNAPSHOT_MAX_SECONDS ? "ok" : "warning",
      freshness_label: age !== null && age <= REALTIME_SNAPSHOT_MAX_SECONDS ? "fresh" : "stale",
      max_age_seconds: REALTIME_SNAPSHOT_MAX_SECONDS,
      age_seconds: age,
      asset: row.asset,
      source: row.source,
      mode: "near_realtime_polling",
      limitation: "Free Cloudflare Workers use scheduled polling here, not a permanent WebSocket process.",
      price: row.price,
      bid: row.bid,
      ask: row.ask,
      spread_bps: row.spread_bps,
      funding_rate: row.funding_rate,
      open_interest: row.open_interest,
      liquidations_status: row.liquidations_status,
      observed_at_utc: row.observed_at_utc,
      observed_at_paris: typeof row.observed_at_utc === "string" ? parisIso(new Date(row.observed_at_utc)) : null,
      created_at_utc: createdAt,
      created_at_paris: createdAt ? parisIso(new Date(createdAt)) : null
    };
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : String(error)
    };
  }
}

async function fetchRealtimeSnapshot(env: Env): Promise<Record<string, unknown>> {
  try {
    const [ticker, orderbook, funding, oi] = await Promise.all([
      fetchBitgetTickerSnapshot(),
      fetchBitgetOrderBookSnapshot(),
      fetchBitgetFundingRate(),
      fetchBitgetOpenInterest()
    ]);
    const bid = numberOrNull(orderbook.bid);
    const ask = numberOrNull(orderbook.ask);
    const spreadBps = bid !== null && ask !== null && bid > 0 && ask >= bid
      ? ((ask - bid) / ((ask + bid) / 2)) * 10000
      : null;
    return {
      status: "ok",
      source: "bitget_direct_rest_from_cloudflare",
      route: "direct",
      price: numberOrNull(ticker.price),
      bid,
      ask,
      spread_bps: spreadBps,
      funding_rate: funding.value,
      open_interest: oi.value,
      liquidations_status: "absent",
      observed_at_utc: stringOrNull(ticker.timestamp_utc) || new Date().toISOString(),
      ticker,
      orderbook,
      funding,
      open_interest_snapshot: oi,
      liquidations: {
        status: "absent",
        source: "bitget_liquidations_websocket",
        note: "Cloudflare Worker free tier cannot keep a permanent public WebSocket collector alive; liquidation capture requires an external long-running collector."
      }
    };
  } catch (error) {
    return await fetchRenderBitgetRealtimeSnapshot(env, error instanceof Error ? error.message : String(error));
  }
}

async function fetchRenderBitgetRealtimeSnapshot(env: Env, directError: string): Promise<Record<string, unknown>> {
  const started = Date.now();
  const result = await proxyRenderPost("/multi-run", {
    asset: "BTC",
    horizons: [1],
    simulations: 100,
    model: "ensemble",
    skip_corpus: true,
    no_online: false
  }, env);
  if (result.error) {
    throw new Error(`Bitget direct failed (${directError}); Render Bitget bridge failed: ${result.message || result.error}`);
  }
  const provenance = objectValue(result.provenance_summary);
  const sharedSpot = objectValue(provenance.shared_spot_snapshot);
  const frame = objectValue(Array.isArray(result.frames) ? result.frames[0] : {});
  const frameProvenance = objectValue(frame.provenance);
  const liquidity = objectValue(result.liquidity);
  const bestBid = numberOrNull(liquidity.best_bid);
  const bestAsk = numberOrNull(liquidity.best_ask);
  const spotRaw = sharedSpot.price ?? frameProvenance.reference_spot ?? (Array.isArray(provenance.reference_spots) ? provenance.reference_spots[0] : null);
  const timestampRaw = stringOrNull(sharedSpot.timestamp) || stringOrNull(frameProvenance.reference_spot_timestamp_utc) || stringOrNull(frameProvenance.reference_spot_timestamp);
  const observedAt = timestampRaw ? new Date(timestampRaw).toISOString() : new Date().toISOString();
  await persistRunToD1(result, "/realtime/collect-render-bridge", {
    asset: "BTC",
    horizons: [1],
    simulations: 100,
    model: "ensemble"
  }, env);
  await persistUsageToD1(result, "/realtime/collect-render-bridge", {
    asset: "BTC",
    horizons: [1],
    simulations: 100,
    model: "ensemble"
  }, env);
  return {
    status: "ok",
    source: "bitget_via_render_bridge_spot_probe",
    route: "render_bridge",
    direct_cloudflare_error: directError,
    latency_ms: Date.now() - started,
    archive_id: archiveIdFromPayload(result),
    price: parsePriceValue(spotRaw),
    bid: bestBid,
    ask: bestAsk,
    spread_bps: numberOrNull(liquidity.spread_bps),
    funding_rate: numberOrNull(objectValue(result.fundamental_inputs).values && objectValue(objectValue(result.fundamental_inputs).values).funding_rate),
    open_interest: numberOrNull(objectValue(result.fundamental_inputs).values && objectValue(objectValue(result.fundamental_inputs).values).open_interest),
    liquidations_status: "absent",
    observed_at_utc: observedAt,
    observed_at_paris: parisIso(new Date(observedAt)),
    render_version: result.version,
    note: "Cloudflare direct Bitget was blocked; Render fetched Bitget and no non-Bitget exchange fallback was used."
  };
}

async function fetchBitgetTickerSnapshot(): Promise<Record<string, unknown>> {
  const response = await fetch("https://api.bitget.com/api/v2/spot/market/tickers?symbol=BTCUSDT", {
    headers: { "accept": "application/json", "user-agent": "quant-btc-model-worker-realtime/1.0" },
    cf: { cacheTtl: 0, cacheEverything: false }
  });
  if (!response.ok) {
    throw new Error(`Bitget ticker HTTP ${response.status}`);
  }
  const payload = objectValue(await response.json());
  const data = Array.isArray(payload.data) ? objectValue(payload.data[0]) : objectValue(payload.data);
  const requestTime = numberOrNull(payload.requestTime);
  const exchangeTime = numberOrNull(data.ts);
  const timestamp = exchangeTime || requestTime || Date.now();
  return {
    status: "real",
    source: "bitget_btcusdt_spot_ticker_rest",
    price: parseNullableNumber(data.lastPr ?? data.close ?? data.last),
    bid: parseNullableNumber(data.bidPr ?? data.bestBid),
    ask: parseNullableNumber(data.askPr ?? data.bestAsk),
    high_24h: parseNullableNumber(data.high24h),
    low_24h: parseNullableNumber(data.low24h),
    volume_24h: parseNullableNumber(data.baseVolume ?? data.quoteVolume),
    timestamp_utc: new Date(timestamp).toISOString(),
    timestamp_paris: parisIso(new Date(timestamp))
  };
}

async function fetchBitgetOrderBookSnapshot(): Promise<Record<string, unknown>> {
  const response = await fetch("https://api.bitget.com/api/v2/spot/market/orderbook?symbol=BTCUSDT&type=step0&limit=50", {
    headers: { "accept": "application/json", "user-agent": "quant-btc-model-worker-realtime/1.0" },
    cf: { cacheTtl: 0, cacheEverything: false }
  });
  if (!response.ok) {
    throw new Error(`Bitget orderbook HTTP ${response.status}`);
  }
  const payload = objectValue(await response.json());
  const data = objectValue(payload.data);
  const bids = Array.isArray(data.bids) ? data.bids : [];
  const asks = Array.isArray(data.asks) ? data.asks : [];
  const bestBid = parseOrderBookLevel(bids[0]);
  const bestAsk = parseOrderBookLevel(asks[0]);
  return {
    status: "real",
    source: "bitget_btcusdt_spot_orderbook_rest",
    bid: bestBid.price,
    ask: bestAsk.price,
    bid_size: bestBid.size,
    ask_size: bestAsk.size,
    levels_bid: bids.length,
    levels_ask: asks.length,
    timestamp_utc: new Date(numberOrNull(data.ts) || numberOrNull(payload.requestTime) || Date.now()).toISOString()
  };
}

function parseOrderBookLevel(value: unknown): { price: number | null; size: number | null } {
  if (Array.isArray(value)) {
    return { price: parseNullableNumber(value[0]), size: parseNullableNumber(value[1]) };
  }
  const row = objectValue(value);
  return {
    price: parseNullableNumber(row.price ?? row.px),
    size: parseNullableNumber(row.size ?? row.qty)
  };
}

async function createDeepJob(env: Env, input: Record<string, unknown>): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 binding is required for the deep job queue." };
  }
  const now = new Date();
  const jobId = `deep_${now.toISOString().replace(/[-:.]/g, "").slice(0, 15)}_${randomRunSuffix()}`;
  const chatId = stringOrNull(input.chat_id) || stringOrNull(input.notify_target) || stringOrNull(env.TELEGRAM_CHAT_ID);
  const request = {
    asset: normalizeAsset(input.asset),
    model: normalizeRenderModel(input.model),
    preset: "deep",
    horizons: ANALYSIS_PRESETS["/deep"].horizons,
    simulations: Math.min(ANALYSIS_PRESETS["/deep"].simulations, getMaxSimulations(env))
  };
  await env.DB.prepare(`
    INSERT INTO deep_jobs (
      job_id, asset, preset, status, request_json, notify_channel, notify_target,
      created_at_utc, updated_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    jobId,
    request.asset,
    "deep",
    "queued",
    JSON.stringify(request),
    chatId ? "telegram" : "none",
    chatId,
    now.toISOString(),
    now.toISOString()
  ).run();
  return {
    status: "queued",
    job_id: jobId,
    request,
    notify_channel: chatId ? "telegram" : "none",
    created_at_utc: now.toISOString(),
    created_at_paris: parisIso(now),
    note: "Deep run queued; it completes when a fresh deep cache is produced by the scheduled refresh, avoiding long Worker request timeouts."
  };
}

async function listDeepJobs(env: Env, limit: number): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", jobs: [] };
  }
  const { results } = await env.DB.prepare(`
    SELECT job_id, asset, preset, status, result_archive_id, error,
           notify_channel, created_at_utc, updated_at_utc, completed_at_utc
    FROM deep_jobs
    ORDER BY created_at_utc DESC
    LIMIT ?
  `).bind(limit).all();
  return {
    status: "ok",
    jobs: (results || []).map((item) => {
      const row = objectValue(item);
      return {
        job_id: row.job_id,
        asset: row.asset,
        preset: row.preset,
        status: row.status,
        result_archive_id: row.result_archive_id,
        error: row.error,
        notify_channel: row.notify_channel,
        created_at_utc: row.created_at_utc,
        created_at_paris: typeof row.created_at_utc === "string" ? parisIso(new Date(row.created_at_utc)) : null,
        updated_at_utc: row.updated_at_utc,
        completed_at_utc: row.completed_at_utc
      };
    })
  };
}

async function processDeepJobQueue(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", reason: "D1 binding is not configured" };
  }
  const lock = await acquireD1Lock(env, "deep-job-processor", 15 * 60, { worker_version: WORKER_VERSION });
  if (!lock.acquired) {
    return { status: "skipped", reason: "lock_active", lock };
  }
  try {
    const row = objectValue(await env.DB.prepare(`
      SELECT job_id, request_json, notify_channel, notify_target, status, created_at_utc, updated_at_utc
      FROM deep_jobs
      WHERE status IN ('queued', 'running')
      ORDER BY created_at_utc ASC
      LIMIT 1
    `).first());
    const jobId = stringOrNull(row.job_id);
    if (!jobId) {
      return { status: "idle", message: "No queued deep job." };
    }
    const preset = ANALYSIS_PRESETS["/deep"];
    const input = objectValue(JSON.parse(stringOrNull(row.request_json) || "{}"));
    const asset = normalizeAsset(input.asset);
    const latestDeep = await latestD1CacheSummary(env, asset, preset.horizons);
    const jobCreatedAt = stringOrNull(row.created_at_utc);
    const cacheCreatedAt = stringOrNull(latestDeep.created_at_utc);
    const cacheIsNewEnough = Boolean(
      latestDeep.status === "present" &&
      cacheCreatedAt &&
      (!jobCreatedAt || new Date(cacheCreatedAt).getTime() >= new Date(jobCreatedAt).getTime())
    );

    if (!cacheIsNewEnough) {
      const jobStatus = stringOrNull(row.status) || "queued";
      const updatedAt = stringOrNull(row.updated_at_utc);
      const runningAgeSeconds = updatedAt ? Math.max(0, Math.round((Date.now() - new Date(updatedAt).getTime()) / 1000)) : null;
      if (jobStatus === "running" && runningAgeSeconds !== null && runningAgeSeconds > 20 * 60) {
        const now = new Date();
        await env.DB.prepare(`
          UPDATE deep_jobs SET status = ?, error = ?, updated_at_utc = ? WHERE job_id = ?
        `).bind("queued", "running_timeout_requeued_waiting_for_next_deep_cache", now.toISOString(), jobId).run();
        return {
          status: "requeued",
          job_id: jobId,
          reason: "Previous running state exceeded 20 minutes without a newer deep archive."
        };
      }
      return {
        status: "waiting_for_deep_cache",
        job_id: jobId,
        job_status: jobStatus,
        latest_deep_cache: latestDeep,
        note: "The Worker does not hold a long HTTP request for 10k simulations. The job will complete after the next scheduled deep refresh creates a newer deep archive."
      };
    }

    const archiveId = stringOrNull(latestDeep.archive_id);
    const finished = new Date();
    await env.DB.prepare(`
      UPDATE deep_jobs SET status = ?, result_archive_id = ?, updated_at_utc = ?, completed_at_utc = ? WHERE job_id = ?
    `).bind("completed", archiveId, finished.toISOString(), finished.toISOString(), jobId).run();
    await notifyDeepJob(env, row, [
      "Quant BTC - Deep job termine",
      `Job: ${jobId}`,
      `Archive: ${archiveId || "absente"}`,
      `UTC: ${finished.toISOString()}`,
      `Paris: ${parisIso(finished)}`,
      "Source: cache deep D1 frais",
      "Sortie: distribution probabiliste, pas prediction certaine."
    ].join("\n"));
    return {
      status: "completed",
      job_id: jobId,
      archive_id: archiveId,
      completed_at_utc: finished.toISOString(),
      completed_at_paris: parisIso(finished)
    };
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : String(error)
    };
  } finally {
    await releaseD1Lock(env, String(lock.name), String(lock.owner));
  }
}

async function notifyDeepJob(env: Env, row: Record<string, unknown>, text: string): Promise<void> {
  if (stringOrNull(row.notify_channel) !== "telegram") {
    return;
  }
  const chatId = stringOrNull(row.notify_target);
  if (chatId) {
    await sendTelegramMessage(env, chatId, text);
  }
}

function getTradingConfig(env: Env): Record<string, unknown> {
  const mode = String(env.TRADING_MODE || "paper").toLowerCase() === "live" ? "live" : "paper";
  const keysConfigured = Boolean(env.BITGET_API_KEY && env.BITGET_API_SECRET && env.BITGET_API_PASSPHRASE);
  return {
    mode,
    symbol: "BTCUSDT",
    default_notional_usdt: clampFloat(parseNumber(env.TRADING_DEFAULT_NOTIONAL_USDT, TRADING_DEFAULT_NOTIONAL_USDT_DEFAULT), 1, 100000),
    max_notional_usdt: clampFloat(parseNumber(env.TRADING_MAX_NOTIONAL_USDT, TRADING_MAX_NOTIONAL_USDT_DEFAULT), 1, 100000),
    min_confidence: clampFloat(parseNumber(env.TRADING_MIN_CONFIDENCE, TRADING_MIN_CONFIDENCE_DEFAULT), 1, 100),
    max_var95: clampFloat(parseNumber(env.TRADING_MAX_VAR95, TRADING_MAX_VAR95_DEFAULT), 0.01, 0.99),
    max_transition: clampFloat(parseNumber(env.TRADING_MAX_TRANSITION, TRADING_MAX_TRANSITION_DEFAULT), 0.01, 0.99),
    buy_prob_up: clampFloat(parseNumber(env.TRADING_BUY_PROB_UP, TRADING_BUY_PROB_UP_DEFAULT), 0.01, 0.99),
    sell_prob_up: clampFloat(parseNumber(env.TRADING_SELL_PROB_UP, TRADING_SELL_PROB_UP_DEFAULT), 0.01, 0.99),
    max_spot_age_seconds: clampInt(parseNumber(env.TRADING_MAX_SPOT_AGE_SECONDS, TRADING_MAX_SPOT_AGE_SECONDS_DEFAULT), 15, 3600),
    bitget_trade_secrets: keysConfigured ? "configured" : "absent",
    live_confirmation: env.TRADING_LIVE_CONFIRMATION ? "configured" : "absent",
    telegram_approval_enabled: parseBoolean(env.TRADING_TELEGRAM_APPROVAL_ENABLED, false),
    live_ready: mode === "live" && keysConfigured
  };
}

function tradingPublicStatus(env: Env): Record<string, unknown> {
  const config = getTradingConfig(env);
  return {
    mode: config.mode,
    paper_trading: "enabled",
    live_trading: config.live_ready ? "guarded_available" : "disabled",
    exchange: "Bitget spot BTCUSDT",
    order_policy: [
      "GPT may request a probabilistic signal, create paper orders and create proposals.",
      "Live orders are disabled unless TRADING_MODE=live and Bitget trade secrets are configured.",
      "Live execution also requires explicit owner approval through Telegram or a confirmation code.",
      "Withdraw/transfer permissions must never be enabled on the Bitget API key."
    ],
    risk_gates: {
      min_confidence: config.min_confidence,
      max_var95: config.max_var95,
      max_transition: config.max_transition,
      buy_prob_up: config.buy_prob_up,
      max_notional_usdt: config.max_notional_usdt,
      max_spot_age_seconds: config.max_spot_age_seconds
    }
  };
}

async function tradingStatus(env: Env): Promise<Record<string, unknown>> {
  return {
    status: "ok",
    service: "quant-btc-model-trading",
    worker_version: WORKER_VERSION,
    schema_version: SCHEMA_VERSION,
    ...tradingPublicStatus(env),
    d1: env.DB ? "configured" : "absent",
    checked_at_utc: new Date().toISOString(),
    checked_at_paris: parisIso(new Date()),
    warning: "Trading outputs are infrastructure actions, not financial advice."
  };
}

function getStrategyConfig(env: Env): Record<string, unknown> {
  return {
    min_ensemble_score: clampFloat(parseNumber(env.STRATEGY_MIN_ENSEMBLE_SCORE, STRATEGY_MIN_ENSEMBLE_SCORE_DEFAULT), 1, 100),
    min_agreement: clampFloat(parseNumber(env.STRATEGY_MIN_AGREEMENT, STRATEGY_MIN_AGREEMENT_DEFAULT), 0.10, 1),
    default_horizon: 30,
    supported_methods: [
      "trend_momentum",
      "mean_reversion",
      "volatility_breakout",
      "regime_filter",
      "risk_adjusted_quant",
      "flow_liquidity_context"
    ],
    ensemble_policy: "Weighted score in [-100,+100]. Positive means buy bias candidate, negative means sell/reduce candidate, neutral means hold.",
    execution_policy: "Strategy Engine only creates inferred candidates. Paper/proposal routes must still pass the trading journal and approval rules."
  };
}

function strategyPublicStatus(env: Env): Record<string, unknown> {
  return {
    status: "enabled",
    version: "strategy_engine_v1",
    ...getStrategyConfig(env),
    data_policy: {
      market_price: "real Bitget when available",
      model_outputs: "inferred",
      strategy_scores: "inferred",
      non_bitget_spot_fallback: "absent"
    }
  };
}

async function strategyStatus(env: Env): Promise<Record<string, unknown>> {
  return {
    status: "ok",
    service: "quant-btc-model-strategies",
    worker_version: WORKER_VERSION,
    schema_version: SCHEMA_VERSION,
    strategies: strategyPublicStatus(env),
    d1: env.DB ? "configured" : "absent",
    checked_at_utc: new Date().toISOString(),
    checked_at_paris: parisIso(new Date()),
    warning: "Strategy scores are probabilistic infrastructure signals, not financial advice."
  };
}

async function buildStrategySummary(env: Env): Promise<Record<string, unknown>> {
  const signal = await buildStrategySignal(env, { asset: "BTC", preset: "deep", horizon: 30 });
  const gates = Array.isArray(signal.gates) ? signal.gates.map((item) => objectValue(item)) : [];
  const blockingGates = gates.filter((gateItem) => gateItem.passed !== true).map((gateItem) => ({
    name: gateItem.name,
    detail: gateItem.detail
  }));
  const provenance = objectValue(signal.provenance);
  const frame = objectValue(signal.selected_frame);
  return {
    status: signal.status,
    action: signal.action || "hold",
    side: signal.side || "hold",
    score: signal.ensemble_score ?? null,
    agreement: signal.agreement ?? null,
    confidence: signal.confidence ?? null,
    blocking_gates: blockingGates,
    key_frame: {
      horizon: frame.horizon || 30,
      prob_up: frame.prob_up ?? null,
      var_95: frame.var_95 ?? null,
      cvar_95: frame.cvar_95 ?? null,
      transition: frame.transition ?? null,
      model_confidence: frame.confidence ?? null
    },
    provenance: {
      archive_id: provenance.archive_id || null,
      run_id: provenance.run_id || null,
      report_date_utc: provenance.report_date_utc || null,
      report_date_paris: provenance.report_date_paris || null,
      realtime_spot: provenance.realtime_spot ?? null,
      realtime_spot_age_seconds: provenance.realtime_spot_age_seconds ?? null,
      realtime_source: provenance.realtime_source || null,
      worker_version: WORKER_VERSION,
      schema_version: SCHEMA_VERSION
    },
    conclusion: strategyConclusion(signal, blockingGates),
    data_status: signal.data_status,
    warning: "Resume compact pour GPT: probabiliste, pas conseil financier."
  };
}

function strategyConclusion(signal: Record<string, unknown>, blockingGates: Record<string, unknown>[]): string {
  const action = String(signal.action || "hold");
  if (signal.status !== "ok") {
    return "Sortie strategie absente ou non exploitable; ne pas fournir de signal.";
  }
  if (action === "hold") {
    return blockingGates.length
      ? "Hold/no-trade: le score ou les gates de risque ne valident pas un biais operationnel robuste."
      : "Hold/no-trade: le moteur ne detecte pas de consensus directionnel suffisant.";
  }
  return action === "buy_candidate"
    ? "Candidat achat probabiliste, a traiter uniquement en paper/proposal et avec gates de risque."
    : "Candidat reduction/vente probabiliste, a traiter uniquement en paper/proposal et avec verification de position.";
}

async function buildStrategySignal(env: Env, input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const asset = normalizeAsset(input.asset);
  const horizon = clampInt(parseNumber(input.horizon, 30), 1, 3650);
  const presetPath = tradingPresetPath(input);
  const preset = ANALYSIS_PRESETS[presetPath];
  let payload = await latestD1RunPayload(env, asset, preset.horizons, 0);
  if (!payload && parseBoolean(input.refresh, false)) {
    await refreshPresetForModelAlerts(env, presetPath, "/strategies/signal", 1, true);
    payload = await latestD1RunPayload(env, asset, preset.horizons, 0);
  }
  if (!payload) {
    return {
      status: "absent",
      action: "hold",
      reason: `No ${preset.name} run available in D1 cache.`,
      data_status: { model_output: "absent", market_data: "absent", strategy_scores: "absent" }
    };
  }

  let realtime = await realtimeStatus(env);
  if (realtime.status !== "ok") {
    await collectRealtimeMarketSnapshot(env, "strategy_signal");
    realtime = await realtimeStatus(env);
  }
  const frame = findFrameForHorizon(payload, horizon) || findFrameForHorizon(payload, 30) || objectValue(Array.isArray(payload.frames) ? payload.frames[0] : {});
  const frames = Array.isArray(payload.frames) ? payload.frames.map((item) => objectValue(item)) : [];
  const spot = numberOrNull(realtime.price) || parsePriceValue(payload.reference_spot) || parsePriceValue(frame.reference_spot);
  const spotAge = numberOrNull(realtime.age_seconds);
  const strategy = evaluateStrategyEnsemble(env, payload, frames, frame, spot, realtime);
  const signalId = `strategy_${new Date().toISOString().replace(/[-:.]/g, "").slice(0, 15)}_${randomRunSuffix()}`;
  const result: Record<string, unknown> = {
    status: "ok",
    signal_id: signalId,
    asset,
    preset: preset.name,
    horizon: numberOrNull(frame.horizon) || horizon,
    action: strategy.action,
    side: strategy.side,
    ensemble_score: strategy.ensemble_score,
    agreement: strategy.agreement,
    confidence: strategy.confidence,
    suggested_notional_usdt: strategy.side === "buy" ? getTradingConfig(env).default_notional_usdt : null,
    strategies: strategy.strategies,
    gates: strategy.gates,
    provenance: {
      archive_id: payload.archive_id,
      run_id: stringOrNull(frame.run_id),
      report_date_utc: payload.report_date_utc,
      report_date_paris: payload.report_date_paris,
      reference_spot: payload.reference_spot,
      reference_spot_timestamp_utc: payload.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: payload.reference_spot_timestamp_paris,
      realtime_spot: spot,
      realtime_spot_age_seconds: spotAge,
      realtime_source: realtime.source,
      worker_version: WORKER_VERSION,
      schema_version: SCHEMA_VERSION
    },
    selected_frame: summarizeStrategyFrame(frame),
    context: {
      realtime,
      liquidity: objectValue(objectValue(payload.context).liquidity),
      options: objectValue(objectValue(payload.context).options),
      etf_flow_trends: objectValue(objectValue(payload.context).etf_flow_trends)
    },
    data_status: {
      price: "real",
      model_outputs: "inferred",
      strategy_scores: "inferred",
      trade_execution: "not_executed"
    },
    warning: "Signal de strategie probabiliste uniquement; pas une prediction certaine ni un conseil financier."
  };
  result.d1_persist = await persistStrategySignal(env, result);
  return result;
}

function evaluateStrategyEnsemble(
  env: Env,
  payload: Record<string, unknown>,
  frames: Record<string, unknown>[],
  selectedFrame: Record<string, unknown>,
  spot: number | null,
  realtime: Record<string, unknown>
): Record<string, unknown> {
  const config = getStrategyConfig(env);
  const trading = getTradingConfig(env);
  const strategies = [
    scoreTrendMomentum(frames),
    scoreMeanReversion(selectedFrame, spot),
    scoreVolatilityBreakout(selectedFrame, spot),
    scoreRegimeFilter(selectedFrame),
    scoreRiskAdjustedQuant(selectedFrame),
    scoreFlowLiquidityContext(payload, realtime)
  ];
  const totalWeight = strategies.reduce((sum, item) => sum + Number(item.weight || 0), 0) || 1;
  const ensembleScore = clampFloat(
    strategies.reduce((sum, item) => sum + Number(item.score || 0) * Number(item.weight || 0), 0) / totalWeight,
    -100,
    100
  );
  const sign = ensembleScore > 0 ? 1 : ensembleScore < 0 ? -1 : 0;
  const active = strategies.filter((item) => Math.abs(Number(item.score || 0)) >= 8);
  const agreeing = sign === 0 ? 0 : active.filter((item) => Math.sign(Number(item.score || 0)) === sign).length;
  const agreement = active.length ? agreeing / active.length : 0;
  const confidenceScore = numberOrNull(objectValue(selectedFrame.confidence).score);
  const risk = objectValue(selectedFrame.risk_metrics);
  const regime = objectValue(selectedFrame.regime_distribution);
  const var95 = normalizeRatio(risk.var_95);
  const transition = normalizeRatio(regime.non_classified_transition);
  const confidence = clampFloat(
    ((confidenceScore ?? 50) * 0.55) + (Math.abs(ensembleScore) * 0.20) + (agreement * 100 * 0.25),
    0,
    100
  );
  const gates = [
    gate("model_payload_present", true, "model output present"),
    gate("spot_real_and_fresh", Boolean(spot && numberOrNull(realtime.age_seconds) !== null && Number(realtime.age_seconds) <= Number(trading.max_spot_age_seconds)), `spot age ${numberOrNull(realtime.age_seconds) ?? "absent"}s <= ${trading.max_spot_age_seconds}s`),
    gate("ensemble_score_ok", Math.abs(ensembleScore) >= Number(config.min_ensemble_score), `score ${ensembleScore.toFixed(2)} >= ${config.min_ensemble_score}`),
    gate("strategy_agreement_ok", agreement >= Number(config.min_agreement), `agreement ${(agreement * 100).toFixed(1)}% >= ${formatPercent(Number(config.min_agreement))}`),
    gate("confidence_ok", confidenceScore !== null && confidenceScore >= Number(trading.min_confidence), `model confidence ${confidenceScore ?? "absent"} >= ${trading.min_confidence}`),
    gate("var95_ok", var95 !== null && var95 <= Number(trading.max_var95), `VaR95 ${formatMaybePercent(var95)} <= ${formatPercent(Number(trading.max_var95))}`),
    gate("transition_ok", transition !== null && transition <= Number(trading.max_transition), `transition ${formatMaybePercent(transition)} <= ${formatPercent(Number(trading.max_transition))}`)
  ];
  const gatesPass = gates.every((item) => item.passed);
  const action = !gatesPass
    ? "hold"
    : ensembleScore > 0
      ? "buy_candidate"
      : ensembleScore < 0
        ? "sell_or_reduce_candidate"
        : "hold";
  return {
    action,
    side: action === "buy_candidate" ? "buy" : action === "sell_or_reduce_candidate" ? "sell" : "hold",
    ensemble_score: Number(ensembleScore.toFixed(2)),
    agreement: Number(agreement.toFixed(4)),
    confidence: Number(confidence.toFixed(2)),
    strategies,
    gates
  };
}

function scoreTrendMomentum(frames: Record<string, unknown>[]): Record<string, unknown> {
  const weights: Record<number, number> = { 1: 0.04, 3: 0.05, 7: 0.09, 14: 0.10, 30: 0.18, 90: 0.22, 180: 0.17, 365: 0.15 };
  let weighted = 0;
  let total = 0;
  const inputs: Record<string, unknown>[] = [];
  for (const frame of frames) {
    const horizon = numberOrNull(frame.horizon);
    const distribution = objectValue(frame.distribution);
    const probUp = normalizeRatio(distribution.prob_up);
    const medianReturn = normalizeRatio(distribution.median_return);
    if (!horizon || probUp === null || medianReturn === null) {
      continue;
    }
    const weight = weights[horizon] || 0.05;
    const score = clampFloat(((probUp - 0.5) * 180) + (medianReturn * 120), -100, 100);
    weighted += score * weight;
    total += weight;
    inputs.push({ horizon, prob_up: probUp, median_return: medianReturn, score: Number(score.toFixed(2)) });
  }
  const score = total ? weighted / total : 0;
  return strategyScore("trend_momentum", score, 0.22, "Momentum multi-horizon base sur P(up) et rendement median.", inputs);
}

function scoreMeanReversion(frame: Record<string, unknown>, spot: number | null): Record<string, unknown> {
  const distribution = objectValue(frame.distribution);
  const p10 = parsePriceValue(distribution.p10_price);
  const median = parsePriceValue(distribution.median_price);
  const p90 = parsePriceValue(distribution.p90_price);
  if (!spot || !p10 || !median || !p90 || p90 <= p10) {
    return strategyScore("mean_reversion", 0, 0.14, "Prix/percentiles indisponibles.", { spot, p10, median, p90 });
  }
  const halfRange = (p90 - p10) / 2;
  const score = clampFloat(((median - spot) / halfRange) * 45, -100, 100);
  return strategyScore("mean_reversion", score, 0.14, "Score positif si le spot est sous le centre de distribution, negatif s'il est riche vs distribution.", { spot, p10, median, p90 });
}

function scoreVolatilityBreakout(frame: Record<string, unknown>, spot: number | null): Record<string, unknown> {
  const distribution = objectValue(frame.distribution);
  const risk = objectValue(frame.risk_metrics);
  const p10 = parsePriceValue(distribution.p10_price);
  const p90 = parsePriceValue(distribution.p90_price);
  const probUp = normalizeRatio(distribution.prob_up);
  const medianReturn = normalizeRatio(distribution.median_return);
  const var95 = normalizeRatio(risk.var_95);
  const width = spot && p10 && p90 ? Math.max(0, (p90 - p10) / spot) : null;
  const score = probUp === null || medianReturn === null
    ? 0
    : ((probUp - 0.5) * 150) + (medianReturn * 110) + ((width || 0) * 12) - ((var95 || 0) * 70);
  return strategyScore("volatility_breakout", score, 0.16, "Cherche une asymetrie positive en penalisation du risque de queue.", { prob_up: probUp, median_return: medianReturn, distribution_width: width, var95 });
}

function scoreRegimeFilter(frame: Record<string, unknown>): Record<string, unknown> {
  const regime = objectValue(frame.regime_distribution);
  const bull = normalizeRatio(regime.bull) || 0;
  const bear = normalizeRatio(regime.bear) || 0;
  const range = normalizeRatio(regime.range) || 0;
  const transition = normalizeRatio(regime.non_classified_transition) || 0;
  const score = (bull - bear) * 120 - transition * 55 - (range > 0.75 ? 8 : 0);
  return strategyScore("regime_filter", score, 0.18, "Filtre bull/bear/range avec penalisation de la zone transition.", { bull, bear, range, transition });
}

function scoreRiskAdjustedQuant(frame: Record<string, unknown>): Record<string, unknown> {
  const distribution = objectValue(frame.distribution);
  const risk = objectValue(frame.risk_metrics);
  const confidence = objectValue(frame.confidence);
  const regime = objectValue(frame.regime_distribution);
  const probUp = normalizeRatio(distribution.prob_up);
  const medianReturn = normalizeRatio(distribution.median_return);
  const var95 = normalizeRatio(risk.var_95);
  const cvar95 = normalizeRatio(risk.cvar_95);
  const confidenceScore = numberOrNull(confidence.score);
  const transition = normalizeRatio(regime.non_classified_transition);
  const score = ((probUp ?? 0.5) - 0.5) * 220
    + ((medianReturn || 0) * 130)
    + (((confidenceScore ?? 50) - 50) * 0.55)
    - ((var95 || 0) * 105)
    - ((cvar95 || 0) * 55)
    - ((transition || 0) * 45);
  return strategyScore("risk_adjusted_quant", score, 0.22, "Score quant ajuste du risque: probabilite, mediane, confiance, VaR/CVaR et transition.", { prob_up: probUp, median_return: medianReturn, var95, cvar95, confidence: confidenceScore, transition });
}

function scoreFlowLiquidityContext(payload: Record<string, unknown>, realtime: Record<string, unknown>): Record<string, unknown> {
  const context = objectValue(payload.context);
  const etf = objectValue(context.etf_flow_trends);
  const liquidity = objectValue(context.liquidity);
  const options = objectValue(context.options);
  let score = 0;
  const latestEtf = numberOrNull(etf.latest_1d_usd_m);
  const flow7d = numberOrNull(etf.flow_7d_usd_m);
  const flow30d = numberOrNull(etf.flow_30d_usd_m);
  const accel7d = numberOrNull(etf.flow_7d_acceleration_usd_m);
  if (latestEtf !== null) score += latestEtf > 0 ? 7 : -7;
  if (flow7d !== null) score += flow7d > 0 ? 8 : -8;
  if (flow30d !== null) score += flow30d > 0 ? 7 : -7;
  if (accel7d !== null) score += accel7d > 0 ? 4 : -5;
  const imbalance = numberOrNull(liquidity.order_book_imbalance_1pct) ?? numberOrNull(realtime.order_book_imbalance_1pct);
  if (imbalance !== null) score += clampFloat(imbalance * 45, -12, 12);
  const putCallVolume = numberOrNull(options.put_call_volume_ratio);
  if (putCallVolume !== null) score += putCallVolume < 0.8 ? 5 : putCallVolume > 1.2 ? -7 : 0;
  const iv = numberOrNull(options.implied_volatility_median);
  if (iv !== null) score += iv > 70 ? -5 : iv < 35 ? -3 : 0;
  return strategyScore("flow_liquidity_context", score, 0.08, "Contexte ETF, carnet Bitget et options Deribit; faible poids car plusieurs donnees sont snapshots.", { latest_etf_flow_usd_m: latestEtf, flow_7d_usd_m: flow7d, flow_30d_usd_m: flow30d, flow_7d_acceleration_usd_m: accel7d, order_book_imbalance_1pct: imbalance, put_call_volume_ratio: putCallVolume, iv_median: iv });
}

function strategyScore(name: string, scoreRaw: number, weight: number, rationale: string, inputs: unknown): Record<string, unknown> {
  const score = clampFloat(scoreRaw, -100, 100);
  return {
    name,
    score: Number(score.toFixed(2)),
    weight,
    direction: score > 8 ? "positive" : score < -8 ? "negative" : "neutral",
    rationale,
    inputs
  };
}

function summarizeStrategyFrame(frame: Record<string, unknown>): Record<string, unknown> {
  const distribution = objectValue(frame.distribution);
  const risk = objectValue(frame.risk_metrics);
  const regime = objectValue(frame.regime_distribution);
  const confidence = objectValue(frame.confidence);
  return {
    horizon: frame.horizon,
    run_id: frame.run_id,
    prob_up: normalizeRatio(distribution.prob_up),
    median_return: normalizeRatio(distribution.median_return),
    p10_price: distribution.p10_price,
    median_price: distribution.median_price,
    p90_price: distribution.p90_price,
    var_95: normalizeRatio(risk.var_95),
    cvar_95: normalizeRatio(risk.cvar_95),
    bull: normalizeRatio(regime.bull),
    bear: normalizeRatio(regime.bear),
    range: normalizeRatio(regime.range),
    transition: normalizeRatio(regime.non_classified_transition),
    confidence: confidence.score
  };
}

async function persistStrategySignal(env: Env, signal: Record<string, unknown>): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", reason: "D1 binding is not configured" };
  }
  try {
    const provenance = objectValue(signal.provenance);
    await env.DB.prepare(`
      INSERT INTO strategy_signals (
        signal_id, asset, preset, horizon, ensemble_score, ensemble_action, agreement,
        confidence, archive_id, run_id, payload_json, created_at_utc
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).bind(
      signal.signal_id,
      signal.asset,
      signal.preset,
      signal.horizon,
      signal.ensemble_score,
      signal.action,
      signal.agreement,
      signal.confidence,
      stringOrNull(provenance.archive_id),
      stringOrNull(provenance.run_id),
      JSON.stringify(signal),
      new Date().toISOString()
    ).run();
    return { status: "stored", target: "cloudflare_d1" };
  } catch (error) {
    return { status: "error", message: error instanceof Error ? error.message : String(error) };
  }
}

async function listStrategySignals(env: Env, limit: number): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", signals: [] };
  }
  try {
    const { results } = await env.DB.prepare(`
      SELECT signal_id, asset, preset, horizon, ensemble_score, ensemble_action,
             agreement, confidence, archive_id, run_id, created_at_utc
      FROM strategy_signals
      ORDER BY created_at_utc DESC
      LIMIT ?
    `).bind(limit).all();
    return {
      status: "ok",
      signals: (results || []).map((item) => {
        const row = objectValue(item);
        return {
          ...row,
          created_at_paris: stringOrNull(row.created_at_utc) ? parisIso(new Date(String(row.created_at_utc))) : null
        };
      })
    };
  } catch (error) {
    return { status: "error", signals: [], message: error instanceof Error ? error.message : String(error) };
  }
}

function strategySignalToTradingSignal(strategy: Record<string, unknown>, env: Env): Record<string, unknown> {
  const provenance = objectValue(strategy.provenance);
  const selected = objectValue(strategy.selected_frame);
  const side = normalizeTradingSide(strategy.side);
  const spot = numberOrNull(provenance.realtime_spot) || numberOrNull(provenance.reference_spot);
  const notional = side === "buy" ? Number(getTradingConfig(env).default_notional_usdt) : null;
  return {
    status: strategy.status,
    asset: strategy.asset,
    symbol: "BTCUSDT",
    signal: side === "buy" ? "strategy_buy_candidate" : side === "sell" ? "strategy_sell_or_reduce_candidate" : "no_trade",
    side,
    order_type: "market",
    suggested_notional_usdt: notional,
    suggested_size_base: side === "buy" && spot && notional ? notional / spot : null,
    gates: strategy.gates,
    provenance: {
      ...provenance,
      strategy_signal_id: strategy.signal_id,
      strategy_ensemble_score: strategy.ensemble_score,
      strategy_agreement: strategy.agreement
    },
    model_frame: {
      horizon: selected.horizon,
      prob_up: selected.prob_up,
      median_return: selected.median_return,
      var95: selected.var_95,
      cvar95: selected.cvar_95,
      confidence: selected.confidence,
      transition: selected.transition
    },
    data_status: {
      price: "real",
      model_outputs: "inferred",
      strategy_scores: "inferred",
      trade_execution: "not_executed"
    },
    warning: "Ordre derive d'un score de strategie probabiliste; pas conseil financier."
  };
}

async function createStrategyPaperOrder(env: Env, input: Record<string, unknown>, createdBy: string): Promise<Record<string, unknown>> {
  const strategy = await buildStrategySignal(env, input);
  const signal = strategySignalToTradingSignal(strategy, env);
  const order = await createTradeOrder(env, input, signal, "paper", "paper_filled", createdBy);
  return { ...order, strategy_signal: strategy };
}

async function proposeStrategyTradeOrder(env: Env, input: Record<string, unknown>, createdBy: string): Promise<Record<string, unknown>> {
  const requestedMode = String(input.mode || "paper").toLowerCase() === "live" ? "live" : "paper";
  const strategy = await buildStrategySignal(env, input);
  const signal = strategySignalToTradingSignal(strategy, env);
  const status = requestedMode === "live" ? "pending_live_approval" : "pending_paper_approval";
  const order = await createTradeOrder(env, input, signal, requestedMode, status, createdBy);
  const chatId = stringOrNull(input.chat_id) || stringOrNull(env.TELEGRAM_CHAT_ID);
  if (chatId && order.status !== "error") {
    await sendTelegramMessage(env, chatId, formatStrategyProposalForTelegram(order, strategy), tradeApprovalKeyboard(String(order.order_id)));
  }
  return {
    ...order,
    strategy_signal: strategy,
    notification: chatId ? "telegram_sent_or_attempted" : "telegram_absent"
  };
}

function formatStrategyProposalForTelegram(order: Record<string, unknown>, strategy: Record<string, unknown>): string {
  return [
    "Quant BTC - Proposition strategie",
    `Ordre: ${order.order_id}`,
    `Mode: ${order.mode}`,
    `Side: ${order.side}`,
    `Score: ${strategy.ensemble_score}`,
    `Accord: ${formatPercent(numberOrNull(strategy.agreement) || 0)}`,
    `Action: ${strategy.action}`,
    `Archive: ${objectValue(strategy.provenance).archive_id || "absente"}`,
    `Run: ${objectValue(strategy.provenance).run_id || "absent"}`,
    "Aucun ordre reel n'est envoye sans approbation.",
    "Sortie probabiliste, pas conseil financier."
  ].join("\n");
}

async function buildTradingSignal(env: Env, input: Record<string, unknown>): Promise<Record<string, unknown>> {
  const config = getTradingConfig(env);
  const asset = normalizeAsset(input.asset);
  const horizon = clampInt(parseNumber(input.horizon, 30), 1, 3650);
  const presetPath = tradingPresetPath(input);
  const preset = ANALYSIS_PRESETS[presetPath];
  let payload = await latestD1RunPayload(env, asset, preset.horizons, 0);
  if (!payload && parseBoolean(input.refresh, false)) {
    await refreshPresetForModelAlerts(env, presetPath, "/trading/signal", 1, true);
    payload = await latestD1RunPayload(env, asset, preset.horizons, 0);
  }
  if (!payload) {
    return {
      status: "absent",
      signal: "no_trade",
      reason: `No ${preset.name} run available in D1 cache.`,
      data_status: { model_output: "absent", market_data: "absent" }
    };
  }

  let realtime = await realtimeStatus(env);
  if (realtime.status !== "ok") {
    await collectRealtimeMarketSnapshot(env, "trading_signal");
    realtime = await realtimeStatus(env);
  }
  const frame = findFrameForHorizon(payload, horizon) || findFrameForHorizon(payload, 30) || objectValue(Array.isArray(payload.frames) ? payload.frames[0] : {});
  const distribution = objectValue(frame.distribution);
  const risk = objectValue(frame.risk_metrics);
  const regime = objectValue(frame.regime_distribution);
  const confidence = objectValue(frame.confidence);
  const probUp = numberOrNull(distribution.prob_up);
  const var95 = numberOrNull(risk.var_95);
  const transition = numberOrNull(regime.non_classified_transition);
  const confidenceScore = numberOrNull(confidence.score);
  const spot = numberOrNull(realtime.price) || parsePriceValue(payload.reference_spot) || parsePriceValue(frame.reference_spot);
  const spotAge = numberOrNull(realtime.age_seconds);
  const gates = [
    gate("model_payload_present", true, "model output present"),
    gate("spot_real_and_fresh", Boolean(spot && spotAge !== null && spotAge <= Number(config.max_spot_age_seconds)), `spot age ${spotAge ?? "absent"}s <= ${config.max_spot_age_seconds}s`),
    gate("confidence_ok", confidenceScore !== null && confidenceScore >= Number(config.min_confidence), `confidence ${confidenceScore ?? "absent"} >= ${config.min_confidence}`),
    gate("var95_ok", var95 !== null && var95 <= Number(config.max_var95), `VaR95 ${formatMaybePercent(var95)} <= ${formatPercent(Number(config.max_var95))}`),
    gate("transition_ok", transition !== null && transition <= Number(config.max_transition), `transition ${formatMaybePercent(transition)} <= ${formatPercent(Number(config.max_transition))}`),
    gate("prob_up_buy_ok", probUp !== null && probUp >= Number(config.buy_prob_up), `P(up) ${formatMaybePercent(probUp)} >= ${formatPercent(Number(config.buy_prob_up))}`)
  ];
  const buyAllowed = gates.every((item) => item.passed);
  const sellCandidate = probUp !== null && probUp <= Number(config.sell_prob_up) && confidenceScore !== null && confidenceScore >= Number(config.min_confidence);
  const side = buyAllowed ? "buy" : sellCandidate ? "sell" : "hold";
  const signal = buyAllowed ? "paper_buy_candidate" : sellCandidate ? "reduce_candidate_no_position_check" : "no_trade";
  const sizeUsdt = Math.min(Number(config.default_notional_usdt), Number(config.max_notional_usdt));
  const sizeBase = side === "buy" && spot ? sizeUsdt / spot : null;
  const runId = stringOrNull(frame.run_id);
  return {
    status: "ok",
    asset,
    symbol: config.symbol,
    signal,
    side,
    order_type: "market",
    suggested_notional_usdt: side === "buy" ? sizeUsdt : null,
    suggested_size_base: sizeBase,
    gates,
    decision_policy: "All buy gates must pass. Otherwise no trade is recommended by the execution engine.",
    provenance: {
      archive_id: payload.archive_id,
      run_id: runId,
      report_date_utc: payload.report_date_utc,
      report_date_paris: payload.report_date_paris,
      reference_spot: payload.reference_spot,
      realtime_spot: spot,
      realtime_spot_age_seconds: spotAge,
      realtime_source: realtime.source,
      worker_version: WORKER_VERSION,
      schema_version: SCHEMA_VERSION
    },
    model_frame: {
      horizon: frame.horizon,
      prob_up: probUp,
      median_return: distribution.median_return,
      p10_return: distribution.p10_return,
      p90_return: distribution.p90_return,
      var95,
      cvar95: risk.cvar_95,
      confidence: confidenceScore,
      transition
    },
    data_status: {
      price: "real",
      model_outputs: "inferred",
      trade_execution: "not_executed"
    },
    warning: "Signal probabiliste uniquement; pas une prediction certaine ni un conseil financier."
  };
}

function gate(name: string, passed: boolean, detail: string): Record<string, unknown> {
  return { name, passed, detail };
}

function tradingPresetPath(input: Record<string, unknown>): string {
  const preset = String(input.preset || "deep").toLowerCase();
  if (preset === "quick") return "/quick";
  if (preset === "tactical") return "/tactical";
  return "/deep";
}

async function createPaperTradeOrder(env: Env, input: Record<string, unknown>, createdBy: string): Promise<Record<string, unknown>> {
  const signal = await buildTradingSignal(env, input);
  return await createTradeOrder(env, input, signal, "paper", "paper_filled", createdBy);
}

async function proposeTradeOrder(env: Env, input: Record<string, unknown>, createdBy: string): Promise<Record<string, unknown>> {
  const requestedMode = String(input.mode || "paper").toLowerCase() === "live" ? "live" : "paper";
  const signal = await buildTradingSignal(env, input);
  const status = requestedMode === "live" ? "pending_live_approval" : "pending_paper_approval";
  const order = await createTradeOrder(env, input, signal, requestedMode, status, createdBy);
  const chatId = stringOrNull(input.chat_id) || stringOrNull(env.TELEGRAM_CHAT_ID);
  if (chatId && order.status !== "error") {
    await sendTelegramMessage(env, chatId, formatTradeProposalForTelegram(order), tradeApprovalKeyboard(String(order.order_id)));
  }
  return {
    ...order,
    notification: chatId ? "telegram_sent_or_attempted" : "telegram_absent",
    approval_policy: requestedMode === "live"
      ? "A live order is not sent until /trading/approve is called with confirmation or Telegram owner approval."
      : "Paper proposal can be approved without live exchange execution."
  };
}

async function createTradeOrder(
  env: Env,
  input: Record<string, unknown>,
  signal: Record<string, unknown>,
  mode: string,
  status: string,
  createdBy: string
): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "error", message: "D1 is required for the trading journal." };
  }
  if (signal.status !== "ok") {
    return { status: "error", message: "Trading signal is absent; no order created.", signal };
  }
  const side = normalizeTradingSide(input.side || signal.side);
  const force = parseBoolean(input.force, false);
  if (side === "hold" || (!force && signal.signal === "no_trade")) {
    return {
      status: "blocked",
      message: "No trade created because risk gates did not pass. Use force=true only for paper/manual testing.",
      signal
    };
  }
  const config = getTradingConfig(env);
  const now = new Date();
  const orderId = `trade_${now.toISOString().replace(/[-:.]/g, "").slice(0, 15)}_${randomRunSuffix()}`;
  const clientOid = `qbtc_${now.toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}_${randomRunSuffix()}`.slice(0, 32);
  const spot = numberOrNull(objectValue(signal.provenance).realtime_spot);
  const maxNotional = Number(config.max_notional_usdt);
  const requestedNotional = numberOrNull(input.size_usdt) || numberOrNull(signal.suggested_notional_usdt) || Number(config.default_notional_usdt);
  const sizeUsdt = side === "buy" ? Math.min(Math.max(requestedNotional, 1), maxNotional) : null;
  const requestedBase = numberOrNull(input.size_base) || numberOrNull(signal.suggested_size_base);
  const sizeBase = side === "sell" ? requestedBase : (side === "buy" && spot && sizeUsdt ? sizeUsdt / spot : requestedBase);
  const orderType = normalizeOrderType(input.order_type);
  const limitPrice = orderType === "limit" ? (numberOrNull(input.limit_price) || spot) : null;
  const filledPrice = status === "paper_filled" ? spot : null;
  const proposal = {
    signal,
    source: "quant_btc_trading_engine",
    policy: tradingPublicStatus(env),
    input: safeTradingInput(input)
  };
  await env.DB.prepare(`
    INSERT INTO trade_orders (
      order_id, asset, symbol, mode, status, side, order_type, size_usdt, size_base,
      limit_price, filled_price, client_oid, archive_id, run_id, proposal_json,
      created_by, created_at_utc, updated_at_utc, executed_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    orderId,
    normalizeAsset(input.asset),
    String(config.symbol),
    mode,
    status,
    side,
    orderType,
    sizeUsdt,
    sizeBase,
    limitPrice,
    filledPrice,
    clientOid,
    stringOrNull(objectValue(signal.provenance).archive_id),
    stringOrNull(objectValue(signal.provenance).run_id),
    JSON.stringify(proposal),
    createdBy,
    now.toISOString(),
    now.toISOString(),
    status === "paper_filled" ? now.toISOString() : null
  ).run();
  await persistTradeEvent(env, orderId, "order_created", status, `${mode} ${side} ${orderType} order ${status}`, proposal);
  return {
    status,
    order_id: orderId,
    mode,
    asset: normalizeAsset(input.asset),
    symbol: config.symbol,
    side,
    order_type: orderType,
    size_usdt: sizeUsdt,
    size_base: sizeBase,
    limit_price: limitPrice,
    filled_price: filledPrice,
    client_oid: clientOid,
    provenance: objectValue(signal.provenance),
    risk_gates: signal.gates,
    data_status: {
      price: "real",
      model_outputs: "inferred",
      order: mode === "paper" ? "mock" : "pending"
    },
    warning: mode === "paper"
      ? "Paper order only; no exchange order was sent."
      : "Live proposal only; no exchange order was sent until explicit approval."
  };
}

async function approveTradeOrder(env: Env, input: Record<string, unknown>, source: string): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "error", message: "D1 is required for trading approval." };
  }
  const orderId = stringOrNull(input.order_id) || stringOrNull(input.id);
  if (!orderId) {
    return { status: "error", message: "order_id is required." };
  }
  const row = objectValue(await env.DB.prepare("SELECT * FROM trade_orders WHERE order_id = ?").bind(orderId).first());
  if (!stringOrNull(row.order_id)) {
    return { status: "absent", message: "Trade order not found.", order_id: orderId };
  }
  const mode = stringOrNull(row.mode) || "paper";
  const now = new Date();
  if (mode !== "live") {
    const realtime = await realtimeStatus(env);
    const fillPrice = numberOrNull(row.filled_price) || numberOrNull(row.limit_price) || numberOrNull(realtime.price);
    await env.DB.prepare(`
      UPDATE trade_orders SET status = ?, filled_price = ?, approved_by = ?, approved_at_utc = ?, executed_at_utc = ?, updated_at_utc = ? WHERE order_id = ?
    `).bind("paper_approved_filled", fillPrice, source, now.toISOString(), now.toISOString(), now.toISOString(), orderId).run();
    await persistTradeEvent(env, orderId, "paper_approved", "paper_approved_filled", "Paper order approved and marked filled.", { source });
    return { status: "paper_approved_filled", order_id: orderId, message: "Paper order approved; no exchange order was sent." };
  }

  const liveAuth = canApproveLiveTrade(env, input, source);
  if (!liveAuth.allowed) {
    return { status: "blocked", order_id: orderId, reason: liveAuth.reason, message: "Live order was not sent." };
  }
  const execution = await placeBitgetSpotOrder(env, row);
  const finalStatus = execution.status === "sent" ? "live_sent" : "live_error";
  await env.DB.prepare(`
    UPDATE trade_orders SET status = ?, exchange_order_id = ?, execution_json = ?, error = ?,
      approved_by = ?, approved_at_utc = ?, executed_at_utc = ?, updated_at_utc = ?
    WHERE order_id = ?
  `).bind(
    finalStatus,
    stringOrNull(objectValue(execution.exchange_response).orderId) || stringOrNull(objectValue(objectValue(execution.exchange_response).data).orderId),
    JSON.stringify(execution),
    finalStatus === "live_error" ? stringOrNull(execution.message) || stringOrNull(execution.error) : null,
    source,
    now.toISOString(),
    now.toISOString(),
    now.toISOString(),
    orderId
  ).run();
  await persistTradeEvent(env, orderId, "live_execution", finalStatus, finalStatus === "live_sent" ? "Live Bitget order sent." : "Live Bitget order failed.", execution);
  return {
    status: finalStatus,
    order_id: orderId,
    execution,
    warning: "Live exchange response returned by Bitget; verify directly in Bitget before relying on position state."
  };
}

function canApproveLiveTrade(env: Env, input: Record<string, unknown>, source: string): Record<string, unknown> {
  const config = getTradingConfig(env);
  if (config.live_ready !== true) {
    return { allowed: false, reason: "TRADING_MODE is not live or Bitget trade secrets are absent." };
  }
  if (source === "telegram_owner" && config.telegram_approval_enabled === true) {
    return { allowed: true, reason: "telegram_owner_approval" };
  }
  const expected = stringOrNull(env.TRADING_LIVE_CONFIRMATION);
  const provided = stringOrNull(input.confirmation) || stringOrNull(input.approval_code);
  if (expected && provided === expected) {
    return { allowed: true, reason: "confirmation_code_valid" };
  }
  return { allowed: false, reason: "Live approval requires Telegram owner approval or TRADING_LIVE_CONFIRMATION." };
}

async function placeBitgetSpotOrder(env: Env, order: Record<string, unknown>): Promise<Record<string, unknown>> {
  const apiKey = stringOrNull(env.BITGET_API_KEY);
  const apiSecret = stringOrNull(env.BITGET_API_SECRET);
  const passphrase = stringOrNull(env.BITGET_API_PASSPHRASE);
  if (!apiKey || !apiSecret || !passphrase) {
    return { status: "error", error: "bitget_trade_secrets_absent" };
  }
  const side = normalizeTradingSide(order.side);
  const orderType = normalizeOrderType(order.order_type);
  const sizeUsdt = numberOrNull(order.size_usdt);
  const sizeBase = numberOrNull(order.size_base);
  if (side === "sell" && !sizeBase) {
    return { status: "error", error: "sell_size_base_absent", message: "Spot market sell requires base coin size." };
  }
  const size = side === "buy" && orderType === "market" ? sizeUsdt : sizeBase;
  if (!size || size <= 0) {
    return { status: "error", error: "order_size_absent" };
  }
  const body: Record<string, unknown> = {
    symbol: stringOrNull(order.symbol) || "BTCUSDT",
    side,
    orderType,
    size: formatOrderNumber(size),
    clientOid: stringOrNull(order.client_oid) || `qbtc_${randomRunSuffix()}`
  };
  if (orderType === "limit") {
    const limitPrice = numberOrNull(order.limit_price);
    if (!limitPrice) {
      return { status: "error", error: "limit_price_absent" };
    }
    body.force = "gtc";
    body.price = formatOrderNumber(limitPrice);
  }
  const timestamp = String(Date.now());
  const bodyText = JSON.stringify(body);
  const signature = await bitgetSign(apiSecret, timestamp, "POST", BITGET_SPOT_PLACE_ORDER_PATH, bodyText);
  const response = await fetch(`https://api.bitget.com${BITGET_SPOT_PLACE_ORDER_PATH}`, {
    method: "POST",
    headers: {
      "ACCESS-KEY": apiKey,
      "ACCESS-SIGN": signature,
      "ACCESS-PASSPHRASE": passphrase,
      "ACCESS-TIMESTAMP": timestamp,
      "locale": "en-US",
      "content-type": "application/json"
    },
    body: bodyText,
    cf: { cacheTtl: 0, cacheEverything: false }
  });
  const text = await response.text();
  let parsed: unknown = {};
  try {
    parsed = text ? JSON.parse(text) : {};
  } catch {
    parsed = { raw_response: text.slice(0, 1000) };
  }
  const payload = objectValue(parsed);
  const ok = response.ok && (payload.code === "00000" || payload.msg === "success");
  return {
    status: ok ? "sent" : "error",
    http_status: response.status,
    exchange: "bitget",
    endpoint: BITGET_SPOT_PLACE_ORDER_PATH,
    request: { ...body, size: body.size },
    exchange_response: payload,
    message: ok ? "Bitget spot order accepted." : stringOrNull(payload.msg) || `HTTP ${response.status}`
  };
}

async function bitgetSign(secret: string, timestamp: string, method: string, requestPath: string, body: string): Promise<string> {
  const payload = `${timestamp}${method.toUpperCase()}${requestPath}${body}`;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(payload));
  return arrayBufferToBase64(signature);
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary);
}

async function listTradeOrders(env: Env, limit: number): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", orders: [] };
  }
  const { results } = await env.DB.prepare(`
    SELECT order_id, asset, symbol, mode, status, side, order_type, size_usdt, size_base,
           limit_price, filled_price, exchange_order_id, client_oid, archive_id, run_id,
           error, created_by, approved_by, created_at_utc, updated_at_utc, approved_at_utc, executed_at_utc
    FROM trade_orders
    ORDER BY created_at_utc DESC
    LIMIT ?
  `).bind(limit).all();
  return {
    status: "ok",
    orders: (results || []).map((item) => {
      const row = objectValue(item);
      return {
        ...row,
        created_at_paris: stringOrNull(row.created_at_utc) ? parisIso(new Date(String(row.created_at_utc))) : null,
        updated_at_paris: stringOrNull(row.updated_at_utc) ? parisIso(new Date(String(row.updated_at_utc))) : null
      };
    })
  };
}

async function paperTradingPnl(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 is required for paper PnL." };
  }
  const realtime = await freshRealtimeForPaper(env);
  const markPrice = numberOrNull(realtime.price);
  const orders = await paperFilledOrders(env, 100);
  const rows = orders.map((order) => paperPnlForOrder(order, markPrice));
  const snapshots = markPrice ? await upsertDuePaperPnlSnapshots(env, orders, markPrice) : { status: "skipped", reason: "mark_price_absent" };
  const total = rows.reduce((sum, row) => sum + (numberOrNull(row.pnl_usdt) || 0), 0);
  return {
    status: "ok",
    mark_price: markPrice,
    mark_source: realtime.source || "absent",
    mark_age_seconds: realtime.age_seconds ?? null,
    mark_timestamp_utc: realtime.observed_at_utc || null,
    mark_timestamp_paris: realtime.observed_at_paris || null,
    total_open_pnl_usdt: Number(total.toFixed(4)),
    orders: rows,
    checkpoints: snapshots,
    data_status: {
      mark_price: markPrice ? "real" : "absent",
      paper_orders: "mock",
      pnl: "inferred"
    },
    warning: "Paper PnL is hypothetical and not an exchange/account statement."
  };
}

async function paperPortfolioState(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 is required for paper portfolio state." };
  }
  const realtime = await freshRealtimeForPaper(env);
  const markPrice = numberOrNull(realtime.price);
  const orders = await paperFilledOrders(env, 500);
  let buyBase = 0;
  let buyCost = 0;
  let sellBase = 0;
  let sellProceeds = 0;
  for (const order of orders) {
    const side = normalizeTradingSide(order.side);
    const base = numberOrNull(order.size_base) || 0;
    const fill = numberOrNull(order.filled_price) || 0;
    if (side === "buy") {
      buyBase += base;
      buyCost += base * fill;
    } else if (side === "sell") {
      sellBase += base;
      sellProceeds += base * fill;
    }
  }
  const netBase = buyBase - sellBase;
  const avgEntry = buyBase > 0 ? buyCost / buyBase : null;
  const exposure = markPrice !== null ? netBase * markPrice : null;
  const unrealized = markPrice !== null && avgEntry !== null ? netBase * (markPrice - avgEntry) : null;
  const latestDeep = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0);
  const frame30 = findFrameForHorizon(latestDeep, 30);
  const distribution = objectValue(frame30?.distribution);
  const riskStop = avgEntry !== null ? avgEntry * (1 - Number(getTradingConfig(env).max_var95)) : null;
  const p10 = parsePriceValue(distribution.p10_price);
  return {
    status: "ok",
    asset: "BTC",
    mode: "paper",
    net_position_btc: Number(netBase.toFixed(10)),
    average_entry_price: avgEntry,
    mark_price: markPrice,
    exposure_usdt: exposure !== null ? Number(exposure.toFixed(4)) : null,
    unrealized_pnl_usdt: unrealized !== null ? Number(unrealized.toFixed(4)) : null,
    unrealized_pnl_pct_on_buy_cost: buyCost > 0 && unrealized !== null ? unrealized / buyCost : null,
    buy_cost_usdt: Number(buyCost.toFixed(4)),
    sell_proceeds_usdt: Number(sellProceeds.toFixed(4)),
    open_orders_count: orders.length,
    invalidation_proxy: {
      method: "lower_of_risk_stop_proxy_and_30d_p10_when_available",
      risk_stop_proxy: riskStop,
      p10_30d_price: p10,
      level: riskStop !== null && p10 !== null ? Math.min(riskStop, p10) : riskStop ?? p10,
      warning: "Proxy analytique seulement; pas un stop order ni conseil financier."
    },
    data_status: {
      mark_price: markPrice ? "real" : "absent",
      portfolio: "mock_paper",
      pnl: "inferred"
    },
    checked_at_utc: new Date().toISOString(),
    checked_at_paris: parisIso(new Date())
  };
}

async function cleanupPaperTestOrders(env: Env, input: Record<string, unknown>): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 is required for cleanup." };
  }
  if (stringOrNull(input.confirm) !== "cleanup_paper_tests") {
    return {
      status: "blocked",
      message: "Cleanup requires confirm=cleanup_paper_tests. This endpoint is not exposed in GPT Actions."
    };
  }
  const testOrderIds = [
    "trade_20260507T003800_f621df45",
    "trade_20260507T003800_1ffddf74"
  ];
  const placeholders = testOrderIds.map(() => "?").join(",");
  const events = await env.DB.prepare(`DELETE FROM trade_events WHERE order_id IN (${placeholders})`).bind(...testOrderIds).run();
  const orders = await env.DB.prepare(`DELETE FROM trade_orders WHERE mode = 'paper' AND order_id IN (${placeholders})`).bind(...testOrderIds).run();
  return {
    status: "cleaned",
    deleted_order_ids: testOrderIds,
    trade_events_deleted: objectValue(events.meta).changes ?? null,
    trade_orders_deleted: objectValue(orders.meta).changes ?? null,
    cleaned_at_utc: new Date().toISOString(),
    cleaned_at_paris: parisIso(new Date())
  };
}

async function freshRealtimeForPaper(env: Env): Promise<Record<string, unknown>> {
  let realtime = await realtimeStatus(env);
  const age = numberOrNull(realtime.age_seconds);
  if (realtime.status !== "ok" || age === null || age > Number(getTradingConfig(env).max_spot_age_seconds)) {
    await collectRealtimeMarketSnapshot(env, "paper_pnl");
    realtime = await realtimeStatus(env);
  }
  return realtime;
}

async function paperFilledOrders(env: Env, limit: number): Promise<Record<string, unknown>[]> {
  if (!env.DB) {
    return [];
  }
  const { results } = await env.DB.prepare(`
    SELECT order_id, asset, symbol, status, side, order_type, size_usdt, size_base,
           limit_price, filled_price, archive_id, run_id, created_by, created_at_utc, executed_at_utc
    FROM trade_orders
    WHERE mode = 'paper' AND status LIKE '%filled%'
    ORDER BY created_at_utc DESC
    LIMIT ?
  `).bind(limit).all();
  return (results || []).map((item) => objectValue(item));
}

function paperPnlForOrder(order: Record<string, unknown>, markPrice: number | null): Record<string, unknown> {
  const side = normalizeTradingSide(order.side);
  const entry = numberOrNull(order.filled_price) || numberOrNull(order.limit_price);
  const base = numberOrNull(order.size_base);
  const notional = numberOrNull(order.size_usdt);
  const direction = side === "sell" ? -1 : 1;
  const pnl = markPrice !== null && entry !== null && base !== null ? (markPrice - entry) * base * direction : null;
  const pnlPct = markPrice !== null && entry !== null && entry > 0 ? ((markPrice / entry) - 1) * direction : null;
  const executedAt = stringOrNull(order.executed_at_utc) || stringOrNull(order.created_at_utc);
  const ageSeconds = executedAt ? Math.max(0, Math.round((Date.now() - new Date(executedAt).getTime()) / 1000)) : null;
  return {
    order_id: order.order_id,
    side,
    status: order.status,
    entry_price: entry,
    mark_price: markPrice,
    size_base: base,
    size_usdt: notional,
    pnl_usdt: pnl !== null ? Number(pnl.toFixed(4)) : null,
    pnl_pct: pnlPct,
    age_seconds: ageSeconds,
    checkpoints: [1, 3, 7].map((days) => ({
      horizon_days: days,
      due: ageSeconds !== null && ageSeconds >= days * 86400
    })),
    created_at_utc: order.created_at_utc,
    executed_at_utc: order.executed_at_utc
  };
}

async function upsertDuePaperPnlSnapshots(env: Env, orders: Record<string, unknown>[], markPrice: number): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent" };
  }
  let inserted = 0;
  for (const order of orders) {
    const executedAt = stringOrNull(order.executed_at_utc) || stringOrNull(order.created_at_utc);
    if (!executedAt) {
      continue;
    }
    const ageDays = (Date.now() - new Date(executedAt).getTime()) / 86400000;
    for (const horizon of [1, 3, 7]) {
      if (ageDays < horizon) {
        continue;
      }
      const pnl = paperPnlForOrder(order, markPrice);
      const result = await env.DB.prepare(`
        INSERT OR IGNORE INTO paper_pnl_snapshots (
          order_id, horizon_days, asset, side, entry_price, mark_price, size_base,
          size_usdt, pnl_usdt, pnl_pct, created_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).bind(
        order.order_id,
        horizon,
        order.asset || "BTC",
        pnl.side,
        pnl.entry_price,
        markPrice,
        pnl.size_base,
        pnl.size_usdt,
        pnl.pnl_usdt,
        pnl.pnl_pct,
        new Date().toISOString()
      ).run();
      inserted += Number(objectValue(result.meta).changes || 0);
    }
  }
  const { results } = await env.DB.prepare(`
    SELECT order_id, horizon_days, asset, side, entry_price, mark_price, size_base,
           size_usdt, pnl_usdt, pnl_pct, created_at_utc
    FROM paper_pnl_snapshots
    ORDER BY created_at_utc DESC
    LIMIT 50
  `).all();
  return {
    status: "ok",
    inserted,
    horizons_days: [1, 3, 7],
    snapshots: (results || []).map((item) => objectValue(item))
  };
}

async function persistTradeEvent(env: Env, orderId: string, kind: string, status: string, message: string, payload: unknown): Promise<void> {
  if (!env.DB) {
    return;
  }
  await env.DB.prepare(`
    INSERT INTO trade_events (order_id, kind, status, message, payload_json, created_at_utc)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(orderId, kind, status, message, JSON.stringify(payload), new Date().toISOString()).run();
}

function formatTradeProposalForTelegram(order: Record<string, unknown>): string {
  const provenance = objectValue(order.provenance);
  return [
    "Quant BTC - Proposition trading",
    `Ordre: ${order.order_id}`,
    `Mode: ${order.mode}`,
    `Side: ${order.side}`,
    `Notional: ${order.size_usdt ? `${order.size_usdt} USDT` : "absent"}`,
    `Base: ${order.size_base || "absent"} BTC`,
    `Archive: ${provenance.archive_id || "absente"}`,
    `Run: ${provenance.run_id || "absent"}`,
    "Aucun ordre reel n'est envoye sans approbation.",
    "Sortie probabiliste, pas conseil financier."
  ].join("\n");
}

function tradeApprovalKeyboard(orderId: string): Record<string, unknown> {
  return {
    inline_keyboard: [
      [
        { text: "Approuver", callback_data: `/trade_approve ${orderId}` },
        { text: "Refuser", callback_data: `/trade_cancel ${orderId}` }
      ],
      [
        { text: "Signal", callback_data: "/trade_signal" },
        { text: "Ordres", callback_data: "/trade_orders" }
      ]
    ]
  };
}

function normalizeTradingSide(value: unknown): string {
  const side = String(value || "hold").toLowerCase();
  if (side === "buy" || side === "long") return "buy";
  if (side === "sell" || side === "reduce") return "sell";
  return "hold";
}

function normalizeOrderType(value: unknown): string {
  return String(value || "market").toLowerCase() === "limit" ? "limit" : "market";
}

function formatOrderNumber(value: number): string {
  return value >= 1 ? value.toFixed(2).replace(/\.?0+$/, "") : value.toFixed(8).replace(/\.?0+$/, "");
}

function safeTradingInput(input: Record<string, unknown>): Record<string, unknown> {
  return {
    asset: input.asset,
    preset: input.preset,
    horizon: input.horizon,
    mode: input.mode,
    side: input.side,
    order_type: input.order_type,
    size_usdt: input.size_usdt,
    size_base: input.size_base,
    limit_price: input.limit_price,
    force: input.force
  };
}

async function cancelTradeOrder(env: Env, orderIdRaw: unknown, cancelledBy: string): Promise<Record<string, unknown>> {
  const orderId = stringOrNull(orderIdRaw);
  if (!env.DB || !orderId) {
    return { status: "error", message: "order_id is required." };
  }
  const row = objectValue(await env.DB.prepare("SELECT status FROM trade_orders WHERE order_id = ?").bind(orderId).first());
  if (!stringOrNull(row.status)) {
    return { status: "absent", message: "Trade order not found.", order_id: orderId };
  }
  if (String(row.status).includes("sent") || String(row.status).includes("filled")) {
    return { status: "blocked", message: "Already executed paper/live order cannot be cancelled here.", order_id: orderId };
  }
  const now = new Date();
  await env.DB.prepare("UPDATE trade_orders SET status = ?, approved_by = ?, updated_at_utc = ? WHERE order_id = ?")
    .bind("cancelled", cancelledBy, now.toISOString(), orderId).run();
  await persistTradeEvent(env, orderId, "order_cancelled", "cancelled", "Trade proposal cancelled.", { cancelled_by: cancelledBy });
  return { status: "cancelled", order_id: orderId };
}

function formatTradingSignalForTelegram(signal: Record<string, unknown>): string {
  const provenance = objectValue(signal.provenance);
  const frame = objectValue(signal.model_frame);
  return [
    "Quant BTC - Signal trading",
    `Statut: ${signal.status}`,
    `Signal: ${signal.signal || "absent"}`,
    `Side: ${signal.side || "hold"}`,
    `P(up): ${formatMaybePercent(numberOrNull(frame.prob_up))}`,
    `VaR95: ${formatMaybePercent(numberOrNull(frame.var95))}`,
    `Confiance: ${frame.confidence ?? "absente"}/100`,
    `Transition: ${formatMaybePercent(numberOrNull(frame.transition))}`,
    `Archive: ${provenance.archive_id || "absente"}`,
    `Run: ${provenance.run_id || "absent"}`,
    "Aucun ordre reel n'est envoye par ce signal."
  ].join("\n");
}

function formatTradeOrderForTelegram(order: Record<string, unknown>): string {
  return [
    "Quant BTC - Ordre",
    `Statut: ${order.status}`,
    `Order ID: ${order.order_id || "absent"}`,
    `Mode: ${order.mode || "absent"}`,
    `Side: ${order.side || "absent"}`,
    `Type: ${order.order_type || "absent"}`,
    `Notional: ${order.size_usdt || "absent"} USDT`,
    `Base: ${order.size_base || "absent"} BTC`,
    `Message: ${order.message || order.warning || "absent"}`
  ].join("\n");
}

function formatTradeOrdersForTelegram(payload: Record<string, unknown>): string {
  const orders = Array.isArray(payload.orders) ? payload.orders.map((item) => objectValue(item)).slice(0, 5) : [];
  if (orders.length === 0) {
    return "Quant BTC - Ordres\nAucun ordre journalise.";
  }
  return [
    "Quant BTC - Derniers ordres",
    ...orders.map((order) => `${order.order_id} | ${order.mode} | ${order.status} | ${order.side} | ${order.size_usdt || "?"} USDT`)
  ].join("\n");
}

function formatStrategySignalForTelegram(signal: Record<string, unknown>): string {
  const provenance = objectValue(signal.provenance);
  const frame = objectValue(signal.selected_frame);
  return [
    "Quant BTC - Strategie",
    `Statut: ${signal.status}`,
    `Action: ${signal.action || "hold"}`,
    `Side: ${signal.side || "hold"}`,
    `Score: ${signal.ensemble_score ?? "absent"}`,
    `Accord: ${formatMaybePercent(signal.agreement)}`,
    `Confiance strategie: ${signal.confidence ?? "absente"}/100`,
    `Horizon: ${frame.horizon || signal.horizon || "absent"}j`,
    `P(up): ${formatMaybePercent(frame.prob_up)}`,
    `VaR95: ${formatMaybePercent(frame.var_95)}`,
    `Archive: ${provenance.archive_id || "absente"}`,
    `Run: ${provenance.run_id || "absent"}`,
    "Scores inferred; aucun ordre reel n'est envoye par ce signal."
  ].join("\n");
}

function formatStrategySignalsForTelegram(payload: Record<string, unknown>): string {
  const signals = Array.isArray(payload.signals) ? payload.signals.map((item) => objectValue(item)).slice(0, 5) : [];
  if (signals.length === 0) {
    return "Quant BTC - Strategies\nAucun score journalise.";
  }
  return [
    "Quant BTC - Derniers scores strategie",
    ...signals.map((signal) => `${signal.signal_id} | ${signal.preset} ${signal.horizon}j | ${signal.ensemble_action} | score ${signal.ensemble_score}`)
  ].join("\n");
}

async function createCustomAlertRule(env: Env, input: Record<string, unknown>): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 binding is required for alert rules." };
  }
  const metric = normalizeAlertMetric(input.metric);
  const operator = normalizeAlertOperator(input.operator);
  const threshold = numberOrNull(input.threshold);
  if (!metric || !operator || threshold === null) {
    return {
      status: "error",
      message: "metric, operator and numeric threshold are required.",
      allowed_metrics: ["btc_price", "var95", "confidence", "transition", "prob_up"],
      allowed_operators: [">", ">=", "<", "<="]
    };
  }
  const now = new Date();
  const ruleId = `rule_${now.toISOString().replace(/[-:.]/g, "").slice(0, 15)}_${randomRunSuffix()}`;
  const chatId = stringOrNull(input.chat_id) || stringOrNull(env.TELEGRAM_CHAT_ID);
  const horizon = metric === "btc_price" ? null : clampInt(parseNumber(input.horizon, 365), 1, 3650);
  const cooldown = clampInt(parseNumber(input.cooldown_seconds, 1800), 60, 24 * 60 * 60);
  await env.DB.prepare(`
    INSERT INTO user_alert_rules (
      rule_id, client_id, chat_id, asset, metric, operator, threshold, horizon,
      status, cooldown_seconds, created_at_utc, updated_at_utc
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    ruleId,
    stringOrNull(input.client_id),
    chatId,
    normalizeAsset(input.asset),
    metric,
    operator,
    threshold,
    horizon,
    "active",
    cooldown,
    now.toISOString(),
    now.toISOString()
  ).run();
  return {
    status: "created",
    rule_id: ruleId,
    metric,
    operator,
    threshold,
    horizon,
    chat_id: chatId,
    cooldown_seconds: cooldown,
    created_at_utc: now.toISOString(),
    created_at_paris: parisIso(now)
  };
}

async function listCustomAlertRules(env: Env, chatId?: string): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", rules: [] };
  }
  const query = chatId
    ? env.DB.prepare(`
        SELECT rule_id, client_id, chat_id, asset, metric, operator, threshold, horizon,
               status, cooldown_seconds, last_triggered_at_utc, created_at_utc, updated_at_utc
        FROM user_alert_rules
        WHERE chat_id = ?
        ORDER BY created_at_utc DESC
        LIMIT 50
      `).bind(chatId)
    : env.DB.prepare(`
        SELECT rule_id, client_id, chat_id, asset, metric, operator, threshold, horizon,
               status, cooldown_seconds, last_triggered_at_utc, created_at_utc, updated_at_utc
        FROM user_alert_rules
        ORDER BY created_at_utc DESC
        LIMIT 50
      `);
  const { results } = await query.all();
  return {
    status: "ok",
    rules: (results || []).map((item) => objectValue(item))
  };
}

async function evaluateCustomAlertRules(env: Env): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent" };
  }
  const lock = await acquireD1Lock(env, "custom-alert-rules", 120, { worker_version: WORKER_VERSION });
  if (!lock.acquired) {
    return { status: "skipped", reason: "lock_active", lock };
  }
  try {
    const { results } = await env.DB.prepare(`
      SELECT rule_id, chat_id, asset, metric, operator, threshold, horizon, cooldown_seconds, last_triggered_at_utc
      FROM user_alert_rules
      WHERE status = 'active'
      ORDER BY created_at_utc ASC
      LIMIT 100
    `).all();
    const realtime = await realtimeStatus(env);
    const quick = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0);
    const deep = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0);
    const triggered: Record<string, unknown>[] = [];
    for (const item of results || []) {
      const rule = objectValue(item);
      const evaluation = evaluateOneCustomRule(rule, realtime, quick, deep);
      if (!evaluation.triggered) {
        continue;
      }
      const cooldown = clampInt(parseNumber(rule.cooldown_seconds, 1800), 60, 24 * 60 * 60);
      const last = stringOrNull(rule.last_triggered_at_utc);
      if (last && (Date.now() - new Date(last).getTime()) / 1000 < cooldown) {
        continue;
      }
      const now = new Date();
      await env.DB.prepare("UPDATE user_alert_rules SET last_triggered_at_utc = ?, updated_at_utc = ? WHERE rule_id = ?")
        .bind(now.toISOString(), now.toISOString(), rule.rule_id).run();
      const chatId = stringOrNull(rule.chat_id) || stringOrNull(env.TELEGRAM_CHAT_ID);
      const message = formatCustomRuleAlert(rule, evaluation);
      if (chatId && !(await isTelegramMuted(env, chatId))) {
        await sendTelegramMessage(env, chatId, message);
      }
      triggered.push({
        rule_id: rule.rule_id,
        metric: rule.metric,
        value: evaluation.value,
        threshold: rule.threshold,
        sent_to_telegram: Boolean(chatId)
      });
    }
    return {
      status: "ok",
      checked_rules: (results || []).length,
      triggered_count: triggered.length,
      triggered
    };
  } finally {
    await releaseD1Lock(env, String(lock.name), String(lock.owner));
  }
}

function evaluateOneCustomRule(
  rule: Record<string, unknown>,
  realtime: Record<string, unknown>,
  quick: Record<string, unknown> | null,
  deep: Record<string, unknown> | null
): Record<string, unknown> {
  const metric = stringOrNull(rule.metric);
  const horizon = numberOrNull(rule.horizon);
  let value: number | null = null;
  let source = "absent";
  if (metric === "btc_price") {
    value = numberOrNull(realtime.price);
    source = "realtime_bitget_polling_snapshot";
  } else {
    const frame = findFrameForHorizon(deep, horizon) || findFrameForHorizon(quick, horizon);
    const risk = objectValue(frame?.risk_metrics);
    const confidence = objectValue(frame?.confidence);
    const regime = objectValue(frame?.regime_distribution);
    const distribution = objectValue(frame?.distribution);
    if (metric === "var95") {
      value = numberOrNull(risk.var_95);
    } else if (metric === "confidence") {
      value = numberOrNull(confidence.score);
    } else if (metric === "transition") {
      value = numberOrNull(regime.non_classified_transition);
    } else if (metric === "prob_up") {
      value = numberOrNull(distribution.prob_up);
    }
    source = stringOrNull(frame?.run_id) || "latest_d1_model_frame";
  }
  const threshold = numberOrNull(rule.threshold);
  const operator = stringOrNull(rule.operator);
  const triggered = value !== null && threshold !== null && compareNumeric(value, threshold, operator);
  return { triggered, value, threshold, operator, source };
}

function findFrameForHorizon(payload: Record<string, unknown> | null, horizon: number | null): Record<string, unknown> | null {
  if (!payload || horizon === null) {
    return null;
  }
  for (const item of Array.isArray(payload.frames) ? payload.frames : []) {
    const frame = objectValue(item);
    if (numberOrNull(frame.horizon) === horizon) {
      return frame;
    }
  }
  return null;
}

function compareNumeric(value: number, threshold: number, operator: string | null): boolean {
  if (operator === ">") return value > threshold;
  if (operator === ">=") return value >= threshold;
  if (operator === "<") return value < threshold;
  if (operator === "<=") return value <= threshold;
  return false;
}

function formatCustomRuleAlert(rule: Record<string, unknown>, evaluation: Record<string, unknown>): string {
  return [
    "Quant BTC - Alerte personnalisee",
    `Regle: ${rule.rule_id}`,
    `Metric: ${rule.metric}${rule.horizon ? ` ${rule.horizon}j` : ""}`,
    `Condition: ${rule.operator} ${rule.threshold}`,
    `Valeur: ${formatMetricValue(String(rule.metric), numberOrNull(evaluation.value))}`,
    `Source: ${evaluation.source || "absente"}`,
    "Sortie probabiliste, pas conseil financier.",
    `UTC: ${new Date().toISOString()}`,
    `Paris: ${parisIso(new Date())}`
  ].join("\n");
}

function formatMetricValue(metric: string, value: number | null): string {
  if (value === null) {
    return "absente";
  }
  if (["var95", "transition", "prob_up"].includes(metric)) {
    return formatPercent(value);
  }
  if (metric === "btc_price") {
    return `$${value.toFixed(2)}`;
  }
  return String(value);
}

function normalizeAlertMetric(value: unknown): string | null {
  const metric = String(value || "").trim().toLowerCase();
  const aliases: Record<string, string> = {
    price: "btc_price",
    spot: "btc_price",
    btc: "btc_price",
    var: "var95",
    var_95: "var95",
    confidence_score: "confidence",
    conf: "confidence",
    regime_transition: "transition",
    p_up: "prob_up",
    pup: "prob_up"
  };
  const normalized = aliases[metric] || metric;
  return ["btc_price", "var95", "confidence", "transition", "prob_up"].includes(normalized) ? normalized : null;
}

function normalizeAlertOperator(value: unknown): string | null {
  const operator = String(value || "").trim();
  if ([">", ">=", "<", "<="].includes(operator)) {
    return operator;
  }
  const lower = operator.toLowerCase();
  if (lower === "above" || lower === "gt") return ">";
  if (lower === "below" || lower === "lt") return "<";
  if (lower === "gte") return ">=";
  if (lower === "lte") return "<=";
  return null;
}

async function checkRenderHealth(env: Env): Promise<Record<string, unknown>> {
  const started = Date.now();
  try {
    const response = await fetchWithTimeout(renderUrl("/health", env), {
      method: "GET",
      headers: {
        "accept": "application/json",
        "user-agent": "quant-btc-model-cloudflare-ops-monitor/1.0"
      },
      cf: { cacheTtl: 0, cacheEverything: false }
    }, 8000);
    const text = await response.text();
    let body: unknown = {};
    try {
      body = text ? JSON.parse(text) : {};
    } catch {
      body = { raw_response: text.slice(0, 500) };
    }
    return {
      status: response.ok ? "ok" : "error",
      http_status: response.status,
      latency_ms: Date.now() - started,
      body: objectValue(body)
    };
  } catch (error) {
    return {
      status: "error",
      latency_ms: Date.now() - started,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function latestD1CacheSummary(env: Env, asset: string, requestedHorizons: number[]): Promise<Record<string, unknown>> {
  if (!env.DB) {
    return { status: "absent", message: "D1 binding is absent" };
  }
  try {
    const { results } = await env.DB.prepare(`
      SELECT archive_id, horizons_json, report_date_utc, reference_spot, created_at_utc, payload_json
      FROM quant_runs
      WHERE asset = ?
      ORDER BY created_at_utc DESC
      LIMIT 20
    `).bind(asset).all();
    for (const row of results || []) {
      const horizons = parseStoredJsonArray(row.horizons_json).map(Number);
      if (!sameNumberArray(horizons, requestedHorizons)) {
        continue;
      }
      const createdAt = stringOrNull(row.created_at_utc);
      const payload = stringOrNull(row.payload_json) ? objectValue(JSON.parse(String(row.payload_json))) : {};
      const firstFrame = objectValue(Array.isArray(payload.frames) ? payload.frames[0] : {});
      return {
        status: "present",
        archive_id: row.archive_id,
        horizons,
        report_date_utc: row.report_date_utc,
        report_date_paris: typeof row.report_date_utc === "string" ? parisIso(new Date(row.report_date_utc)) : null,
        reference_spot: row.reference_spot,
        reference_spot_timestamp_utc: firstFrame.reference_spot_timestamp_utc,
        reference_spot_timestamp_paris: firstFrame.reference_spot_timestamp_paris,
        created_at_utc: createdAt,
        created_at_paris: createdAt ? parisIso(new Date(createdAt)) : null,
        age_seconds: createdAt ? Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 1000)) : null
      };
    }
    return {
      status: "absent",
      message: `No D1 cache found for horizons ${requestedHorizons.join(",")}`
    };
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : String(error)
    };
  }
}

function classifyCacheSummary(summary: Record<string, unknown>, policy: Record<string, number>): Record<string, unknown> {
  if (summary.status !== "present") {
    return {
      ...summary,
      status: summary.status === "error" ? "error" : "absent",
      cache_decision: "analysis_blocked_until_fresh_run",
      message: stringOrNull(summary.message) || "No matching D1 cache is available"
    };
  }
  const age = numberOrNull(summary.age_seconds);
  const freshSeconds = Number(policy.fresh_seconds);
  const warningSeconds = Number(policy.warning_seconds);
  if (age === null) {
    return {
      ...summary,
      status: "error",
      cache_decision: "analysis_blocked_until_fresh_run",
      message: "Cache age is unavailable"
    };
  }
  if (age <= freshSeconds) {
    return {
      ...summary,
      status: "ok",
      freshness_label: "fresh",
      cache_decision: "analysis_allowed_recent_cache",
      message: `Cache age ${age}s is within fresh threshold ${freshSeconds}s`
    };
  }
  if (age <= warningSeconds) {
    return {
      ...summary,
      status: "warning",
      freshness_label: "warning_age",
      cache_decision: "analysis_allowed_only_with_warning",
      message: `Cache age ${age}s exceeds fresh threshold ${freshSeconds}s but remains below hard block ${warningSeconds}s`
    };
  }
  return {
    ...summary,
    status: "blocked",
    freshness_label: "stale_blocked",
    cache_decision: "analysis_blocked_stale_cache",
    message: `Cache age ${age}s exceeds hard block threshold ${warningSeconds}s`
  };
}

async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

function getOpsAlertChannels(env: Env): Record<string, string> {
  return {
    discord_webhook: getDiscordOpsWebhook(env) ? "configured" : "absent",
    telegram: getTelegramConfig(env) ? "configured" : "absent"
  };
}

function getDiscordOpsWebhook(env: Env): string | null {
  return stringOrNull(env.OPS_ALERT_WEBHOOK_URL) || stringOrNull(env.DISCORD_WEBHOOK_URL);
}

function getTelegramConfig(env: Env): { token: string; chatId: string } | null {
  const token = stringOrNull(env.TELEGRAM_BOT_TOKEN);
  const chatId = stringOrNull(env.TELEGRAM_CHAT_ID);
  if (!token || !chatId) {
    return null;
  }
  return { token, chatId };
}

function getDailySummaryParisHour(env: Env): number {
  return clampInt(parseNumber(env.OPS_DAILY_SUMMARY_PARIS_HOUR, OPS_DAILY_SUMMARY_PARIS_HOUR_DEFAULT), 0, 23);
}

function getModelAlertConfig(env: Env): Record<string, number> {
  return {
    var95_threshold: clampFloat(parseNumber(env.MODEL_ALERT_VAR95_THRESHOLD, MODEL_ALERT_VAR95_THRESHOLD_DEFAULT), 0.01, 0.99),
    confidence_threshold: clampFloat(parseNumber(env.MODEL_ALERT_CONFIDENCE_THRESHOLD, MODEL_ALERT_CONFIDENCE_THRESHOLD_DEFAULT), 1, 100),
    transition_threshold: clampFloat(parseNumber(env.MODEL_ALERT_TRANSITION_THRESHOLD, MODEL_ALERT_TRANSITION_THRESHOLD_DEFAULT), 0.01, 0.99),
    bias_delta_threshold: clampFloat(parseNumber(env.MODEL_ALERT_BIAS_DELTA_THRESHOLD, MODEL_ALERT_BIAS_DELTA_THRESHOLD_DEFAULT), 0.01, 0.99),
    cooldown_seconds: clampInt(parseNumber(env.MODEL_ALERT_COOLDOWN_SECONDS, MODEL_ALERT_COOLDOWN_SECONDS_DEFAULT), 60, 24 * 60 * 60),
    quick_refresh_seconds: clampInt(parseNumber(env.MODEL_ALERT_QUICK_REFRESH_SECONDS, MODEL_ALERT_QUICK_REFRESH_SECONDS_DEFAULT), 60, 60 * 60),
    deep_refresh_seconds: clampInt(parseNumber(env.MODEL_ALERT_DEEP_REFRESH_SECONDS, MODEL_ALERT_DEEP_REFRESH_SECONDS_DEFAULT), 5 * 60, 6 * 60 * 60)
  };
}

async function refreshModelAlertRunsIfNeeded(env: Env, force = false): Promise<Record<string, unknown>> {
  const now = new Date();
  const config = getModelAlertConfig(env);
  const quick = await refreshPresetForModelAlerts(
    env,
    "/quick",
    "/model-alerts/quick-refresh",
    Number(config.quick_refresh_seconds),
    force
  );
  const deep = await refreshPresetForModelAlerts(
    env,
    "/deep",
    "/model-alerts/deep-refresh",
    Number(config.deep_refresh_seconds),
    force
  );
  return {
    status: "checked",
    policy: "Before Telegram model alerts, refresh quick/deep if their latest matching D1 archive is older than the configured threshold.",
    force,
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now),
    quick,
    deep
  };
}

async function refreshPresetForModelAlerts(
  env: Env,
  presetPath: string,
  operationPath: string,
  maxAgeSeconds: number,
  force: boolean
): Promise<Record<string, unknown>> {
  const preset = ANALYSIS_PRESETS[presetPath];
  if (!preset) {
    return { status: "error", preset_path: presetPath, message: "Unknown analysis preset" };
  }
  const before = await latestD1CacheSummary(env, "BTC", preset.horizons);
  const beforeAge = numberOrNull(before.age_seconds);
  if (!force && before.status === "present" && beforeAge !== null && beforeAge < maxAgeSeconds) {
    return {
      status: "cache_fresh",
      preset: preset.name,
      max_age_seconds: maxAgeSeconds,
      cache_age_seconds: beforeAge,
      archive_id: before.archive_id,
      report_date_utc: before.report_date_utc,
      report_date_paris: before.report_date_paris,
      reference_spot: before.reference_spot,
      reference_spot_timestamp_utc: before.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: before.reference_spot_timestamp_paris,
      note: "No new Render run was needed because the cache is still inside the real-time alert window."
    };
  }

  const started = Date.now();
  const body = normalizeRenderPresetPayload({ asset: "BTC", model: "ensemble" }, env, preset);
  const lock = await acquireD1Lock(env, `model-alert-refresh-${preset.name}`, Math.max(90, Math.min(maxAgeSeconds, 15 * 60)), {
    preset: preset.name,
    operation_path: operationPath,
    force
  });
  if (!lock.acquired) {
    return {
      status: "refresh_skipped_lock_active",
      preset: preset.name,
      max_age_seconds: maxAgeSeconds,
      previous_cache_status: before.status,
      previous_cache_age_seconds: beforeAge,
      lock
    };
  }
  try {
    const result = await proxyRenderPost("/multi-run", body, env);
    result.analysis_preset = {
      ...publicAnalysisPreset(presetPath, env),
      requested_endpoint: operationPath,
      requested_preset: preset.name
    };
    result.cloudflare_bridge = {
      ...objectValue(result.cloudflare_bridge),
      operation_path: operationPath,
      render_operation_path: "/multi-run",
      analysis_preset: preset.name,
      refresh_reason: force ? "manual_force_refresh" : "model_alert_cache_expired"
    };
    if (result.error) {
      return {
        status: "refresh_failed",
        preset: preset.name,
        max_age_seconds: maxAgeSeconds,
        previous_cache_status: before.status,
        previous_cache_age_seconds: beforeAge,
        latency_ms: Date.now() - started,
        error: result.error,
        message: result.message,
        render_status: result.render_status,
        data_status: result.data_status
      };
    }
    const compact = compactRunPayload(result);
    const frames = Array.isArray(compact.frames) ? compact.frames : [];
    if (!compact.archive_id || frames.length === 0) {
      return {
        status: "refresh_failed",
        preset: preset.name,
        max_age_seconds: maxAgeSeconds,
        previous_cache_status: before.status,
        previous_cache_age_seconds: beforeAge,
        latency_ms: Date.now() - started,
        message: "Render returned no archive_id or no frames; refreshed output was not stored.",
        data_status: result.data_status
      };
    }
    await persistRunToD1(result, operationPath, body, env);
    await persistUsageToD1(result, operationPath, body, env);
    return {
      status: "fresh_run",
      preset: preset.name,
      max_age_seconds: maxAgeSeconds,
      previous_cache_status: before.status,
      previous_cache_age_seconds: beforeAge,
      latency_ms: Date.now() - started,
      archive_id: compact.archive_id,
      report_date_utc: compact.report_date_utc,
      report_date_paris: compact.report_date_paris,
      reference_spot: compact.reference_spot,
      reference_spot_timestamp_utc: compact.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: compact.reference_spot_timestamp_paris,
      horizons: compact.horizons,
      simulations: body.simulations
    };
  } catch (error) {
    return {
      status: "refresh_failed",
      preset: preset.name,
      max_age_seconds: maxAgeSeconds,
      previous_cache_status: before.status,
      previous_cache_age_seconds: beforeAge,
      latency_ms: Date.now() - started,
      message: error instanceof Error ? error.message : String(error)
    };
  } finally {
    await releaseD1Lock(env, String(lock.name), String(lock.owner));
  }
}

async function evaluateLatestModelAlerts(env: Env, refreshStatus?: Record<string, unknown>): Promise<Record<string, unknown>> {
  const now = new Date();
  const config = getModelAlertConfig(env);
  const [quickCurrent, quickPrevious, deepCurrent, deepPrevious] = await Promise.all([
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0),
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 1),
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0),
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 1)
  ]);
  const issues = [
    ...evaluateRunModelIssues("quick", quickCurrent, config),
    ...evaluateRunModelIssues("deep", deepCurrent, config),
    ...compareRunBias("quick", quickCurrent, quickPrevious, config),
    ...compareRunBias("deep", deepCurrent, deepPrevious, config)
  ];
  const criticalCount = issues.filter((issue) => issue.level === "CRITICAL").length;
  const warningCount = issues.filter((issue) => issue.level === "WARNING").length;
  const status = criticalCount > 0 ? "critical" : warningCount > 0 ? "warning" : "ok";
  return {
    status,
    worker_version: WORKER_VERSION,
    schema_version: SCHEMA_VERSION,
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now),
    thresholds: config,
    refresh_status: refreshStatus || {
      status: "not_requested",
      reason: "Evaluation used the latest matching D1 archives without attempting a pre-alert refresh."
    },
    latest_runs: {
      quick: compactRunReference(quickCurrent),
      deep: compactRunReference(deepCurrent),
      quick_previous: compactRunReference(quickPrevious),
      deep_previous: compactRunReference(deepPrevious)
    },
    issue_count: issues.length,
    critical_count: criticalCount,
    warning_count: warningCount,
    issues,
    channels: getOpsAlertChannels(env),
    policy: [
      "VaR95 above threshold triggers a model risk alert.",
      "Confidence below threshold triggers a fragility alert.",
      "Transition/non-classified regime above threshold triggers a regime uncertainty alert.",
      "P(up) change above threshold versus the previous matching run triggers a bias shift alert."
    ]
  };
}

async function runModelAlertMonitor(env: Env, manual = false, refreshBeforeEvaluate = true, forceRefresh = false): Promise<Record<string, unknown>> {
  const lock = manual
    ? { acquired: true, owner: "manual", name: "manual-model-alert" }
    : await acquireD1Lock(env, "model-alert-monitor", LOCK_TTL_SECONDS_DEFAULT, { worker_version: WORKER_VERSION });
  if (!lock.acquired) {
    return {
      status: "skipped",
      reason: "lock_active",
      lock,
      checked_at_utc: new Date().toISOString(),
      checked_at_paris: parisIso(new Date())
    };
  }
  try {
    const refreshStatus = refreshBeforeEvaluate
      ? await refreshModelAlertRunsIfNeeded(env, forceRefresh)
      : { status: "not_requested", reason: "refreshBeforeEvaluate=false" };
    const evaluation = await evaluateLatestModelAlerts(env, refreshStatus);
    if (evaluation.status === "ok" && !manual) {
      return evaluation;
    }
    const issues = Array.isArray(evaluation.issues) ? evaluation.issues.map((item) => objectValue(item)) : [];
    const fingerprint = manual
      ? `model-alert-test:${new Date().toISOString()}`
      : modelAlertFingerprint(evaluation);
    const cooldown = Number(objectValue(evaluation.thresholds).cooldown_seconds || MODEL_ALERT_COOLDOWN_SECONDS_DEFAULT);
    if (!manual && !(await shouldSendOpsAlert(env, fingerprint, cooldown))) {
      return {
        ...evaluation,
        alert_delivery: {
          status: "skipped",
          reason: "cooldown_active",
          cooldown_seconds: cooldown
        }
      };
    }
    const text = formatModelAlertText(evaluation, manual);
    const [discord, telegram] = await Promise.all([
      sendDiscordOpsAlert(env, manual ? "Quant BTC model alert TEST" : `Quant BTC model alert ${String(evaluation.status).toUpperCase()}`, text, evaluation),
      sendTelegramOpsAlert(env, text)
    ]);
    const sent = [discord, telegram].some((item) => objectValue(item).status === "sent");
    await persistOpsEventToD1(env, {
      kind: manual ? "manual_model_alert" : "model_alert",
      status: sent ? "sent" : "error",
      severity: evaluation.status === "critical" ? "critical" : evaluation.status === "warning" ? "warning" : "info",
      message: issues.length ? issues.slice(0, 5).map((issue) => String(issue.message || issue.type || "model issue")).join("; ") : "No active model alert",
      fingerprint,
      payload: {
        evaluation,
        delivery: { discord, telegram }
      }
    });
    return {
      ...evaluation,
      alert_delivery: {
        status: sent ? "sent" : "error",
        discord,
        telegram
      }
    };
  } finally {
    if (!manual) {
      await releaseD1Lock(env, String(lock.name), String(lock.owner));
    }
  }
}

async function latestD1RunPayload(env: Env, asset: string, requestedHorizons: number[], offset: number): Promise<Record<string, unknown> | null> {
  if (!env.DB) {
    return null;
  }
  try {
    const { results } = await env.DB.prepare(`
      SELECT payload_json, created_at_utc
      FROM quant_runs
      WHERE asset = ?
      ORDER BY created_at_utc DESC
      LIMIT 30
    `).bind(asset).all();
    let matches = 0;
    for (const row of results || []) {
      const payloadRaw = stringOrNull(objectValue(row).payload_json);
      if (!payloadRaw) {
        continue;
      }
      const payload = objectValue(JSON.parse(payloadRaw));
      const horizons = Array.isArray(payload.horizons) ? payload.horizons.map(Number) : [];
      if (!sameNumberArray(horizons, requestedHorizons)) {
        continue;
      }
      if (matches === offset) {
        const createdAt = stringOrNull(objectValue(row).created_at_utc);
        return {
          ...payload,
          d1_created_at_utc: createdAt,
          d1_created_at_paris: createdAt ? parisIso(new Date(createdAt)) : null,
          d1_age_seconds: createdAt ? Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 1000)) : null
        };
      }
      matches += 1;
    }
  } catch {
    return null;
  }
  return null;
}

function evaluateRunModelIssues(mode: string, payload: Record<string, unknown> | null, config: Record<string, number>): Record<string, unknown>[] {
  if (!payload) {
    return [{
      level: "WARNING",
      type: "run_absent",
      mode,
      message: `Run ${mode} absent du cache D1`
    }];
  }
  const archiveId = stringOrNull(payload.archive_id) || "absent";
  const frames = Array.isArray(payload.frames) ? payload.frames.map((item) => objectValue(item)) : [];
  const issues: Record<string, unknown>[] = [];
  for (const frame of frames) {
    const horizon = numberOrNull(frame.horizon);
    const runId = stringOrNull(frame.run_id) || "absent";
    const risk = objectValue(frame.risk_metrics);
    const confidence = objectValue(frame.confidence);
    const regime = objectValue(frame.regime_distribution);
    const var95 = numberOrNull(risk.var_95);
    const confidenceScore = numberOrNull(confidence.score);
    const transition = numberOrNull(regime.non_classified_transition);
    if (var95 !== null && var95 >= Number(config.var95_threshold)) {
      issues.push({
        level: var95 >= 0.45 ? "CRITICAL" : "WARNING",
        type: "var95_high",
        mode,
        horizon,
        value: var95,
        threshold: config.var95_threshold,
        archive_id: archiveId,
        run_id: runId,
        message: `${mode} ${horizon}j : VaR95 ${formatPercent(var95)} depasse ${formatPercent(Number(config.var95_threshold))}`
      });
    }
    if (confidenceScore !== null && confidenceScore < Number(config.confidence_threshold)) {
      issues.push({
        level: confidenceScore <= 35 ? "CRITICAL" : "WARNING",
        type: "confidence_low",
        mode,
        horizon,
        value: confidenceScore,
        threshold: config.confidence_threshold,
        archive_id: archiveId,
        run_id: runId,
        message: `${mode} ${horizon}j : confiance ${confidenceScore}/100 inferieure a ${config.confidence_threshold}/100`
      });
    }
    if (transition !== null && transition >= Number(config.transition_threshold)) {
      issues.push({
        level: transition >= 0.35 ? "CRITICAL" : "WARNING",
        type: "transition_high",
        mode,
        horizon,
        value: transition,
        threshold: config.transition_threshold,
        archive_id: archiveId,
        run_id: runId,
        message: `${mode} ${horizon}j : transition ${formatPercent(transition)} depasse ${formatPercent(Number(config.transition_threshold))}`
      });
    }
  }
  return issues;
}

function compareRunBias(mode: string, current: Record<string, unknown> | null, previous: Record<string, unknown> | null, config: Record<string, number>): Record<string, unknown>[] {
  if (!current || !previous) {
    return [];
  }
  const threshold = Number(config.bias_delta_threshold);
  const previousByHorizon = new Map<number, Record<string, unknown>>();
  for (const frame of Array.isArray(previous.frames) ? previous.frames.map((item) => objectValue(item)) : []) {
    const horizon = numberOrNull(frame.horizon);
    if (horizon !== null) {
      previousByHorizon.set(horizon, frame);
    }
  }
  const issues: Record<string, unknown>[] = [];
  for (const frame of Array.isArray(current.frames) ? current.frames.map((item) => objectValue(item)) : []) {
    const horizon = numberOrNull(frame.horizon);
    if (horizon === null) {
      continue;
    }
    const previousFrame = previousByHorizon.get(horizon);
    if (!previousFrame) {
      continue;
    }
    const currentProbUp = numberOrNull(objectValue(frame.distribution).prob_up);
    const previousProbUp = numberOrNull(objectValue(previousFrame.distribution).prob_up);
    if (currentProbUp === null || previousProbUp === null) {
      continue;
    }
    const delta = currentProbUp - previousProbUp;
    if (Math.abs(delta) >= threshold) {
      issues.push({
        level: Math.abs(delta) >= threshold * 2 ? "CRITICAL" : "WARNING",
        type: "bias_shift",
        mode,
        horizon,
        value: delta,
        threshold,
        archive_id: current.archive_id,
        previous_archive_id: previous.archive_id,
        run_id: frame.run_id,
        previous_run_id: previousFrame.run_id,
        message: `${mode} ${horizon}j : P(up) varie de ${formatPercent(delta)} vs run precedent`
      });
    }
  }
  return issues;
}

function compactRunReference(payload: Record<string, unknown> | null): Record<string, unknown> | null {
  if (!payload) {
    return null;
  }
  return {
    archive_id: payload.archive_id,
    report_date_utc: payload.report_date_utc,
    report_date_paris: payload.report_date_paris,
    reference_spot: payload.reference_spot,
    reference_spot_timestamp_utc: payload.reference_spot_timestamp_utc,
    reference_spot_timestamp_paris: payload.reference_spot_timestamp_paris,
    horizons: payload.horizons,
    d1_created_at_utc: payload.d1_created_at_utc,
    d1_created_at_paris: payload.d1_created_at_paris,
    d1_age_seconds: payload.d1_age_seconds
  };
}

function modelAlertFingerprint(evaluation: Record<string, unknown>): string {
  const issues = Array.isArray(evaluation.issues) ? evaluation.issues.map((item) => objectValue(item)) : [];
  const archiveIds = objectValue(evaluation.latest_runs);
  const quick = objectValue(archiveIds.quick);
  const deep = objectValue(archiveIds.deep);
  const issueKey = issues
    .map((issue) => `${issue.type}:${issue.mode}:${issue.horizon}:${issue.level}`)
    .sort()
    .join("|");
  return `model:${evaluation.status}:${quick.archive_id || "noquick"}:${deep.archive_id || "nodeep"}:${issueKey}`;
}

function formatModelAlertText(evaluation: Record<string, unknown>, manual: boolean): string {
  const latestRuns = objectValue(evaluation.latest_runs);
  const quick = objectValue(latestRuns.quick);
  const deep = objectValue(latestRuns.deep);
  const refresh = objectValue(evaluation.refresh_status);
  const issues = Array.isArray(evaluation.issues) ? evaluation.issues.map((item) => objectValue(item)) : [];
  const topIssues = issues.length
    ? issues.slice(0, 10).map((issue) => `- ${formatIssueLevel(issue.level)}: ${issue.message}`).join("\n")
    : "- Aucune alerte modele active aux seuils actuels.";
  const header = manual ? "Quant BTC - Alerte modele TEST" : "Quant BTC - Alerte modele";
  return [
    header,
    `Niveau: ${formatStatusLabel(evaluation.status)}`,
    `Alertes: ${issues.length}`,
    ``,
    topIssues,
    ``,
    refreshSummaryLine("Rafraichissement quick", objectValue(refresh.quick)),
    refreshSummaryLine("Rafraichissement deep", objectValue(refresh.deep)),
    ``,
    `Archive quick: ${quick.archive_id || "absente"}`,
    `Archive deep: ${deep.archive_id || "absente"}`,
    ...spotReferenceLines(quick, deep),
    ``,
    `Regle: alerte de risque probabiliste, pas un conseil financier.`,
    `UTC: ${evaluation.checked_at_utc || new Date().toISOString()}`,
    `Paris: ${evaluation.checked_at_paris || parisIso(new Date())}`
  ].join("\n");
}

function refreshSummaryLine(label: string, refresh: Record<string, unknown>): string {
  if (!Object.keys(refresh).length) {
    return `${label}: non demande`;
  }
  const parts = [formatRefreshStatus(refresh.status)];
  const archiveId = stringOrNull(refresh.archive_id);
  const age = numberOrNull(refresh.cache_age_seconds ?? refresh.previous_cache_age_seconds);
  const maxAge = numberOrNull(refresh.max_age_seconds);
  const latency = numberOrNull(refresh.latency_ms);
  const spot = numberOrNull(refresh.reference_spot);
  const message = stringOrNull(refresh.message);
  if (archiveId) {
    parts.push(`archive=${archiveId}`);
  }
  if (spot !== null) {
    parts.push(`spot=$${spot.toFixed(2)}`);
  }
  if (age !== null && maxAge !== null) {
    parts.push(`age=${age}s/${maxAge}s`);
  }
  if (latency !== null) {
    parts.push(`latence=${latency}ms`);
  }
  if (message) {
    parts.push(message.slice(0, 100));
  }
  return `${label}: ${parts.join(" | ")}`;
}

function formatIssueLevel(value: unknown): string {
  const level = String(value || "unknown").toUpperCase();
  if (level === "CRITICAL") {
    return "CRITIQUE";
  }
  if (level === "WARNING") {
    return "AVERTISSEMENT";
  }
  if (level === "INFO") {
    return "INFO";
  }
  return level;
}

function formatStatusLabel(value: unknown): string {
  const status = String(value || "unknown").toLowerCase();
  if (status === "critical") {
    return "CRITIQUE";
  }
  if (status === "warning") {
    return "AVERTISSEMENT";
  }
  if (status === "degraded") {
    return "DEGRADE";
  }
  if (status === "ok") {
    return "OK";
  }
  if (status === "error") {
    return "ERREUR";
  }
  return status.toUpperCase();
}

function formatRefreshStatus(value: unknown): string {
  const status = String(value || "unknown");
  const labels: Record<string, string> = {
    cache_fresh: "cache recent",
    fresh_run: "nouveau calcul",
    refresh_failed: "echec du recalcul",
    checked: "verifie",
    not_requested: "non demande",
    error: "erreur"
  };
  return labels[status] || status;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

async function sendOpsAlertIfNeeded(env: Env, fingerprint: string, message: string, status: Record<string, unknown>): Promise<void> {
  const hasDiscord = Boolean(getDiscordOpsWebhook(env));
  const hasTelegram = Boolean(getTelegramConfig(env));
  if (!hasDiscord && !hasTelegram) {
    return;
  }
  const cooldown = clampInt(parseNumber(env.OPS_MONITOR_ALERT_COOLDOWN_SECONDS, OPS_MONITOR_ALERT_COOLDOWN_SECONDS_DEFAULT), 60, 24 * 60 * 60);
  if (!(await shouldSendOpsAlert(env, fingerprint, cooldown))) {
    return;
  }
  const title = `Quant BTC Ops ${opsLevel(status)}`;
  const text = formatOpsAlertText(status, message);
  await Promise.all([
    sendDiscordOpsAlert(env, title, message, status),
    sendTelegramOpsAlert(env, text)
  ]);
}

function opsLevel(status: Record<string, unknown>): string {
  const value = String(status.status || "unknown").toLowerCase();
  if (value === "degraded") {
    return "CRITICAL";
  }
  if (value === "warning") {
    return "WARNING";
  }
  if (value === "ok") {
    return "OK";
  }
  return value.toUpperCase();
}

function formatOpsAlertText(status: Record<string, unknown>, message: string): string {
  const checks = objectValue(status.checks);
  const render = objectValue(checks.render_health);
  const d1 = objectValue(checks.cloudflare_d1);
  const quick = objectValue(checks.quick_cache);
  const deep = objectValue(checks.deep_cache);
  return [
    `Quant BTC - Alerte operationnelle`,
    `Niveau: ${opsLevel(status)}`,
    `Cause: ${message}`,
    ``,
    `Render: ${render.status || "unknown"}`,
    `D1: ${d1.status || "unknown"}`,
    cacheSummaryLine("Cache quick", quick),
    cacheSummaryLine("Cache deep", deep),
    ``,
    `Worker: ${WORKER_VERSION}`,
    `UTC: ${status.checked_at_utc || new Date().toISOString()}`,
    `Paris: ${status.checked_at_paris || parisIso(new Date())}`
  ].join("\n");
}

function formatDailySummaryText(status: Record<string, unknown>, manual: boolean): string {
  const checks = objectValue(status.checks);
  const render = objectValue(checks.render_health);
  const d1 = objectValue(checks.cloudflare_d1);
  const quick = objectValue(checks.quick_cache);
  const deep = objectValue(checks.deep_cache);
  const warnings = Array.isArray(status.warnings) ? status.warnings : [];
  const blockers = Array.isArray(status.blockers) ? status.blockers : [];
  const header = manual ? "Quant BTC - Resume quotidien TEST" : "Quant BTC - Resume quotidien";
  return [
    header,
    `Statut: ${opsLevel(status)}`,
    `Render: ${render.status || "unknown"}`,
    `D1: ${d1.status || "unknown"}`,
    cacheSummaryLine("Cache quick", quick),
    cacheSummaryLine("Cache deep", deep),
    ``,
    `Archive quick: ${quick.archive_id || "absente"}`,
    `Archive deep: ${deep.archive_id || "absente"}`,
    ...spotReferenceLines(quick, deep),
    ``,
    `Avertissements: ${warnings.length ? warnings.join(" | ") : "aucun"}`,
    `Blocages: ${blockers.length ? blockers.join(" | ") : "aucun"}`,
    ``,
    `Worker: ${WORKER_VERSION}`,
    `UTC: ${status.checked_at_utc || new Date().toISOString()}`,
    `Paris: ${status.checked_at_paris || parisIso(new Date())}`
  ].join("\n");
}

function cacheSummaryLine(label: string, cache: Record<string, unknown>): string {
  const status = formatCacheStatus(cache.status);
  const age = numberOrNull(cache.age_seconds);
  const ageText = age === null ? "age inconnu" : `age ${Math.round(age / 60)} min`;
  const decision = formatCacheDecision(cache.cache_decision);
  return `${label}: ${status} (${ageText}, ${decision})`;
}

function formatCacheStatus(value: unknown): string {
  const status = String(value || "unknown");
  const labels: Record<string, string> = {
    ok: "ok",
    warning: "avertissement",
    blocked: "bloque",
    absent: "absent",
    error: "erreur",
    present: "present",
    unknown: "inconnu"
  };
  return labels[status] || status;
}

function formatCacheDecision(value: unknown): string {
  const decision = String(value || "unknown");
  const labels: Record<string, string> = {
    analysis_allowed_recent_cache: "cache recent utilisable",
    analysis_allowed_only_with_warning: "utilisable avec avertissement",
    analysis_blocked_stale_cache: "bloque car cache trop ancien",
    analysis_blocked_until_fresh_run: "bloque jusqu'au prochain run frais",
    unknown: "decision absente"
  };
  return labels[decision] || decision;
}

function spotReferenceLines(quick: Record<string, unknown>, deep: Record<string, unknown>): string[] {
  const quickSpot = stringOrNull(quick.reference_spot);
  const deepSpot = stringOrNull(deep.reference_spot);
  const quickTs = stringOrNull(quick.reference_spot_timestamp_paris) || stringOrNull(quick.reference_spot_timestamp_utc);
  const deepTs = stringOrNull(deep.reference_spot_timestamp_paris) || stringOrNull(deep.reference_spot_timestamp_utc);
  if (quickSpot && deepSpot && quickSpot === deepSpot) {
    if (quickTs && deepTs && quickTs === deepTs) {
      return [`Spot de reference: ${quickSpot} (meme snapshot Bitget pour quick/deep, ${quickTs})`];
    }
    return [
      `Spot de reference: ${quickSpot} (meme prix, snapshots separes)`,
      `Timestamp spot quick: ${quickTs || "absent"}`,
      `Timestamp spot deep: ${deepTs || "absent"}`
    ];
  }
  return [
    `Spot quick: ${quickSpot || "absent"} (${quickTs || "timestamp absent"})`,
    `Spot deep: ${deepSpot || "absent"} (${deepTs || "timestamp absent"})`
  ];
}

async function sendDiscordOpsAlert(env: Env, title: string, message: string, status: Record<string, unknown>): Promise<Record<string, unknown>> {
  const webhook = getDiscordOpsWebhook(env);
  if (!webhook) {
    return { status: "absent" };
  }
  try {
    const response = await fetch(webhook, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        content: `${title}: ${message}`,
        embeds: [
          {
            title: "Quant BTC operational monitor",
            description: message,
            color: status.status === "degraded" ? 15158332 : 16776960,
            timestamp: new Date().toISOString()
          }
        ]
      })
    });
    return {
      status: response.ok ? "sent" : "error",
      http_status: response.status
    };
  } catch (error) {
    // Discord delivery is best-effort; /ops/status remains the source of truth.
    return {
      status: "error",
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function sendTelegramOpsAlert(env: Env, text: string): Promise<Record<string, unknown>> {
  const config = getTelegramConfig(env);
  if (!config) {
    return { status: "absent" };
  }
  if (await isTelegramMuted(env, config.chatId)) {
    return { status: "skipped", reason: "telegram_muted" };
  }
  return await sendTelegramMessage(env, config.chatId, text);
}

async function sendTelegramMessage(env: Env, chatId: string, text: string, replyMarkup?: Record<string, unknown>): Promise<Record<string, unknown>> {
  const config = getTelegramConfig(env);
  if (!config) {
    return { status: "absent" };
  }
  try {
    const response = await fetch(`https://api.telegram.org/bot${config.token}/sendMessage`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        disable_web_page_preview: true,
        reply_markup: replyMarkup
      })
    });
    const textBody = await response.text();
    let body: unknown = {};
    try {
      body = textBody ? JSON.parse(textBody) : {};
    } catch {
      body = { raw_response: textBody.slice(0, 500) };
    }
    return {
      status: response.ok && objectValue(body).ok !== false ? "sent" : "error",
      http_status: response.status,
      telegram_ok: objectValue(body).ok,
      description: objectValue(body).description
    };
  } catch (error) {
    // Telegram delivery is best-effort; /ops/status remains the source of truth.
    return {
      status: "error",
      error: error instanceof Error ? error.message : String(error)
    };
  }
}

async function setupTelegramWebhook(env: Env, request: Request): Promise<Record<string, unknown>> {
  const config = getTelegramConfig(env);
  if (!config) {
    return { status: "absent", message: "Telegram secrets are not configured." };
  }
  const url = new URL(request.url);
  const chatId = url.searchParams.get("chat_id");
  if (chatId !== config.chatId) {
    return {
      status: "forbidden",
      message: "Pass ?chat_id=<TELEGRAM_CHAT_ID> to confirm webhook setup for the configured owner chat."
    };
  }
  const webhookUrl = `${url.origin}/telegram/webhook`;
  const response = await fetch(`https://api.telegram.org/bot${config.token}/setWebhook`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      url: webhookUrl,
      allowed_updates: ["message", "callback_query"]
    })
  });
  const body = objectValue(await response.json().catch(() => ({})));
  return {
    status: response.ok && body.ok !== false ? "ok" : "error",
    webhook_url: webhookUrl,
    telegram_ok: body.ok,
    description: body.description,
    checked_at_utc: new Date().toISOString(),
    checked_at_paris: parisIso(new Date())
  };
}

async function handleTelegramWebhook(env: Env, update: Record<string, unknown>): Promise<Record<string, unknown>> {
  const message = objectValue(update.message || objectValue(update.callback_query).message);
  const callback = objectValue(update.callback_query);
  const chat = objectValue(message.chat);
  const chatId = stringOrNull(chat.id) || (chat.id !== undefined ? String(chat.id) : null);
  if (!chatId) {
    return { status: "ignored", reason: "chat_id_absent" };
  }
  const config = getTelegramConfig(env);
  if (config && chatId !== config.chatId) {
    return { status: "ignored", reason: "unauthorized_chat", chat_id: chatId };
  }
  const text = stringOrNull(callback.data) || stringOrNull(message.text) || "/help";
  await upsertTelegramSession(env, chatId, chat, text);
  const response = await handleTelegramCommand(env, chatId, text);
  return { status: "ok", chat_id: chatId, command: text, response };
}

async function upsertTelegramSession(env: Env, chatId: string, chat: Record<string, unknown>, command: string): Promise<void> {
  if (!env.DB) {
    return;
  }
  const now = new Date().toISOString();
  await env.DB.prepare(`
    INSERT INTO telegram_sessions (chat_id, username, first_name, last_command, created_at_utc, updated_at_utc)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(chat_id) DO UPDATE SET
      username = excluded.username,
      first_name = excluded.first_name,
      last_command = excluded.last_command,
      updated_at_utc = excluded.updated_at_utc
  `).bind(
    chatId,
    stringOrNull(chat.username),
    stringOrNull(chat.first_name),
    command,
    now,
    now
  ).run();
}

async function handleTelegramCommand(env: Env, chatId: string, raw: string): Promise<Record<string, unknown>> {
  const [commandRaw, ...args] = raw.trim().split(/\s+/);
  const command = commandRaw.toLowerCase();
  if (command === "/start" || command === "/help") {
    return await sendTelegramMessage(env, chatId, telegramHelpText(), telegramMainKeyboard());
  }
  if (command === "/status") {
    const status = await buildOpsStatus(env);
    return await sendTelegramMessage(env, chatId, formatOpsStatusForTelegram(status), telegramMainKeyboard());
  }
  if (command === "/quick") {
    const quick = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0);
    return await sendTelegramMessage(env, chatId, formatRunShortForTelegram("quick", quick), telegramMainKeyboard());
  }
  if (command === "/quick_fresh") {
    const refresh = await refreshPresetForModelAlerts(env, "/quick", "/telegram/quick_fresh", 1, true);
    const quick = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0);
    return await sendTelegramMessage(env, chatId, `${refreshSummaryLine("Rafraichissement quick", refresh)}\n\n${formatRunShortForTelegram("quick", quick)}`, telegramMainKeyboard());
  }
  if (command === "/deep") {
    const deep = await latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0);
    return await sendTelegramMessage(env, chatId, formatRunShortForTelegram("deep", deep), telegramMainKeyboard());
  }
  if (command === "/deep_run") {
    const job = await createDeepJob(env, { asset: "BTC", chat_id: chatId });
    return await sendTelegramMessage(env, chatId, `Deep job cree\nJob: ${job.job_id || "absent"}\nStatut: ${job.status}\nJe t'envoie Telegram quand c'est fini.`, telegramMainKeyboard());
  }
  if (command === "/alerts") {
    const evaluation = await evaluateLatestModelAlerts(env, { status: "not_requested", reason: "telegram_alerts_command" });
    return await sendTelegramMessage(env, chatId, formatModelAlertText(evaluation, true), telegramMainKeyboard());
  }
  if (command === "/last") {
    const [quick, deep, realtime] = await Promise.all([
      latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0),
      latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0),
      realtimeStatus(env)
    ]);
    return await sendTelegramMessage(env, chatId, [
      "Quant BTC - Dernier etat",
      formatRealtimeForTelegram(realtime),
      "",
      formatRunShortForTelegram("quick", quick),
      "",
      formatRunShortForTelegram("deep", deep)
    ].join("\n"), telegramMainKeyboard());
  }
  if (command === "/mute") {
    const minutes = clampInt(parseNumber(args[0], 60), 1, 24 * 60);
    await muteTelegramSession(env, chatId, minutes);
    return await sendTelegramMessage(env, chatId, `Alertes mutees pendant ${minutes} min.`, telegramMainKeyboard());
  }
  if (command === "/rule") {
    const rule = await createRuleFromTelegram(env, chatId, args);
    return await sendTelegramMessage(env, chatId, String(rule.message || `Regle: ${rule.status}`), telegramMainKeyboard());
  }
  if (command === "/trade_signal") {
    const signal = await buildTradingSignal(env, { asset: "BTC", preset: "deep", horizon: 30 });
    return await sendTelegramMessage(env, chatId, formatTradingSignalForTelegram(signal), telegramMainKeyboard());
  }
  if (command === "/paper_trade") {
    const order = await createPaperTradeOrder(env, { asset: "BTC", preset: "deep", horizon: 30 }, "telegram_owner");
    return await sendTelegramMessage(env, chatId, formatTradeOrderForTelegram(order), telegramMainKeyboard());
  }
  if (command === "/trade_propose") {
    const mode = String(args[0] || "paper").toLowerCase() === "live" ? "live" : "paper";
    const order = await proposeTradeOrder(env, { asset: "BTC", preset: "deep", horizon: 30, mode, chat_id: chatId }, "telegram_owner");
    return await sendTelegramMessage(env, chatId, formatTradeOrderForTelegram(order), telegramMainKeyboard());
  }
  if (command === "/trade_orders") {
    const orders = await listTradeOrders(env, 5);
    return await sendTelegramMessage(env, chatId, formatTradeOrdersForTelegram(orders), telegramMainKeyboard());
  }
  if (command === "/trade_approve") {
    const orderId = args[0];
    const approved = await approveTradeOrder(env, { order_id: orderId }, "telegram_owner");
    return await sendTelegramMessage(env, chatId, formatTradeOrderForTelegram(approved), telegramMainKeyboard());
  }
  if (command === "/trade_cancel") {
    const cancelled = await cancelTradeOrder(env, args[0], "telegram_owner");
    return await sendTelegramMessage(env, chatId, formatTradeOrderForTelegram(cancelled), telegramMainKeyboard());
  }
  if (command === "/strategy") {
    const signal = await buildStrategySignal(env, { asset: "BTC", preset: "quick", horizon: Number(args[0]) || 30 });
    return await sendTelegramMessage(env, chatId, formatStrategySignalForTelegram(signal), telegramMainKeyboard());
  }
  if (command === "/strategy_deep") {
    const signal = await buildStrategySignal(env, { asset: "BTC", preset: "deep", horizon: Number(args[0]) || 30 });
    return await sendTelegramMessage(env, chatId, formatStrategySignalForTelegram(signal), telegramMainKeyboard());
  }
  if (command === "/paper_strategy") {
    const order = await createStrategyPaperOrder(env, { asset: "BTC", preset: "deep", horizon: Number(args[0]) || 30 }, "telegram_owner");
    return await sendTelegramMessage(env, chatId, formatTradeOrderForTelegram(order), telegramMainKeyboard());
  }
  if (command === "/strategy_orders") {
    const signals = await listStrategySignals(env, 5);
    return await sendTelegramMessage(env, chatId, formatStrategySignalsForTelegram(signals), telegramMainKeyboard());
  }
  return await sendTelegramMessage(env, chatId, telegramHelpText(), telegramMainKeyboard());
}

function telegramMainKeyboard(): Record<string, unknown> {
  return {
    inline_keyboard: [
      [
        { text: "Status", callback_data: "/status" },
        { text: "Quick", callback_data: "/quick" },
        { text: "Deep", callback_data: "/deep" }
      ],
      [
        { text: "Alertes", callback_data: "/alerts" },
        { text: "Dernier", callback_data: "/last" },
        { text: "Deep run", callback_data: "/deep_run" }
      ],
      [
        { text: "Signal trade", callback_data: "/trade_signal" },
        { text: "Paper trade", callback_data: "/paper_trade" },
        { text: "Ordres", callback_data: "/trade_orders" }
      ],
      [
        { text: "Strategie", callback_data: "/strategy" },
        { text: "Strategie deep", callback_data: "/strategy_deep" },
        { text: "Paper strat", callback_data: "/paper_strategy" }
      ]
    ]
  };
}

function telegramHelpText(): string {
  return [
    "Quant BTC - Commandes",
    "/status : statut ops",
    "/quick : dernier run quick",
    "/quick_fresh : force un quick frais",
    "/deep : dernier run deep",
    "/deep_run : met un deep en file d'attente",
    "/alerts : alertes modele",
    "/last : spot + derniers runs",
    "/mute 60 : silence 60 minutes",
    "/rule var95 365 > 0.40 : alerte perso",
    "/trade_signal : signal execution prudent",
    "/paper_trade : cree un ordre paper si les gates passent",
    "/trade_propose live : propose un ordre live a approuver",
    "/trade_orders : derniers ordres",
    "/strategy : score strategie quick 30j",
    "/strategy_deep : score strategie deep 30j",
    "/paper_strategy : ordre paper derive du score strategie",
    "/strategy_orders : derniers scores strategie",
    "",
    "Toutes les sorties sont probabilistes, jamais des certitudes."
  ].join("\n");
}

async function muteTelegramSession(env: Env, chatId: string, minutes: number): Promise<void> {
  if (!env.DB) {
    return;
  }
  const now = new Date();
  const mutedUntil = new Date(now.getTime() + minutes * 60 * 1000);
  await env.DB.prepare(`
    INSERT INTO telegram_sessions (chat_id, muted_until_utc, created_at_utc, updated_at_utc)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(chat_id) DO UPDATE SET muted_until_utc = excluded.muted_until_utc, updated_at_utc = excluded.updated_at_utc
  `).bind(chatId, mutedUntil.toISOString(), now.toISOString(), now.toISOString()).run();
}

async function isTelegramMuted(env: Env, chatId: string): Promise<boolean> {
  if (!env.DB) {
    return false;
  }
  try {
    const row = objectValue(await env.DB.prepare("SELECT muted_until_utc FROM telegram_sessions WHERE chat_id = ?").bind(chatId).first());
    const mutedUntil = stringOrNull(row.muted_until_utc);
    return Boolean(mutedUntil && new Date(mutedUntil).getTime() > Date.now());
  } catch {
    return false;
  }
}

async function createRuleFromTelegram(env: Env, chatId: string, args: string[]): Promise<Record<string, unknown>> {
  if (args.length < 4) {
    return {
      status: "error",
      message: "Format: /rule var95 365 > 0.40 ou /rule btc_price > 85000"
    };
  }
  let metric = args[0];
  let horizon: number | null = null;
  let operator = args[1];
  let thresholdRaw = args[2];
  if (metric !== "btc_price") {
    horizon = clampInt(parseNumber(args[1], 365), 1, 3650);
    operator = args[2];
    thresholdRaw = args[3];
  }
  const rule = await createCustomAlertRule(env, {
    chat_id: chatId,
    asset: "BTC",
    metric,
    horizon,
    operator,
    threshold: Number(thresholdRaw)
  });
  return {
    ...rule,
    message: rule.status === "created"
      ? `Regle creee: ${rule.rule_id}\n${metric}${horizon ? ` ${horizon}j` : ""} ${operator} ${thresholdRaw}`
      : rule.message
  };
}

function formatOpsStatusForTelegram(status: Record<string, unknown>): string {
  const checks = objectValue(status.checks);
  const quick = objectValue(checks.quick_cache);
  const deep = objectValue(checks.deep_cache);
  return [
    "Quant BTC - Statut",
    `Niveau: ${formatStatusLabel(status.status)}`,
    cacheSummaryLine("Cache quick", quick),
    cacheSummaryLine("Cache deep", deep),
    `UTC: ${status.checked_at_utc}`,
    `Paris: ${status.checked_at_paris}`
  ].join("\n");
}

function formatRunShortForTelegram(label: string, payload: Record<string, unknown> | null): string {
  if (!payload) {
    return `Run ${label}: absent`;
  }
  const frames = Array.isArray(payload.frames) ? payload.frames.map((item) => objectValue(item)) : [];
  const last = frames[frames.length - 1] || {};
  const distribution = objectValue(last.distribution);
  const risk = objectValue(last.risk_metrics);
  const confidence = objectValue(last.confidence);
  return [
    `Run ${label}: ${payload.archive_id || "absent"}`,
    `Spot: ${payload.reference_spot || "absent"} (${payload.reference_spot_timestamp_paris || payload.reference_spot_timestamp_utc || "timestamp absent"})`,
    `Frames: ${(payload.horizons as unknown[])?.join?.("/") || "absentes"}`,
    frames.length ? `Derniere frame ${last.horizon}j: P(up) ${formatMetricValue("prob_up", numberOrNull(distribution.prob_up))}, VaR95 ${formatMetricValue("var95", numberOrNull(risk.var_95))}, confiance ${confidence.score || "absente"}/100` : "Frame: absente",
    `Cache age: ${payload.d1_age_seconds ?? "inconnu"}s`
  ].join("\n");
}

function formatRealtimeForTelegram(realtime: Record<string, unknown>): string {
  return [
    `Spot temps reel: ${realtime.price ? `$${Number(realtime.price).toFixed(2)}` : "absent"}`,
    `Statut: ${realtime.status || "absent"} (${realtime.freshness_label || "n/a"})`,
    `Source: ${realtime.source || "absente"}`
  ].join("\n");
}

async function visibleBacktestReport(env: Env): Promise<Record<string, unknown>> {
  const [deep, quick] = await Promise.all([
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/deep"].horizons, 0),
    latestD1RunPayload(env, "BTC", ANALYSIS_PRESETS["/quick"].horizons, 0)
  ]);
  const source = deep || quick;
  const backtests = Array.isArray(source?.backtest_diagnostics) ? source.backtest_diagnostics.map((item) => objectValue(item)) : [];
  const rows = backtests.map((row) => ({
    horizon_days: row.horizon_days,
    hit_rate: row.hit_rate,
    brier_score: row.brier_score,
    calibration_error: row.calibration_error,
    interval_coverage: row.interval_coverage,
    var95_breach_rate: row.var95_breach_rate,
    expected_var95_breach_rate: row.expected_var95_breach_rate,
    random_walk_hit_rate: row.random_walk_hit_rate,
    brier_skill_vs_random_walk: row.brier_skill_vs_random_walk,
    observations: row.observations,
    interpretation: interpretBacktestRow(row)
  }));
  return {
    status: source ? "ok" : "absent",
    source_archive_id: source?.archive_id || null,
    source_report_date_utc: source?.report_date_utc || null,
    source_report_date_paris: source?.report_date_paris || null,
    data_status: source ? "real_backtest_diagnostics_from_archived_run" : "absent",
    rows,
    warning: "Backtests are diagnostics, not a guarantee of future calibration. Long-horizon VaR breaches must reduce confidence.",
    checked_at_utc: new Date().toISOString(),
    checked_at_paris: parisIso(new Date())
  };
}

function interpretBacktestRow(row: Record<string, unknown>): string {
  const breach = numberOrNull(row.var95_breach_rate);
  const expected = numberOrNull(row.expected_var95_breach_rate) || 0.05;
  const skill = numberOrNull(row.brier_skill_vs_random_walk);
  if (breach !== null && breach > expected * 2) {
    return "Risque probablement sous-calibre historiquement.";
  }
  if (skill !== null && skill < 0) {
    return "Skill inferieur au benchmark random walk sur ce diagnostic.";
  }
  return "Diagnostic utilisable avec prudence.";
}

async function dashboardHtml(env: Env): Promise<string> {
  const [ops, realtime, alerts, backtests, jobs] = await Promise.all([
    buildOpsStatus(env),
    realtimeStatus(env),
    evaluateLatestModelAlerts(env),
    visibleBacktestReport(env),
    listDeepJobs(env, 5)
  ]);
  const latestRuns = objectValue(alerts.latest_runs);
  const quick = objectValue(latestRuns.quick);
  const deep = objectValue(latestRuns.deep);
  return `<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quant BTC Ops</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif; }
    body { margin:0; background:#f6f7f9; color:#111827; }
    header { background:#0f172a; color:white; padding:24px; }
    main { max-width:1180px; margin:0 auto; padding:22px; }
    h1 { margin:0; font-size:28px; }
    h2 { font-size:18px; margin:0 0 12px; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:14px; }
    .card { background:white; border:1px solid #e5e7eb; border-radius:8px; padding:16px; box-shadow:0 1px 2px rgba(15,23,42,.04); }
    .value { font-size:24px; font-weight:700; margin:6px 0; }
    .muted { color:#667085; font-size:13px; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { text-align:left; padding:8px; border-bottom:1px solid #e5e7eb; }
    th { color:#475467; font-weight:600; }
    a { color:#155eef; text-decoration:none; }
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; background:#eef4ff; color:#1849a9; font-size:12px; }
    .warn { background:#fff7ed; color:#9a3412; }
    .crit { background:#fef2f2; color:#991b1b; }
    .ok { background:#ecfdf3; color:#027a48; }
  </style>
</head>
<body>
  <header>
    <h1>Quant BTC Model - Dashboard operationnel</h1>
    <div class="muted">UTC ${new Date().toISOString()} / Paris ${parisIso(new Date())}</div>
  </header>
  <main>
    <section class="grid">
      ${dashboardCard("Ops", formatStatusLabel(ops.status), `Worker ${WORKER_VERSION}`, statusClass(ops.status))}
      ${dashboardCard("Spot Bitget", realtime.price ? `$${Number(realtime.price).toFixed(2)}` : "Absent", `${realtime.status || "absent"} - age ${realtime.age_seconds ?? "?"}s`, statusClass(realtime.status))}
      ${dashboardCard("Alertes modele", `${alerts.issue_count || 0}`, `niveau ${formatStatusLabel(alerts.status)}`, statusClass(alerts.status))}
      ${dashboardCard("Deep jobs", String((objectValue(jobs).jobs as unknown[])?.length || 0), "file locale D1", "pill")}
    </section>
    <section class="card" style="margin-top:14px">
      <h2>Derniers runs</h2>
      <table><tr><th>Mode</th><th>Archive</th><th>Spot</th><th>Age D1</th><th>Frames</th></tr>
        ${dashboardRunRow("Quick", quick)}
        ${dashboardRunRow("Deep", deep)}
      </table>
    </section>
    <section class="card" style="margin-top:14px">
      <h2>Backtests visibles</h2>
      ${dashboardBacktestTable(objectValue(backtests).rows)}
    </section>
    <section class="grid" style="margin-top:14px">
      <div class="card"><h2>Actions</h2><p><a href="/realtime/collect">Collecter snapshot Bitget</a></p><p><a href="/model-alerts/test">Tester alerte modele Telegram</a></p><p><a href="/deep-jobs/process">Traiter un job deep</a></p></div>
      <div class="card"><h2>Legal</h2><p><a href="/legal/privacy">Privacy</a></p><p><a href="/legal/terms">Terms</a></p><p><a href="/legal/disclaimer">Disclaimer</a></p><p><a href="/legal/refund">Refund</a></p></div>
    </section>
  </main>
</body>
</html>`;
}

function dashboardCard(title: string, value: string, detail: string, cls: string): string {
  return `<div class="card"><h2>${escapeHtml(title)}</h2><div class="value">${escapeHtml(value)}</div><span class="${cls}">${escapeHtml(detail)}</span></div>`;
}

function dashboardRunRow(label: string, run: Record<string, unknown>): string {
  return `<tr><td>${escapeHtml(label)}</td><td>${escapeHtml(String(run.archive_id || "absente"))}</td><td>${escapeHtml(String(run.reference_spot || "absent"))}</td><td>${escapeHtml(String(run.d1_age_seconds ?? "inconnu"))}s</td><td>${escapeHtml(Array.isArray(run.horizons) ? run.horizons.join("/") : "absentes")}</td></tr>`;
}

function dashboardBacktestTable(rowsValue: unknown): string {
  const rows = Array.isArray(rowsValue) ? rowsValue.map((item) => objectValue(item)) : [];
  if (!rows.length) {
    return `<p class="muted">Backtests absents du dernier run archive.</p>`;
  }
  return `<table><tr><th>Horizon</th><th>Hit rate</th><th>Brier</th><th>VaR breach</th><th>Lecture</th></tr>${rows.map((row) => `<tr><td>${row.horizon_days}j</td><td>${formatMaybePercent(row.hit_rate)}</td><td>${escapeHtml(String(row.brier_score ?? "absent"))}</td><td>${formatMaybePercent(row.var95_breach_rate)}</td><td>${escapeHtml(String(row.interpretation || ""))}</td></tr>`).join("")}</table>`;
}

function statusClass(value: unknown): string {
  const status = String(value || "").toLowerCase();
  if (status === "ok") return "pill ok";
  if (status === "critical" || status === "degraded" || status === "blocked" || status === "error") return "pill crit";
  return "pill warn";
}

function formatMaybePercent(value: unknown): string {
  const number = numberOrNull(value);
  return number === null ? "absent" : formatPercent(number);
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char] || char));
}

function legalIndexHtml(): string {
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Quant BTC Legal</title></head><body><h1>Quant BTC - Documents legaux</h1><ul><li><a href="/legal/privacy">Privacy Policy</a></li><li><a href="/legal/terms">Terms</a></li><li><a href="/legal/disclaimer">Disclaimer financier</a></li><li><a href="/legal/refund">Refund Policy</a></li></ul></body></html>`;
}

function legalPageHtml(path: string): string {
  const pages: Record<string, { title: string; body: string[] }> = {
    "/legal/privacy": {
      title: "Privacy Policy",
      body: [
        "Quant BTC Model stocke uniquement les donnees operationnelles necessaires: archives de runs, metadonnees d'usage, preferences d'alertes et identifiants Telegram si fournis.",
        "Aucune cle secrete utilisateur n'est exposee dans les reponses publiques.",
        "Les donnees de marche proviennent de sources externes telles que Bitget et peuvent etre indisponibles ou retardees."
      ]
    },
    "/legal/terms": {
      title: "Terms of Service",
      body: [
        "Le service fournit des analyses probabilistes de scenarios BTC.",
        "L'utilisateur accepte que les sorties puissent etre partielles, inferred, absentes ou basees sur cache recent selon l'etat des sources.",
        "Le service peut limiter les runs deep et utiliser une file d'attente pour proteger l'infrastructure gratuite."
      ]
    },
    "/legal/disclaimer": {
      title: "Disclaimer financier",
      body: [
        "Quant BTC Model ne fournit aucun conseil financier, fiscal, juridique ou d'investissement.",
        "Les probabilites, VaR, CVaR, regimes et stress tests sont des sorties de modele, pas des certitudes ni des objectifs garantis.",
        "Toute decision financiere reste sous la responsabilite de l'utilisateur."
      ]
    },
    "/legal/refund": {
      title: "Refund Policy",
      body: [
        "Si le produit est vendu via une plateforme tierce, la politique de remboursement applicable est celle de cette plateforme sauf mention contraire.",
        "Un remboursement peut etre refuse si l'utilisateur a consomme des runs, exports ou alertes au-dela d'une periode d'essai indiquee.",
        "Les interruptions de sources externes ne garantissent pas un remboursement automatique."
      ]
    }
  };
  const page = pages[path] || pages["/legal/disclaimer"];
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(page.title)}</title><style>body{font-family:system-ui,Segoe UI,sans-serif;max-width:820px;margin:40px auto;padding:0 20px;line-height:1.55;color:#111827}a{color:#155eef}</style></head><body><p><a href="/legal">Legal</a></p><h1>${escapeHtml(page.title)}</h1>${page.body.map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`).join("")}<p><strong>Version:</strong> ${WORKER_VERSION}</p></body></html>`;
}

async function sendOpsTestAlert(env: Env): Promise<Record<string, unknown>> {
  const channels = getOpsAlertChannels(env);
  const hasDiscord = channels.discord_webhook === "configured";
  const hasTelegram = channels.telegram === "configured";
  if (!hasDiscord && !hasTelegram) {
    return {
      status: "not_configured",
      channels,
      message: "Aucun canal d'alerte n'est configure. Renseigne TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID, ou OPS_ALERT_WEBHOOK_URL/DISCORD_WEBHOOK_URL."
    };
  }
  const now = new Date();
  const payload = {
    status: "test",
    worker_version: WORKER_VERSION,
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now)
  };
  const [discord, telegram] = await Promise.all([
    sendDiscordOpsAlert(env, "Quant BTC ops TEST", "Test alert from Quant BTC Worker.", payload),
    sendTelegramOpsAlert(env, `Quant BTC - Test alerte ops\nWorker: ${WORKER_VERSION}\nUTC: ${now.toISOString()}\nParis: ${parisIso(now)}`)
  ]);
  const sent = [discord, telegram].some((item) => objectValue(item).status === "sent");
  return {
    status: sent ? "sent" : "error",
    channels,
    delivery: {
      discord,
      telegram
    },
    message: "Alerte de test envoyee aux canaux configures.",
    checked_at_utc: now.toISOString(),
    checked_at_paris: parisIso(now)
  };
}

async function shouldSendOpsAlert(env: Env, fingerprint: string, cooldownSeconds: number): Promise<boolean> {
  if (!env.DB) {
    return true;
  }
  try {
    const since = new Date(Date.now() - cooldownSeconds * 1000).toISOString();
    const { results } = await env.DB.prepare(`
      SELECT COUNT(*) AS count
      FROM ops_events
      WHERE fingerprint = ? AND created_at_utc >= ?
    `).bind(fingerprint, since).all();
    const first = objectValue(results?.[0]);
    return Number(first.count || 0) === 0;
  } catch {
    return true;
  }
}

async function persistOpsEventToD1(env: Env, event: { kind: string; status: string; severity: string; message: string; fingerprint: string; payload: Record<string, unknown> }): Promise<void> {
  if (!env.DB) {
    return;
  }
  try {
    await env.DB.prepare(`
      INSERT INTO ops_events (
        kind, status, severity, message, fingerprint, payload_json, created_at_utc
      )
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(
      event.kind,
      event.status,
      event.severity,
      event.message,
      event.fingerprint,
      JSON.stringify(event.payload),
      new Date().toISOString()
    ).run();
  } catch {
    // Ops logging is best-effort and must never block analysis endpoints.
  }
}

function compactRunPayload(result: Record<string, unknown>): Record<string, unknown> {
  const archive = objectValue(result.archive);
  const provenance = objectValue(result.provenance_summary);
  const referenceSpots = Array.isArray(provenance.reference_spots) ? provenance.reference_spots : [];
  const frames = Array.isArray(result.frames) ? result.frames.map((item) => {
    const frame = objectValue(item);
    const frameProvenance = objectValue(frame.provenance);
    return {
      horizon: frame.horizon,
      run_id: frame.run_id,
      report_date_utc: frameProvenance.report_date_utc || frameProvenance.report_date,
      report_date_paris: frameProvenance.report_date_paris,
      reference_spot: frameProvenance.reference_spot,
      reference_spot_timestamp_utc: frameProvenance.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: frameProvenance.reference_spot_timestamp_paris,
      reference_spot_source: frameProvenance.reference_spot_source,
      data_status: frame.data_status,
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
    reference_spot_timestamp_utc: objectValue(frames[0]).reference_spot_timestamp_utc,
    reference_spot_timestamp_paris: objectValue(frames[0]).reference_spot_timestamp_paris,
    reference_spot_source: objectValue(frames[0]).reference_spot_source,
    data_status: result.data_status,
    alerts: result.alerts,
    backtest_diagnostics: result.backtest_diagnostics,
    context: {
      liquidity: result.liquidity,
      options: result.options,
      etf_flow_trends: result.etf_flow_trends
    },
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

async function latestCachedAnalyzeResponse(
  env: Env,
  body: Record<string, unknown>,
  presetPath: string,
  rateLimit: Record<string, unknown>,
  maxAgeSeconds = 10 * 60,
  cacheStatus = "hit",
  requestedEndpoint = "/analyze"
): Promise<Record<string, unknown> | null> {
  if (!env.DB) {
    return null;
  }
  const asset = normalizeAsset(body.asset);
  const requestedHorizons = Array.isArray(body.horizons) ? body.horizons.map(Number) : [];
  try {
    const { results } = await env.DB.prepare(`
      SELECT payload_json, created_at_utc
      FROM quant_runs
      WHERE asset = ?
      ORDER BY created_at_utc DESC
      LIMIT 10
    `).bind(asset).all();
    for (const row of results || []) {
      const createdAt = stringOrNull(objectValue(row).created_at_utc);
      if (!createdAt || (Date.now() - new Date(createdAt).getTime()) / 1000 > maxAgeSeconds) {
        continue;
      }
      const payloadRaw = stringOrNull(objectValue(row).payload_json);
      if (!payloadRaw) {
        continue;
      }
      const payload = objectValue(JSON.parse(payloadRaw));
      const cachedHorizons = Array.isArray(payload.horizons) ? payload.horizons.map(Number) : [];
      if (!sameNumberArray(cachedHorizons, requestedHorizons)) {
        continue;
      }
      const frames = Array.isArray(payload.frames) ? payload.frames.map((item) => objectValue(item)) : [];
      if (!stringOrNull(payload.archive_id) || frames.length === 0 || !objectValue(frames[0]).reference_spot_timestamp_utc) {
        continue;
      }
      return compactCachedAnalyzeResponse(payload, presetPath, rateLimit, createdAt, maxAgeSeconds, cacheStatus, requestedEndpoint);
    }
  } catch {
    return null;
  }
  return null;
}

function compactCachedAnalyzeResponse(
  payload: Record<string, unknown>,
  presetPath: string,
  rateLimit: Record<string, unknown>,
  cachedAtUtc: string,
  maxAgeSeconds: number,
  cacheStatus: string,
  requestedEndpoint: string
): Record<string, unknown> {
  const version = objectValue(payload.version);
  const bridge = objectValue(payload.cloudflare_bridge);
  const firstFrame = objectValue(Array.isArray(payload.frames) ? payload.frames[0] : {});
  const preset = ANALYSIS_PRESETS[presetPath];
  const ageSeconds = Math.max(0, Math.round((Date.now() - new Date(cachedAtUtc).getTime()) / 1000));
  const cacheLabel = cacheStatus === "hit" ? "fresh" : "warning_age";
  return {
    status: "ok",
    asset: stringOrNull(payload.asset) || "BTC",
    model: stringOrNull(payload.model) || "ensemble",
    horizons: Array.isArray(payload.horizons) ? payload.horizons : preset.horizons,
    simulations_per_horizon: preset.simulations,
    archive_id: payload.archive_id,
    report_date_utc: payload.report_date_utc,
    report_date_paris: payload.report_date_paris,
    reference_spot: payload.reference_spot || firstFrame.reference_spot,
    reference_spot_timestamp_utc: payload.reference_spot_timestamp_utc || firstFrame.reference_spot_timestamp_utc,
    reference_spot_timestamp_paris: payload.reference_spot_timestamp_paris || firstFrame.reference_spot_timestamp_paris,
    reference_spot_source: payload.reference_spot_source || firstFrame.reference_spot_source,
    frames_count: Array.isArray(payload.frames) ? payload.frames.length : 0,
    run_ids: payload.run_ids,
    versions: {
      worker_version: WORKER_VERSION,
      worker_schema_version: SCHEMA_VERSION,
      render_api_version: version.api_version,
      render_model_version: version.model_version,
      render_schema_version: version.schema_version,
      render_git_commit: version.git_commit
    },
    response_type: cacheStatus === "hit" ? "cached_recent_d1_payload" : "cached_stale_d1_fallback_payload",
    cache: {
      status: cacheStatus,
      freshness_label: cacheLabel,
      cached_at_utc: cachedAtUtc,
      cached_at_paris: parisIso(new Date(cachedAtUtc)),
      age_seconds: ageSeconds,
      max_age_seconds: maxAgeSeconds,
      hard_block_after_seconds: maxAgeSeconds,
      note: cacheStatus === "hit"
        ? "Recent Cloudflare D1 cache used to avoid long GPT Action loading. Ask for fresh=true to force a new Render calculation."
        : "Warning-age Cloudflare D1 fallback used because the Render engine failed or deep compute quota was exhausted. This is not a fresh live run."
    },
    response_policy: {
      numeric_traceability_required: true,
      deterministic_prediction_forbidden: true,
      use_archive_for_full_detail: true,
      note: "Cached recent response; cite archive_id and report timestamp."
    },
    analysis_preset: {
      name: preset.name,
      label: preset.label,
      endpoint: presetPath,
      requested_endpoint: requestedEndpoint,
      requested_preset: preset.name,
      horizons: preset.horizons,
      simulations_per_horizon: preset.simulations,
      status: "cached_recent"
    },
    provenance: {
      source: "cloudflare_d1_recent_cache",
      archive_id: payload.archive_id,
      report_date_utc: payload.report_date_utc,
      report_date_paris: payload.report_date_paris,
      reference_spot: payload.reference_spot || firstFrame.reference_spot,
      reference_spot_timestamp_utc: payload.reference_spot_timestamp_utc || firstFrame.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: payload.reference_spot_timestamp_paris || firstFrame.reference_spot_timestamp_paris,
      reference_spot_source: payload.reference_spot_source || firstFrame.reference_spot_source,
      run_ids: payload.run_ids,
      worker_version: WORKER_VERSION,
      worker_schema_version: SCHEMA_VERSION,
      render_api_version: version.api_version,
      render_model_version: version.model_version,
      render_schema_version: version.schema_version,
      render_git_commit: version.git_commit,
      operation_path: requestedEndpoint,
      render_operation_path: bridge.render_operation_path || "/multi-run",
      timezone_policy: TIMEZONE_POLICY
    },
    data_status: payload.data_status,
    frames: payload.frames,
    alerts: compactAlerts(payload.alerts),
    backtest_diagnostics: compactBacktests(payload.backtest_diagnostics),
    context: payload.context || {},
    rate_limit: rateLimit,
    warning: "Recent cached probabilistic scenario distribution, not a deterministic forecast.",
    limitations: [
      "Recent D1 cache is used for speed; force fresh=true for a new Render calculation.",
      "Every number must be cited with archive_id, report date, run_id when frame-specific, reference spot and real/inferred/absent status.",
      "If confidence is below 50/100, directional conclusions must be described as weak or fragile.",
      "VaR and CVaR are simulated loss metrics, not guaranteed maximum losses."
    ],
    generated_at_utc: new Date().toISOString(),
    generated_at_paris: parisIso(new Date())
  };
}

function compactAnalyzeResponse(
  result: Record<string, unknown>,
  rateLimit: Record<string, unknown>,
  env: Env
): Record<string, unknown> {
  const archive = objectValue(result.archive);
  const version = objectValue(result.version);
  const bridge = objectValue(result.cloudflare_bridge);
  const preset = objectValue(result.analysis_preset);
  const frames = Array.isArray(result.frames)
    ? result.frames.map((item) => compactAnalyzeFrame(objectValue(item)))
    : [];
  const firstFrame = objectValue(frames[0]);
  const archiveId = stringOrNull(archive.archive_id) || archiveIdFromPayload(result);
  const reportDateUtc = stringOrNull(archive.report_date_utc) || stringOrNull(archive.report_date);
  const reportDateParis = stringOrNull(archive.report_date_paris);
  const hasEngineError = Boolean(result.error);
  const status = hasEngineError
    ? "error"
    : frames.length === 0
      ? "absent"
      : stringOrNull(result.status) || "ok";
  const runIds = Array.isArray(archive.run_ids)
    ? archive.run_ids
    : frames.map((frame) => objectValue(frame).run_id).filter(Boolean);
  return {
    status,
    error: result.error,
    message: result.message,
    render_status: result.render_status,
    asset: stringOrNull(result.asset) || "BTC",
    model: stringOrNull(result.model) || "ensemble",
    horizons: Array.isArray(result.horizons) ? result.horizons : frames.map((frame) => frame.horizon),
    simulations_per_horizon: numberOrNull(result.simulations_per_horizon) || numberOrNull(preset.simulations_per_horizon),
    archive_id: archiveId,
    report_date_utc: reportDateUtc,
    report_date_paris: reportDateParis,
    reference_spot: archive.reference_spot || firstFrame.reference_spot,
    reference_spot_timestamp_utc: firstFrame.reference_spot_timestamp_utc,
    reference_spot_timestamp_paris: firstFrame.reference_spot_timestamp_paris,
    reference_spot_source: firstFrame.reference_spot_source,
    frames_count: frames.length,
    run_ids: runIds,
    versions: {
      worker_version: WORKER_VERSION,
      worker_schema_version: SCHEMA_VERSION,
      render_api_version: version.api_version,
      render_model_version: version.model_version,
      render_schema_version: version.schema_version,
      render_git_commit: version.git_commit
    },
    response_type: "compact_gpt_action_payload",
    response_policy: {
      numeric_traceability_required: true,
      deterministic_prediction_forbidden: true,
      use_archive_for_full_detail: true,
      note: "This compact response is designed for GPT Actions size limits. Full raw output remains archived by archive_id when provided."
    },
    analysis_preset: {
      name: preset.name,
      label: preset.label,
      endpoint: preset.endpoint,
      requested_endpoint: preset.requested_endpoint,
      requested_preset: preset.requested_preset,
      horizons: preset.horizons,
      simulations_per_horizon: preset.simulations_per_horizon,
      status: preset.status
    },
    provenance: {
      source: "cloudflare_worker_analyze_compact",
      archive_id: archiveId,
      archive_status: archive.status,
      report_date_utc: reportDateUtc,
      report_date_paris: reportDateParis,
      reference_spot: archive.reference_spot || firstFrame.reference_spot,
      reference_spot_timestamp_utc: firstFrame.reference_spot_timestamp_utc,
      reference_spot_timestamp_paris: firstFrame.reference_spot_timestamp_paris,
      reference_spot_source: firstFrame.reference_spot_source,
      run_ids: runIds,
      worker_version: WORKER_VERSION,
      worker_schema_version: SCHEMA_VERSION,
      render_api_version: version.api_version,
      render_model_version: version.model_version,
      render_schema_version: version.schema_version,
      render_git_commit: version.git_commit,
      operation_path: bridge.operation_path,
      render_operation_path: bridge.render_operation_path,
      bridge_timestamp_utc: bridge.bridge_timestamp_utc,
      bridge_timestamp_paris: bridge.bridge_timestamp_paris,
      timezone_policy: TIMEZONE_POLICY
    },
    data_status: result.data_status,
    freshness: compactFreshness(objectValue(result.freshness)),
    frames,
    alerts: compactAlerts(result.alerts),
    backtest_diagnostics: compactBacktests(result.backtest_diagnostics),
    context: {
      liquidity: compactLiquidity(objectValue(result.liquidity)),
      options: compactOptions(objectValue(result.options)),
      etf_flow_trends: compactEtfFlows(objectValue(result.etf_flow_trends))
    },
    cloudflare_d1: result.cloudflare_d1,
    rate_limit: rateLimit,
    warning: result.warning || "Probabilistic scenario distribution only; not financial advice.",
    limitations: [
      "Compact payload: raw simulation arrays and large nested diagnostics are intentionally excluded.",
      "Every number must be cited with archive_id, report date, run_id when frame-specific, reference spot and real/inferred/absent status.",
      "If confidence is below 50/100, directional conclusions must be described as weak or fragile.",
      "VaR and CVaR are simulated loss metrics, not guaranteed maximum losses."
    ],
    generated_at_utc: new Date().toISOString(),
    generated_at_paris: parisIso(new Date())
  };
}

function compactAnalyzeFrame(frame: Record<string, unknown>): Record<string, unknown> {
  const distribution = objectValue(frame.distribution);
  const regime = objectValue(frame.regime_distribution);
  const risk = objectValue(frame.risk_metrics);
  const confidence = objectValue(frame.confidence);
  const mc = objectValue(frame.monte_carlo_error);
  const stability = objectValue(frame.multi_seed_stability);
  const provenance = objectValue(frame.provenance);
  return {
    horizon: frame.horizon,
    run_id: frame.run_id,
    report_date_utc: provenance.report_date_utc || provenance.report_date,
    report_date_paris: provenance.report_date_paris,
    reference_spot: provenance.reference_spot,
    reference_spot_timestamp_utc: provenance.reference_spot_timestamp_utc,
    reference_spot_timestamp_paris: provenance.reference_spot_timestamp_paris,
    reference_spot_source: provenance.reference_spot_source,
    data_status: frame.data_status,
    distribution: {
      p10_return: distribution.p10_return,
      median_return: distribution.median_return,
      p90_return: distribution.p90_return,
      p10_price: distribution.p10_price,
      median_price: distribution.median_price,
      p90_price: distribution.p90_price,
      prob_up: distribution.prob_up ?? distribution.probability_positive_return,
      prob_down_10: distribution.prob_down_10 ?? distribution.probability_loss_10_or_more,
      prob_down_30: distribution.prob_down_30 ?? distribution.probability_loss_30_or_more,
      prob_up_30: distribution.prob_up_30 ?? distribution.probability_gain_30_or_more
    },
    regime_distribution: {
      bull: regime.bull,
      bear: regime.bear,
      range: regime.range,
      classified_total: regime.classified_total ?? regime.sum_without_residual,
      non_classified_transition: regime.non_classified_transition,
      is_complete: regime.is_complete
    },
    risk_metrics: {
      var_95: risk.var_95,
      cvar_95: risk.cvar_95,
      var_99: risk.var_99,
      cvar_99: risk.cvar_99,
      expected_max_drawdown: risk.expected_max_drawdown ?? risk.mean_simulated_max_drawdown ?? risk.max_drawdown,
      median_max_drawdown: risk.median_max_drawdown,
      p95_max_drawdown: risk.p95_max_drawdown,
      worst_sample_drawdown: risk.worst_sample_drawdown,
      conditional_volatility: risk.conditional_volatility
    },
    monte_carlo_error: {
      status: mc.status,
      method: mc.method,
      warnings: mc.warnings
    },
    multi_seed_stability: {
      status: stability.status,
      seed_runs: stability.seed_runs,
      directional_stability: stability.directional_stability,
      bias_stability_label: stability.bias_stability_label
    },
    confidence: {
      score: confidence.score
    }
  };
}

function compactAlerts(value: unknown): unknown[] {
  return Array.isArray(value)
    ? value.slice(0, 20).map((item) => {
      const alert = objectValue(item);
      return {
        level: alert.level,
        type: alert.type,
        horizon: alert.horizon,
        value: alert.value
      };
    })
    : [];
}

function compactBacktests(value: unknown): unknown[] {
  return Array.isArray(value)
    ? value.map((item) => {
      const row = objectValue(item);
      return {
        horizon_days: row.horizon_days,
        hit_rate: row.hit_rate,
        brier_score: row.brier_score,
        calibration_error: row.calibration_error,
        interval_coverage: row.interval_coverage ?? row.p10_p90_coverage,
        var95_breach_rate: row.var95_breach_rate,
        expected_var95_breach_rate: row.expected_var95_breach_rate,
        random_walk_hit_rate: row.random_walk_hit_rate,
        brier_skill_vs_random_walk: row.brier_skill_vs_random_walk,
        observations: row.observations,
        source: row.source,
        statut: row.statut
      };
    })
    : [];
}

function compactFreshness(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    spot: value.spot,
    fundamentals: value.fundamentals,
    latest_runtime_archive: value.latest_runtime_archive
  };
}

function compactLiquidity(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    source: value.source,
    timestamp_utc: value.timestamp_utc,
    timestamp_paris: value.timestamp_paris,
    best_bid: value.best_bid,
    best_ask: value.best_ask,
    spread_bps: value.spread_bps,
    order_book_imbalance_1pct: value.order_book_imbalance_1pct
  };
}

function compactOptions(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    source: value.source,
    timestamp_utc: value.timestamp_utc,
    timestamp_paris: value.timestamp_paris,
    implied_volatility_mean: value.implied_volatility_mean,
    implied_volatility_median: value.implied_volatility_median,
    put_call_volume_ratio: value.put_call_volume_ratio,
    put_call_open_interest_ratio: value.put_call_open_interest_ratio,
    max_pain_status: value.max_pain_status
  };
}

function compactEtfFlows(value: Record<string, unknown>): Record<string, unknown> {
  return {
    status: value.status,
    source: value.source,
    timestamp_utc: value.timestamp_utc,
    timestamp_paris: value.timestamp_paris,
    latest_1d_usd_m: value.latest_1d_usd_m,
    flow_7d_usd_m: value.flow_7d_usd_m,
    flow_30d_usd_m: value.flow_30d_usd_m,
    flow_7d_acceleration_usd_m: value.flow_7d_acceleration_usd_m,
    unit: value.unit
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

function sameNumberArray(a: number[], b: number[]): boolean {
  if (a.length !== b.length) {
    return false;
  }
  return a.every((value, index) => value === b[index]);
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function numberOrNull(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function normalizeRatio(value: unknown): number | null {
  const parsed = numberOrNull(value);
  if (parsed === null) {
    return null;
  }
  return Math.abs(parsed) > 1.5 ? parsed / 100 : parsed;
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
  return checkRateLimitWithPolicy(request, limit, windowSeconds, "public");
}

function getDeepRateLimit(env: Env) {
  return {
    limit: clampInt(parseNumber(env.DEEP_RATE_LIMIT_RUNS_PER_MINUTE, 2), 1, 30),
    windowSeconds: clampInt(parseNumber(env.DEEP_RATE_LIMIT_WINDOW_SECONDS, 60), 10, 3600)
  };
}

function checkDeepRateLimit(request: Request, env: Env): RateLimitResult {
  const { limit, windowSeconds } = getDeepRateLimit(env);
  return checkRateLimitWithPolicy(request, limit, windowSeconds, "deep_compute");
}

function checkRateLimitWithPolicy(request: Request, limit: number, windowSeconds: number, scope: string): RateLimitResult {
  const now = Date.now();
  const windowMs = windowSeconds * 1000;
  const clientKey = request.headers.get("cf-connecting-ip")
    || request.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
    || "unknown-client";
  const key = `${scope}:${clientKey}`;
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
    service: workerServiceName(env),
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
    service: workerServiceName(env),
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

function parseBoolean(value: unknown, fallback = false): boolean {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (["true", "1", "yes", "y", "on"].includes(normalized)) {
      return true;
    }
    if (["false", "0", "no", "n", "off"].includes(normalized)) {
      return false;
    }
  }
  return fallback;
}

function parsePriceValue(value: unknown): number | null {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const cleaned = value.replace(/[$,\s]/g, "");
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return parseNullableNumber(value);
}

function clampInt(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, Math.round(value)));
}

function clampFloat(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function objectValue(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function workerServiceName(env: Env): string {
  return stringOrNull(env.WORKER_SERVICE_NAME) || DEFAULT_WORKER_SERVICE_NAME;
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

function deepRateLimitResponse(rateLimit: RateLimitResult) {
  return {
    error: "deep_compute_rate_limited",
    message: "Deep BTC computation quota reached. Use the recent cache, wait for the reset, or request the quick analysis.",
    rate_limit: publicRateLimit(rateLimit),
    cache_policy: {
      fresh_cache: "accepted",
      warning_age_cache: "accepted only with explicit stale/fallback warning",
      stale_over_limit: "analysis blocked"
    },
    data_status: {
      model_output: "absent",
      market_data: "absent"
    },
    warning: "No deterministic prediction was produced."
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
  return new Response(JSON.stringify(payload), {
    status,
    headers: JSON_HEADERS
  });
}

function html(markup: string, status = 200): Response {
  return new Response(markup, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "access-control-allow-origin": "*"
    }
  });
}
