# Task Plan: WorldCup Predictor 后端实现计划

## Goal
基于 [2026-04-18-worldcup-backend-design.md](D:/develop/WorldCup/docs/superpowers/specs/2026-04-18-worldcup-backend-design.md) 制定一套可执行的后端开发计划，覆盖项目骨架、数据库、数据同步、预测、评估、统计、测试与前端联调顺序，并明确每个阶段的交付物、依赖关系和验证方式。

## Current Phase
Accuracy-First Prediction Enhancement / DuckDuckGo Research D6 Complete / Live Chain Verified

## Phases

### Phase 1: Context Reset & Constraint Check
- [x] 接管已有 planning files，确认当前上下文
- [x] 对齐已批准的 backend spec
- [x] 确认现有前端 API 契约和仓库现状
- **Status:** complete

### Phase 2: Define Implementation Order
- [x] 确定后端推荐技术栈与目录结构
- [x] 确定按“可运行切片”推进的实现顺序
- [x] 明确每阶段完成标准和阻塞关系
- **Status:** complete

### Phase 3: Break Down Phase-by-Phase Work
- [x] 拆分基础设施、同步、预测、评估、统计、联调六大块
- [x] 为每块列出核心文件、接口、测试和风险
- [x] 标记哪些任务适合先做、哪些必须后置
- **Status:** complete

### Phase 4: Verification Strategy
- [x] 规划单元测试、集成测试、接口测试和回归测试顺序
- [x] 明确每阶段最小验证命令与预期结果
- [x] 明确假数据、夹具和手工验收路径
- **Status:** complete

### Phase 5: Delivery Plan
- [x] 输出完整实施路线图
- [x] 记录关键决策、已知风险和非目标
- [x] 同步 progress.md 与 findings.md，形成可继续执行的计划基线
- **Status:** complete

## Key Questions
1. 如何让后端尽快和现有前端联通，而不是等全部能力做完后再一次性接入？
2. 哪些能力必须先打通才能支持后续开发复用，例如数据库、仓储层和统一 schema？
3. LLM 主解析器是核心能力，如何先设计可替换接口，以便没有真实模型时也能完成开发和测试？

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 规划目标限定为“实施计划”，不开始编码 | 用户当前只要求 planning-with-files 输出开发计划 |
| 第一优先级是兼容现有前端 `/api/matches`、`POST /api/refresh`、`POST /api/predict/{match_id}` | 前端已存在并依赖这些接口 |
| 后端按“基础设施 -> 同步 -> 预测 -> 评估 -> 统计 -> 前端联调”顺序推进 | 这样依赖链最短，且每一阶段都能形成可验证切片 |
| 数据同步、预测、评估分别独立成域模块 | 与已批准 spec 一致，后续可测试、可替换、可扩展 |
| 测试策略跟随实现切片逐步补齐，不等最后统一补测 | 降低返工风险，保证每阶段都可验收 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `git commit` 无法创建 `.git/index.lock` | 1 | 当前会话先只写计划与 spec 文件，不依赖 git 提交完成本轮任务 |

## Notes
- 当前仓库只有前端代码、Node 测试和设计文档，没有任何后端目录或 Python 工程文件。
- 计划文件应只保存可信的内部结论；外部资料和网页信息只写入 `findings.md`。
- 后续如果开始实施，应在进入编码前切换到 TDD 工作流。

## Assumptions
- 使用 Python 3.12 与 `pip` 作为本地后端运行环境；当前没有 `py` launcher。
- v1 以单进程本地部署为前提，数据库先选 `SQLite + SQLAlchemy + Alembic`，后续若需要多实例部署再迁移到 PostgreSQL。
- 周期刷新先用 `APScheduler`，手动刷新和定时刷新共用同一条同步流水线。
- LLM 相关能力先按“可替换 provider 接口 + fake provider 测试桩”设计，避免真实模型调用阻塞开发。

## Recommended Stack
- Web: `FastAPI`
- Data validation: `Pydantic v2`
- ORM / migrations: `SQLAlchemy 2.x` + `Alembic`
- HTTP crawling: `httpx`
- HTML parsing: `BeautifulSoup4` 或 `lxml`
- Scheduler: `APScheduler`
- Tests: `pytest` + `httpx` mocking + repository fixtures

## Implementation Roadmap

### Milestone 1: Backend Scaffold & Dev Baseline
- 目标：
  - 建立可启动的后端工程骨架和最小测试基线。
- 主要文件：
  - `backend/main.py`
  - `backend/api/health.py`
  - `backend/core/config.py`
  - `backend/database/session.py`
  - `backend/tests/test_health.py`
  - `backend/requirements.txt`
  - `.env.example`
- 主要工作：
  - 建立 app factory、配置加载、数据库会话、健康检查接口。
  - 统一项目目录和依赖管理。
- 完成标准：
  - `uvicorn backend.main:app --reload` 可启动。
  - `GET /api/health` 返回 200。
  - `pytest` 至少有一个后端 smoke test 通过。

### Milestone 2: Matches Baseline & Frontend Cutover Slice
- 目标：
  - 让前端先从真实后端获取比赛列表，而不是继续依赖本地 fallback。
- 主要文件：
  - `backend/models/match.py`
  - `backend/repositories/matches.py`
  - `backend/api/matches.py`
  - `backend/scripts/import_fixture.py`
  - `backend/tests/test_matches_api.py`
  - `backend/tests/fixtures/fifa_schedule.json`
