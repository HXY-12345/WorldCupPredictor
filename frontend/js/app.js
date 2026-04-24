/* 核心功能：组织页面初始化、状态管理、轮询刷新、统计加载和预测交互，驱动整个前端应用运行。 */
import { createApiClient } from "./api.js";
import { fallbackMatchesPayload } from "./mock-data.js";
import { resolveApiBaseUrl } from "./runtime-config.js";
import {
  formatUpdatedTime,
  renderAnalyticsMarkup,
  renderCalendarMarkup,
  renderNoticeMarkup,
  renderScheduleMarkup
} from "./ui.js";

const POLL_INTERVAL_MS = 30_000;

function queryRequired(documentRef, selector) {
  const element = documentRef.querySelector(selector);

  if (!element) {
    throw new Error(`缺少必需的 DOM 节点: ${selector}`);
  }

  return element;
}

export function mergePredictionIntoMatches(matches, matchId, prediction) {
  return matches.map((match) =>
    match.id === matchId
      ? {
          ...match,
          prediction
        }
      : match
  );
}

export function createDefaultApiClient({
  windowRef = globalThis.window,
  documentRef = windowRef?.document,
  locationRef = windowRef?.location ?? globalThis.location,
  fetchImpl = globalThis.fetch?.bind(globalThis),
  fallbackPayload = fallbackMatchesPayload
} = {}) {
  const baseUrl = resolveApiBaseUrl({
    windowRef,
    documentRef,
    locationRef
  });

  return createApiClient({
    baseUrl,
    fetchImpl,
    fallbackPayload
  });
}

