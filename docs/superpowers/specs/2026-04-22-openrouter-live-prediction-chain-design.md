# WorldCup Predictor OpenRouter 真实预测链路设计
**日期**: 2026-04-22  
**状态**: 待用户 Review

## 1. 目标与范围
### 1.1 目标

- 将当前预测系统收敛为“真实 OpenRouter 链路优先”的执行模式。
- 保持现有 `POST /api/predict/{match_id}` 作为唯一手动触发入口。
- 让 `research -> evidence -> decider` 三阶段中，规划、搜索、证据压缩和最终预测都以大模型为主执行。
- 在允许部分 fallback 的前提下，明确区分“纯真实链路成功”和“带 fallback 的可用结果”。
- 为前端和后续效果分析提供稳定的链路可观测性，能够回答每次预测到底用了哪些真实模型、哪一段发生了 fallback、失败原因是什么。

### 1.2 非目标

- 本阶段不做自动定时预测，仍然只支持手动点击触发。
- 本阶段不引入新的本地搜索器，不做独立的爬虫调度系统。
- 本阶段不把历史 `prediction_versions` 回灌给新的预测请求。
- 本阶段不做多模型投票，不做 ensemble，不做批量预测任务编排。
- 本阶段不继续提升本地 fallback 内容质量，fallback 仅作为真实链路失败时的兜底。

## 2. 已确认决策
| 决策项 | 选择 | 说明 |
|---|---|---|
| 主链路策略 | 真实 OpenRouter 优先 | 三阶段都优先走真实 OpenRouter |
| fallback 策略 | 方案 B | `research` 和 `evidence` 允许 fallback，`decider` 不允许 fallback |
| research 行为 | 模型负责规划与搜索 | 规划和搜索都由大模型完成，并启用 OpenRouter `web` 能力 |
| evidence 行为 | 模型压缩证据 | 使用真实模型把 research 输出压缩成结构化证据包 |
| decider 行为 | 必须真实模型决策 | 最终预测必须由真实 OpenRouter 模型产生 |
| 历史预测使用 | 禁止 | 新预测不得读取或引用历史 `prediction_versions` |
| 触发方式 | 手动点击 | 保持现有手动触发 |
| 可观测性 | 强化 | 需要记录每个阶段的执行模式、模型名、错误、耗时 |

## 3. 总体方案

### 3.1 核心思路

- `POST /api/predict/{match_id}` 继续作为唯一预测入口。
- 每次触发都创建一条新的 `prediction_runs` 记录，作为本次预测执行的审计主记录。
- 编排器固定执行三段：
  1. `research`
  2. `evidence`
  3. `decider`
- 三段都先尝试真实 OpenRouter。
- 如果 `research` 或 `evidence` 失败，则允许回退到本地 fallback 并继续。
- 如果 `decider` 失败，则整次预测失败，不生成新的 `prediction_version`。
- 只有当 `decider` 成功返回合法预测结构时，才落库到 `prediction_versions`，并同步更新 `matches.prediction`。

### 3.2 成功结果的两种语义

- `纯真实链路成功`
  - `research`、`evidence`、`decider` 三段都走真实 OpenRouter
  - `is_full_live_chain = true`
  - `has_any_fallback = false`
- `部分 fallback 但结果可用`
  - `research` 或 `evidence` 至少一段走了 fallback
  - `decider` 仍为真实 OpenRouter
  - `is_full_live_chain = false`
  - `has_any_fallback = true`

这样可以避免把“成功返回预测”与“纯真实链路成功”混为一谈。

## 4. 阶段设计

### 4.1 Research 阶段

`research` 负责赛前信息规划、搜索执行和资料整理。

真实链路要求：
- 使用独立的 research OpenRouter 模型配置。
- 启用 `web` 插件，使模型能够自己决定搜索、打开页面和整理结果。
- 由模型同时完成：
  - 搜索规划
  - 实际搜索
  - 打开搜索结果
  - 提炼页面信息
  - 生成结构化 `search_plan`、`search_trace`、`search_documents`

输出要求：
- `search_plan`
  - 本次研究的查询主题、查询词、来源策略