- 主要工作：
  - 定义 `matches` 表与仓储层。
  - 先把当前前端内置的官方赛程抽成后端 fixture，导入数据库。
  - 实现 `GET /api/matches`，返回前端现有字段结构。
- 完成标准：
  - 前端切到后端后能正常渲染赛程，不再走 fallback。
  - `GET /api/matches` 返回 `matches + last_updated + total`。
  - upsert / 排序 / 日期过滤有测试覆盖。

### Milestone 3: Sync Pipeline v1
- 目标：
  - 打通“刷新 -> 抓取 -> 快照 -> 解析 -> 校验 -> 入库”的真实同步链路。
- 主要文件：
  - `backend/sync/fetchers/fifa.py`
  - `backend/sync/fetchers/fallback.py`
  - `backend/sync/parser_service.py`
  - `backend/sync/validator.py`
  - `backend/sync/service.py`
  - `backend/api/refresh.py`
  - `backend/api/sync_runs.py`
  - `backend/models/sync_run.py`
  - `backend/models/source_snapshot.py`
  - `backend/models/parse_output.py`
  - `backend/tests/test_sync_service.py`
- 主要工作：
  - 实现 `POST /api/refresh` 与 `sync_runs` 状态跟踪。
  - 记录原始抓取内容、解析结果和失败原因。
  - 增加同步互斥，避免并发刷新。
- 完成标准：
  - 手动刷新能生成一条 `sync_run`。
  - FIFA 失败时可以走备用策略。
  - 解析失败不会污染 `matches`。

### Milestone 4: Prediction Domain v1
- 目标：
  - 支持赛前手动生成预测并保留历史版本。
- 主要文件：
  - `backend/prediction/service.py`
  - `backend/prediction/context_builder.py`
  - `backend/llm/provider.py`
  - `backend/llm/fake_provider.py`
  - `backend/models/prediction_version.py`
  - `backend/repositories/predictions.py`
  - `backend/api/predict.py`
  - `backend/api/match_predictions.py`
  - `backend/tests/test_prediction_service.py`
- 主要工作：
  - 实现 `POST /api/predict/{match_id}`。
  - 做开赛前限制、版本号递增、历史保留。
  - provider 层先支持 fake 实现，真实模型通过配置接入。
- 完成标准：
  - 同一场比赛可生成多版预测。
  - 已开赛比赛返回 `409`。
  - 前端预测按钮可以拿到真实后端响应。

### Milestone 5: Evaluation & Analytics v1
- 目标：
  - 赛后自动评估预测命中情况，并输出统计接口。
- 主要文件：
  - `backend/evaluation/scorer.py`
  - `backend/evaluation/service.py`
  - `backend/models/match_evaluation.py`
  - `backend/repositories/evaluations.py`
  - `backend/api/evaluations.py`
  - `backend/api/analytics.py`
  - `backend/tests/test_evaluation_rules.py`
  - `backend/tests/test_analytics_api.py`
- 主要工作：
  - 只取开赛前最后一版预测参与评估。
  - 按常规时间计算 outcome / exact score / home goals / away goals / total goals。
  - 输出总览和按阶段聚合的成功率。
- 完成标准：
  - 赛后同步后可自动写入 `match_evaluations`。
  - `GET /api/analytics/summary` 返回稳定结构。
  - 分层命中规则有完整单测。

### Milestone 6: Scheduler, Deep Health & Hardening
- 目标：
  - 增加后台调度、深度健康检查和收尾的可靠性增强。
- 主要文件：
  - `backend/scheduler/jobs.py`
  - `backend/api/health_deep.py`
  - `backend/tests/test_scheduler_guard.py`
  - `backend/tests/test_health_deep.py`
- 主要工作：
  - 接入 `APScheduler`。
  - 深度健康检查覆盖数据库、LLM provider 配置和最近一次同步状态。
  - 补日志、超时、重试与错误码统一处理。
- 完成标准：
  - 定时同步与手动刷新不会并发冲突。
  - 深度健康检查可用于日常巡检。

### Milestone 7: Frontend Analytics Integration
- 目标：
  - 把后端统计结果接到前端统计模块。
- 主要文件：
  - `frontend/js/api.js`
  - `frontend/js/ui.js`
  - `frontend/js/app.js`
  - `tests/ui.test.js`
  - `tests/api.test.js`
- 主要工作：
  - 新增成功率展示区块。
  - 接入 `/api/analytics/summary` 和 `/api/analytics/by-stage`。
  - 保持无后端时的退化体验。
- 完成标准：
  - 首页可展示预测成功率概览。
  - 前后端联调后页面和接口字段一致。

## Test & Verification Order
1. 先建后端 `pytest` 基线，再开始任何实现。
2. 每个里程碑先补对应测试，再写实现。
3. 验证顺序固定为：
   - 单元测试
   - 仓储/数据库集成测试
   - API 测试
   - 前端联调手工验收

## First Execution Slice
- 如果下一步开始真正实现，建议先做 Milestone 1 + Milestone 2。
- 原因：
  - 这两个阶段能最快切掉前端 fallback。
  - 同时会建立后续同步、预测、评估都要复用的数据库和 API 骨架。

## Implementation Progress
- 已完成 Milestone 1：
  - `FastAPI` 应用骨架
  - `GET /api/health`
  - SQLite 会话与表初始化
  - 后端 pytest 基线
