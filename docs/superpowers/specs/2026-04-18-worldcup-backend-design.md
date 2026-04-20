# WorldCup Predictor 后端设计

**日期**: 2026-04-18  
**状态**: 待实现

## 1. 目标与范围

### 1.1 目标

- 将 FIFA 2026 世界杯赛程写入数据库，并支持后续持续更新。
- 提供一个数据爬取解析智能体，负责抓取、解析、校验和入库。
- 提供一个预测智能体，支持手动点击生成、保留历史版本的比赛预测。
- 在赛后自动拿到真实结果，按多个角度评估预测是否命中。
- 提供统计接口，支持前端展示不同维度的预测成功率。

### 1.2 非目标

- 不做模型训练平台。
- 不做用户登录和权限体系。
- 不做博彩或盘口相关功能。
- 不在 v1 中做复杂的多表归一化扩展，例如独立 `teams` 维表。

## 2. 关键设计决策

| 决策 | 选择 | 说明 |
|---|---|---|
| 后端形态 | 模块化单体 + 后台任务 | 先把同步、预测、评估拆成清晰域，再决定是否拆服务 |
| 主数据源 | FIFA 官网优先 | 官方赛程和结果优先入库 |
| 备用数据源 | 由爬取智能体自行决定 | FIFA 失败后由智能体根据可用性选择来源 |
| 解析方式 | LLM 作为主解析器 | 先抓原始内容，再交给大模型结构化解析 |
| 预测触发 | 手动点击 | 不自动批量生成，避免无意义预测 |
| 预测版本 | 允许多次预测并保留历史 | 不覆盖旧版本 |
| 评估依据 | 开赛前最后一版预测 | 只取 `kickoff_at` 之前最近的一版 |
| 淘汰赛判定 | 只按常规时间 | 不把加时和点球纳入命中判定 |
| 命中评分 | 分层命中 | `core_hit` / `partial_hit` / `miss` |

## 3. 系统架构

### 3.1 组件划分

- `API Layer`
  - 提供比赛列表、单场详情、刷新、预测、评估和统计接口。
- `Sync Domain`
  - 负责抓取 FIFA 官方赛程和结果，触发 LLM 解析，写入比赛库。
- `Prediction Domain`
  - 负责手动生成预测，保存多版本历史。
- `Evaluation Domain`
  - 负责赛后评估预测是否命中，并生成统计口径。
- `LLM Adapter`
  - 封装大模型调用，统一管理 prompt、模型名、重试和解析错误。
- `Repository Layer`
  - 所有数据库读写都通过仓储层完成。
- `Scheduler`
  - 负责周期性触发同步任务，和手动刷新共用同一条流水线。

### 3.2 推荐结构

```
backend/
  api/
  sync/
  prediction/
  evaluation/
  llm/
  repositories/
  models/
  database/
  scheduler/
```

### 3.3 数据流

1. 定时器或用户点击触发一次同步。
2. 爬虫先抓 FIFA，失败后由爬取智能体自行选择备用来源。
3. 原始内容写入 `source_snapshots`。
4. LLM 主解析器把原始内容转成结构化赛程数据。
5. 校验通过后写入 `matches`。
6. 用户点击某场比赛的预测按钮，生成新的 `prediction_versions`。
7. 赛后同步拿到真实结果，选择开赛前最后一版预测，写入 `match_evaluations`。
8. 聚合统计接口从 `match_evaluations` 直接计算命中率。

## 4. 数据模型

### 4.1 `sync_runs`

记录每次同步任务的状态和结果。

- `id`
- `trigger_type`，如 `manual` / `schedule`
- `status`，如 `queued` / `running` / `partial_success` / `success` / `failed`
- `started_at`
- `finished_at`
- `source_name`
- `fetched_count`
- `parsed_count`
- `upserted_count`
- `error_message`

### 4.2 `source_snapshots`

保存抓取到的原始内容，便于追溯和重放。

- `id`
- `sync_run_id`
- `source_name`
- `source_url`
- `content_type`
- `content_hash`
- `fetched_at`
- `raw_body`
- `fetch_status`

### 4.3 `parse_outputs`

保存 LLM 解析后的结构化结果和校验信息。

