/* 核心功能：负责赛程日历、比赛卡片、统计模块和页面状态提示的纯渲染逻辑。 */
const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
const OUTCOME_LABELS = {
  home_win: "主胜",
  draw: "平局",
  away_win: "客胜"
};

const STATUS_META = {
  not_started: { label: "未开始", tone: "scheduled" },
  live: { label: "进行中", tone: "live" },
  finished: { label: "已结束", tone: "finished" },
  postponed: { label: "已延期", tone: "postponed" }
};
const BEIJING_TIME_FORMATTER = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  month: "numeric",
  day: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false
});

const CALENDAR_STAGE_META = [
  {
    tone: "group-stage",
    label: "小组赛",
    rank: 1,
    patterns: ["小组赛", "group stage"]
  },
  {
    tone: "round-of-32",
    label: "32强",
    rank: 2,
    patterns: ["32强赛", "32强", "round of 32", "last 32", "round-of-32"]
  },
  {
    tone: "round-of-16",
    label: "16强",
    rank: 3,
    patterns: ["16强赛", "16强", "round of 16", "last 16", "round-of-16"]
  },
  {
    tone: "quarter-finals",
    label: "1/4决赛",
    rank: 4,
    patterns: ["1/4 决赛", "1/4决赛", "quarter-final", "quarter final", "quarter-finals"]
  },
  {
    tone: "semi-finals",
    label: "半决赛",
    rank: 5,
    patterns: ["半决赛", "semi-final", "semi final", "semi-finals"]
  },
  {
    tone: "semi-finals",
    label: "季军赛",
    rank: 5,
    patterns: ["季军赛", "third-place", "third place", "third-place play-off", "third place play-off"]
  },
  {
    tone: "final",
    label: "决赛",
    rank: 6,
    patterns: ["决赛", "final"]
  }
];

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function compareMatchDateTime(left, right) {
  if (left.date !== right.date) {
    return left.date.localeCompare(right.date);
  }

  const leftStamp = `${left.date}T${
    typeof left.time === "string" && /^\d{2}:\d{2}$/.test(left.time) ? left.time : "99:99"
  }:00`;
  const rightStamp = `${right.date}T${
    typeof right.time === "string" && /^\d{2}:\d{2}$/.test(right.time) ? right.time : "99:99"
  }:00`;

  const timeCompare = leftStamp.localeCompare(rightStamp);
  if (timeCompare !== 0) {
    return timeCompare;
  }

  if (typeof left.sort_order === "number" && typeof right.sort_order === "number") {
    return left.sort_order - right.sort_order;
  }

  return String(left.id ?? "").localeCompare(String(right.id ?? ""));
}

function renderScore(match) {
  if (match.score && typeof match.score.home === "number" && typeof match.score.away === "number") {
    return {
      home: String(match.score.home),
      away: String(match.score.away),
      detail:
        match.status === "live" && typeof match.score.minute === "number"
          ? `${match.score.minute}'`
          : match.status === "finished"
            ? "全场"
            : ""
    };
  }

  return {
    home: "对阵",
    away: "",
    detail: ""
  };
}

function formatStage(match) {
  const groupPart = match.group ? ` ${match.group}组` : "";
  return `${match.stage}${groupPart}`;
}

function formatForm(team) {
  return safeArray(team?.form).join(" / ") || "待更新";
}

function hasProbabilityBreakdown(prediction) {
  return Boolean(
    prediction?.probabilities &&
      typeof prediction.probabilities === "object" &&
      Object.keys(prediction.probabilities).length
  );
}