- 已完成 Milestone 2：
  - `matches` 模型与仓储层
  - 默认官方赛程 fixture seed
  - `GET /api/matches`
  - 与现有前端字段契约对齐
- 下一步建议进入 Milestone 3：
  - `POST /api/refresh`
  - `sync_runs` / `source_snapshots` / `parse_outputs`
  - 抓取、解析、校验、入库流水线
- 已额外完成的前端直连能力：
  - `POST /api/refresh`
  - `POST /api/predict/{match_id}`
  - `prediction_versions` 最小版本化落库
  - `sync_runs` 最小状态记录
  - 前端运行时 API base URL 解析与默认接线
- 已完成的 Milestone 3 真实 refresh 流水线能力：
  - `source_snapshots` 与 `parse_outputs` 审计表落库
  - `backend/config/openrouter.model.json` 与 `backend/config/openrouter.key` 分离配置
  - `FifaOfficialFetcher + OpenRouterScheduleParser` 默认生产 refresh 管线
  - `POST /api/refresh` 在存在 OpenRouter key 时走真实抓取/解析入库，否则回退到 fixture refresh
- 已补齐的 refresh 增量更新规则：
  - 新增 `match_changes` 字段级变更历史表
  - refresh 改为字段级 diff + guarded upsert，而不是每次整行覆盖
  - 首刷允许淘汰赛占位名入库，后续确认真实球队后再覆盖
  - `TBD` / 占位球队 / 空比分不会回退已确认的真实事实
  - refresh 不再覆盖已有 `prediction`
  - 数据库为空时，首刷会先导入 fixture 基线，再叠加实时官方更新
  - refresh parser 已区分 `baseline` / `incremental` 两种模式
  - 已提供 `GET /api/matches/{match_id}/changes` 查询单场比赛事实变更历史
- 已补齐的同步审计查询能力：
  - 已提供 `GET /api/sync-runs` 查询同步任务列表
  - 已提供 `GET /api/sync-runs/{sync_run_id}` 查询单次同步详情
  - 已提供 `GET /api/parse-outputs/{parse_output_id}` 查询单次解析结果详情
  - 已完成真实首刷 + 增量刷新端到端验证，确认上述审计接口可直接查询落库结果
  - 已补齐前后端现有代码文件开头的中文核心功能注释
- 已完成的真实预测智能体设计收敛：
  - 已输出 [2026-04-19-worldcup-prediction-agent-design.md](D:/develop/WorldCup/docs/superpowers/specs/2026-04-19-worldcup-prediction-agent-design.md)
  - 方案确定为“单智能体 + OpenRouter + 强约束结构化输出 + 每次点击实时抓证据”
- 真实预测智能体具体实施计划：
  - Slice 4.1：Provider 抽象与输出 Schema 落地
    - 文件：
      - `backend/llm/provider.py`
      - `backend/services/prediction_schema.py`
      - `backend/tests/test_prediction_schema.py`
    - 工作：
      - 定义预测 provider 接口、统一异常类型、结构化输出 schema 和标准化函数
      - 明确 `predicted_score/outcome_pick/.../model_meta/input_snapshot` 必填规则
    - 验收：
      - 非法 JSON、缺字段、非法枚举和非法分数的测试全部失败后转绿
  - Slice 4.2：预测上下文组装与 Prompt 协议
    - 文件：
      - `backend/services/prediction_context.py`
      - `backend/services/prediction_prompt.py`
      - `backend/tests/test_prediction_context.py`
    - 工作：
      - 从 `matches` 与现有历史预测中构造 `match_facts + database_context`
      - 固化证据等级、来源优先级、输出字段要求和软失败处理约束
    - 验收：
      - 上下文字段稳定、无前端临时字段泄漏、prompt 中明确禁止非结构化输出
  - Slice 4.3：Fake Provider 与服务层重构
    - 文件：
      - `backend/services/predictions.py`
      - `backend/tests/test_predict_api.py`
      - `backend/tests/test_prediction_service.py`
    - 工作：
      - 先引入 fake provider 测试桩，替换当前 seeded-default 逻辑
      - 保持 `POST /api/predict/{match_id}` 外层响应不变
      - 保留版本号递增与 `matches.prediction` 最新摘要同步
    - 验收：
      - 同一场比赛重复预测生成多个版本
      - 已开赛比赛继续返回 `409`
      - provider 失败时不写入新版本
  - Slice 4.4：OpenRouter 真实预测 Provider [complete]
    - 文件：
      - `backend/llm/openrouter_prediction.py`
      - `backend/core/config.py`
      - `backend/tests/test_openrouter_prediction.py`
    - 工作：
      - 复用现有 `OpenRouterClient` 能力，新增预测专用请求封装
      - 加入预测请求超时、模型元信息回填和结构化响应解析
      - 增加预测专用配置项，避免与 refresh prompt 混淆
    - 验收：
      - 预测 provider 单测覆盖请求体、超时、响应解析和异常转换
  - Slice 4.5：真实 API 集成与并发保护 [in_progress]
    - 文件：
      - `backend/api/predict.py`
      - `backend/services/predictions.py`
      - `backend/tests/test_predict_api.py`
    - 工作：
      - 把真实 provider 注入到预测服务
      - 为同一场比赛增加单飞/互斥保护，防止重复点击并发预测
      - 明确硬失败与软失败的 API 行为
    - 验收：
      - 并发预测保护测试通过
      - 软失败结果可落库且带 `uncertainties`
      - 硬失败结果不落库
  - Slice 4.6：真实端到端验证与前端验收
    - 文件：
      - `backend/tests/test_live_prediction_api.py` 或运行时验证脚本
      - 必要时更新 `frontend/js/ui.js`
      - 必要时更新 `tests/api.test.js`
    - 工作：
      - 选择 1-2 场未开赛比赛做真实预测
      - 验证 `prediction_versions` 和 `matches.prediction` 落库内容
      - 验证前端列表页能直接展示新的结构化预测摘要
    - 验收：
      - 真实 `POST /api/predict/{match_id}` 返回 200
      - 数据库存在新版本记录
      - 前端页面或 API 响应可读到最新摘要