- `id`
- `sync_run_id`
- `snapshot_id`
- `parser_version`
- `model_name`
- `structured_json`
- `confidence`
- `warnings`
- `parse_status`
- `error_message`

### 4.4 `matches`

比赛主表，是赛程和结果的事实来源。

- `id`
- `fifa_match_id`，若可用则唯一
- `natural_key`，用于回退匹配
- `kickoff_at`，统一存 UTC
- `stage`
- `group_name`
- `venue`
- `home_team_name`
- `away_team_name`
- `home_team_flag`
- `away_team_flag`
- `home_team_rank`
- `away_team_rank`
- `status`
- `regular_home_score`
- `regular_away_score`
- `extra_home_score`
- `extra_away_score`
- `penalty_home_score`
- `penalty_away_score`
- `source_name`
- `source_updated_at`
- `raw_source_hash`
- `updated_at`

约束：

- 优先用 `fifa_match_id` 做唯一键。
- 拿不到官方 ID 时，用 `stage + kickoff_at + home_team_name + away_team_name + venue` 兜底。
- 所有时间以 UTC 入库，前端按本地时区展示。

### 4.5 `prediction_versions`

保存每次手动生成的预测，保留完整历史。

- `id`
- `match_id`
- `version_no`
- `created_at`
- `created_by`
- `model_name`
- `prompt_version`
- `pred_home_score`
- `pred_away_score`
- `pred_outcome`
- `probabilities_json`
- `confidence`
- `reasoning`
- `context_hash`
- `status`

约束：

- 同一场比赛允许多次预测。
- 新预测只追加，不覆盖旧记录。
- 列表接口可返回最新一版预测摘要，详情接口返回全部历史。

### 4.6 `match_evaluations`

保存赛后评分卡，是统计接口的唯一来源。

- `id`
- `match_id`
- `prediction_version_id`
- `evaluation_status`，如 `scored` / `no_prediction` / `pending_result` / `invalid`
- `actual_home_score`
- `actual_away_score`
- `outcome_hit`
- `exact_score_hit`
- `home_goals_hit`
- `away_goals_hit`
- `total_goals_hit`
- `grade`
- `rule_version`
- `evaluated_at`

评分规则：

- `exact_score_hit`：比分完全一致。
- `outcome_hit`：胜负平一致。
- `home_goals_hit`：主队进球数一致。
- `away_goals_hit`：客队进球数一致。
- `total_goals_hit`：总进球数一致。
- `core_hit`：比分完全一致，或胜负平命中且至少再命中一个其他维度。
- `partial_hit`：没有达到 `core_hit`，但至少命中一个维度。
- `miss`：所有维度都未命中。

## 5. 核心工作流

### 5.1 同步工作流

1. 创建 `sync_runs` 记录，状态设为 `running`。
2. 优先抓取 FIFA 官方页面或接口。
3. 若 FIFA 抓取失败，由爬取智能体自行选择备用来源。
4. 将每个原始响应写入 `source_snapshots`。
5. 将原始内容交给 LLM 主解析器，输出结构化赛程 JSON。
6. 通过确定性校验器检查字段完整性、时间格式、重复比赛和比分合法性。
7. 校验通过后 upsert 到 `matches`。
8. 若比赛已结束且常规时间比分完整，则可触发评估任务。
9. 结束时更新 `sync_runs` 状态和统计计数。

### 5.2 预测工作流

1. 用户在前端手动点击预测按钮。
2. API 检查比赛是否仍未开赛。
3. 聚合当前比赛事实和最近历史预测作为上下文。
4. 调用预测智能体生成新结果。
5. 新结果写入 `prediction_versions`，版本号递增。
6. 返回新版本的预测快照给前端。

### 5.3 评估工作流

1. 当比赛进入 `finished` 且常规时间比分已知时触发评估。
2. 查找所有 `created_at < kickoff_at` 的预测版本。
3. 选出最近的一版作为官方评估对象。
4. 按常规时间比分计算五个维度的命中情况。
5. 写入或更新 `match_evaluations`。
6. 若没有任何赛前预测，也要保留一条 `no_prediction` 记录，方便统计口径统一。

### 5.4 统计工作流

- 统计接口直接读取 `match_evaluations`。
- 只统计 `evaluation_status = scored` 的记录进入成功率分母。
- 无预测场次单独计数，不进入命中率分母。
- 成功率支持按总览和按阶段聚合。