- `search_trace`
  - 实际执行的查询、打开的 URL、回合数、完成状态
- `search_documents`
  - 每条文档包含 `title`、`url`、`domain`、`source_tier`、`fetched_at`、`content_text` 等

失败后 fallback：
- 触发条件包括：
  - OpenRouter 配置缺失
  - 超时
  - 上游 HTTP 错误
  - 返回内容无法解析为合法结构
  - 返回结构虽合法但文档无效或为空
- fallback 后继续使用本地 `FakePredictionResearcher`
- 同时在阶段记录中保留真实失败原因

### 4.2 Evidence 阶段

`evidence` 负责把 research 全量结果压缩为适合最终决策的证据包。

真实链路要求：
- 使用独立的 evidence OpenRouter 模型配置。
- 输入只包括：
  - `match_facts`
  - `search_plan`
  - `search_trace`
  - `search_documents`
- 模型不得再次联网搜索。
- 模型输出必须是结构化 `evidence_bundle`。

输出重点：
- 支持主队的证据
- 支持客队的证据
- 中性因素
- 市场观点
- 冲突与不确定性
- 高置信摘要

失败后 fallback：
- 触发条件与 research 类似，包括超时、上游错误、JSON 非法、结构无效等
- fallback 后使用本地 `FakePredictionEvidenceSynthesizer`
- 必须把真实 evidence 阶段的失败原因保留到阶段记录中

### 4.3 Decider 阶段

`decider` 负责生成最终预测结果，是唯一允许写入 `prediction_versions` 的阶段。

真实链路要求：
- 使用独立的 decider OpenRouter 模型配置。
- 输入仅包括：
  - `match_facts`
  - `evidence_bundle`
- 不允许读取或引用历史 `prediction_versions`
- 输出必须满足现有 prediction schema

失败策略：
- `decider` 不允许 fallback
- 一旦失败，整次 `prediction_run` 标记为 `failed`
- 不创建新的 `prediction_version`
- API 返回 `502`

## 5. 运行记录设计

### 5.1 保留现有字段

继续保留现有 `prediction_runs` 字段：
- `planner_model`
- `synthesizer_model`
- `decider_model`
- `document_count`
- `used_fallback_sources`
- `error_message`
- `search_plan_json`
- `search_trace_json`
- `search_documents_json`
- `evidence_bundle_json`

### 5.2 新增链路追踪字段

新增 `stage_trace_json`，用于记录三阶段的细粒度执行信息。

建议结构：

```json
{
  "research": {
    "mode": "live",
    "model_name": "qwen/...",
    "elapsed_ms": 14321,
    "error_message": null
  },
  "evidence": {
    "mode": "fallback",
    "model_name": "fallback-evidence-v1",
    "elapsed_ms": 2210,
    "error_message": "OpenRouter evidence request timed out."
  },
  "decider": {
    "mode": "live",
    "model_name": "qwen/...",
    "elapsed_ms": 10983,
    "error_message": null
  }
}
```

### 5.3 新增顶层摘要语义

在 `prediction_runs` 中新增两个显式布尔字段：
- `is_full_live_chain`
- `has_any_fallback`

语义：
- `is_full_live_chain = true`
  - 三阶段都为 `live`
- `has_any_fallback = true`
  - `research` 或 `evidence` 至少一段为 `fallback`

这两个字段本阶段直接落库，不走 API 临时推导方案，避免后续统计和前端展示出现语义分叉。

## 6. API 设计

### 6.1 `POST /api/predict/{match_id}`

保持现有外层响应结构不变：

```json
{
  "match_id": "fwc2026-m001",
  "prediction": {},
  "cached": false
}
```

行为变化：
- 默认执行真实 OpenRouter 主链路
- `research/evidence` 失败时允许 fallback
- `decider` 失败时返回 `502`

### 6.2 `GET /api/matches/{match_id}/prediction-runs`

摘要列表增加以下字段：
- `planner_model`
- `synthesizer_model`
- `decider_model`
- `is_full_live_chain`
- `has_any_fallback`
- `used_fallback_sources`
- `error_message`

