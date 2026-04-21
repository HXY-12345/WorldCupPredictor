# WorldCup Predictor 准确率优先预测增强设计
**日期**: 2026-04-22  
**状态**: 待用户 Review

## 1. 目标与范围

### 1.1 目标

- 将当前主要依赖比赛静态事实的预测流程，升级为“赛前信息检索增强”的预测流程。
- 在保持现有 `POST /api/predict/{match_id}` 接口不变的前提下，提高赛前预测，尤其是胜负预测的准确率。
- 让每次手动预测都具备完整可审计链路，包括搜索计划、搜索轨迹、抓取全文、证据提炼和最终结论。
- 为后续预测复盘、来源效果分析和预测详情页提供稳定的数据基础。

### 1.2 非目标

- 本阶段不做自动定时预测，只保留手动点击触发。
- 本阶段不做跨请求搜索缓存；每次点击都重新全量检索。
- 本阶段不引入结构化足球数据层；主要通过网页检索增强预测。
- 本阶段不做多模型投票；最终结论仍由单个模型直接拍板。
- 本阶段不优先追求比分、总进球等维度提升，准确率优化重点放在胜负预测。

## 2. 已确认决策

| 决策项 | 选择 | 说明 |
|---|---|---|
| 优化目标 | 准确率优先 | 优先提升胜负预测命中率 |
| 信息获取 | 网页检索增强 | 允许搜索比赛相关资料并综合判断 |
| 信息源边界 | 受控模式 | 官方信息 + 主流体育媒体 + 可靠数据站，赔率谨慎使用 |
| 来源策略 | 半白名单 | 优先固定域名，命中不足时允许补少量高相关来源 |
| 赔率策略 | 谨慎使用 | 可作为参考和校准信号，但不能主导最终结论 |
| 单次时延 | 重检索重分析 | 单场允许 `20-60` 秒 |
| 触发方式 | 仅手动触发 | 不做自动批量预测 |
| 调用次数 | `2-3` 次核心模型阶段 | Search Planner、Evidence Synthesizer、Prediction Decider 为核心阶段，Agent 检索回合需受限 |
| 历史预测 | 不参考历史版本 | 本次预测不能读取或引用历史预测结论 |
| 冲突处理 | 必须给结论 | 证据冲突时仍输出胜负，但降低置信度 |
| 搜索刷新 | 每次全量重搜 | 不复用最近搜索结果 |
| 全文落库 | 是 | 搜索抓到的网页正文入库 |
| 摘录落库 | 是 | 证据提炼结果也入库 |

## 3. 总体方案

### 3.1 核心思路

- 保留现有 `POST /api/predict/{match_id}` 作为唯一预测入口。
- 每次点击都会新建一个 `prediction_runs`，记录本次预测执行全过程。
- 预测流程拆成三段：
  - 检索研究
  - 证据提炼
  - 最终决策
- 最终预测成功后，继续写入 `prediction_versions`，并同步更新 `matches.prediction` 为最新摘要。

### 3.2 推荐架构

1. 前端点击“刷新 AI 预测”。
2. 后端创建 `prediction_runs`，状态置为 `running`。
3. `LLM Search Planner` 基于比赛事实生成搜索计划和查询词。
4. `Agent Collector` 使用联网能力执行真实搜索、点开页面、抓取正文，并在必要时补搜。
5. 系统把搜索轨迹和网页全文写入 `prediction_runs`。
6. `Evidence Synthesizer` 对全文进行结构化提炼，输出证据包。
7. 系统把证据包写入 `prediction_runs`。
8. `Prediction Decider` 基于比赛事实和证据包输出最终胜负结论。
9. 后端校验结构后写入 `prediction_versions`。
10. `prediction_runs` 关联成功生成的 `prediction_version_id`，状态更新为 `succeeded`。

## 4. 检索与证据策略

### 4.1 Search Planner

`Search Planner` 由大模型完成，负责：

- 根据比赛事实生成搜索主题，如球队近况、伤停、阵容、赛前分析、赔率倾向。
- 生成中英文查询词变体。
- 指定优先搜索的白名单来源类型。
- 决定何时触发补充检索。

`Search Planner` 不直接产生最终预测结论。

### 4.2 Agent Collector

`Agent Collector` 采用全 Agent 形态，由大模型决定：

