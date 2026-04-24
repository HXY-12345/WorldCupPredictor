# Findings & Decisions

## Current Product State
- Frontend is implemented and wired to backend APIs.
- Backend supports:
  - match schedule storage and query
  - refresh pipeline and sync audit
  - prediction versioning
  - post-match evaluation and analytics
  - Swagger / FastAPI route surface
- Latest backend regression is green:
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - result: `47 passed`

## Frontend Findings
- Frontend uses static HTML/CSS/JS without a build step.
- Frontend already consumes:
  - `GET /api/matches`
  - `POST /api/refresh`
  - `POST /api/predict/{match_id}`
  - `GET /api/analytics/summary`
  - `GET /api/analytics/by-stage`
- Frontend has fallback behavior:
  - match API failure falls back to built-in FIFA official static schedule
  - analytics API failure does not block schedule rendering

## Refresh Findings
- Refresh pipeline is already live and verified with real FIFA + OpenRouter parsing.
- Current refresh architecture:
  - FIFA official source first
  - fallback source allowed
  - first refresh bootstraps baseline
  - later refreshes apply guarded incremental updates
  - `match_changes` persists field-level change history
- Audit APIs already exist:
  - `GET /api/sync-runs`
  - `GET /api/sync-runs/{sync_run_id}`
  - `GET /api/parse-outputs/{parse_output_id}`
  - `GET /api/matches/{match_id}/changes`

## Evaluation & Analytics Findings
- Evaluation is based on regular-time score only.
- Database stores per-match evaluation results and analytics aggregates.
- Current analytics APIs:
  - `GET /api/evaluations`
  - `GET /api/evaluations/{match_id}`
  - `GET /api/analytics/summary`
  - `GET /api/analytics/by-stage`

## Real Prediction Stabilization Findings (2026-04-20)
- The original real prediction path had three runtime blockers:
  - the old system prompt pushed the model into slow, retrieval-like behavior
  - OpenRouter-side `json_schema` / `json_object` formatting increased latency further on this model
  - real responses often contained `</think>` prefixes and relaxed JSON fields that strict `json.loads(...) + Pydantic` rejected
- The stabilized production path is now:
  - fact-only prompt grounded in database input
  - default prediction config:
    - `max_tokens = 800`
    - `enable_web_plugin = false`
    - `enable_response_healing = false`
  - no OpenRouter `response_format` on the live prediction path
  - local normalization followed by strict Pydantic validation

## Real Prediction Output Normalization
- Current normalization handles:
  - `</think>` and other JSON prefixes/suffixes
  - code fences
  - string score formats such as `"1-2"`
  - relaxed outcomes such as `"Away Win"`
  - string-only `evidence_items`
  - single-string `uncertainties`
  - loose `model_meta` fields such as `timestamp`
  - nested `input_snapshot.match_facts`
  - partial `input_snapshot` values backfilled from request `match_facts`

## Real Prediction Verification (2026-04-20)
- Verified with real `backend/config/openrouter.prediction.key`.
- Isolated DB smoke test result:
  - `POST /api/predict/fwc2026-m001` returned `200`
  - `prediction_versions = 1`
  - persisted `model_name = qwen/qwen3.5-flash-20260224`
  - returned prediction summary:
    - `confidence = 55`
    - `outcome_pick = away_win`
    - `predicted_score = {"home": 1, "away": 2}`
- Conclusion:
  - Slice 4.6 real prediction end-to-end verification is complete
  - remaining work is prediction-quality improvement, not runtime unblock

## FIFA Official Schedule Research (2026-04-20)
- Official schedule source checked:
  - FIFA article: `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/updated-fifa-world-cup-2026-match-schedule-now-available`
  - FIFA inside article: `https://inside.fifa.com/news/world-cup-2026-match-schedule-fixtures-ronaldo-infantino`
  - FIFA schedule PDF: `https://digitalhub.fifa.com/asset/4b5d4417-3343-4732-9cdf-14b6662af407/FWC26-Match-Schedule_English.pdf`