- 真实预测智能体实施顺序建议：
  - 严格按 `Schema -> Context/Prompt -> Fake Provider -> Real Provider -> API 集成 -> 真实验证` 顺序推进
  - 先把 provider 接口和输出合同钉死，再接真实模型，避免 prompt 与落库结构来回漂移
- 下一步建议优先补齐：
  - 在可用的 prediction key 下补完 Slice 4.6 的成功态 200 验证
  - 深度健康检查接口与运维巡检能力
  - 如有需要，继续补前端统计图表与预测历史详情页

## Milestone 5 Completion Update (2026-04-19)
- 已完成赛后评估与统计主链路：
  - `match_evaluations` ORM 模型
  - `backend/evaluation/scorer.py` 五维命中与 `core_hit / partial_hit / miss` 评分规则
  - `backend/evaluation/service.py` 开赛前最后一版预测选择与评估幂等写入
  - `backend/repositories/evaluations.py` 总览与按阶段聚合
  - `backend/api/evaluations.py`
  - `backend/api/analytics.py`
- refresh 已接入自动评估：
  - fixture refresh 与真实 refresh 在完赛后都会触发评估
  - 若无赛前预测会写入 `no_prediction`
  - 若结果未完整则写入 `pending_result`
  - 后续结果修正会覆盖同一场比赛的评估记录
- 当前里程碑状态：
  - Milestone 5：complete
  - Slice 4.5：complete
  - Slice 4.6：pending

## Slice 4.6 And Milestone 7 Update (2026-04-19)
- Slice 4.6 真实预测端到端验证进展：
  - 默认应用启动时，因为缺少 `backend/config/openrouter.prediction.key`，预测 provider 会按设计回退到 `FakePredictionProvider`
  - 已通过一次性 `Settings` 覆盖把预测链路显式指向现有 `backend/config/openrouter.key`
  - 应用已成功注入 `OpenRouterPredictionProvider`
  - 真实 `POST /api/predict/{match_id}` 已打到 OpenRouter，上游返回 `403 Key limit exceeded (total limit)`
  - 当前 `502` API 映射与“失败不落新版本”行为已验证通过
  - 仍缺一次在有效 key 条件下的 `200 + prediction_versions 落库` 成功态验收
- Milestone 7 前端联调进展：
  - 已完成前端对真实结构化预测结果的兼容
  - 已完成前端对 `/api/analytics/summary` 与 `/api/analytics/by-stage` 的接入
  - 已在首页新增统计模块展示总览命中率、分层结果和按阶段拆分
  - 当前前端在后端不可用时会对统计模块回退到空白占位，不影响赛程浏览

## Accuracy-First Prediction Enhancement Plan (2026-04-22)

### Goal
- 基于 [2026-04-22-worldcup-accuracy-first-prediction-design.md](D:/develop/WorldCup/docs/superpowers/specs/2026-04-22-worldcup-accuracy-first-prediction-design.md) 制定“准确率优先预测增强”的可执行开发计划。
- 在保持现有 `POST /api/predict/{match_id}` 契约不变的前提下，引入 `prediction_runs`、Agent 检索增强、证据提炼和最终决策链路。
- 控制改造风险：先保住当前真实预测链路可用，再逐步替换为新的 run-based orchestration。

### New Phases

#### Phase A: Run Data Model & Read APIs
- [x] 新增 `backend/models/prediction_run.py`
- [x] 为 `prediction_runs` 补数据库初始化/迁移逻辑
- [x] 新增 `backend/repositories/prediction_runs.py`
- [x] 新增只读接口：
  - `GET /api/matches/{match_id}/prediction-runs`
  - `GET /api/prediction-runs/{run_id}`
- [x] 先补测试：
  - `backend/tests/test_prediction_run_service.py`
  - `backend/tests/test_prediction_runs_api.py`
- **Deliverables:**
  - `prediction_runs` 混合型单对象已可落库和查询
  - 当前代码仍可继续使用旧预测链路
- **Status:** complete

#### Phase B: Orchestrator Shell & Persistence Refactor
- [x] 新增 `backend/services/prediction_runs.py` 作为单次预测执行总编排器
- [x] 收缩 `backend/services/predictions.py` 职责，只负责：
  - 赛前可预测校验
  - `prediction_versions` 版本号递增与落库
  - `matches.prediction` 更新
- [x] 保持 `backend/api/predict.py` 路由不变，但改为走 run orchestration
- [x] 先补测试：
  - `backend/tests/test_prediction_run_service.py`
  - `backend/tests/test_predict_api.py`
- **Deliverables:**
  - `POST /api/predict/{match_id}` 成功时会创建 `prediction_runs`
  - 失败时 `prediction_runs` 可记录状态与错误
  - 成功时 `prediction_runs.prediction_version_id` 正确关联