## 6. API 设计

### 6.1 兼容现有前端的核心接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/matches` | 比赛列表 |
| GET | `/api/matches/{match_id}` | 比赛详情 |
| GET | `/api/matches/{match_id}/changes` | 比赛事实字段变更时间线 |
| POST | `/api/predict/{match_id}` | 手动生成预测 |
| POST | `/api/refresh` | 触发同步 |
| GET | `/api/health` | 基础健康检查 |

### 6.2 扩展接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/sync-runs` | 同步任务列表 |
| GET | `/api/sync-runs/{sync_run_id}` | 同步任务详情 |
| GET | `/api/parse-outputs/{parse_output_id}` | 单次解析结果详情 |
| GET | `/api/matches/{match_id}/predictions` | 预测历史 |
| GET | `/api/predictions/{prediction_id}` | 单条预测详情 |
| GET | `/api/evaluations` | 评估记录列表 |
| GET | `/api/evaluations/{match_id}` | 单场评估详情 |
| GET | `/api/analytics/summary` | 总览成功率 |
| GET | `/api/analytics/by-stage` | 按阶段统计 |
| GET | `/api/health/deep` | 深度健康检查 |

### 6.3 返回约定

- 列表接口统一返回 `items`、`total`、`last_updated`、`meta`。
- 详情接口返回稳定对象，不依赖前端临时拼接。
- `GET /api/matches` 中的 `prediction` 字段返回“当前最新预测快照”，便于前端直接渲染。
- `GET /api/matches/{match_id}` 返回完整比赛事实、预测历史和评估结果。
- `POST /api/refresh` 只返回 `sync_run_id` 和状态即可，不必等待整个同步完成。
- 时间字段统一使用 ISO-8601，建议 UTC。

### 6.4 关键状态码

- `200`：正常查询或预测成功。
- `202`：刷新任务已接受，正在后台执行。
- `409`：比赛已开赛，禁止再生成新预测，或当前已有同步任务运行中。
- `422`：输入或解析结果不合法。
- `500`：未知系统错误。

## 7. 异常处理与恢复

- FIFA 抓取失败时，不删除旧数据，优先返回历史可用赛程。
- 备用来源由爬取智能体自行选择，但必须记录来源和原因。
- 解析失败时保留原始快照和错误信息，不写入错误赛程。
- 解析成功但校验失败时，阻止入库，避免脏数据污染 `matches`。
- 同一场比赛重复同步时，通过唯一键 upsert，不产生重复行。
- 预测生成失败时不写入新版本，历史版本保持不变。
- 评估任务幂等执行，重复触发只会更新同一场比赛的评估记录。
- 后台同步只允许一个活跃任务，避免并发写库冲突。
- 任务状态和错误信息必须能在 `sync_runs` 中追踪到。

## 8. 统计与前端模块

前端的统计模块直接消费后端统计接口，展示以下维度：

- 胜负命中率
- 比分命中率
- 主队进球数命中率
- 客队进球数命中率
- 总进球数命中率
- `core_hit` / `partial_hit` / `miss` 分布
- 按阶段拆分的命中率

推荐接口输出示例：

```json
{
  "total_scored_matches": 24,
  "dimensions": {
    "outcome": { "hit": 15, "rate": 0.625 },
    "exact_score": { "hit": 6, "rate": 0.25 },
    "home_goals": { "hit": 10, "rate": 0.4167 },
    "away_goals": { "hit": 11, "rate": 0.4583 },
    "total_goals": { "hit": 12, "rate": 0.5 }
  },
  "grade_distribution": {
    "core_hit": 5,
    "partial_hit": 14,
    "miss": 5
  }
}
```

## 9. 测试策略

### 9.1 单元测试

- 赛程解析校验
- 时间标准化
- 唯一键和 upsert 规则
- 预测版本号递增
- 赛前最后一版预测的选择逻辑
- 五维命中和分层评分规则

### 9.2 集成测试

- FIFA 抓取 -> 解析 -> 入库
- FIFA 失败 -> 备用源 -> 解析 -> 入库
- 手动预测 -> 新版本保存
- 赛后同步 -> 自动评估 -> 统计接口返回正确结果

### 9.3 接口测试

