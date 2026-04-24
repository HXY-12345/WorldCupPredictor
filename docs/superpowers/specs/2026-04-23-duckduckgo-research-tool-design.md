# WorldCup Predictor DuckDuckGo Research 工具链设计
**日期**: 2026-04-23  
**状态**: 待用户 Review

## 1. 目标与范围

### 1.1 目标

- 将 `research` 阶段的联网搜索能力从 OpenRouter `web` 插件切换为后端本地 DuckDuckGo 搜索工具。
- 保持现有预测主链路不变：
  - `POST /api/predict/{match_id}` 仍是唯一手动触发入口
  - 编排仍为 `research -> evidence -> decider`
- 让 `research` 模型通过工具调用方式自主决定：
  - 搜索哪些 query
  - 搜索几轮
  - 何时结束搜索并整理最终 research 结果
- 保持现有可观测性模型：
  - `prediction_runs.stage_trace_json`
  - `search_trace_json`
  - `search_documents_json`
- 保持现有 fallback 语义：
  - `research` 失败允许 fallback
  - `evidence` 失败允许 fallback
  - `decider` 不允许 fallback

### 1.2 非目标

- 本阶段不开放 DuckDuckGo 工具给 `evidence` 或 `decider`。
- 本阶段不做网页正文抓取，只做搜索结果级别的资料收集。
- 本阶段不读取或引用历史 `prediction_versions`。
- 本阶段不引入异步任务队列，仍保留同步手动触发。
- 本阶段不做多工具编排，不加入浏览器自动化或 HTML 正文抽取器。

## 2. 已确认决策

| 决策项 | 选择 | 说明 |
|---|---|---|
| 工具开放范围 | 仅 `research` | `evidence / decider` 继续保持离线输入边界 |
| 搜索来源 | DuckDuckGo | 由后端本地工具执行 |
| 工具调用方式 | 模型 tool calling 循环 | 模型自主决定 query 与轮次 |
| 第一版资料粒度 | 搜索结果摘要 | `snippet` 直接作为 `content_text` |
| 网页正文抓取 | 不做 | 避免复杂度、延迟与失败面扩大 |
| 历史预测参与 | 禁止 | 新预测不读旧 `prediction_versions` |
| 触发方式 | 手动点击 | 不引入自动调度 |

## 3. 设计概览

### 3.1 核心思路

- 保留现有 `OpenRouterPredictionResearcher` 的职责边界，但把“联网能力”从 OpenRouter 平台插件切换为本地工具循环。
- `research` 阶段内部改为三层：
  1. Research LLM 会话控制
  2. 本地 DuckDuckGo 搜索工具执行
  3. 结构化 research 输出归一化
- 模型不直接访问外网搜索插件，而是通过后端提供的工具接口发出搜索请求。
- 后端负责：
  - 执行真实 DuckDuckGo 搜索
  - 限制单次结果数与总轮次
  - 记录工具调用轨迹
  - 在超时或异常时转入 fallback

### 3.2 与现有链路的关系

- `research`：
  - 从“OpenRouter + web 插件”改为“OpenRouter + 本地 DuckDuckGo 工具”
- `evidence`：
  - 输入仍为 `match_facts + search_plan + search_trace + search_documents`
  - 不新增联网能力
- `decider`：
  - 输入仍为 `match_facts + evidence_bundle`
  - 不新增联网能力

因此这次改动只替换 `research` 的联网执行方式，不改变后两段的输入契约。

## 4. Research 阶段设计

### 4.1 新的执行模型

`research` 阶段改为如下流程：

1. 后端构造 research 系统提示词与用户输入：
   - `match_facts`
   - research 任务说明
   - 工具使用约束
2. OpenRouter Research 模型收到一个可调用的本地工具：
   - `duckduckgo_search`
3. 模型可进行 0 到 N 轮工具调用。
4. 每次工具调用由后端执行真实 DuckDuckGo 搜索并把结果回填给模型。
5. 模型在结束时输出最终结构化 research JSON：
   - `search_plan`
   - `search_trace`
   - `search_documents`
   - `used_fallback_sources`
6. 若任一步骤失败，则回落到 `FakePredictionResearcher`。

### 4.2 工具定义

第一版只实现一个最小工具：

`duckduckgo_search(query: str, max_results: int) -> { results: [...] }`

返回结构：

```json
{
  "results": [
    {
      "title": "Mexico vs South Africa preview",
      "url": "https://example.com/preview",
      "domain": "example.com",
      "snippet": "Mexico enters with steadier recent form and venue familiarity."
    }
  ]
}
```

约束：

- `query` 必填，空字符串视为非法调用。
- `max_results` 由后端裁剪到安全区间，建议最大值为 `5`。
- 工具不负责网页正文抓取。
- 工具不负责翻页。
- 工具不返回 HTML 原文，只返回标准化结果对象。

### 4.3 工具调用循环

Research LLM 循环应支持：

- 模型返回工具调用请求
- 后端执行工具并回填 `tool` 消息
- 模型继续决定是否追加搜索
- 直到模型输出最终 research JSON 或命中终止条件

终止条件：

- 模型输出了合法 research JSON
- 超过最大工具调用轮次
- 超过整体 research 超时
- 工具调用参数非法
- OpenRouter 上游失败

建议的安全上限：

- 最大工具调用轮次：`4`
- 单次搜索最大结果数：`5`
- 整体 research 超时：单独配置，默认高于当前 45 秒

### 4.4 搜索结果到文档的映射

DuckDuckGo 工具结果需映射为现有 `search_documents` 结构：