- Verified findings:
  - The FIFA PDF contains all `104` match numbers with kickoff times.
  - The extracted PDF text yields a complete `match number -> time` set with no missing matches.
  - FIFA article copy explicitly references notable kickoff times in `EDT`, so the canonical schedule time base should be treated as `America/New_York` / `EDT` before converting to Beijing time.
  - The current frontend/backend schedule data still stores `time = 待定` in the backend fixture and omits Beijing conversion in the canonical schedule.
- Working rule for the upcoming update:
  - Store the canonical public-facing schedule in Beijing time for UI grouping and display.
  - Keep the official source time zone in mind when converting from FIFA schedule data to avoid date rollover mistakes.

## Beijing Schedule Implementation (2026-04-20)
- Canonical schedule has now been converted to Beijing time and synced into:
  - `backend/data/fixtures/official_schedule.json`
  - `frontend/js/official-schedule.js`
- Conversion rule used:
  - official FIFA kickoff times from the verified schedule PDF
  - source timezone interpreted as `America/New_York`
  - persisted display schedule converted to `Asia/Shanghai`
- Important behavioral changes:
  - frontend match cards now show `time` as the primary kickoff label
  - kickoff label such as `M001` is retained as supporting metadata
  - fallback calendar groups now use Beijing calendar dates, so some matches moved to the next day
  - default backend seed data now starts on `2026-06-12` Beijing time and ends on `2026-07-20`
- Backend consistency fixes:
  - refresh normalization now converts incoming `date/time/timezone` payloads into Beijing time before upsert
  - evaluation no longer treats stored schedule time as naive UTC; stored `date/time` is interpreted as Beijing time before comparing prediction cutoff
  - refresh prompt now explicitly requires Beijing-time output from the parser

## Key Code Decisions
- Real provider configuration must actually flow into request construction.
- Live prediction path should prefer local normalization over upstream structured-output enforcement for this model/provider combination.
- Dirty prediction versions must not persist on provider failure.
- `input_snapshot` should be treated as a server-owned fact snapshot and backfilled from request metadata when the model returns partial data.

## Important Files
- Backend app wiring:
  - `backend/main.py`
- Prediction provider:
  - `backend/llm/openrouter_prediction.py`
- OpenRouter client:
  - `backend/llm/openrouter.py`
- Prediction prompt:
  - `backend/services/prediction_prompt.py`
- Prediction schema and normalization:
  - `backend/services/prediction_schema.py`
- Prediction orchestration:
  - `backend/services/predictions.py`
- Prediction config:
  - `backend/config/openrouter.prediction.model.json`
- Backend tests:
  - `backend/tests/test_prediction_prompt.py`
  - `backend/tests/test_prediction_schema.py`
  - `backend/tests/test_openrouter_prediction.py`
  - `backend/tests/test_prediction_service.py`

## Remaining Backend Focus
- Improve prediction quality and evidence quality.
- Decide whether to reintroduce external evidence retrieval later with a safer provider/model strategy.
- Milestone 6 hardening remains:
  - deeper health checks
  - scheduler hardening
  - operational observability

## Accuracy-First Prediction Enhancement Findings (2026-04-22)
- The current real prediction path is runtime-stable, but prediction quality is limited by thin input context rather than provider plumbing.
- The key quality issue is architectural:
  - current prediction mainly uses database match facts
  - it does not perform pre-match web research
  - it does not build a reusable evidence bundle before final prediction
- Approved direction:
  - accuracy first
  - web-search-enhanced prediction
  - controlled source boundary
  - cautious use of odds
  - manual trigger only
  - outcome accuracy prioritized over exact score optimization