- 先搜哪些查询词
- 打开哪些搜索结果
- 是否继续追踪详情页
- 是否补充搜索
- 何时结束本轮检索

系统层保留硬约束：

- 总耗时上限
- 最大抓取页面数
- 最大 Agent 搜索回合数
- 记录每次搜索和访问轨迹
- 记录来源是否来自白名单或补充来源
- 统一抽取并落库标题、URL、域名、抓取时间和正文全文

### 4.3 Evidence Synthesizer

`Evidence Synthesizer` 负责把网页全文压缩成结构化证据包，至少覆盖：

- 支持主队的证据
- 支持客队的证据
- 中性背景因素
- 赔率与市场倾向
- 伤停与阵容不确定性
- 明显冲突的信息点
- 可直接供最终决策使用的高置信摘要

### 4.4 Prediction Decider

`Prediction Decider` 只读取：

- 比赛事实
- 证据包

它不直接浏览网页全文，也不参考历史预测版本。最终由它直接输出胜负结论和置信度。

## 5. 数据模型

### 5.1 `prediction_versions`

继续保留现有职责，只记录每次成功预测的最终结果版本，用于：

- 前端展示最新预测
- 赛后评估
- 历史版本保留

`prediction_versions` 不承担执行过程审计职责。

### 5.2 `prediction_runs`

新增 `prediction_runs`，用于记录一次手动点击预测的完整执行过程。

推荐采用“混合型单对象”设计：

- 标量字段
  - `id`
  - `match_id`
  - `triggered_at`
  - `finished_at`
  - `status`
  - `prediction_version_id`
  - `planner_model`
  - `synthesizer_model`
  - `decider_model`
  - `elapsed_ms`
  - `document_count`
  - `used_fallback_sources`
  - `error_message`
- JSON 字段
  - `search_plan_json`
  - `search_trace_json`
  - `search_documents_json`
  - `evidence_bundle_json`

约束：

- 不冗余保存 `final_prediction_snapshot`
- 通过 `prediction_version_id` 关联最终结果
- 一次点击对应一条 `prediction_runs`

### 5.3 JSON 内容建议

`search_plan_json`：

- 搜索主题
- 查询词列表
- 来源优先级策略
- 补搜条件

`search_trace_json`：

- 实际执行过的查询
- 打开过的页面
- 补搜行为
- 过滤原因

`search_documents_json`：

- `query`
- `title`
- `url`
- `domain`
- `source_tier`
- `published_at`
- `fetched_at`
- `content_text`
- `content_hash`

`evidence_bundle_json`：

- 主队支持证据
- 客队支持证据
- 中性因素
- 市场倾向
- 冲突项
- 高置信摘要

## 6. 执行流程

### 6.1 成功路径

1. 前端调用 `POST /api/predict/{match_id}`。
2. 后端校验比赛存在且尚未开赛。
3. 后端创建 `prediction_runs`，状态写为 `running`。
4. 更新状态为 `researching`，执行 `LLM Search Planner` 和 `Agent Collector`。
5. 写入 `search_plan_json`、`search_trace_json`、`search_documents_json`。
6. 更新状态为 `synthesizing`，执行 `Evidence Synthesizer`。
7. 写入 `evidence_bundle_json`。
8. 更新状态为 `deciding`，执行 `Prediction Decider`。
9. 校验输出结构和业务约束。
10. 调用现有版本落库逻辑，创建新的 `prediction_versions`。
11. 回写 `prediction_runs.prediction_version_id`。
12. 更新状态为 `succeeded`，并写入 `finished_at` 和 `elapsed_ms`。

### 6.2 状态流

推荐状态流如下：

- `running`
- `researching`
- `synthesizing`
- `deciding`
- `succeeded`
- `failed`

这样便于定位失败发生在哪一段。

## 7. 置信度与冲突处理

### 7.1 证据冲突

当不同来源明显互相矛盾时：

- 系统仍然必须输出胜负结论
- 不允许返回“无法预测”
- 必须显著下调 `confidence`
- 必须在 `evidence_bundle_json` 和最终 `uncertainties` 中记录冲突点

### 7.2 赔率使用原则

- 赔率只作为市场倾向参考
- 不允许赔率主导最终结论
- 若赔率与球队近况、阵容信息明显冲突，应作为冲突项处理，而不是直接覆盖其他证据

### 7.3 证据不足

若可用证据不足但并非完全为空：