用于前端列表直接区分：
- 纯真实成功
- 带 fallback 成功
- 失败 run

### 6.3 `GET /api/prediction-runs/{prediction_run_id}`

详情接口增加返回：
- `stage_trace_json`
- 完整 `search_plan_json`
- 完整 `search_trace_json`
- 完整 `search_documents_json`
- 完整 `evidence_bundle_json`

供前端展示本次预测到底走了什么链路。

## 7. 编排与错误语义

### 7.1 状态流

保留并强化现有状态流：
- `running`
- `researching`
- `synthesizing`
- `deciding`
- `succeeded`
- `failed`

### 7.2 错误分类

`research/evidence` 失败但可恢复：
- 真实模型配置缺失
- 请求超时
- HTTP 上游错误
- 响应非 JSON
- 结构化结果不满足要求

处理方式：
- 记录 `stage_trace_json.{stage}.mode = fallback`
- 保留真实失败原因
- 用 fallback 结果继续后续流程

`decider` 不可恢复失败：
- 真实模型请求失败
- 响应非法
- prediction schema 校验失败

处理方式：
- `prediction_runs.status = failed`
- `stage_trace_json.decider.mode = failed`
- 不落新的 `prediction_versions`
- `/api/predict/{match_id}` 返回 `502`

## 8. 配置设计

三阶段继续使用独立配置：
- `prediction_research_openrouter_model_config_path`
- `prediction_research_openrouter_key_path`
- `prediction_evidence_openrouter_model_config_path`
- `prediction_evidence_openrouter_key_path`
- `prediction_openrouter_model_config_path`
- `prediction_openrouter_key_path`

约束：
- research 模型配置必须启用 `web`
- evidence 模型配置不启用 `web`
- decider 模型配置允许 `response-healing`

## 9. 测试策略

### 9.1 单元测试

- 真实 research 成功时，`stage_trace_json.research.mode = live`
- 真实 research 失败时，自动 fallback，且保留失败原因
- 真实 evidence 失败时，自动 fallback
- decider 失败时，整次 run 失败且不生成 `prediction_version`
- `is_full_live_chain` 与 `has_any_fallback` 语义正确

### 9.2 集成测试

- `POST /api/predict/{match_id}` 在四种场景下的行为：
  - 纯真实成功
  - research fallback
  - evidence fallback
  - decider 失败
- `GET /api/matches/{match_id}/prediction-runs` 返回新增摘要字段
- `GET /api/prediction-runs/{id}` 返回 `stage_trace_json`

### 9.3 真实端到端验证

- 使用已配置的真实 OpenRouter key 执行至少一次线上预测
- 验证 research、evidence、decider 三阶段都成功时：
  - `is_full_live_chain = true`
  - `has_any_fallback = false`
  - 三个模型名都为真实 OpenRouter 模型

## 10. 实施顺序

1. 为 `prediction_runs` 增加 `stage_trace_json` 与链路摘要字段。
2. 先补测试，定义真实链路与 fallback 行为。
3. 改造 `run_prediction` 编排器，记录每个阶段的模式、错误和耗时。
4. 改造 `research` 阶段，让真实 OpenRouter 成为默认主路径。
5. 改造 `evidence` 阶段，让真实 OpenRouter 成为默认主路径。
6. 收紧 `decider` 阶段，确保失败时不再隐式 fallback。
7. 调整 prediction-runs API 暴露新的链路字段。
8. 补做一次真实线上验证。

## 11. 推荐落地方案

本阶段推荐方案为：
- 保持单入口 `POST /api/predict/{match_id}`
- 以真实 OpenRouter 三阶段链路为主
- 只允许 `research/evidence` fallback
- `decider` 强制真实模型
- 用 `prediction_runs` 承担链路审计
- 用 `prediction_versions` 承担最终结果历史

这个方案兼顾了三点：
- 结果可用性：真实 research/evidence 偶发失败时仍可产出预测
- 结果可解释性：前端和后端都能明确知道这次是不是纯真实链路
- 实施成本可控：在现有 `prediction_runs` 架构上增量演进，不推翻已有实现