## Approved Data Boundary
- `prediction_versions` remains the source of truth for final prediction history only.
- A new `prediction_runs` object should record one complete manual prediction execution.
- `prediction_runs` should not duplicate the final prediction snapshot.
- Successful runs must point to `prediction_versions` through `prediction_version_id`.
- `matches.prediction` remains a latest-summary cache for frontend rendering.

## Approved Execution Shape
- Prediction flow should be split into three explicit stages:
  - research
  - evidence synthesis
  - final decision
- The route `POST /api/predict/{match_id}` must remain unchanged externally.
- Internally it should transition to run-based orchestration.
- The final decision is still made by the model, not by backend scoring rules.
- Historical prediction versions must not be fed back into the prediction context.

## Research Layer Constraints
- Search Planner may be model-driven.
- Agent Collector is approved as a full agent-style collector, but system-side hard limits are still required:
  - max total elapsed time
  - max fetched pages
  - max agent search rounds
  - explicit source-tier recording
  - full trace persistence
- Every manual click should perform a fresh full search; no reuse of recent search results in this phase.

## Persistence Strategy
- `prediction_runs` should use a hybrid object shape:
  - queryable scalar columns for status, timing, model names, counts, and linkage
  - JSON columns for search plan, search trace, fetched documents, and evidence bundle
- Search persistence is intentionally heavy:
  - full fetched text is stored
  - extracted evidence summaries are also stored
- This design optimizes for auditability and later replay/debug, not storage minimization.

## Core Business Rules
- When sources conflict, the system must still output an outcome prediction.
- Conflict should lower `confidence`, not block prediction.
- If evidence is thin but non-empty, prediction may proceed with lower confidence.
- Odds may influence market-view interpretation, but must not dominate the final conclusion.

## Implementation Implications
- The first safe implementation slice is data model plus orchestration shell, not real search integration.
- Existing `backend/services/predictions.py` should be narrowed to persistence responsibilities.
- New orchestration should live in a separate service to avoid mixing:
  - run lifecycle
  - research
  - evidence synthesis
  - final prediction persistence
- The current real OpenRouter prediction path is reusable as a starting point for the final decision stage, but research and evidence stages need their own contracts and tests.

## Main Risks
- A free-form Agent Collector can easily create unstable runtime and noisy source selection if not bounded tightly.
- Full-text persistence may grow quickly; JSON payload size and SQLite performance should be monitored early.
- If research, evidence, and decision stages are introduced all at once, failures will be difficult to localize.
- Therefore the implementation plan should preserve the order:
  - `prediction_runs` first
  - fake pipeline second
  - real search integration last

## Implemented In Phase A + B (2026-04-22)
- `prediction_runs` is now a real ORM-backed table.
- The prediction route still exposes the same external contract, but internally now runs through a new orchestration shell.
- Current shell behavior:
  - create a `prediction_runs` row with `running`
  - advance it to `deciding`
  - reuse prediction persistence logic to create `prediction_versions`
  - mark the run as `succeeded` or `failed`
- The current shell does not yet populate:
  - `search_plan_json`
  - `search_trace_json`
  - `search_documents_json`
  - `evidence_bundle_json`
- That is intentional; these fields are reserved for the next slice rather than being filled with fake placeholders from the wrong layer.

## New Read Surface
- New APIs now exist for execution-record inspection:
  - `GET /api/matches/{match_id}/prediction-runs`
  - `GET /api/prediction-runs/{run_id}`
- This gives the project its first prediction execution audit surface without breaking the homepage contract.

## Implemented In Phase C (2026-04-22)
- A fake research stage is now wired into the run lifecycle.
- Current run status progression is:
  - `running`
  - `researching`
  - `deciding`
  - `succeeded` / `failed`
- The fake research stage now persists:
  - `planner_model = fake-research-v1`
  - `search_plan_json`
  - `search_trace_json`
  - `search_documents_json`
  - `document_count`
  - `used_fallback_sources`
- This means the project now has a real persistence slot for future Agent Collector work, while still keeping runtime deterministic in tests.