- **Status:** complete

#### Phase C: Research Stage Contracts & Fake Pipeline
- [x] 新增 `backend/services/prediction_research.py`
- [x] 定义 Search Planner / Agent Collector 的输入输出合同
- [x] 先接 fake 研究阶段，实现：
  - `search_plan_json`
  - `search_trace_json`
  - `search_documents_json`
- [x] 记录受控约束：
  - 最大搜索回合数
  - 最大页面数
  - 白名单 / 补充来源标记
- [x] 先补测试：
  - `backend/tests/test_prediction_research.py`
- **Deliverables:**
  - 不依赖真实联网也能跑通 run -> research -> version 主链路
  - `prediction_runs` 中可见完整研究阶段痕迹
- **Status:** complete

#### Phase D: Evidence Synthesizer & Decision Stage
- [ ] 新增 `backend/services/prediction_evidence.py`
- [ ] 新增 `backend/services/prediction_decider.py`
- [ ] 定义 `evidence_bundle_json` 结构
- [ ] 保持最终输出兼容现有 prediction schema
- [ ] 落实关键业务规则：
  - 不参考历史预测版本
  - 证据冲突时仍必须给结论
  - 证据不足时降低 `confidence`
- [ ] 先补测试：
  - `backend/tests/test_prediction_evidence.py`
  - `backend/tests/test_prediction_decider.py`
- **Deliverables:**
  - 证据提炼与最终决策阶段从 orchestrator 中解耦
  - fake / static 输入下可稳定生成结构化最终预测
- **Status:** pending

#### Phase E: Real OpenRouter Research Integration
- [ ] 将真实 OpenRouter 能力接到：
  - Search Planner
  - Evidence Synthesizer
  - Prediction Decider
- [ ] 为 Agent Collector 接入真实联网搜索执行与页面抓取
- [ ] 记录来源分层、白名单命中和补充来源使用情况
- [ ] 加入超时、阶段级错误收口和 `failed` run 保留策略
- [ ] 先补测试：
  - `backend/tests/test_prediction_research_openrouter.py`
  - `backend/tests/test_prediction_run_failures.py`
- **Deliverables:**
  - 单次预测可真实搜索、抓全文、提炼证据并做最终判断
  - provider 失败不会污染 `prediction_versions`
- **Status:** pending

#### Phase F: End-to-End Verification & Optional Frontend Surfacing
- [ ] 真实跑通 1-2 场比赛的 `POST /api/predict/{match_id}`
- [ ] 验证：
  - `prediction_runs` 中已保存搜索轨迹、全文和证据包
  - `prediction_versions` 已保存最终预测结果
  - `matches.prediction` 保持前端兼容
- [ ] 视需要补调试页或只读前端模块，展示 run 明细
- [ ] 回归：
  - `backend/tests -q`
  - `npm test -- --runInBand`

## 2026-04-23 Live-Chain Implementation Update

### Completed In This Session
- `Phase L1` complete
- `Phase L2` complete
- `Phase L5` complete
- SQLite schema compatibility for legacy `prediction_runs` complete
- OpenRouter client trailing-noise JSON recovery complete

### L6 Current State
- Real end-to-end verification ran against configured OpenRouter credentials.
- `POST /api/predict/fwc2026-m001` returned `200`.
- Latest `prediction_run` succeeded and wrote a new `prediction_version`.
- `evidence` and `decider` were `live`.
- `research` hit upstream `429` and correctly fell back, so this run is not a pure full-live-chain sample.

## DuckDuckGo Research Tool Plan (2026-04-23)

### Goal
- 基于 [2026-04-23-duckduckgo-research-tool-design.md](D:/develop/WorldCup/docs/superpowers/specs/2026-04-23-duckduckgo-research-tool-design.md) 把 `research` 阶段从 OpenRouter `web` 插件切换为“OpenRouter tool calling + 本地 DuckDuckGo 搜索工具”。
- 保持 `evidence / decider` 边界不变，继续禁止这两个阶段联网搜索。
- 保持 `prediction_runs`、`search_trace_json`、`search_documents_json` 的审计能力，并让真实 `research=live` 样本可验证。

### Current Phase
- DuckDuckGo Research Tool / Phase D1 ready

### Phases

#### Phase D1: Dependency And Config Baseline
- [ ] 选定 DuckDuckGo Python 依赖实现
- [ ] 在 `backend/requirements.txt` 记录新增依赖
- [ ] 在 `backend/core/config.py` 新增：
  - `prediction_research_duckduckgo_enabled`
  - `prediction_research_duckduckgo_timeout_seconds`
  - `prediction_research_duckduckgo_max_rounds`
  - `prediction_research_duckduckgo_max_results_per_query`
- [ ] 校准 `backend/config/openrouter.research.model.json`
  - 关闭 `enable_web_plugin`
  - 保留 Research 模型配置入口
- [ ] 给用户补充最终依赖安装命令
- **Status:** pending

#### Phase D2: OpenRouter Tool-Calling Transport
- [ ] 扩展 `backend/llm/openrouter.py`
  - 支持 `tools`
  - 支持 `tool_choice`
  - 支持 `parallel_tool_calls`
- [ ] 为 Research 增加最小 agentic loop 所需的消息往返结构
  - assistant `tool_calls`
  - tool result message
- [ ] 保持现有 prediction / evidence 普通 chat completion 调用不被破坏
- [ ] 先补失败测试：
  - OpenRouter client 正确转发 `tools`
  - 能解析 `tool_calls` 响应
