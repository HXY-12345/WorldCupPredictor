/* 核心功能：封装前端访问比赛、刷新、预测与统计接口的 API 客户端，并在失败时回退到本地数据。 */
import { cloneFallbackPayload, fallbackMatchesPayload } from "./mock-data.js";

const EMPTY_DIMENSIONS = Object.freeze({
  outcome: { hit: 0, rate: 0 },
  exact_score: { hit: 0, rate: 0 },
  home_goals: { hit: 0, rate: 0 },
  away_goals: { hit: 0, rate: 0 },
  total_goals: { hit: 0, rate: 0 }
});

const EMPTY_GRADE_DISTRIBUTION = Object.freeze({
  core_hit: 0,
  partial_hit: 0,
  miss: 0
});

function cloneData(value) {
  if (typeof structuredClone === "function") {
    return structuredClone(value);
  }

  return JSON.parse(JSON.stringify(value));
}

function normalizePredictionPayload(prediction) {
  if (!prediction || typeof prediction !== "object") {
    return null;
  }

  const predictedScore =
    prediction.predicted_score && typeof prediction.predicted_score === "object"
      ? prediction.predicted_score
      : null;
  const modelMeta =
    prediction.model_meta && typeof prediction.model_meta === "object"
      ? prediction.model_meta
      : {};

  const homeScore =
    typeof prediction.home_score === "number"
      ? prediction.home_score
      : typeof predictedScore?.home === "number"
        ? predictedScore.home
        : null;
  const awayScore =
    typeof prediction.away_score === "number"
      ? prediction.away_score
      : typeof predictedScore?.away === "number"
        ? predictedScore.away
        : null;

  return {
    ...cloneData(prediction),
    home_score: homeScore,
    away_score: awayScore,
    reasoning: prediction.reasoning ?? prediction.reasoning_summary ?? "",
    predicted_at: prediction.predicted_at ?? modelMeta.predicted_at ?? null,
    provider: prediction.provider ?? modelMeta.provider ?? null,
    model_name: prediction.model_name ?? modelMeta.model_name ?? null,
    evidence_items: Array.isArray(prediction.evidence_items) ? cloneData(prediction.evidence_items) : [],
    uncertainties: Array.isArray(prediction.uncertainties) ? cloneData(prediction.uncertainties) : [],
    probabilities:
      prediction.probabilities && typeof prediction.probabilities === "object"
        ? cloneData(prediction.probabilities)
        : null
  };
}

function normalizeMatch(match) {
  return {
    ...cloneData(match),
    prediction: normalizePredictionPayload(match?.prediction ?? null)
  };
}

function normalizeMatchesPayload(payload, source, error = "") {
  const matches = Array.isArray(payload?.matches) ? payload.matches.map(normalizeMatch) : [];

  return {
    matches,
    lastUpdated: payload?.last_updated ?? payload?.lastUpdated ?? null,
    total: payload?.total ?? matches.length,
    source,
    error
  };
}

function normalizePredictionRunSummary(item) {
  return {
    id: item?.id ?? "",
    match_id: item?.match_id ?? "",
    triggered_at: item?.triggered_at ?? null,
    finished_at: item?.finished_at ?? null,
    status: item?.status ?? "unknown",
    prediction_version_id: item?.prediction_version_id ?? null,
    planner_model: item?.planner_model ?? null,
    synthesizer_model: item?.synthesizer_model ?? null,
    decider_model: item?.decider_model ?? null,
    elapsed_ms: Number.isFinite(item?.elapsed_ms) ? item.elapsed_ms : null,
    document_count: Number.isFinite(item?.document_count) ? item.document_count : 0,
    used_fallback_sources: Boolean(item?.used_fallback_sources),
    error_message: item?.error_message ?? null
  };
}

function normalizePredictionRunListPayload(payload, source, error = "") {
  const items = Array.isArray(payload?.items)
    ? payload.items.map(normalizePredictionRunSummary)
    : [];

  return {
    items,
    total: Number.isFinite(payload?.total) ? payload.total : items.length,
    source,
    error
  };
}