## Accuracy-First Prediction Enhancement Update (2026-04-22)
- The prediction pipeline is now explicitly split into:
  - research
  - evidence synthesis
  - final decision
- `prediction_runs` now persists both execution-stage metadata and audit payloads:
  - `planner_model`
  - `synthesizer_model`
  - `search_plan_json`
  - `search_trace_json`
  - `search_documents_json`
  - `evidence_bundle_json`
  - `document_count`
  - `used_fallback_sources`
- Real OpenRouter integration now exists for the first two stages:
  - `OpenRouterPredictionResearcher`
  - `OpenRouterPredictionEvidenceSynthesizer`
- Default wiring behavior:
  - valid research/evidence config -> real OpenRouter stage
  - missing or invalid config -> deterministic fake fallback

## New Config Surface
- `backend/core/config.py` now exposes:
  - `prediction_research_openrouter_model_config_path`
  - `prediction_research_openrouter_key_path`
  - `prediction_research_request_timeout_seconds`
  - `prediction_evidence_openrouter_model_config_path`
  - `prediction_evidence_openrouter_key_path`
  - `prediction_evidence_request_timeout_seconds`

## Current Quality Boundary
- The collector is still model-mediated rather than a browser-level raw-page crawler.
- `search_documents_json[].content_text` should currently be understood as structured research text produced by the research stage, not guaranteed byte-for-byte raw page HTML/body.
- This is already enough for:
  - auditability
  - run replay/debug
  - evidence inspection
  - downstream decider grounding

## Latest Regression Status
- Latest backend regression is green:
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - result: `65 passed`

## Remaining Gap Before Real Search
- `evidence_bundle_json` is still empty in the live path.
- The current final prediction still comes directly from the existing provider path.
- The next architectural step is to split final prediction into:
  - research
  - evidence synthesis
  - decision

## Frontend Prediction Run Surfacing (2026-04-22)
- Frontend now supports on-demand display of the latest prediction run detail for a match.
- Current interaction shape:
  - user clicks `查看预测依据`
  - frontend requests `GET /api/matches/{match_id}/prediction-runs`
  - frontend reads the latest run id
  - frontend requests `GET /api/prediction-runs/{run_id}`
  - UI expands a compact detail block under the AI prediction card
- Current detail block shows:
  - 执行时间
  - 研究模型
  - 证据模型
  - 最终模型
  - 参考文档数
  - 是否使用补充来源
  - 最多 2 条参考文档标题
  - 高置信摘要
  - 冲突因素
- The implementation is intentionally on-demand rather than prefetch-all:
  - avoids issuing 104 场比赛的批量详情请求
  - keeps homepage initial load light
  - still gives audit visibility exactly where the user asks for it

## Phase F Live Verification Update (2026-04-22)
- A real isolated smoke test was run against:
  - `POST /api/predict/fwc2026-m001`
- Result:
  - API returned `502`
  - upstream failed in the research stage with OpenRouter `403 Key limit exceeded`
  - `prediction_runs` persisted one `failed` run with the upstream error message
  - `prediction_versions` remained empty
- Conclusion:
  - current failure handling is correct for the new three-stage pipeline
  - remaining blocker for a successful live end-to-end run is provider quota, not local orchestration
## Phase F Completion Update (2026-04-22)
- 真实预测链路已新增三类稳定性补强：
  - research / evidence 结构化输出的 JSON 包裹提取
  - research / evidence provider 失败时的本地 fallback
  - final decider JSON 解析失败时的 `response-healing` 单次重试
- 默认 OpenRouter 分阶段配置现已拆分：
  - `backend/config/openrouter.research.model.json`
  - `backend/config/openrouter.evidence.model.json`
- 默认 research / evidence 超时已调整为 45 秒，优先保证手动触发体验。
- 最新真实隔离烟测结果：
  - `POST /api/predict/fwc2026-m001` 返回 `200`
  - `prediction_runs` 成功写入，样本中 research 命中 fallback，evidence 与 decider 为真实模型
  - `prediction_versions` 成功落库