- **Status:** pending

#### Phase D3: DuckDuckGo Search Adapter
- [ ] 新增本地 DuckDuckGo 搜索适配层
  - 建议文件：`backend/services/duckduckgo_search.py`
- [ ] 对外提供单一工具接口：
  - `duckduckgo_search(query, max_results)`
- [ ] 统一结果映射：
  - `title`
  - `url`
  - `domain`
  - `snippet`
- [ ] 增加安全约束：
  - 空 query 拒绝
  - `max_results` 上限裁剪
  - 工具级超时
- [ ] 先补失败测试：
  - 空 query
  - 结果数裁剪
  - 搜索异常映射
  - 空结果处理
- **Status:** pending

#### Phase D4: Research Tool Loop Rewrite
- [ ] 改造 `backend/services/prediction_research.py`
- [ ] 用本地 DuckDuckGo 工具循环替换 OpenRouter `web` 插件依赖
- [ ] 维护 tool loop 审计数据：
  - `tool_name`
  - `executed_queries`
  - `round_count`
  - `result_count`
- [ ] 把工具结果映射进 `search_documents`
- [ ] 保持最终输出仍为：
  - `search_plan`
  - `search_trace`
  - `search_documents`
  - `used_fallback_sources`
- [ ] 失败时继续 fallback 到 `FakePredictionResearcher`
- [ ] 先补失败测试：
  - 单轮 tool call 成功
  - 多轮 tool call 成功
  - 超轮次 fallback
  - tool error fallback
  - 非法最终 JSON fallback
- **Status:** pending

#### Phase D5: App Integration And Compatibility
- [ ] 校准 `backend/main.py` 与默认 research provider 装配
- [ ] 保持 `POST /api/predict/{match_id}` 外部契约不变
- [ ] 确认 `prediction_runs` 列表/详情接口能展示新的 DuckDuckGo trace 语义
- [ ] 如有需要补最小前端文案/说明调整
- [ ] 回归：
  - `backend/tests/test_prediction_research.py`
  - `backend/tests/test_prediction_run_service.py`
  - `backend/tests/test_predict_api.py`
  - `npm test -- --runInBand`
- **Status:** pending

#### Phase D6: Real End-To-End Verification
- [ ] 用真实配置执行至少一次：
  - `POST /api/predict/{match_id}`
- [ ] 验证：
  - `stage_trace_json.research.mode = live`
  - `search_trace_json.tool_name = duckduckgo_search`
  - `search_documents_json` 来自 DuckDuckGo 结果摘要
  - `prediction_version` 正常落库
- [ ] 若仍 fallback，记录具体失败源：
  - 工具超时
  - OpenRouter tool loop 问题
  - DuckDuckGo 依赖行为问题
- **Status:** pending

### Dependencies & Order
- `Phase D1 -> Phase D2 -> Phase D3 -> Phase D4 -> Phase D5 -> Phase D6`
- 推荐首个执行切片：
  - `Phase D1 + Phase D2 + Phase D3`
- 原因：
  - 先把依赖、transport、工具适配层独立立住
  - 这样 `prediction_research.py` 的重写能在明确接口上进行
  - 风险比直接改 Research 主流程更低

### Verification Strategy
- 每个 phase 都先写失败测试，再写实现
- 强制回归顺序：
  - targeted pytest
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - `npm test -- --runInBand`

## 2026-04-24 DuckDuckGo Research Verification Completion Update

### Completed In This Session
- Updated DuckDuckGo Research runtime defaults:
  - `prediction_research_duckduckgo_timeout_seconds = 5.0`
  - `prediction_research_duckduckgo_backend = "duckduckgo,mojeek"`
- Wired the configured backend chain through `build_default_prediction_researcher(...)`.
- Tightened the final prediction prompt so `input_snapshot` stays limited to `match_facts` and the JSON stays compact.
- Raised `backend/config/openrouter.prediction.model.json` `max_tokens` from `800` to `1200` to reduce decider truncation risk.

### D6 Result
- Real isolated end-to-end verification completed successfully:
  - `POST /api/predict/fwc2026-m001` returned `200`
  - latest `prediction_run.status = succeeded`
  - `is_full_live_chain = true`
  - `has_any_fallback = false`
  - `prediction_versions` persisted successfully
- Verified live stage trace:
  - `research = live`
  - `evidence = live`
  - `decider = live`

### Latest Regression
- `D:\\develop\\WorldCup\\.conda\\WorldCup\\python.exe -m pytest backend/tests -q`
  - `90 passed`
- `npm test -- --runInBand`
  - `26 passed`

## 2026-04-24 OpenRouter Empty-Body Hardening Update

### Completed In This Session
- Hardened `backend/llm/openrouter.py` so an empty OpenRouter HTTP response body now surfaces as `JSONDecodeError` instead of leaking a raw `ValueError`.
- This keeps `OpenRouterPredictionProvider` on the existing `PredictionProviderResponseError` path, so the API returns `502` instead of `500`.

### Latest Regression
- `D:\\develop\\WorldCup\\.conda\\WorldCup\\python.exe -m pytest backend/tests/test_openrouter_client.py backend/tests/test_openrouter_prediction.py -q`
  - `14 passed`
- `D:\\develop\\WorldCup\\.conda\\WorldCup\\python.exe -m pytest backend/tests -q`
  - `92 passed`

