/* 核心功能：校验前端 UI 渲染函数在日历、比赛卡片和状态提示场景下的输出结构。 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  escapeHtml,
  formatUpdatedTime,
  renderCalendarMarkup,
  formatDisplayDate,
  groupMatchesByDate,
  renderAnalyticsMarkup,
  renderNoticeMarkup,
  renderScheduleMarkup
} from "../frontend/js/ui.js";
import { fallbackMatchesPayload } from "../frontend/js/mock-data.js";

test("escapeHtml escapes risky markup before rendering", () => {
  assert.equal(
    escapeHtml('<script>alert("x")</script>'),
    "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
  );
});

test("formatDisplayDate formats ISO date into short Chinese match label", () => {
  assert.equal(formatDisplayDate("2026-06-18"), "6月18日 周四");
});

test("formatUpdatedTime always renders Beijing time for prediction timestamps", () => {
  const RealDate = globalThis.Date;

  class UtcDateMock extends RealDate {
    getMonth() {
      return super.getUTCMonth();
    }

    getDate() {
      return super.getUTCDate();
    }

    getHours() {
      return super.getUTCHours();
    }

    getMinutes() {
      return super.getUTCMinutes();
    }
  }

  globalThis.Date = UtcDateMock;

  try {
    assert.equal(formatUpdatedTime("2026-04-19T12:00:00Z"), "4月19日 20:00");
  } finally {
    globalThis.Date = RealDate;
  }
});

test("groupMatchesByDate sorts groups and matches chronologically", () => {
  const scrambledMatches = [
    fallbackMatchesPayload.matches[8],
    fallbackMatchesPayload.matches[3],
    fallbackMatchesPayload.matches[2]
  ];
  const groups = groupMatchesByDate(scrambledMatches);

  assert.equal(groups.length, 2);
  assert.equal(groups[0].date, "2026-06-13");
  assert.equal(groups[0].matches[0].id, "fwc2026-m003");
  assert.equal(groups[1].date, "2026-06-15");
});

test("renderCalendarMarkup renders active date buttons with match counts", () => {
  const html = renderCalendarMarkup({
    matches: fallbackMatchesPayload.matches,
    selectedDate: "2026-06-12"
  });

  assert.match(html, /data-calendar-date="2026-06-12"/);
  assert.match(html, /calendar-day-button is-active/);
  assert.match(html, /2 场/);
});

test("renderCalendarMarkup adds championship stage classes and labels to calendar buttons", () => {
  const html = renderCalendarMarkup({
    matches: [
      fallbackMatchesPayload.matches[0],
      fallbackMatchesPayload.matches[fallbackMatchesPayload.matches.length - 1]
    ],
    selectedDate: "2026-07-20"
  });

  assert.match(html, /calendar-day-button--group-stage/);
  assert.match(html, /calendar-day-button--final/);
  assert.match(html, /calendar-day-button__stage">小组赛<\/span>/);
  assert.match(html, /calendar-day-button__stage">决赛<\/span>/);
});

test("renderCalendarMarkup maps third-place playoff into semi-final color family", () => {
  const html = renderCalendarMarkup({
    matches: [
      {
        id: "fwc2026-third-place",
        date: "2026-07-19",
        time: "03:00",
        stage: "季军赛",
        group: null,
        sort_order: 103,
        home_team: { name: "Team A", flag: "", form: [] },
        away_team: { name: "Team B", flag: "", form: [] }
      }
    ],
    selectedDate: "2026-07-19"
  });

  assert.match(html, /calendar-day-button--semi-finals/);
  assert.match(html, /calendar-day-button__stage">季军赛<\/span>/);
});

test("renderScheduleMarkup renders only the selected date group and keeps prediction actions", () => {
  const html = renderScheduleMarkup({
    matches: fallbackMatchesPayload.matches,
    loading: false,
    selectedDate: "2026-06-12",
    pendingPredictionId: "match_20260618_01"
  });

  assert.match(html, /AI 预测/);
  assert.match(html, /data-date-toggle="2026-06-12"/);
  assert.match(html, /03:00/);
  assert.match(html, /M001/);
  assert.match(html, /Mexico/);
  assert.match(html, /South Africa/);
  assert.doesNotMatch(html, /Canada/);
});

test("renderScheduleMarkup shows structured prediction metadata when available", () => {
  const html = renderScheduleMarkup({
    matches: [
      {
        ...fallbackMatchesPayload.matches[0],
        prediction: {
          home_score: 2,
          away_score: 1,
          confidence: 83,
          reasoning: "墨西哥的主场推进和控场能力更强。",
          outcome_pick: "home_win",
          total_goals_pick: 3,
          provider: "openrouter",
          model_name: "qwen/qwen3.5-flash-20260224",
          evidence_items: [
            { claim: "近期状态更稳定", source_name: "form" },
            { claim: "主场场地熟悉度更高", source_name: "venue" }
          ],
          uncertainties: ["首发名单尚未最终确认"]
        }
      }
    ],
    loading: false,
    selectedDate: "2026-06-12"
  });

  assert.match(html, /预测模型/);
  assert.match(html, /qwen\/qwen3\.5-flash-20260224/);
  assert.match(html, /胜负倾向/);
  assert.match(html, /主胜/);
  assert.match(html, /总进球/);
  assert.match(html, /预测时间/);
  assert.match(html, /依据/);
  assert.match(html, /不确定因素/);
  assert.match(html, /近期状态更稳定/);
  assert.match(html, /首发名单尚未最终确认/);
});

test("renderScheduleMarkup renders expanded prediction run detail in Chinese when available", () => {
  const html = renderScheduleMarkup({
    matches: [
      {
        ...fallbackMatchesPayload.matches[0],
        prediction: {
          home_score: 2,
          away_score: 1,
          confidence: 83,
          reasoning: "墨西哥主场推进更强。",
          outcome_pick: "home_win",
          total_goals_pick: 3,
          provider: "openrouter",
          model_name: "qwen/qwen3.5-flash-20260224",
          predicted_at: "2026-04-22T10:00:00Z",
          evidence_items: [],
          uncertainties: []
        }
      }
    ],
    loading: false,
    selectedDate: "2026-06-12",
    expandedPredictionRunMatchIds: new Set(["fwc2026-m001"]),
    predictionRunDetails: {
      "fwc2026-m001": {
        id: "predrun_001",
        triggered_at: "2026-04-22T10:00:00Z",
        planner_model: "qwen/research-model",
        synthesizer_model: "qwen/evidence-model",
        decider_model: "qwen/decider-model",
        document_count: 4,
        used_fallback_sources: true,
        search_documents_json: [
          {
            title: "Mexico vs South Africa preview",
            domain: "example.com"
          }
        ],
        evidence_bundle_json: {
          high_confidence_summary: ["墨西哥整体状态更稳。"],
          conflicts: ["部分阵容消息仍待确认。"]
        }
      }
    }
  });

  assert.match(html, /本次预测依据/);
  assert.match(html, /研究模型/);
  assert.match(html, /证据模型/);
  assert.match(html, /最终模型/);
  assert.match(html, /参考文档/);
  assert.match(html, /高置信摘要/);
  assert.match(html, /冲突因素/);
  assert.match(html, /补充来源/);
  assert.match(html, /Mexico vs South Africa preview/);
  assert.match(html, /墨西哥整体状态更稳/);
});

test("renderAnalyticsMarkup renders summary cards and stage breakdown rows", () => {
  const html = renderAnalyticsMarkup({
    loading: false,
    summary: {
      source: "api",
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
    },
    byStage: {
      source: "api",
      items: [
        {
          stage: "Group Stage",
          total_scored_matches: 4,
          no_prediction_matches: 1,
          pending_result_matches: 0,
          grade_distribution: {
            core_hit: 1,
            partial_hit: 2,
            miss: 1
          },
          dimensions: {
            outcome: { hit: 3, rate: 0.75 }
          }
        }
      ],
      total: 1
    }
  });

  assert.match(html, /预测成功率总览/);
  assert.match(html, /62.5%/);
  assert.match(html, /预测准确率/);
  assert.match(html, /按阶段/);
  assert.match(html, /核心命中/);
  assert.match(html, /部分命中/);
  assert.match(html, /未命中/);
  assert.match(html, /Group Stage/);
  assert.match(html, /75.0%/);
});

test("renderNoticeMarkup shows network errors and fallback warning together", () => {
  const html = renderNoticeMarkup({
    error: "接口暂时不可用",
    source: "fallback"
  });

  assert.match(html, /接口暂时不可用/);
  assert.match(html, /官方静态赛程/);
});

test("official fallback schedule uses FIFA schedule scale and boundaries", () => {
  assert.equal(fallbackMatchesPayload.total, 104);
  assert.equal(fallbackMatchesPayload.matches.length, 104);
  assert.equal(fallbackMatchesPayload.matches[0].date, "2026-06-12");
  assert.equal(fallbackMatchesPayload.matches[0].time, "03:00");
  assert.equal(fallbackMatchesPayload.matches[0].home_team.name, "Mexico");
  assert.equal(
    fallbackMatchesPayload.matches[fallbackMatchesPayload.matches.length - 1].date,
    "2026-07-20"
  );
  assert.equal(
    fallbackMatchesPayload.matches[fallbackMatchesPayload.matches.length - 1].time,
    "03:00"
  );
});