- 当前残余风险：research fallback 采用本地 deterministic 证据，稳定性更高但信息密度低于成功联网 research；后续仍可继续增强 fallback 质量。
## OpenRouter Live Prediction Chain Planning Findings (2026-04-23)
- The approved spec is narrower than the previous “improve fallback quality” direction.
- New implementation target is not better local fallback content; it is stronger observability and clearer semantics for the existing real-first pipeline.

## Confirmed Current Gaps
- `backend/models/prediction_run.py` does not yet contain:
  - `stage_trace_json`
  - `is_full_live_chain`
  - `has_any_fallback`
- `backend/repositories/prediction_runs.py` currently serializes only:
  - model names
  - document count
  - used_fallback_sources
  - error_message
  - search/evidence JSON payloads
- `backend/services/prediction_runs.py` currently records only whole-run elapsed time.
- The orchestrator does not yet persist per-stage:
  - execution mode
  - elapsed time
  - error message
- Current list/detail APIs cannot directly distinguish:
  - pure live success
  - fallback-assisted success
  - decider-fatal failure

## Implementation Implications
- The first slice should be audit-surface work, not deeper model tuning.
- `Phase L1 + L2` is the safest next cut because it changes no external write contract for prediction payloads.
- Research/evidence tightening should come only after the run schema can express `live|fallback|failed` cleanly.
- The existing real OpenRouter path is already usable; the remaining work is semantic hardening, not basic runtime enablement.

## Test Implications
- The next red/green cycle should start in:
  - `backend/tests/test_prediction_run_service.py`
  - `backend/tests/test_prediction_runs_api.py`
- Those tests should define the new canonical behaviors:
  - `stage_trace_json`
  - `is_full_live_chain`
  - `has_any_fallback`
  - decider failure leaves `prediction_versions` untouched

## OpenRouter Live-Chain Implementation Findings (2026-04-23)
- `backend/database/session.py` needed an explicit SQLite post-`create_all()` upgrade path because SQLAlchemy did not add new columns onto existing `prediction_runs` tables.
- Required legacy-added columns are now:
  - `stage_trace_json`
  - `is_full_live_chain`
  - `has_any_fallback`
- `backend/llm/openrouter.py` was still vulnerable to upstream responses that contained valid JSON plus trailing noise text such as request-id diagnostics.
- A minimal client-side recovery path using raw-response JSON extraction fixes the earlier `json.decoder.JSONDecodeError: Extra data` class of failure without changing provider-facing behavior.
- Real end-to-end verification on `fwc2026-m001` now succeeds under the new run-tracing semantics:
  - API returned `200`
  - `prediction_run.status = succeeded`
  - `prediction_version` persisted
  - `stage_trace_json` showed `research = fallback`, `evidence = live`, `decider = live`
- A follow-up real re-test on `fwc2026-m001` showed that the research stage no longer failed with `429`.
- The current blocker for observing `is_full_live_chain = true` is the 45-second research-stage timeout guard:
  - raw upstream research responses can still arrive with `200`
  - but the live researcher times out first and falls back locally
- This means the remaining gap is now timeout tuning / model latency, not rate limiting.

## DuckDuckGo Research Tool Planning Findings (2026-04-23)
- The repository currently uses `backend/requirements.txt` for Python dependencies; there is no `pyproject.toml` or Poetry/Pipenv setup to update instead.
- `backend/requirements.txt` does not currently contain any DuckDuckGo search dependency.
- `backend/tests/test_prediction_research.py` already provides a strong base to extend with red/green coverage for:
  - tool-loop success
  - multi-round search
  - fallback on tool failure
  - timeout / invalid output handling
