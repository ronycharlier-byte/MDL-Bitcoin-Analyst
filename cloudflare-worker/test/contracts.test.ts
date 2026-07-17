import { describe, expect, it } from "vitest";

import { canonicalizeAnalysis, stableError, validateCanonicalAnalysis } from "../src/contracts";
import worker, { splitTelegramText } from "../src/index";
import sharedFixture from "../../contracts/fixtures/analysis.valid.json";

const frame = {
  horizon_days: 30,
  run_id: "run-ts-fixture",
  model_name: "ensemble",
  model_version: "fixture-v1",
  simulation_count: 5000,
  probability_up: 0.56,
  quantiles: { p10: -0.2, median: 0.03, p90: 0.3 },
  regimes: { bull: 0.3, bear: 0.2, range: 0.4, transition: 0.1 },
  risk: { var95_loss: 0.28, cvar95_loss: 0.35, var99_loss: 0.39, cvar99_loss: 0.47 },
  confidence: { score: 60 },
  monte_carlo: {},
  stability: {},
  warnings: [],
  status: "inferred"
};

describe("canonical analysis contract", () => {
  it("validates the same canonical JSON fixture as Python", () => {
    const payload = canonicalizeAnalysis(sharedFixture as unknown as Record<string, unknown>);
    expect(validateCanonicalAnalysis(payload)).toEqual([]);
  });

  it("preserves canonical probabilistic fields and validates invariants", () => {
    const payload = canonicalizeAnalysis({
      status: "ok",
      asset: "BTC",
      archive_id: "archive-ts-fixture",
      reference_spot: "$102,345.67",
      reference_spot_source: "bitget_public_market_api",
      reference_spot_timestamp_utc: "2026-07-17T12:00:00Z",
      frames: [frame],
      alerts: []
    });
    const canonicalFrame = (payload.frames as Record<string, unknown>[])[0];
    expect(canonicalFrame.probability_up).toBe(0.56);
    expect(canonicalFrame.quantiles).toEqual(frame.quantiles);
    expect(validateCanonicalAnalysis(payload)).toEqual([]);
    expect((payload.policy as Record<string, unknown>).execution_authority).toBe("none");
  });

  it("returns stable machine-readable errors", () => {
    expect(stableError("RATE_LIMITED", "Too many requests.", "req-1", true)).toEqual({
      status: "error",
      error_code: "RATE_LIMITED",
      message: "Too many requests.",
      retryable: true,
      details: {},
      request_id: "req-1"
    });
  });

  it("keeps Telegram message chunks below the platform limit", () => {
    const chunks = splitTelegramText("x".repeat(9000));
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.every((chunk) => chunk.length <= 4096)).toBe(true);
  });

  it("rejects mutation routes over GET and keeps status reads cache-only", async () => {
    const context = {} as ExecutionContext;
    const mutationResponse = await worker.fetch(new Request("https://worker.example/ops/monitor"), {}, context);
    expect(mutationResponse.status).toBe(405);
    const mutation = (await mutationResponse.json()) as Record<string, unknown>;
    expect(mutation.error_code).toBe("METHOD_NOT_ALLOWED");
    expect(mutationResponse.headers.get("x-request-id")).toBe(mutation.request_id);

    const statusResponse = await worker.fetch(
      new Request("https://worker.example/model-alerts/status?fresh=true"),
      {},
      context
    );
    expect(statusResponse.status).toBe(200);
    const status = (await statusResponse.json()) as Record<string, unknown>;
    expect((status.refresh_status as Record<string, unknown>).reason).toBe(
      "GET status endpoints are strictly cache-only"
    );
  });

  it("fails Telegram webhook authentication and idempotency closed", async () => {
    const context = {} as ExecutionContext;
    const invalidSecret = await worker.fetch(
      new Request("https://worker.example/telegram/webhook", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ update_id: 1 })
      }),
      { TELEGRAM_WEBHOOK_SECRET: "expected-secret" },
      context
    );
    expect(invalidSecret.status).toBe(401);

    const missingD1 = await worker.fetch(
      new Request("https://worker.example/telegram/webhook", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-telegram-bot-api-secret-token": "expected-secret"
        },
        body: JSON.stringify({ update_id: 1 })
      }),
      { TELEGRAM_WEBHOOK_SECRET: "expected-secret" },
      context
    );
    expect((await missingD1.json()) as Record<string, unknown>).toMatchObject({
      status: "blocked",
      reason: "d1_required_for_webhook_idempotency"
    });

    const duplicateDb = {
      prepare: () => ({
        bind: () => ({
          run: async () => ({ meta: { changes: 0 } })
        })
      })
    } as unknown as D1Database;
    const duplicate = await worker.fetch(
      new Request("https://worker.example/telegram/webhook", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-telegram-bot-api-secret-token": "expected-secret"
        },
        body: JSON.stringify({ update_id: 42, message: { date: Math.floor(Date.now() / 1000) } })
      }),
      { TELEGRAM_WEBHOOK_SECRET: "expected-secret", DB: duplicateDb },
      context
    );
    expect((await duplicate.json()) as Record<string, unknown>).toMatchObject({
      status: "duplicate",
      update_id: 42
    });

    const oversized = await worker.fetch(
      new Request("https://worker.example/telegram/webhook", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "content-length": "70000",
          "x-telegram-bot-api-secret-token": "expected-secret"
        },
        body: "{}"
      }),
      { TELEGRAM_WEBHOOK_SECRET: "expected-secret", DB: duplicateDb },
      context
    );
    expect(oversized.status).toBe(413);
    expect((await oversized.json()) as Record<string, unknown>).toMatchObject({
      status: "error",
      error_code: "INVALID_REQUEST"
    });
  });
});