function renderProbabilityRows(probabilities = {}) {
  const rows = [
    { label: "主胜", value: probabilities.home_win ?? 0 },
    { label: "平局", value: probabilities.draw ?? 0 },
    { label: "客胜", value: probabilities.away_win ?? 0 }
  ];

  return `
    <div class="probability-grid">
      ${rows
        .map(
          (row) => `
            <div class="probability-row">
              <span>${row.label}</span>
              <span class="probability-row__track"><span style="width: ${row.value}%"></span></span>
              <strong>${row.value}%</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPredictionFactGrid(prediction) {
  const items = [
    {
      label: "预测模型",
      value: prediction.model_name ?? "--"
    },
    {
      label: "胜负倾向",
      value: OUTCOME_LABELS[prediction.outcome_pick] ?? prediction.outcome_pick ?? "--"
    },
    {
      label: "总进球",
      value:
        typeof prediction.total_goals_pick === "number"
          ? String(prediction.total_goals_pick)
          : "--"
    },
    {
      label: "预测时间",
      value: prediction.predicted_at ? formatUpdatedTime(prediction.predicted_at) : "--"
    }
  ];

  return `
    <div class="prediction-meta-grid">
      ${items
        .map(
          (item) => `
            <div class="prediction-meta-card">
              <span class="prediction-meta-card__label">${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.value)}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPredictionEvidence(prediction) {
  const evidenceItems = safeArray(prediction.evidence_items).slice(0, 2);
  const uncertaintyItems = safeArray(prediction.uncertainties).slice(0, 1);

  if (!evidenceItems.length && !uncertaintyItems.length) {
    return "";
  }

  return `
    <div class="prediction-evidence">
      ${
        evidenceItems.length
          ? `
            <div class="prediction-evidence__group">
              <span class="prediction-evidence__title">依据</span>
              <ul class="prediction-evidence__list">
                ${evidenceItems
                  .map(
                    (item) => `
                      <li>${escapeHtml(item.claim ?? item.source_name ?? "未提供依据")}</li>
                    `
                  )
                  .join("")}
              </ul>
            </div>
          `
          : ""
      }
      ${
        uncertaintyItems.length
          ? `
            <div class="prediction-evidence__group">
              <span class="prediction-evidence__title">不确定因素</span>
              <p>${escapeHtml(uncertaintyItems[0])}</p>
            </div>
          `
          : ""
      }
    </div>
  `;
}

function renderPredictionRunFactGrid(predictionRunDetail) {
  const items = [
    {
      label: "执行时间",
      value: predictionRunDetail?.triggered_at
        ? formatUpdatedTime(predictionRunDetail.triggered_at)
        : "--"
    },
    {
      label: "研究模型",
      value: predictionRunDetail?.planner_model ?? "--"
    },
    {
      label: "证据模型",
      value: predictionRunDetail?.synthesizer_model ?? "--"
    },
    {
      label: "最终模型",
      value: predictionRunDetail?.decider_model ?? "--"
    },
    {
      label: "参考文档",
      value: String(predictionRunDetail?.document_count ?? 0)
    },
    {
      label: "补充来源",
      value: predictionRunDetail?.used_fallback_sources ? "已使用" : "未使用"
    }
  ];

  return `
    <div class="prediction-run__meta-grid">
      ${items
        .map(
          (item) => `
            <div class="prediction-run__meta-card">
              <span class="prediction-run__meta-label">${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.value)}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderPredictionRunDocuments(predictionRunDetail) {
  const documents = safeArray(predictionRunDetail?.search_documents_json).slice(0, 2);

  if (!documents.length) {
    return "";
  }

  return `
    <div class="prediction-run__group">
      <span class="prediction-run__title">参考文档</span>
      <ul class="prediction-run__list">
        ${documents
          .map(
            (document) => `
              <li>
                <strong>${escapeHtml(document.title ?? "未命名文档")}</strong>
                <span>${escapeHtml(document.domain ?? "--")}</span>
              </li>
            `
          )
          .join("")}
      </ul>
    </div>
  `;
}

function renderPredictionRunEvidenceBundle(predictionRunDetail) {
  const evidenceBundle = predictionRunDetail?.evidence_bundle_json;
  const summaryItems = safeArray(evidenceBundle?.high_confidence_summary).slice(0, 2);
  const conflictItems = safeArray(evidenceBundle?.conflicts).slice(0, 2);

  if (!summaryItems.length && !conflictItems.length) {
    return "";
  }

  return `
    <div class="prediction-run__columns">
      ${
        summaryItems.length
          ? `
            <div class="prediction-run__group">
              <span class="prediction-run__title">高置信摘要</span>
              <ul class="prediction-run__list">
                ${summaryItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
              </ul>
            </div>
          `
          : ""
      }
      ${
        conflictItems.length
          ? `
            <div class="prediction-run__group">
              <span class="prediction-run__title">冲突因素</span>
              <ul class="prediction-run__list">
                ${conflictItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
              </ul>
            </div>
          `
          : ""
      }
    </div>
  `;
}

function renderPredictionRunDetail(predictionRunDetail) {
  if (!predictionRunDetail) {
    return "";
  }

  return `
    <section class="prediction-run">
      <div class="prediction-run__header">
        <span class="prediction-run__eyebrow">本次预测依据</span>
      </div>
      ${renderPredictionRunFactGrid(predictionRunDetail)}
      ${renderPredictionRunDocuments(predictionRunDetail)}
      ${renderPredictionRunEvidenceBundle(predictionRunDetail)}
    </section>
  `;
}

function renderPredictionCard(
  match,
  pendingPredictionId,
  predictionRunDetail,
  isPredictionRunExpanded,
  isPredictionRunLoading
) {
  const isPending = pendingPredictionId === match.id;
  const prediction = match.prediction;

  if (!prediction) {
    return `
      <section class="prediction-card">
        <div class="prediction-card__header">
          <span class="prediction-card__eyebrow">AI 预测</span>
          <button
            type="button"
            class="chip-button"
            data-predict-match="${escapeHtml(match.id)}"
            ${isPending ? "disabled" : ""}
          >
            ${isPending ? "预测中..." : "生成 AI 预测"}
          </button>
        </div>
        <div class="prediction-card__empty">
          <p>当前还没有预测结果，可立即触发生成。</p>
        </div>
      </section>
    `;
  }

  return `
    <section class="prediction-card">
      <div class="prediction-card__header">
        <span class="prediction-card__eyebrow">AI 预测</span>
        <div class="prediction-card__actions">
          <button
            type="button"
            class="chip-button"
            data-predict-match="${escapeHtml(match.id)}"
            ${isPending ? "disabled" : ""}
          >
            ${isPending ? "预测中..." : "刷新 AI 预测"}
          </button>
          <button
            type="button"
            class="chip-button chip-button--secondary"
            data-toggle-prediction-run="${escapeHtml(match.id)}"
            ${isPredictionRunLoading ? "disabled" : ""}
            aria-expanded="${isPredictionRunExpanded ? "true" : "false"}"
          >
            ${
              isPredictionRunLoading
                ? "加载依据..."
                : isPredictionRunExpanded
                  ? "收起预测依据"
                  : "查看预测依据"
            }
          </button>
        </div>
      </div>

      <div class="prediction-card__scoreboard">
        <div class="prediction-card__team">
          <p class="prediction-card__team-name">${escapeHtml(match.home_team.name)}</p>
        </div>
        <div class="prediction-card__score" aria-label="预测比分">
          <span>${prediction.home_score ?? "--"}</span>
          <span>:</span>
          <span>${prediction.away_score ?? "--"}</span>
        </div>
        <div class="prediction-card__team">
          <p class="prediction-card__team-name">${escapeHtml(match.away_team.name)}</p>
        </div>
      </div>

      <div class="prediction-card__confidence">
        <div class="prediction-card__confidence-top">
          <span>置信度</span>
          <strong>${prediction.confidence ?? 0}%</strong>
        </div>
        <div class="meter" aria-hidden="true">
          <span style="width: ${prediction.confidence ?? 0}%"></span>
        </div>
      </div>

      ${hasProbabilityBreakdown(prediction) ? renderProbabilityRows(prediction.probabilities) : renderPredictionFactGrid(prediction)}

      <p class="prediction-card__reasoning">${escapeHtml(prediction.reasoning ?? "暂无推理摘要。")}</p>

      ${renderPredictionEvidence(prediction)}
      ${isPredictionRunExpanded ? renderPredictionRunDetail(predictionRunDetail) : ""}
    </section>
  `;
}

function renderSupportingInfo(match) {
  const headToHead = match.head_to_head;
  const teamNews = [];

  for (const player of safeArray(match.key_players?.home_injured)) {
    teamNews.push(`${match.home_team.name}伤停：${player}`);
  }

  for (const player of safeArray(match.key_players?.away_suspended)) {
    teamNews.push(`${match.away_team.name}停赛：${player}`);
  }

  const historyText = headToHead
    ? `${match.home_team.name}${headToHead.home_wins}胜${headToHead.draws}平${headToHead.away_wins}负`
    : "历史交锋待更新";

  return `
    <div class="match-card__supporting">
      <p class="support-chip"><strong>场次编号：</strong>${escapeHtml(match.kickoff_label ?? "--")}</p>
      <p class="support-chip"><strong>比赛场地：</strong>${escapeHtml(match.venue ?? "待定")}</p>
      <p class="support-chip"><strong>历史交锋：</strong>${escapeHtml(historyText)}</p>
      <p class="support-chip">
        <strong>近期走势：</strong>
        ${escapeHtml(match.home_team.name)} ${escapeHtml(formatForm(match.home_team))}
        ·
        ${escapeHtml(match.away_team.name)} ${escapeHtml(formatForm(match.away_team))}
      </p>
      <ul class="support-list">
        ${
          teamNews.length
            ? teamNews
                .map((item) => `<li class="support-chip">${escapeHtml(item)}</li>`)
                .join("")
            : `<li class="support-chip">暂无关键伤停提醒</li>`
        }
      </ul>
    </div>
  `;
}

function renderMatchCard(
  match,
  pendingPredictionId,
  predictionRunDetail,
  isPredictionRunExpanded,
  isPredictionRunLoading
) {
  const statusMeta = getStatusMeta(match.status);
  const score = renderScore(match);
  const timeLabel = match.time ?? "--:--";
  const homeRank = Number.isFinite(match.home_team.fifa_rank)
    ? `<p class="team-row__rank">FIFA 排名 #${escapeHtml(match.home_team.fifa_rank)}</p>`
    : "";
  const awayRank = Number.isFinite(match.away_team.fifa_rank)
    ? `<p class="team-row__rank">FIFA 排名 #${escapeHtml(match.away_team.fifa_rank)}</p>`
    : "";

  return `
    <article class="match-card" data-match-id="${escapeHtml(match.id)}">
      <header class="match-card__header">
        <div class="match-card__header-main">
          <span class="match-card__time">${escapeHtml(timeLabel)}</span>
          <span class="status-badge status-badge--${statusMeta.tone}">${statusMeta.label}</span>
          ${score.detail ? `<span class="match-card__stage">${escapeHtml(score.detail)}</span>` : ""}
        </div>
        <span class="match-card__stage">${escapeHtml(formatStage(match))}</span>
      </header>

      <div class="match-card__body">
        <div class="teams">
          <div class="team-row">
            <div class="team-row__meta">
              <span class="team-row__flag" aria-hidden="true">${escapeHtml(match.home_team.flag ?? "")}</span>
              <div>
                <p class="team-row__name">${escapeHtml(match.home_team.name)}</p>
                ${homeRank}
              </div>
            </div>
            <span class="team-row__score ${score.away ? "" : "team-row__score--placeholder"}">
              ${score.home}
            </span>
          </div>

          <div class="team-row">
            <div class="team-row__meta">
              <span class="team-row__flag" aria-hidden="true">${escapeHtml(match.away_team.flag ?? "")}</span>
              <div>
                <p class="team-row__name">${escapeHtml(match.away_team.name)}</p>
                ${awayRank}
              </div>
            </div>
            <span class="team-row__score ${score.away ? "" : "team-row__score--placeholder"}">
              ${score.away || ""}
            </span>
          </div>

          ${renderSupportingInfo(match)}
        </div>

        ${renderPredictionCard(
          match,
          pendingPredictionId,
          predictionRunDetail,
          isPredictionRunExpanded,
          isPredictionRunLoading
        )}
      </div>
    </article>
  `;
}

function renderDateSection(
  group,
  collapsedDates,
  pendingPredictionId,
  predictionRunDetails,
  expandedPredictionRunMatchIds,
  pendingPredictionRunMatchId
) {
  const isCollapsed = collapsedDates.has(group.date);

  return `
    <section class="date-group">
      <button
        type="button"
        class="date-group__trigger"
        data-date-toggle="${group.date}"
        aria-expanded="${isCollapsed ? "false" : "true"}"
      >
        <span class="date-group__title">
          <span class="date-group__date">${escapeHtml(group.label)}</span>
          <span class="date-group__count">${group.matches.length} 场比赛</span>
        </span>
        <span class="date-group__toggle">${isCollapsed ? "展开" : "收起"}</span>
      </button>
      <div class="date-group__content ${isCollapsed ? "is-collapsed" : ""}">
        ${group.matches
          .map((match) =>
            renderMatchCard(
              match,
              pendingPredictionId,
              predictionRunDetails?.[match.id] ?? null,
              expandedPredictionRunMatchIds.has(match.id),
              pendingPredictionRunMatchId === match.id
            )
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderLoadingMarkup() {
  return `
    <div class="skeleton-grid" aria-label="加载中">
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
      <div class="skeleton-card"></div>
    </div>
  `;
}

function formatRate(rate) {
  return `${(Number(rate ?? 0) * 100).toFixed(1)}%`;
}

function renderAnalyticsKpis(summary) {
  const items = [
    { label: "已评分场次", value: summary.total_scored_matches ?? 0 },
    { label: "无赛前预测", value: summary.no_prediction_matches ?? 0 },
    { label: "待最终结果", value: summary.pending_result_matches ?? 0 },
    { label: "无效记录", value: summary.invalid_matches ?? 0 }
  ];

  return `
    <div class="analytics-kpi-grid">
      ${items
        .map(
          (item) => `
            <article class="analytics-kpi-card">
              <span>${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.value)}</strong>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function renderAnalyticsDimensions(summary) {
  const items = [
    { label: "胜负命中率", key: "outcome" },
    { label: "比分命中率", key: "exact_score" },
    { label: "主队进球数", key: "home_goals" },
    { label: "客队进球数", key: "away_goals" },
    { label: "总进球数", key: "total_goals" }
  ];

  return `
    <div class="analytics-dimension-grid">
      ${items
        .map((item) => {
          const dimension = summary.dimensions?.[item.key] ?? { hit: 0, rate: 0 };
          return `
            <article class="analytics-dimension-card">
              <span class="analytics-dimension-card__label">${escapeHtml(item.label)}</span>
              <strong>${formatRate(dimension.rate)}</strong>
              <small>命中 ${dimension.hit} 场</small>
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderGradeDistribution(summary) {
  const items = [
    { label: "核心命中", value: summary.grade_distribution?.core_hit ?? 0, tone: "core" },
    { label: "部分命中", value: summary.grade_distribution?.partial_hit ?? 0, tone: "partial" },
    { label: "未命中", value: summary.grade_distribution?.miss ?? 0, tone: "miss" }
  ];

  return `
    <div class="analytics-grade-grid">
      ${items
        .map(
          (item) => `
            <div class="analytics-grade-chip analytics-grade-chip--${item.tone}">
              <span>${item.label}</span>
              <strong>${item.value}</strong>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderStageRows(byStage) {
  const items = safeArray(byStage?.items);

  if (!items.length) {
    return `
      <div class="empty-state empty-state--compact">
        <h3>暂无阶段统计</h3>
        <p>后端统计接口接通并产生评估记录后，这里会展示各阶段命中率。</p>
      </div>
    `;
  }

  return `
    <div class="analytics-stage-list">
      ${items
        .map(
          (item) => `
            <article class="analytics-stage-row">
              <div class="analytics-stage-row__main">
                <h4>${escapeHtml(item.stage)}</h4>
                <p>已评分 ${item.total_scored_matches} 场 · 无预测 ${item.no_prediction_matches} 场</p>
              </div>
              <div class="analytics-stage-row__metric">
                <span>胜负命中率</span>
                <strong>${formatRate(item.dimensions?.outcome?.rate)}</strong>
              </div>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function formatDisplayDate(isoDate) {
  const [year, month, day] = String(isoDate).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  return `${month}月${day}日 ${WEEKDAYS[date.getUTCDay()]}`;
}

export function formatUpdatedTime(value) {
  if (!value) {
    return "--";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "--";
  }

  const parts = Object.fromEntries(
    BEIJING_TIME_FORMATTER.formatToParts(date).map((part) => [part.type, part.value])
  );

  return `${parts.month}月${parts.day}日 ${parts.hour}:${parts.minute}`;
}

export function getStatusMeta(status) {
  return STATUS_META[status] ?? STATUS_META.not_started;
}

export function formatCalendarShortDate(isoDate) {
  const [year, month, day] = String(isoDate).split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  return {
    month: `${month}月`,
    day: String(day),
    weekday: WEEKDAYS[date.getUTCDay()]
  };
}

function resolveCalendarStageMeta(matches) {
  let resolvedMeta = {
    stageTone: "general",
    stageLabel: "赛程",
    rank: 0
  };

  for (const match of safeArray(matches)) {
    const stage = String(match?.stage ?? "").trim();
    if (!stage) {
      continue;
    }

    const normalizedStage = stage.toLowerCase();
    const matchedMeta =
      CALENDAR_STAGE_META.find((item) =>
        item.patterns.some((pattern) => normalizedStage.includes(pattern))
      ) ?? {
        stageTone: "general",
        stageLabel: stage,
        rank: 0
      };

    if (matchedMeta.rank >= resolvedMeta.rank) {
      resolvedMeta = {
        stageTone: matchedMeta.tone ?? matchedMeta.stageTone,
        stageLabel: matchedMeta.label ?? matchedMeta.stageLabel,
        rank: matchedMeta.rank
      };
    }
  }

  return resolvedMeta;
}

export function groupMatchesByDate(matches) {
  const sortedMatches = [...safeArray(matches)].sort(compareMatchDateTime);
  const groups = new Map();

  for (const match of sortedMatches) {
    if (!groups.has(match.date)) {
      groups.set(match.date, []);
    }

    groups.get(match.date).push(match);
  }

  return [...groups.entries()].map(([date, dateMatches]) => ({
    ...resolveCalendarStageMeta(dateMatches),
    date,
    label: formatDisplayDate(date),
    matches: dateMatches
  }));
}

export function renderCalendarMarkup({ matches = [], selectedDate = null } = {}) {
  const groups = groupMatchesByDate(matches);

  if (!groups.length) {
    return "";
  }

  return `
    <div class="calendar-strip" role="tablist" aria-label="赛程日期">
      ${groups
        .map((group) => {
          const calendarDate = formatCalendarShortDate(group.date);
          const isActive = group.date === selectedDate;
          const buttonClasses = [
            "calendar-day-button",
            isActive ? "is-active" : "",
            `calendar-day-button--${group.stageTone}`
          ]
            .filter(Boolean)
            .join(" ");
          const buttonLabel = `${group.label} ${group.stageLabel} ${group.matches.length} 场比赛`;

          return `
            <button
              type="button"
              class="${buttonClasses}"
              data-calendar-date="${group.date}"
              role="tab"
              aria-selected="${isActive ? "true" : "false"}"
              aria-label="${escapeHtml(buttonLabel)}"
            >
              <span class="calendar-day-button__top">
                <span class="calendar-day-button__month">${calendarDate.month}</span>
                <span class="calendar-day-button__stage">${escapeHtml(group.stageLabel)}</span>
              </span>
              <strong class="calendar-day-button__day">${calendarDate.day}</strong>
              <span class="calendar-day-button__footer">
                <span class="calendar-day-button__weekday">${calendarDate.weekday}</span>
                <span class="calendar-day-button__count">${group.matches.length} 场</span>
              </span>
            </button>
          `;
        })
        .join("")}
    </div>
  `;
}

export function renderNoticeMarkup({ error = "", source = "api" } = {}) {
  const notices = [];

  if (error) {
    notices.push(`
      <div class="notice notice--danger" role="alert">
        <strong>接口提示</strong>
        <span>${escapeHtml(error)}</span>
      </div>
    `);
  }

  if (source === "fallback") {
    notices.push(`
      <div class="notice notice--warning" role="status">
        <strong>当前展示 FIFA 官方静态赛程</strong>
        <span>后端接口尚未连通，页面会继续使用本地内置的官方赛程和占位预测。</span>
      </div>
    `);
  }

  return notices.join("");
}

export function renderAnalyticsMarkup({
  loading = false,
  summary = null,
  byStage = null
} = {}) {
  if (loading && !summary) {
    return renderLoadingMarkup();
  }

  const resolvedSummary = summary ?? {
    total_scored_matches: 0,
    no_prediction_matches: 0,
    pending_result_matches: 0,
    invalid_matches: 0,
    dimensions: {},
    grade_distribution: {},
    source: "fallback",
    error: "统计接口暂不可用。"
  };

  const sourceText = resolvedSummary.source === "fallback" ? "等待后端统计接口" : "实时统计";
  const stageText = byStage?.total ? `${byStage.total} 个阶段已聚合` : "暂无阶段聚合";

  return `
    <div class="analytics-shell">
      <section class="analytics-block">
        <div class="analytics-block__header">
          <div>
            <p class="section-heading__eyebrow">预测准确率</p>
            <h3>预测成功率总览</h3>
          </div>
          <p class="analytics-block__meta">${escapeHtml(sourceText)}</p>
        </div>
        ${renderAnalyticsKpis(resolvedSummary)}
        ${renderAnalyticsDimensions(resolvedSummary)}
        ${renderGradeDistribution(resolvedSummary)}
        ${
          resolvedSummary.error
            ? `<p class="analytics-block__hint">${escapeHtml(resolvedSummary.error)}</p>`
            : ""
        }
      </section>

      <section class="analytics-block analytics-block--stages">
        <div class="analytics-block__header">
          <div>
            <p class="section-heading__eyebrow">按阶段</p>
            <h3>阶段命中拆分</h3>
          </div>
          <p class="analytics-block__meta">${escapeHtml(stageText)}</p>
        </div>
        ${renderStageRows(byStage)}
      </section>
    </div>
  `;
}

export function renderScheduleMarkup({
  matches = [],
  loading = false,
  selectedDate = null,
  collapsedDates = new Set(),
  pendingPredictionId = null,
  predictionRunDetails = {},
  expandedPredictionRunMatchIds = new Set(),
  pendingPredictionRunMatchId = null
} = {}) {
  if (loading && !matches.length) {
    return renderLoadingMarkup();
  }

  const allGroups = groupMatchesByDate(matches);
  const groups = selectedDate
    ? allGroups.filter((group) => group.date === selectedDate)
    : allGroups;

  if (!groups.length) {
    return `
      <div class="empty-state">
        <h3>当前没有可展示的比赛</h3>
        <p>请稍后刷新赛程，或等待后端同步新的比赛数据。</p>
      </div>
    `;
  }

  return groups
    .map((group) =>
      renderDateSection(
        group,
        collapsedDates,
        pendingPredictionId,
        predictionRunDetails,
        expandedPredictionRunMatchIds,
        pendingPredictionRunMatchId
      )
    )
    .join("");
}