export function createWorldCupApp({
  api = createDefaultApiClient({ fallbackPayload: fallbackMatchesPayload }),
  documentRef = document,
  setIntervalFn = globalThis.setInterval?.bind(globalThis),
  clearIntervalFn = globalThis.clearInterval?.bind(globalThis),
  pollIntervalMs = POLL_INTERVAL_MS
} = {}) {
  const elements = {
    refreshButton: queryRequired(documentRef, '[data-action="refresh"]'),
    noticeRegion: queryRequired(documentRef, "#noticeRegion"),
    calendarRegion: queryRequired(documentRef, "#calendarRegion"),
    analyticsRegion: queryRequired(documentRef, "#analyticsRegion"),
    scheduleRegion: queryRequired(documentRef, "#scheduleRegion"),
    feedStatus: queryRequired(documentRef, "#feedStatus"),
    lastUpdated: queryRequired(documentRef, "#lastUpdated"),
    matchCount: queryRequired(documentRef, "#matchCount"),
    pollStatus: queryRequired(documentRef, "#pollStatus")
  };

  let pollTimer = null;
  const state = {
    matches: [],
    source: "api",
    error: "",
    lastUpdated: null,
    loading: false,
    refreshing: false,
    pendingPredictionId: null,
    pendingPredictionRunMatchId: null,
    selectedDate: null,
    collapsedDates: new Set(),
    predictionRunDetails: {},
    expandedPredictionRunMatchIds: new Set(),
    analyticsSummary: null,
    analyticsByStage: null
  };

  function syncSummary() {
    const sourceText =
      state.loading || state.refreshing
        ? "同步中"
        : state.source === "fallback"
          ? "FIFA 静态赛程"
          : "实时接口";

    elements.feedStatus.textContent = sourceText;
    elements.lastUpdated.textContent = formatUpdatedTime(state.lastUpdated);
    elements.matchCount.textContent = String(state.matches.length);
    elements.pollStatus.textContent = pollTimer ? "30 秒轮询中" : "未运行";
  }

  function render() {
    syncSummary();
    elements.noticeRegion.innerHTML = renderNoticeMarkup(state);
    elements.calendarRegion.innerHTML = renderCalendarMarkup(state);
    elements.analyticsRegion.innerHTML = renderAnalyticsMarkup({
      loading: state.loading && !state.analyticsSummary,
      summary: state.analyticsSummary,
      byStage: state.analyticsByStage
    });
    elements.scheduleRegion.innerHTML = renderScheduleMarkup(state);
  }

  function ensureSelectedDate() {
    const availableDates = [...new Set(state.matches.map((match) => match.date))];

    if (!availableDates.length) {
      state.selectedDate = null;
      return;
    }

    if (!state.selectedDate || !availableDates.includes(state.selectedDate)) {
      state.selectedDate = availableDates[0];
    }
  }

  async function loadMatches({ forceRefresh = false } = {}) {
    state.loading = !state.matches.length;
    state.refreshing = forceRefresh;
    state.error = "";
    render();

    try {
      const [matchesResult, analyticsSummary, analyticsByStage] = await Promise.all([
        forceRefresh ? api.refreshMatches() : api.fetchMatches(),
        api.fetchAnalyticsSummary(),
        api.fetchAnalyticsByStage()
      ]);

      state.matches = matchesResult.matches;
      state.lastUpdated = matchesResult.lastUpdated;
      state.source = matchesResult.source;
      state.error = matchesResult.error ?? "";
      state.analyticsSummary = analyticsSummary;
      state.analyticsByStage = analyticsByStage;
      ensureSelectedDate();
    } catch (error) {
      state.error = error instanceof Error ? error.message : "获取比赛数据失败。";
    } finally {
      state.loading = false;
      state.refreshing = false;
      render();
    }
  }

  function toggleDate(date) {
    const nextCollapsedDates = new Set(state.collapsedDates);

    if (nextCollapsedDates.has(date)) {
      nextCollapsedDates.delete(date);
    } else {
      nextCollapsedDates.add(date);
    }

    state.collapsedDates = nextCollapsedDates;
    render();
  }

  async function fetchLatestPredictionRunDetail(matchId) {
    const runListResult = await api.fetchPredictionRuns(matchId);
    const latestRun = runListResult.items[0];

    if (!latestRun) {
      return null;
    }

    return api.fetchPredictionRunDetail(latestRun.id);
  }

  async function handlePredict(matchId) {
    state.pendingPredictionId = matchId;
    state.pendingPredictionRunMatchId = matchId;
    state.error = "";
    render();

    try {
      const result = await api.predictMatch(matchId);
      state.matches = mergePredictionIntoMatches(state.matches, result.matchId, result.prediction);
      if (result.source === "fallback") {
        state.source = "fallback";
      } else {
        const predictionRunDetail = await fetchLatestPredictionRunDetail(result.matchId);
        if (predictionRunDetail) {
          state.predictionRunDetails = {
            ...state.predictionRunDetails,
            [result.matchId]: predictionRunDetail
          };
          const nextExpandedPredictionRunMatchIds = new Set(state.expandedPredictionRunMatchIds);
          nextExpandedPredictionRunMatchIds.add(result.matchId);
          state.expandedPredictionRunMatchIds = nextExpandedPredictionRunMatchIds;
        }
      }
    } catch (error) {
      state.error = error instanceof Error ? error.message : "AI 预测暂时不可用。";
    } finally {
      state.pendingPredictionId = null;
      state.pendingPredictionRunMatchId = null;
      render();
    }
  }

  async function handleTogglePredictionRun(matchId) {
    const nextExpandedPredictionRunMatchIds = new Set(state.expandedPredictionRunMatchIds);

    if (nextExpandedPredictionRunMatchIds.has(matchId)) {
      nextExpandedPredictionRunMatchIds.delete(matchId);
      state.expandedPredictionRunMatchIds = nextExpandedPredictionRunMatchIds;
      render();
      return;
    }

    if (state.predictionRunDetails[matchId]) {
      nextExpandedPredictionRunMatchIds.add(matchId);
      state.expandedPredictionRunMatchIds = nextExpandedPredictionRunMatchIds;
      render();
      return;
    }

    state.pendingPredictionRunMatchId = matchId;
    state.error = "";
    render();

    try {
      const predictionRunDetail = await fetchLatestPredictionRunDetail(matchId);
      if (!predictionRunDetail) {
        throw new Error("当前还没有可查看的预测依据。");
      }

      state.predictionRunDetails = {
        ...state.predictionRunDetails,
        [matchId]: predictionRunDetail
      };
      nextExpandedPredictionRunMatchIds.add(matchId);
      state.expandedPredictionRunMatchIds = nextExpandedPredictionRunMatchIds;
    } catch (error) {
      state.error = error instanceof Error ? error.message : "预测依据暂时不可用。";
    } finally {
      state.pendingPredictionRunMatchId = null;
      render();
    }
  }

  function handleCalendarClick(event) {
    const target = event.target.closest("[data-calendar-date]");

    if (!target) {
      return;
    }

    state.selectedDate = target.getAttribute("data-calendar-date");
    state.collapsedDates = new Set();
    render();
  }

  function handleScheduleClick(event) {
    const target = event.target.closest(
      "[data-date-toggle], [data-predict-match], [data-toggle-prediction-run]"
    );

    if (!target) {
      return;
    }

    if (target.hasAttribute("data-date-toggle")) {
      toggleDate(target.getAttribute("data-date-toggle"));
      return;
    }

    if (target.hasAttribute("data-predict-match")) {
      handlePredict(target.getAttribute("data-predict-match"));
      return;
    }

    if (target.hasAttribute("data-toggle-prediction-run")) {
      handleTogglePredictionRun(target.getAttribute("data-toggle-prediction-run"));
    }
  }

  function startPolling() {
    if (!setIntervalFn || !clearIntervalFn || pollTimer) {
      return;
    }

    pollTimer = setIntervalFn(() => {
      if ("hidden" in documentRef && documentRef.hidden) {
        return;
      }

      loadMatches();
    }, pollIntervalMs);
  }

  function stopPolling() {
    if (!pollTimer || !clearIntervalFn) {
      return;
    }

    clearIntervalFn(pollTimer);
    pollTimer = null;
  }

  function init() {
    elements.refreshButton.addEventListener("click", () => {
      loadMatches({ forceRefresh: true });
    });
    elements.calendarRegion.addEventListener("click", handleCalendarClick);
    elements.scheduleRegion.addEventListener("click", handleScheduleClick);
    startPolling();
    render();
    return loadMatches();
  }

  function destroy() {
    stopPolling();
    elements.calendarRegion.removeEventListener("click", handleCalendarClick);
    elements.scheduleRegion.removeEventListener("click", handleScheduleClick);
  }

  return {
    state,
    init,
    destroy,
    loadMatches,
    toggleDate,
    handlePredict,
    handleTogglePredictionRun
  };
}

if (typeof window !== "undefined" && typeof document !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    const app = createWorldCupApp();
    app.init();
  });
}
