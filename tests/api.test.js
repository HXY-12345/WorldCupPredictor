/* 核心功能：校验前端 API 客户端、默认配置解析和失败回退行为。 */
import test from "node:test";
import assert from "node:assert/strict";

import { createApiClient } from "../frontend/js/api.js";
import { createDefaultApiClient } from "../frontend/js/app.js";
import { fallbackMatchesPayload } from "../frontend/js/mock-data.js";
import { resolveApiBaseUrl } from "../frontend/js/runtime-config.js";

test("resolveApiBaseUrl prefers explicit runtime config", () => {
  const result = resolveApiBaseUrl({
    windowRef: { WORLDCUP_API_BASE_URL: "http://127.0.0.1:8010" },
    locationRef: {
      protocol: "http:",
      hostname: "127.0.0.1",
      port: "3000"
    }
  });

  assert.equal(result, "http://127.0.0.1:8010");
});

test("resolveApiBaseUrl falls back to local backend port for localhost development", () => {
  const result = resolveApiBaseUrl({
    locationRef: {
      protocol: "http:",
      hostname: "127.0.0.1",
      port: "3000"
    }
  });

  assert.equal(result, "http://127.0.0.1:8000");
});

test("createDefaultApiClient wires resolved runtime base url into requests", async () => {
  const requests = [];
  const client = createDefaultApiClient({
    windowRef: { WORLDCUP_API_BASE_URL: "http://127.0.0.1:8000" },
    locationRef: {
      protocol: "http:",
      hostname: "127.0.0.1",
      port: "3000"
    },
    fetchImpl: async (url) => {
      requests.push(url);
      return new Response(
        JSON.stringify({
          matches: [],
          last_updated: "2026-06-18T12:30:00Z",
          total: 0
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      );
    },
    fallbackPayload: fallbackMatchesPayload
  });

  await client.fetchMatches();

  assert.equal(requests[0], "http://127.0.0.1:8000/api/matches");
});

test("fetchMatches returns normalized API payload when backend responds normally", async () => {
  const expectedPayload = {
    matches: [fallbackMatchesPayload.matches[0]],
    last_updated: "2026-06-18T12:30:00Z",
    total: 1
  };

  const client = createApiClient({
    fetchImpl: async () =>
      new Response(JSON.stringify(expectedPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      }),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchMatches();

  assert.equal(result.source, "api");
  assert.equal(result.matches.length, 1);
  assert.equal(result.lastUpdated, "2026-06-18T12:30:00Z");
});

test("fetchMatches normalizes structured backend prediction payloads", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          matches: [
            {
              ...fallbackMatchesPayload.matches[0],
              prediction: {
                predicted_score: { home: 2, away: 1 },
                outcome_pick: "home_win",
                total_goals_pick: 3,
                confidence: 83,
                reasoning_summary: "Mexico looks stronger at home.",
                evidence_items: [
                  { claim: "Recent form edge", source_name: "form" },
                  { claim: "Venue familiarity", source_name: "venue" }
                ],
                uncertainties: ["Lineup not confirmed"],
                model_meta: {
                  provider: "openrouter",
                  model_name: "qwen/qwen3.5-flash-20260224",
                  predicted_at: "2026-04-19T12:00:00Z"
                }
              }
            }
          ],
          last_updated: "2026-06-18T12:30:00Z",
          total: 1
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchMatches();

  assert.equal(result.matches[0].prediction.home_score, 2);
  assert.equal(result.matches[0].prediction.away_score, 1);
  assert.equal(result.matches[0].prediction.reasoning, "Mexico looks stronger at home.");
  assert.equal(result.matches[0].prediction.provider, "openrouter");
  assert.equal(result.matches[0].prediction.model_name, "qwen/qwen3.5-flash-20260224");
  assert.equal(result.matches[0].prediction.evidence_items.length, 2);
});

test("fetchMatches falls back to local sample payload when backend request fails", async () => {
  const client = createApiClient({
    fetchImpl: async () => {
      throw new Error("network down");
    },
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchMatches();

  assert.equal(result.source, "fallback");
  assert.equal(result.matches.length, fallbackMatchesPayload.matches.length);
  assert.equal(result.total, fallbackMatchesPayload.matches.length);
});

test("predictMatch posts to the expected endpoint and returns prediction data", async () => {
  const requests = [];
  const client = createApiClient({
    fetchImpl: async (url, options = {}) => {
      requests.push({ url, options });

      return new Response(
        JSON.stringify({
          match_id: "match_20260618_01",
          prediction: {
            home_score: 3,
            away_score: 1,
            confidence: 81,
            probabilities: {
              home_win: 63,
              draw: 22,
              away_win: 15
            },
            reasoning: "主队压迫更强",
            predicted_at: "2026-06-18T15:00:00Z"
          },
          cached: false
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      );
    },
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.predictMatch("match_20260618_01");

  assert.equal(requests[0].url, "/api/predict/match_20260618_01");
  assert.equal(requests[0].options.method, "POST");
  assert.equal(result.prediction.home_score, 3);
  assert.equal(result.cached, false);
});

test("predictMatch normalizes structured prediction payload from backend", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          match_id: "fwc2026-m001",
          prediction: {
            predicted_score: { home: 2, away: 1 },
            outcome_pick: "home_win",
            total_goals_pick: 3,
            confidence: 83,
            reasoning_summary: "Mexico should control the match.",
            evidence_items: [{ claim: "Higher FIFA rank", source_name: "rank" }],
            uncertainties: ["Late injury checks"],
            model_meta: {
              provider: "openrouter",
              model_name: "qwen/qwen3.5-flash-20260224",
              predicted_at: "2026-04-19T12:00:00Z"
            }
          },
          cached: false
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.predictMatch("fwc2026-m001");

  assert.equal(result.prediction.home_score, 2);
  assert.equal(result.prediction.away_score, 1);
  assert.equal(result.prediction.reasoning, "Mexico should control the match.");
  assert.equal(result.prediction.provider, "openrouter");
  assert.equal(result.prediction.model_name, "qwen/qwen3.5-flash-20260224");
  assert.deepEqual(result.prediction.evidence_items[0], {
    claim: "Higher FIFA rank",
    source_name: "rank"
  });
});

test("fetchPredictionRuns returns normalized run list payload", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          items: [
            {
              id: "predrun_001",
              match_id: "fwc2026-m001",
              triggered_at: "2026-04-22T10:00:00Z",
              finished_at: "2026-04-22T10:00:08Z",
              status: "succeeded",
              prediction_version_id: 3,
              planner_model: "qwen/research-model",
              synthesizer_model: "qwen/evidence-model",
              decider_model: "qwen/decider-model",
              elapsed_ms: 8450,
              document_count: 4,
              used_fallback_sources: true,
              error_message: null
            }
          ],
          total: 1
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchPredictionRuns("fwc2026-m001");

  assert.equal(result.source, "api");
  assert.equal(result.total, 1);
  assert.equal(result.items[0].id, "predrun_001");
  assert.equal(result.items[0].planner_model, "qwen/research-model");
  assert.equal(result.items[0].used_fallback_sources, true);
});

test("fetchPredictionRunDetail returns normalized run detail payload", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          id: "predrun_001",
          match_id: "fwc2026-m001",
          triggered_at: "2026-04-22T10:00:00Z",
          finished_at: "2026-04-22T10:00:08Z",
          status: "succeeded",
          prediction_version_id: 3,
          planner_model: "qwen/research-model",
          synthesizer_model: "qwen/evidence-model",
          decider_model: "qwen/decider-model",
          elapsed_ms: 8450,
          document_count: 4,
          used_fallback_sources: true,
          error_message: null,
          search_plan_json: {
            queries: [{ topic: "preview", query: "Mexico vs South Africa preview" }]
          },
          search_trace_json: {
            completed: true,
            round_count: 1
          },
          search_documents_json: [
            {
              title: "Mexico vs South Africa preview",
              domain: "example.com",
              url: "https://example.com/preview",
              content_text: "Mexico enters with stronger recent form."
            }
          ],
          evidence_bundle_json: {
            high_confidence_summary: ["墨西哥整体状态更稳。"],
            conflicts: ["部分阵容消息仍待确认。"]
          }
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchPredictionRunDetail("predrun_001");

  assert.equal(result.source, "api");
  assert.equal(result.id, "predrun_001");
  assert.equal(result.search_documents_json.length, 1);
  assert.equal(result.evidence_bundle_json.high_confidence_summary[0], "墨西哥整体状态更稳。");
});

test("fetchAnalyticsSummary returns normalized summary payload when backend responds normally", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          total_scored_matches: 8,
          no_prediction_matches: 2,
          pending_result_matches: 1,
          invalid_matches: 0,
          dimensions: {
            outcome: { hit: 5, rate: 0.625 },
            exact_score: { hit: 2, rate: 0.25 },
            home_goals: { hit: 3, rate: 0.375 },
            away_goals: { hit: 4, rate: 0.5 },
            total_goals: { hit: 4, rate: 0.5 }
          },
          grade_distribution: {
            core_hit: 2,
            partial_hit: 3,
            miss: 3
          }
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchAnalyticsSummary();

  assert.equal(result.source, "api");
  assert.equal(result.total_scored_matches, 8);
  assert.equal(result.dimensions.outcome.rate, 0.625);
  assert.equal(result.grade_distribution.partial_hit, 3);
});

test("fetchAnalyticsSummary falls back to empty summary when backend request fails", async () => {
  const client = createApiClient({
    fetchImpl: async () => {
      throw new Error("network down");
    },
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchAnalyticsSummary();

  assert.equal(result.source, "fallback");
  assert.equal(result.total_scored_matches, 0);
  assert.equal(result.dimensions.outcome.rate, 0);
});

test("fetchAnalyticsByStage returns normalized stage payload when backend responds normally", async () => {
  const client = createApiClient({
    fetchImpl: async () =>
      new Response(
        JSON.stringify({
          items: [
            {
              stage: "Group Stage",
              total_scored_matches: 4,
              no_prediction_matches: 1,
              pending_result_matches: 0,
              invalid_matches: 0,
              dimensions: {
                outcome: { hit: 3, rate: 0.75 },
                exact_score: { hit: 1, rate: 0.25 },
                home_goals: { hit: 2, rate: 0.5 },
                away_goals: { hit: 2, rate: 0.5 },
                total_goals: { hit: 2, rate: 0.5 }
              },
              grade_distribution: { core_hit: 1, partial_hit: 2, miss: 1 }
            }
          ],
          total: 1
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" }
        }
      ),
    fallbackPayload: fallbackMatchesPayload
  });

  const result = await client.fetchAnalyticsByStage();

  assert.equal(result.source, "api");
  assert.equal(result.total, 1);
  assert.equal(result.items[0].stage, "Group Stage");
  assert.equal(result.items[0].dimensions.outcome.hit, 3);
});