- 允许继续生成预测
- 必须降低 `confidence`
- 必须在 `uncertainties` 中明确说明证据不足原因

## 8. 错误处理与运行约束

### 8.1 硬失败

以下情况直接失败，不创建新的 `prediction_versions`：

- 比赛不存在
- 比赛已开赛
- 搜索链路整体失败且没有有效材料
- 最终模型输出不是合法 JSON
- 缺少核心字段
- 值域校验失败

发生硬失败时：

- `prediction_runs.status = failed`
- 保留已执行轨迹和已抓取材料
- 记录 `error_message`

### 8.2 软失败

以下情况允许继续预测，但必须降置信度：

- 部分来源打不开
- 白名单来源不足，需要启用补充来源
- 不同媒体报道冲突
- 阵容、伤停、赛前消息不稳定

### 8.3 并发与时延

- 同一场比赛同一时刻只允许一个活跃预测请求
- 若已有请求在运行，再次点击返回 `409`
- 单次预测总时长目标区间为 `20-60` 秒
- Agent 检索必须设置最大回合数，避免无限搜索
- 每次点击都重新全量检索，不复用上次搜索结果

## 9. API 设计

### 9.1 保留现有接口

- `POST /api/predict/{match_id}`

返回外层结构继续保持：

- `match_id`
- `prediction`
- `cached`

### 9.2 新增只读接口

- `GET /api/matches/{match_id}/prediction-runs`
  - 查看某场比赛的预测执行记录列表
- `GET /api/prediction-runs/{run_id}`
  - 查看单次 run 的搜索轨迹、全文和证据包
- `GET /api/matches/{match_id}/predictions`
  - 继续查看最终预测版本历史

## 10. 模块拆分

- `backend/api/predict.py`
  - 保留现有预测入口，只负责接口层和错误映射
- `backend/api/prediction_runs.py`
  - 提供 run 明细查询接口
- `backend/models/prediction_run.py`
  - 新增 `prediction_runs` ORM
- `backend/services/prediction_runs.py`
  - 作为单次预测执行的总编排器
- `backend/services/prediction_research.py`
  - 负责 Search Planner 和 Agent Collector
- `backend/services/prediction_evidence.py`
  - 负责证据提炼
- `backend/services/prediction_decider.py`
  - 负责最终决策
- `backend/services/predictions.py`
  - 收缩为版本落库和 `matches.prediction` 更新逻辑

## 11. 测试策略

### 11.1 单元测试

- `prediction_runs` 状态流转正确
- 比赛已开赛时不允许创建新预测版本
- 失败时不写 `prediction_versions`
- 成功时正确关联 `prediction_version_id`
- 每次成功预测版本号递增

### 11.2 研究阶段测试

- Search Planner 输出结构合法
- Agent Collector 能生成 `search_trace_json`
- 半白名单与补充来源标记正确
- 搜索全文能正确写入 `search_documents_json`

### 11.3 证据与决策测试

- Evidence Synthesizer 能从多篇全文提炼稳定证据包
- 冲突场景下仍然必须输出结论
- 证据不足时 `confidence` 会降低
- 最终输出满足现有 prediction schema

### 11.4 集成与端到端

- 跑通 `POST /api/predict/{match_id}` 到 `prediction_runs` 与 `prediction_versions` 的全链路
- 用真实 OpenRouter 配置对 1-2 场比赛执行真实预测
- 确认前端仍可消费最新预测摘要
- 确认 run 明细接口可复盘本次预测过程

## 12. 实施顺序

1. 新增 `prediction_runs` ORM、迁移和查询接口。
2. 将现有预测入口改造成 run 编排入口。
3. 先用可控假实现打通 `prediction_runs -> prediction_versions` 主链路。
4. 接入真实 `LLM Search Planner`。
5. 接入真实 `Agent Collector`。
6. 接入 `Evidence Synthesizer`。
7. 接入 `Prediction Decider`，替换当前直接预测逻辑。
8. 完成真实端到端验证。

## 13. 推荐落地方案

本阶段推荐落地方案为：

- 单模型最终拍板
- Agent 化检索增强
- 每次点击都全量重搜
- 全文与证据提炼同时落库
- `prediction_versions` 保持结果历史
- `prediction_runs` 承担执行过程审计

这是当前在准确率、可审计性、实现复杂度和后续扩展性之间最平衡的方案。