function normalizePredictionRunDetailPayload(payload, source) {
  return {
    ...normalizePredictionRunSummary(payload),
    source,
    search_plan_json:
      payload?.search_plan_json && typeof payload.search_plan_json === "object"
        ? cloneData(payload.search_plan_json)
        : null,
    search_trace_json:
      payload?.search_trace_json && typeof payload.search_trace_json === "object"
        ? cloneData(payload.search_trace_json)
        : null,
    search_documents_json: Array.isArray(payload?.search_documents_json)
      ? cloneData(payload.search_documents_json)
      : [],
    evidence_bundle_json:
      payload?.evidence_bundle_json && typeof payload.evidence_bundle_json === "object"
        ? cloneData(payload.evidence_bundle_json)
        : null
  };
}

function normalizeDimension(dimension) {
  return {
    hit: Number.isFinite(dimension?.hit) ? dimension.hit : 0,
    rate: Number.isFinite(dimension?.rate) ? dimension.rate : 0
  };
}

function normalizeAnalyticsSummary(payload, source, error = "") {
  const dimensions = payload?.dimensions ?? {};
  const gradeDistribution = payload?.grade_distribution ?? {};

  return {
    total_scored_matches: Number.isFinite(payload?.total_scored_matches) ? payload.total_scored_matches : 0,
    no_prediction_matches: Number.isFinite(payload?.no_prediction_matches) ? payload.no_prediction_matches : 0,
    pending_result_matches: Number.isFinite(payload?.pending_result_matches) ? payload.pending_result_matches : 0,
    invalid_matches: Number.isFinite(payload?.invalid_matches) ? payload.invalid_matches : 0,
    dimensions: {
      outcome: normalizeDimension(dimensions.outcome ?? EMPTY_DIMENSIONS.outcome),
      exact_score: normalizeDimension(dimensions.exact_score ?? EMPTY_DIMENSIONS.exact_score),
      home_goals: normalizeDimension(dimensions.home_goals ?? EMPTY_DIMENSIONS.home_goals),
      away_goals: normalizeDimension(dimensions.away_goals ?? EMPTY_DIMENSIONS.away_goals),
      total_goals: normalizeDimension(dimensions.total_goals ?? EMPTY_DIMENSIONS.total_goals)
    },
    grade_distribution: {
      core_hit: Number.isFinite(gradeDistribution.core_hit) ? gradeDistribution.core_hit : 0,
      partial_hit: Number.isFinite(gradeDistribution.partial_hit) ? gradeDistribution.partial_hit : 0,
      miss: Number.isFinite(gradeDistribution.miss) ? gradeDistribution.miss : 0
    },
    source,
    error
  };
}

function normalizeStageAnalyticsItem(item) {
  return {
    stage: item?.stage ?? "Unknown",
    total_scored_matches: Number.isFinite(item?.total_scored_matches) ? item.total_scored_matches : 0,
    no_prediction_matches: Number.isFinite(item?.no_prediction_matches) ? item.no_prediction_matches : 0,
    pending_result_matches: Number.isFinite(item?.pending_result_matches) ? item.pending_result_matches : 0,
    invalid_matches: Number.isFinite(item?.invalid_matches) ? item.invalid_matches : 0,
    dimensions: {
      outcome: normalizeDimension(item?.dimensions?.outcome ?? EMPTY_DIMENSIONS.outcome),
      exact_score: normalizeDimension(item?.dimensions?.exact_score ?? EMPTY_DIMENSIONS.exact_score),
      home_goals: normalizeDimension(item?.dimensions?.home_goals ?? EMPTY_DIMENSIONS.home_goals),
      away_goals: normalizeDimension(item?.dimensions?.away_goals ?? EMPTY_DIMENSIONS.away_goals),
      total_goals: normalizeDimension(item?.dimensions?.total_goals ?? EMPTY_DIMENSIONS.total_goals)
    },
    grade_distribution: {
      core_hit: Number.isFinite(item?.grade_distribution?.core_hit) ? item.grade_distribution.core_hit : 0,
      partial_hit: Number.isFinite(item?.grade_distribution?.partial_hit) ? item.grade_distribution.partial_hit : 0,
      miss: Number.isFinite(item?.grade_distribution?.miss) ? item.grade_distribution.miss : 0
    }
  };
}