- `/api/matches`
- `/api/matches/{match_id}`
- `/api/predict/{match_id}`
- `/api/refresh`
- `/api/analytics/summary`

重点验证：

- 返回结构稳定
- 分页和过滤参数正确
- 预测历史不丢失
- 统计结果分母分子一致

### 9.4 回归测试

- 解析出错时不污染正式赛程
- 重复同步不重复建赛
- 同一场比赛多次预测保留历史
- 只使用开赛前最后一版预测参与评估
- 淘汰赛只按常规时间判定

## 10. 交付标准

当后端达到以下状态时，视为 v1 完成：

- 能从 FIFA 官方稳定同步赛程。
- 能在 FIFA 失败时切到备用来源并保留追溯信息。
- 能手动生成多版本预测。
- 能赛后自动评估五个维度的命中情况。
- 能输出可供前端展示的成功率统计。
- 能对同步、预测、评估和统计做完整审计。

## 11. 2026-04-19 增量 Refresh 补充规则

### 11.1 总体原则

- 首次 refresh 建立完整赛程基线，包含固定赛程字段与淘汰赛占位对阵。
- 后续 refresh 不再简单全量覆盖，而是基于当前 `matches` 做增量更新。
- 数据库中的 `matches` 始终保存“当前最新事实”。
- 当数据库为空且存在本地官方 fixture 基线时，第一次 refresh 应先完成基线导入，再叠加实时官方更新。
- 若 FIFA 官方源明确修正了时间、场馆、阶段、分组等基线字段，允许覆盖旧值。
- 若后续 refresh 只拿到低信息占位值，例如 `TBD`、`TBD Stadium`、`Winner Group A`，不得把已知真实事实回退成占位值。

### 11.2 增量更新字段策略

- 基线字段：
  - `official_match_number`
  - `kickoff_label`
  - `sort_order`
  - `date`
  - `time`
  - `stage`
  - `group_name`
  - `venue`
- 动态事实字段：
  - `home_team`
  - `away_team`
  - `status`
  - `score`
  - `head_to_head`
  - `key_players`
- 预测字段：
  - `prediction`
  - 不属于 refresh 覆盖范围；refresh 不得清空或覆盖赛前预测结果。

### 11.3 淘汰赛占位对阵

- 首次 refresh 时，淘汰赛可按官方占位名入库，例如：
  - `Winner Group A`
  - `Runner-up Group B`
- 当后续 refresh 能确认真实参赛球队时，允许直接覆盖 `home_team` / `away_team`。
- 如果后续 refresh 又退回到占位名，不得覆盖已确认的真实球队。

### 11.4 结果字段保护

- `status` 与 `score` 属于结果事实。
- 新结果可以覆盖旧结果。
- 空结果或更低信息的结果不能覆盖已存在的结果。
- 对于常见状态值，应阻止明显回退，例如 `finished -> not_started`。

### 11.5 变更历史审计

- 新增 `match_changes` 表，按字段记录 refresh 引起的事实变化。
- 每条记录至少包含：
  - `match_id`
  - `sync_run_id`
  - `field_name`
  - `old_value`
  - `new_value`
  - `change_type`
  - `changed_at`
- `change_type` 约定：
  - `filled`：从占位值/空值补全为更具体事实
  - `corrected`：官方修正已有基线信息
  - `result_updated`：比赛状态或比分更新

### 11.6 Refresh 实现要求

- refresh 在 upsert 之前必须做字段级 diff。
- 无变化则不写 `match_changes`。
- 有变化才更新主表并写入审计记录。
- `match_changes.sync_run_id` 必须能追溯到触发本次变化的 `sync_runs` 记录。
- refresh 需要显式区分两种模式：
  - `baseline`：数据库为空时的首刷建基线
  - `incremental`：已有基线后的事实增量更新
- LLM 解析 prompt 也应随模式切换：
  - `baseline` 模式要求输出完整赛程基线
  - `incremental` 模式要求只输出有新增或修正事实的比赛子集
- 对于真实模型返回的非 canonical 增量结构，refresh 层必须先做规范化再入库，例如：
  - `match_id` 映射到 `id`
  - 字符串形式的 `home_team` / `away_team` 转为标准 team object
  - `Group A` 这类文本归一化为内部一致的 `group_name`