## 2026-04-24 DuckDuckGo Research Tool Implementation Update

### Completed In This Session
- `Phase D1` complete
  - `backend/requirements.txt` 已新增 `ddgs==9.14.0`
  - `backend/core/config.py` 已新增 DuckDuckGo Research 默认配置：
    - `prediction_research_duckduckgo_enabled`
    - `prediction_research_duckduckgo_timeout_seconds`
    - `prediction_research_duckduckgo_max_rounds`
    - `prediction_research_duckduckgo_max_results_per_query`
  - `backend/config/openrouter.research.model.json` 已默认关闭 `enable_web_plugin`
- `Phase D2` complete
  - `backend/llm/openrouter.py` 已支持：
    - `tools`
    - `tool_choice`
    - `parallel_tool_calls`
- `Phase D3` complete
  - 已新增 `backend/services/duckduckgo_search.py`
  - 已实现本地 DuckDuckGo 搜索工具：
    - 空 query 校验
    - `max_results` 裁剪
    - 结果标准化
    - 上游异常映射
- `Phase D4` complete
  - `backend/services/prediction_research.py` 已支持：
    - OpenRouter tool-calling 循环
    - 本地 `duckduckgo_search` 工具执行
    - 工具轨迹注入 `search_trace_json`
    - 工具结果映射为 `search_documents`
    - 超轮次失败并 fallback
- `Phase D5` complete
  - 受影响回归与全量回归均通过

### D6 Current Blocker
- 真实 DuckDuckGo 联调尚未执行。
- 当前本地 Conda 环境中缺少 `ddgs` 依赖，需先安装后再做真实 `POST /api/predict/{match_id}` 验证。
- **Deliverables:**
  - 准确率优先增强链路真实可用
  - 前端不破坏当前展示
- **Status:** pending

### Dependencies & Order
- `Phase A -> Phase B -> Phase C -> Phase D -> Phase E -> Phase F`
- `Phase B` 之前不接真实联网能力，先把 run 生命周期和落库边界钉死。
- `Phase E` 之前不依赖真实 OpenRouter 搜索，以免搜索、证据、决策三段混在一起难排错。
- 当前已有 `prediction_versions`、`matches.prediction`、`OpenRouterPredictionProvider` 要尽量复用，不重复造轮子。

### Verification Strategy
- 每一阶段都先补失败测试，再写实现。
- 优先验证顺序：
  - 单元测试
  - 服务层集成测试
  - API 测试
  - 真实运行时验证
- 强制保留两条主回归：
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - `npm test -- --runInBand`

### First Execution Slice
- 推荐从 `Phase A + Phase B` 开始。
- 原因：
  - 这是本次改造中风险最低、收益最高的底座切片
  - 能先把 `prediction_runs` 和 run orchestration 挂进去
  - 后面的检索、证据、决策阶段都能在这个壳上独立替换和验证

## Phase D + E Completion Update (2026-04-22)
- `Phase D` 已完成：
  - `prediction_evidence.py` 已拆出独立 evidence 合同、fake 实现与真实实现入口
  - `prediction_decider.py` 继续只负责最终预测落库
  - run 状态流已变为 `running -> researching -> synthesizing -> deciding -> succeeded/failed`
  - `evidence_bundle_json` 与 `synthesizer_model` 已稳定入库
- `Phase E` 已完成最小可用真实集成：
  - research 阶段新增 `OpenRouterPredictionResearcher`
  - evidence 阶段新增 `OpenRouterPredictionEvidenceSynthesizer`
  - `main.py` 已把 research / evidence / decider 一并接入应用默认依赖注入
  - 新增配置项：
    - `prediction_research_openrouter_*`
    - `prediction_evidence_openrouter_*`
  - 配置缺失或无效时自动回退 fake 实现
- 当前建议：
  - 进入 `Phase F`
  - 用真实配置跑 1-2 场端到端验证
  - 视需要补前端 run 详情展示
- 最新回归：
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - `65 passed`

### Completed In This Slice
- 已完成 `Phase A + Phase B + Phase C`：
  - `prediction_runs` ORM、repository 和只读查询接口已上线
  - `POST /api/predict/{match_id}` 已改为 run-based orchestration
  - 成功预测会创建 `prediction_runs` 并关联 `prediction_versions`
  - 失败预测会保留 `failed` run 与错误信息
  - fake research pipeline 已接入，run 中会保存：
    - `search_plan_json`
    - `search_trace_json`
    - `search_documents_json`
  - 当前 `planner_model` 会记录为 `fake-research-v1`
- 下一步建议进入 `Phase C`：
  - 开始 `Phase D`
  - 新增 `prediction_evidence.py`
  - 新增 `prediction_decider.py`
  - 把当前直接预测替换成“research -> evidence -> decider”三段式链路

## Phase F Update (2026-04-22)
- 已完成一部分可选前端展示：
  - 首页 AI 预测卡片现支持按需查看最新一次 `prediction_run` 详情
  - 前端已接入：
    - `GET /api/matches/{match_id}/prediction-runs`
    - `GET /api/prediction-runs/{run_id}`
- 当前仍未完成的 `Phase F` 核心项：
  - 用真实配置跑 1-2 场 research + evidence + decider 的端到端验证
  - 视需要补更深的 run 审计页或明细页