function normalizeAnalyticsByStagePayload(payload, source, error = "") {
  const items = Array.isArray(payload?.items) ? payload.items.map(normalizeStageAnalyticsItem) : [];

  return {
    items,
    total: Number.isFinite(payload?.total) ? payload.total : items.length,
    source,
    error
  };
}

function buildUrl(baseUrl, path) {
  if (!baseUrl) {
    return path;
  }

  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

export function createApiClient({
  baseUrl = "",
  fetchImpl = globalThis.fetch?.bind(globalThis),
  fallbackPayload = fallbackMatchesPayload
} = {}) {
  if (!fetchImpl) {
    throw new Error("当前环境不支持 fetch，请提供 fetchImpl。");
  }

  async function requestJson(path, options = {}) {
    const headers = {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers ?? {})
    };

    const response = await fetchImpl(buildUrl(baseUrl, path), {
      ...options,
      headers
    });

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`);
    }

    return response.json();
  }

  function buildFallbackMatchesResult(message) {
    return normalizeMatchesPayload(
      cloneData(fallbackPayload ?? cloneFallbackPayload()),
      "fallback",
      message
    );
  }

  function buildFallbackAnalyticsSummary(message) {
    return normalizeAnalyticsSummary({}, "fallback", message);
  }

  function buildFallbackAnalyticsByStage(message) {
    return normalizeAnalyticsByStagePayload({}, "fallback", message);
  }

  return {
    async fetchMatches() {
      try {
        const payload = await requestJson("/api/matches");
        return normalizeMatchesPayload(payload, "api");
      } catch (error) {
        return buildFallbackMatchesResult("实时接口暂不可用，当前展示 FIFA 官方静态赛程。");
      }
    },

    async refreshMatches() {
      try {
        const refreshPayload = await requestJson("/api/refresh", { method: "POST" });

        if (Array.isArray(refreshPayload?.matches)) {
          return normalizeMatchesPayload(refreshPayload, "api");
        }

        return this.fetchMatches();
      } catch (error) {
        return buildFallbackMatchesResult("刷新接口暂不可用，当前展示 FIFA 官方静态赛程。");
      }
    },

    async predictMatch(matchId) {
      try {
        const payload = await requestJson(`/api/predict/${encodeURIComponent(matchId)}`, {
          method: "POST"
        });

        return {
          matchId: payload?.match_id ?? matchId,
          prediction: normalizePredictionPayload(payload?.prediction ?? null),
          cached: Boolean(payload?.cached),
          source: "api"
        };
      } catch (error) {
        const fallbackMatch = (fallbackPayload?.matches ?? []).find(
          (match) => match.id === matchId
        );

        if (!fallbackMatch?.prediction) {
          throw new Error("AI 预测暂时不可用。");
        }

        return {
          matchId,
          prediction: normalizePredictionPayload(cloneData(fallbackMatch.prediction)),
          cached: true,
          source: "fallback"
        };
      }
    },

    async fetchPredictionRuns(matchId) {
      const payload = await requestJson(
        `/api/matches/${encodeURIComponent(matchId)}/prediction-runs`
      );
      return normalizePredictionRunListPayload(payload, "api");
    },

    async fetchPredictionRunDetail(runId) {
      const payload = await requestJson(
        `/api/prediction-runs/${encodeURIComponent(runId)}`
      );
      return normalizePredictionRunDetailPayload(payload, "api");
    },

    async fetchAnalyticsSummary() {
      try {
        const payload = await requestJson("/api/analytics/summary");
        return normalizeAnalyticsSummary(payload, "api");
      } catch (error) {
        return buildFallbackAnalyticsSummary("统计接口暂不可用，命中率模块使用空白占位。");
      }
    },

    async fetchAnalyticsByStage() {
      try {
        const payload = await requestJson("/api/analytics/by-stage");
        return normalizeAnalyticsByStagePayload(payload, "api");
      } catch (error) {
        return buildFallbackAnalyticsByStage("阶段统计接口暂不可用，命中率模块使用空白占位。");
      }
    }
  };
}