- `backend/main.py` already isolates Research dependency injection cleanly via `build_default_prediction_researcher(settings)`, so the DuckDuckGo migration can stay inside the Research subsystem boundary.
- `backend/core/config.py` is the right place to add DuckDuckGo runtime controls because all current prediction-stage timeouts and model paths already live there.
- Per primary source package metadata on PyPI, the maintained DuckDuckGo package is `ddgs`; the older `duckduckgo_search` name has been renamed.
- Per OpenRouter official docs, tool calling should be modeled by sending a `tools` array and then looping on assistant `tool_calls` plus tool result messages, which matches the proposed local Research tool architecture.

## DuckDuckGo Research Tool Implementation Findings (2026-04-24)
- `backend/services/duckduckgo_search.py` can stay dependency-safe by lazily importing `ddgs` only inside the default factory; this prevents unrelated tests or app bootstrap from crashing before the package is installed.
- `backend/llm/openrouter.py` only needed payload-forwarding support for tool calling; no deeper response parser rewrite was necessary at this stage.
- `backend/services/prediction_research.py` can support both modes safely:
  - direct final JSON response
  - assistant `tool_calls` -> local DuckDuckGo execution -> final JSON response
- The canonical Research audit surface is now best derived from backend-executed tool calls rather than trusting model-emitted `search_trace/search_documents`.
- Full local regression remains green after the DuckDuckGo baseline implementation:
  - backend: `87 passed`
  - frontend: `26 passed`
- The current blocker for real end-to-end DuckDuckGo verification is not code correctness but missing runtime dependency:
  - current Conda environment does not yet have `ddgs` installed

## DuckDuckGo Research Verification Findings (2026-04-24)
- After `ddgs` was installed, the real blocker was not OpenRouter tool calling anymore; it was the search backend choice.
- In this environment:
  - `ddgs` with `backend="duckduckgo"` repeatedly returned no results for mainstream football queries
  - `ddgs` with `backend="duckduckgo,mojeek"` returned stable non-empty result sets
- Practical conclusion:
  - the `duckduckgo_search` tool should remain DuckDuckGo-first in interface and intent
  - but runtime backend selection must allow reachable fallback providers through the `ddgs` backend chain
- Lowering DuckDuckGo search timeout from `15s` to `5s` materially reduced worst-case research latency while still keeping successful result retrieval in this environment.
- Once research returned real documents, the next live failure moved to the decider stage:
  - the model sometimes echoed the full outer request payload into `input_snapshot`
  - this enlarged the output and increased invalid-JSON / truncation risk
- Tightening the decider prompt to keep `input_snapshot` limited to `match_facts` plus raising prediction `max_tokens` to `1200` resolved the observed live decider failure in the isolated verification run.
- Latest isolated real verification result:
  - `POST /api/predict/fwc2026-m001` returned `200`
  - `prediction_run.status = succeeded`
  - `planner_model = qwen/qwen3.6-plus-04-02`
  - `synthesizer_model = qwen/qwen3.5-flash-20260224`
  - `decider_model = qwen/qwen3.5-flash-20260224`
  - `is_full_live_chain = true`
  - `has_any_fallback = false`
  - `document_count = 50`

## OpenRouter Empty-Body Hardening Findings (2026-04-24)
- The `ValueError("Model output was empty.")` path was coming from `extract_json_object_text(...)` after the raw OpenRouter body failed both JSON parsing attempts.
- That `ValueError` bypassed the existing `json.JSONDecodeError` handling in `backend/llm/openrouter.py`, so it escaped the provider stack as an uncaught `500`.
- Wrapping the empty-body case back into `json.JSONDecodeError` restores the intended flow:
  - `OpenRouterClient` raises JSON decode failure
  - `OpenRouterPredictionProvider` converts it to `PredictionProviderResponseError`
  - the API route maps it to `502 Bad Gateway`
- Latest verification after the fix:
  - `backend/tests/test_openrouter_client.py`
  - `backend/tests/test_openrouter_prediction.py`
  - `backend/tests -q`
  all pass