- 最新真实烟测结果：
  - 隔离数据库下执行 `POST /api/predict/fwc2026-m001`
  - research 阶段命中 OpenRouter `403 Key limit exceeded`
  - 本地行为正确：API 返回 `502`、`prediction_runs` 记录失败、`prediction_versions` 不落脏数据
## Phase F Completion Update (2026-04-22)
- 已补强 research / evidence 阶段的 JSON 包裹提取、结构漂移兼容与 provider 失败 fallback。
- 已补强 OpenRouter research / evidence 的快速超时护栏，避免手动点击预测时长时间挂起。
- 已补强 final decider 在 JSON 解析失败时的 `response-healing` 单次重试。
- 已新增默认配置文件：`backend/config/openrouter.research.model.json`、`backend/config/openrouter.evidence.model.json`。
- 已将默认 `prediction_research_request_timeout_seconds` 与 `prediction_evidence_request_timeout_seconds` 收紧到 45 秒。
- 使用仓库默认 `Settings` 和真实 OpenRouter key 在隔离 SQLite 上执行 `POST /api/predict/fwc2026-m001`，API 返回 `200`。
- 真实验收落库结果：`prediction_runs` 成功写入 1 条 `succeeded` run；`prediction_versions` 成功写入 1 条新版本；当前真实样本中 `planner_model = fallback-research-v1`，`synthesizer_model = qwen/qwen3.5-flash-20260224`，`decider_model = qwen/qwen3.5-flash-20260224`。
- 当前结论：accuracy-first 预测主链路已具备真实可用性，后续可继续优化 research fallback 质量与前端 run 状态展示。
## OpenRouter Live Prediction Chain Plan (2026-04-23)

### Goal
- 基于 [2026-04-22-openrouter-live-prediction-chain-design.md](D:/develop/WorldCup/docs/superpowers/specs/2026-04-22-openrouter-live-prediction-chain-design.md) 完成“真实 OpenRouter 主链路 + research/evidence 可 fallback + decider 不可 fallback”的后端收口。
- 保持 `POST /api/predict/{match_id}` 外部契约不变，同时补齐链路审计字段与阶段级语义。

### Current Phase
- Live Prediction Chain / Phase L1 ready

### Phases

#### Phase L1: Run Schema And API Surface
- [ ] 为 `prediction_runs` 新增：
  - `stage_trace_json`
  - `is_full_live_chain`
  - `has_any_fallback`
- [ ] 扩展 `PredictionRunRepository` 的保存与序列化逻辑
- [ ] 扩展 prediction-runs 列表与详情 API 返回
- [ ] 先补失败测试：
  - `backend/tests/test_prediction_run_service.py`
  - `backend/tests/test_prediction_runs_api.py`
- **Status:** pending

#### Phase L2: Orchestrator Stage Trace And Failure Semantics
- [ ] 改造 `backend/services/prediction_runs.py`
- [ ] 为 `research / evidence / decider` 记录：
  - `mode`
  - `model_name`
  - `elapsed_ms`
  - `error_message`
- [ ] 显式落库：
  - `is_full_live_chain`
  - `has_any_fallback`
- [ ] 收紧失败语义：
  - `research` 失败 -> fallback
  - `evidence` 失败 -> fallback
  - `decider` 失败 -> run failed，不落新 version
- [ ] 先补四类测试：
  - 纯真实成功
  - research fallback
  - evidence fallback
  - decider failed
- **Status:** pending

#### Phase L3: Research Live-First Tightening
- [ ] 收紧 `backend/services/prediction_research.py`
- [ ] 明确 live research 成功条件：
  - 结构合法
  - `search_documents` 非空且有效
- [ ] 真实失败时保留 fallback reason 到 `stage_trace_json.research.error_message`
- [ ] 校准 `planner_model` 语义
- [ ] 先补失败测试
- **Status:** pending

#### Phase L4: Evidence Live-First Tightening
- [ ] 收紧 `backend/services/prediction_evidence.py`
- [ ] 明确 evidence live / fallback 的 trace 语义
- [ ] 校准 `synthesizer_model` 语义
- [ ] 先补失败测试
- **Status:** pending

#### Phase L5: API Mapping And Frontend Compatibility Check
- [ ] 确认 `backend/api/predict.py` 对 decider failure 继续映射 `502`
- [ ] 确认 prediction-runs 新字段不破坏前端现有详情展示
- [ ] 视需要补最小前端兼容调整
- [ ] 回归：
  - `backend/tests/test_predict_api.py`
  - `backend/tests/test_predict_api_hardening.py`
  - `npm test -- --runInBand`
- **Status:** pending

#### Phase L6: Real End-to-End Verification
- [ ] 使用真实 OpenRouter 配置跑至少一次 `POST /api/predict/{match_id}`
- [ ] 验证两类结果：
  - 三阶段都 live -> `is_full_live_chain = true`
  - research/evidence 任一 fallback -> `has_any_fallback = true`
- [ ] 核对 `prediction_runs` 与 `prediction_versions` 落库
- **Status:** pending

### Dependencies & Order
- `Phase L1 -> Phase L2 -> Phase L3 -> Phase L4 -> Phase L5 -> Phase L6`
- `Phase L1 + L2` 是第一执行切片，因为它们先把 spec 里最关键的链路可观测性钉死。

### Verification Strategy
- 每个 phase 都先写失败测试，再写实现
- 强制回归顺序：
  - targeted pytest
  - `D:\develop\WorldCup\.conda\WorldCup\python.exe -m pytest backend/tests -q`
  - `npm test -- --runInBand`