```json
{
  "query": "Mexico vs South Africa preview",
  "title": "Mexico vs South Africa preview",
  "url": "https://example.com/preview",
  "domain": "example.com",
  "source_tier": "search",
  "published_at": null,
  "fetched_at": "2026-04-23T08:30:00Z",
  "content_text": "Mexico enters with steadier recent form and venue familiarity.",
  "content_hash": "..."
}
```

说明：

- `content_text` 先使用 DuckDuckGo 返回的 `snippet`
- `source_tier` 第一版固定为 `search`
- `published_at` 第一版允许为空

### 4.5 search_plan / search_trace 语义

模型最终输出的 `search_plan` 继续表示研究意图：

- query 列表
- 主题分组
- 资料策略

后端维护并补强 `search_trace`，至少包含：

```json
{
  "completed": true,
  "tool_name": "duckduckgo_search",
  "round_count": 2,
  "executed_queries": [
    {
      "query": "Mexico vs South Africa preview",
      "max_results": 5,
      "result_count": 5
    }
  ],
  "generated_from_match_facts": false,
  "fallback_mode": null,
  "fallback_reason": null
}
```

如果发生 fallback，则：

- `completed` 仍按 fallback 结果语义写入
- `fallback_mode` 标记为本地 fallback 模式
- `fallback_reason` 记录真实失败原因

## 5. 配置设计

### 5.1 新配置项

在现有 `prediction_research_*` 配置基础上，新增 DuckDuckGo 工具配置：

- `prediction_research_duckduckgo_enabled`
- `prediction_research_duckduckgo_timeout_seconds`
- `prediction_research_duckduckgo_max_rounds`
- `prediction_research_duckduckgo_max_results_per_query`

### 5.2 既有配置的变化

- `prediction_research_openrouter_model_config_path`
- `prediction_research_openrouter_key_path`

继续保留，但对 Research 的约束变为：

- 不再依赖 OpenRouter `web` 插件
- Research 模型配置中的 `enable_web_plugin` 可以关闭
- Research 模型需要支持工具调用

## 6. 错误处理与 fallback

### 6.1 Research 可恢复失败

以下情况视为 `research` 可恢复失败：

- Research 模型配置缺失
- OpenRouter 请求超时
- OpenRouter HTTP 错误
- 工具循环超过最大轮次
- DuckDuckGo 搜索失败
- 工具返回空结果且模型无法产出合法 research
- 最终 research JSON 非法
- 整体 research 超时

处理方式：

- 记录 `stage_trace_json.research.mode = fallback`
- `stage_trace_json.research.error_message` 保留真实失败原因
- 回落到 `FakePredictionResearcher`
- `search_trace_json` 补写 `fallback_reason`

### 6.2 Evidence / Decider 不变

- `evidence` 继续按现有 live/fallback 规则执行
- `decider` 继续保持 fatal failure 语义
- `/api/predict/{match_id}` 的对外响应契约不变

## 7. API 与落库影响

本次不新增 API 路由。

保留既有：

- `POST /api/predict/{match_id}`
- `GET /api/matches/{match_id}/prediction-runs`
- `GET /api/prediction-runs/{prediction_run_id}`

变化只体现在返回内容的数据语义上：

- `search_trace_json` 现在体现 DuckDuckGo 工具调用轨迹
- `search_documents_json` 现在来自 DuckDuckGo 搜索结果摘要
- `planner_model` 仍为 research 模型名
- `is_full_live_chain` 的 `research=live` 语义改为：
  - 研究模型成功
  - 本地 DuckDuckGo 工具调用链成功
  - 未触发 fallback

## 8. 测试策略

### 8.1 单元测试

新增或扩展以下测试场景：

- Research 模型发起单次 DuckDuckGo 工具调用后成功输出 research JSON
- Research 模型发起多次 DuckDuckGo 工具调用后成功输出 research JSON
- DuckDuckGo 工具结果被正确映射到 `search_documents`
- `search_trace_json` 正确记录 query、轮次、结果数
- 工具参数非法时，Research 进入 fallback
- DuckDuckGo 搜索异常时，Research 进入 fallback
- 工具循环超轮次时，Research 进入 fallback

### 8.2 集成测试

- `POST /api/predict/{match_id}` 在 Research 工具链 live 成功时：
  - `research.mode = live`
  - `is_full_live_chain` 可为 `true` 或取决于后续阶段
- `POST /api/predict/{match_id}` 在 Research 工具链失败时：
  - `research.mode = fallback`
  - `fallback_reason` 正确落库
- Prediction-runs 详情接口能看到 DuckDuckGo 工具轨迹

### 8.3 真实端到端验证

至少完成一次真实验证，证明：

- Research 没有使用 OpenRouter `web` 插件
- Research 通过后端 DuckDuckGo 工具完成搜索
- 最新 `prediction_run.stage_trace_json.research.mode = live`
- `search_trace_json.tool_name = duckduckgo_search`

## 9. 实施顺序

1. 先补 Research 工具调用循环的失败测试
2. 新增本地 DuckDuckGo 搜索适配层
3. 扩展 OpenRouter 调用层以支持 Research 工具调用
4. 改造 `OpenRouterPredictionResearcher`
5. 补齐 `search_trace_json` 与 `search_documents_json` 映射
6. 跑后端回归
7. 做真实联调验证

## 10. 推荐落地方案

推荐采用“最小本地工具 + Research 模型 tool calling 循环”的方案：

- 能满足“模型调用工具去搜索”的核心目标
- 不破坏 `evidence / decider` 的现有边界
- 能直接复用现有 prediction-runs 可观测体系
- 能把复杂度控制在单一 research 子系统内

本设计通过后，再进入实现计划阶段。
