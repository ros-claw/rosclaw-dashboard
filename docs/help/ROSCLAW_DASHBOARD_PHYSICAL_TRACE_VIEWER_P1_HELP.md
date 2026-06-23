# ROSClaw Dashboard Help 清单

> 生成时间：2026-06-23
> 对应分支：`feature/physical-trace-viewer`
> 对应 PR：#1 (ros-claw/rosclaw-dashboard)
> 验收指南：`ROSClaw_v1.0_深入验收指南.md`
> 优化方案：`/home/ubuntu/rosclaw/rosclaw/rosclaw_dashboard优化v1.md`

---

## 1. 我已经做了什么

### 1.1 前期：Physical Trace Viewer P1

在 `feature/physical-trace-viewer` 分支完成了 Dashboard 基础能力：

- **后端（FastAPI）**：运行索引、运行列表/详情/事件/失败分析/回放清单、静态资源、导出任务、实时事件 WebSocket、系统状态聚合、MCP 工具网关、Memory 解释、How 恢复、Forge Bundle、防火墙拦截。
- **前端（Next.js）**：运行列表、Trace Viewer、多轨时间轴、同步回放引擎、导出 UI、系统状态首页、Sandbox Replay、Firewall Blocks、Memory Browser、Forge Bundle Viewer。
- **测试**：后端 52 passed，前端类型检查 clean，前端单元测试 6 passed。

### 1.2 本次：Runtime Evidence Center 优化 v1（Phase 2A–2D）

根据优化方案完成四阶段闭环：

#### Phase 2A — 契约与模块模式

- `apps/api/src/models/schemas.py` 新增 `ModuleMode`、`ModuleStatus`、`RosclawEventEnvelope`。
- `apps/api/src/contracts/` 新增事件信封/模块状态/迹线事件契约层。
- `apps/api/src/routers/status.py` 升级，返回每个模块的 `mode`、`message`、`endpoint`、`last_updated`、`evidence`。
- `apps/web/src/components/ModeBadge.tsx` + `app/page.tsx` 展示模式徽章与提示。
- 测试：`test_status_modes.py`、`test_contracts.py`。

#### Phase 2B — EventBus 适配器与实时会话

- `apps/api/src/adapters/eventbus/`：抽象 `EventBusAdapter`，实现 `InMemoryEventBusAdapter`（mock）与 `JsonlTailAdapter`（real，tail JSONL 事件文件，支持死信）。
- `apps/api/src/adapters/practice/`：抽象 `PracticeStoreAdapter`，实现 `LocalPracticeStoreAdapter`（fixture）。
- `apps/api/src/services/live_session_manager.py`：实时会话生命周期管理、事件缓冲、WebSocket 广播、live → closing → offline 切换，关闭后自动落盘并重新索引为 practice run。
- `apps/api/src/routers/live.py`：`/api/live/sessions`、`/api/live/{id}`、`/api/live/{id}/attach-run`、`/api/live/{id}/close`、`WS /api/live/{id}/events`。
- `apps/web/src/hooks/useLiveTrace.ts` 与 `LiveTracePanel.tsx`、`app/runs/page.tsx` 支持 session 作用域 WebSocket 与 offline_ready 横幅。
- 测试：`test_eventbus_adapter.py`、`test_live_session.py`、`test_live_offline_switch.py`。

#### Phase 2C — Evidence Graph

- `apps/api/src/services/evidence_graph.py`：从迹线事件构建证据图，节点/边来自时序关系、同一实体与显式链接。
- `apps/api/src/routers/evidence.py`：`/api/runs/{run_id}/evidence`、`/api/runs/{run_id}/failures/{failure_id}/evidence`、`/api/runs/{run_id}/sandbox/decisions`、`/api/runs/{run_id}/memory/events`、`/api/runs/{run_id}/provider/traces`、`/api/runs/{run_id}/how/recoveries`。
- `apps/web/src/components/trace/EvidenceChain.tsx`：垂直证据链 UI（Task → Plan → Provider → Action → Sandbox → Failure → Memory → How）。
- 测试：`test_evidence_graph.py`。

#### Phase 2D — 验收证据报告

- `apps/api/src/services/report_generator.py`：汇总运行摘要、模块模式、失败/安全/回放/导出/证据图数据，生成 PASS / PARTIAL / FAIL 裁决，输出 `report.json`、`report.md`、`bundle.zip`。
- `apps/api/src/routers/report.py`：`POST /api/runs/{run_id}/report`、`GET /api/runs/{run_id}/report`、`GET /api/runs/{run_id}/report/download`。
- `apps/web/app/runs/[runId]/report/page.tsx`：生成/查看/下载验收报告页面。
- `apps/web/src/components/export/ExportPanel.tsx`：增加 “Acceptance Report” 入口。
- 测试：`test_report_generator.py`。

### 1.3 本次：与 rosclaw 集成及 PyPI 发版

- 将 dashboard 后端重组为独立 Python 包 `rosclaw_dashboard`（`apps/api/src/rosclaw_dashboard`），所有内部 import 统一为 `rosclaw_dashboard.*`。
- 新增 `apps/api/src/rosclaw_dashboard/serve.py` 与 `__init__.py`，提供 `get_app()` / `serve()` / `main()` 入口。
- 重写 `apps/api/pyproject.toml`：包名 `rosclaw-dashboard`，版本 `1.0.0`，hatchling 构建，控制台脚本 `rosclaw-dashboard-serve`。
- 前端 Next.js 增加 `DASHBOARD_STATIC_EXPORT=1` 静态导出配置，构建产物输出到 `apps/api/src/rosclaw_dashboard/static`，随 wheel 一起打包。
- 新增 `apps/api/src/rosclaw_dashboard/core/workspace.py`，对齐 ROSClaw 工作区解析：显式路径 > `ROSCLAW_HOME` > `~/.rosclaw`。
- `apps/api/src/rosclaw_dashboard/core/config.py` 默认目录对齐 rosclaw：`data/practice/runs`、`artifacts/episodes`、`events`、`dashboard/exports`、`dashboard/reports`。
- 新增 `RosclawEpisodeStoreAdapter`（`adapters/practice/rosclaw_episode_store.py`），直接读取 `~/.rosclaw/artifacts/episodes/<id>/` 的 `metadata.json`、`events.jsonl`、`trajectory.jsonl`、`provider_trace.jsonl`，把 ROSClaw runtime episode 暴露为 dashboard run。
- 在 `rosclaw` 侧新增持久化 JSONL EventSink（`rosclaw/core/event_sink.py`），把 EventBus 全量事件写入 `~/.rosclaw/events/live.jsonl`，供 dashboard `JsonlTailAdapter` tail 读取。
- 在 `rosclaw` 侧新增 dashboard launcher（`rosclaw/dashboard/launcher.py`）：优先尝试 `rosclaw_dashboard.serve.serve`，未安装则回退到内置轻量 dashboard。
- `rosclaw/pyproject.toml` 新增 optional dependency `dashboard = ["rosclaw-dashboard>=1.0.0"]`。
- 已发布 `rosclaw-dashboard==1.0.0` 到 PyPI：https://pypi.org/project/rosclaw-dashboard/1.0.0/

---

## 2. 当前状态

| 项目 | 状态 |
|---|---|
| 当前分支 | `feature/physical-trace-viewer` |
| PR #1 状态 | `OPEN`，未合并（用户要求不合并）；已推送本次优化（packaging、episode adapter、PyPI v1.0.0） |
| 后端测试 | **71 passed / 8 failed**（失败项为已知的 acceptance-gap 用例与 export 全 suite 时序隔离问题，单独跑可过） |
| 前端类型检查 | clean |
| 前端单元测试 | 6 passed |
| CI 检查 | 仓库未配置 GitHub Actions / PR checks |
| 未提交文件 | `FEEDBACK`、`ROSClaw_v1.0_深入验收指南.md`（按安全要求不提交） |

---

## 3. 对照验收指南还缺什么

### 3.1 P0 阻塞项（当前 Dashboard 单独无法闭环）

| P0 | 指南要求 | 当前状态 | 缺口说明 |
|---|---|---|---|
| P0-1 | `rosclaw init / doctor / start / status` 一键安装启动 | **未涉及** | Dashboard 只提供 `/api/status`，没有 `rosclaw` CLI 与 Runtime 生命周期管理 |
| P0-2 | Claude Code 作为真实用户调用 provider、运行任务 | **部分涉及** | Dashboard 暴露 MCP tools，但 provider 是 mock 注册表，没有真实 LLM/VLM/skill/critic 推理与路由 |
| P0-3 | Event Bus 真实跨模块事件流 | **部分涉及** | 已提供 `JsonlTailAdapter` 可接入外部 JSONL 事件流，但尚未对接真实 Runtime/Kafka/Redis/NATS 总线 |
| P0-4 | Practice 记录完整 episode 到 `.rosclaw/artifacts/episodes/` | **部分涉及** | Dashboard 能读取并展示 fixture 中的 episode 字段，但真实的 `rosclaw practice list/show/replay` CLI 与目录生成不在本 repo |
| P0-5 | Memory 能回答真实问题（含相似历史、恢复建议） | **部分涉及** | Dashboard Memory/How 基于规则与历史匹配，未接入 LLM；语义理解与根因分析能力有限 |
| P0-6 | How 失败 → 恢复建议 → 下一轮任务应用 | **部分涉及** | Dashboard 能生成 recovery hint，但“下一轮任务自动应用参数 patch”需要 Runtime / Practice 闭环 |
| P0-8 | Dashboard 看到完整 trace | **基本满足** | 已能加载运行、展示时间轴、回放、失败分析、导出、证据图、验收报告 |

### 3.2 L0–L5 分层对照

| 层级 | 指南要求 | 当前状态 |
|---|---|---|
| L0 安装启动 | `rosclaw init/doctor/start/status` 全绿 | **部分涉及**：Dashboard 提供 `/api/status` 聚合健康度，但 CLI 与 Runtime 启动不在本 repo |
| L1 模块契约 | 各模块 API 契约清晰 | **已升级**：新增 `ModuleMode`、`ModuleStatus`、`RosclawEventEnvelope`、适配器契约，模式透明 |
| L2 Claude Code 接入 | MCP tools 可调用 ROSClaw | **已涉及**：`/api/mcp/tools` + `/api/mcp/call` 暴露 8 个稳定工具 |
| L3 单机器人任务 | 小车 PID、机械臂 reach、抓取、巡检、G1 行走 | **未涉及**：只有 mock fixture，没有真实物理仿真 |
| L4 失败恢复与记忆 | Memory 解释、How 恢复、第二轮改进 | **已涉及**：Dashboard 端接口与 UI 已具备，但需真实 episode 与 Runtime 配合才能形成“失败→恢复→重试”闭环 |
| L5 自扩展 | Forge 生成 bundle、Critic validation | **已涉及**：Forge compile/validate/re-validate 已可用，但生成的是模板代码，需与真实 `sdk_to_mcp` / Asset Forge 编译器对接 |

### 3.3 六大验收场景对照

| 场景 | 当前状态 | 缺口 |
|---|---|---|
| A 小车 PID | **不可运行** | 无真实 mobile base profile、PID provider、仿真环境 |
| B 机械臂 reach | **不可运行** | 无真实 URDF / e-URDF、MuJoCo/MoveIt sandbox、碰撞/工作空间检查 |
| C 红杯子抓取 | **不可运行** | 无 VLM 感知、grasp skill、critic、真实仿真 |
| D Unitree Go2 巡检 | **不可运行** | 无导航/巡检 provider、VLN、多点位任务分解 |
| E G1 行走仿真 | **不可运行** | 无人形 robot profile、walking policy、跌倒检测 |
| F Forge 自扩展 | **部分可运行** | Dashboard Forge 可生成并校验 bundle，但缺少与真实 compiler/staging/Claude 可见新 tool 的对接 |

### 3.4 Dashboard 专项验收点对照

| 验收点 | 当前状态 | 备注 |
|---|---|---|
| Runtime Overview | **有** | 首页 `/api/status` 状态卡片，含模块模式徽章 |
| Provider Health | **部分有** | `/providers` 页面存在，但数据是 mock 随机数；已增加 provider traces 证据接口 |
| Robot Registry | **有** | 首页 `/` 与 `/robots` 相关能力 |
| Sandbox Replay | **有** | `/sandbox` 页面；新增 sandbox decisions 证据接口 |
| Firewall Blocks | **有** | `/safety` 页面新增 Firewall Blocks 面板 |
| Practice Timeline | **有** | `/runs` + `/runs/[runId]` |
| Memory Browser | **有** | `/memory` 页面；新增 memory events 证据接口 |
| Event Bus Monitor | **部分有** | `/events` 页面与 WebSocket 存在；新增 `JsonlTailAdapter` 可 tail 外部 JSONL；`rosclaw` 侧新增 `JsonlEventSink` 持久化到 `~/.rosclaw/events/live.jsonl` |
| Rosclaw Episode Adapter | **有** | `RosclawEpisodeStoreAdapter` 直接读取 `~/.rosclaw/artifacts/episodes/<id>/` 的 metadata、events、trajectory、provider_trace |
| Forge Bundle Viewer | **有** | `/forge` 页面 |
| Acceptance Report | **有** | `/runs/[runId]/report` 页面 + `/api/runs/{id}/report` API |
| Evidence Graph | **有** | `/api/runs/{id}/evidence` + `EvidenceChain.tsx` 组件 |
| Live Session | **有** | `/api/live/*` + `useLiveTrace(sessionId)` + live-to-offline 切换 |

---

## 4. 可以在 dashboard repo 内继续补齐的（不需要外部仿真/CLI）

1. **Know 模块页面**
   - 验收指南要求 Know 能在遇到新机器人/SDK 时先查知识再决定 Forge/Provider。
   - Dashboard 当前没有 Know 模块，可在 repo 内新增 `/know` 页面 + `routers/know.py` + 知识库 CRUD。

2. **Event Bus Monitor 增强**
   - 增加 topic 过滤、事件类型统计、按 robot/mission 过滤、事件详情弹窗。
   - 在 `JsonlTailAdapter` 基础上增加 Kafka/Redis/NATS 适配器（如外部提供协议）。

3. **Provider Health 页面升级**
   - 展示 provider schema、输入输出示例、latency/success_rate 趋势图。
   - 增加 provider fallback 记录与错误日志面板。

4. **Robot Registry 增强**
   - 展示 robot capabilities、joint limits、collision links、e-URDF 可视化入口。
   - 支持 `rosclaw robot inspect <robot_id>` 的等效 UI。

5. **E2E 测试建立**
   - 仓库已有 Playwright 依赖但无运行中的 e2e。
   - 可补全 `apps/web/e2e/trace-viewer.spec.ts` 的本地启动脚本与 CI 集成。

6. **LLM-based Memory / How（可选）**
   - 若提供 LLM API key，可将 `/api/memory/explain` 与 `/api/how/recovery` 从规则版升级为 LLM 版。

---

## 5. 需要外部支持（非 dashboard repo 能独立完成）

| 支持项 | 为什么需要 | 期望形态 |
|---|---|---|
| `rosclaw` CLI / Runtime | P0-1 一键安装启动 | 独立的 `rosclaw` 命令行与 runtime 守护进程 |
| 真实 Event Bus | P0-3 跨模块事件流 | Redis / NATS / Kafka 或 runtime 自带 event bus，Dashboard 可订阅；当前 `JsonlTailAdapter` 已可作为 JSONL 形态过渡 |
| Sandbox 物理仿真 | P0-4 / L3 真实任务 | MuJoCo / Isaac Sim / Gazebo backend，能执行 `ALLOW/BLOCK/MODIFY` |
| Provider Router + 真实 Provider | P0-2 / L3 | LLM / VLM / skill / critic provider，能真实推理并返回 schema 化结果 |
| Practice Runtime 记录器 | P0-4 完整 episode | 在任务运行时写入 `.rosclaw/artifacts/episodes/<ep_id>/` 目录结构 |
| e-URDF-Zoo / Robot Profiles | L3 机器人任务 | 标准化 robot profile、capabilities.yaml、joint limits、collision links |
| Know 知识库（若不放 dashboard） | 模块级验收 | 文档/模板/约束知识库，可被 Agent 查询 |
| LLM 服务 | L4/L5 语义能力 | 用于 Memory 根因分析、How 策略生成、Forge 代码生成 |

---

## 6. 我的困惑 / 待确认

1. **Know 模块归属**：验收指南把 Know 列为独立模块。请问 Know 应该在 dashboard repo 内实现（作为一个知识库页面+API），还是由外部 `rosclaw-know` 服务提供？
2. **Event Bus 对接方式**：Dashboard 已提供 `JsonlTailAdapter` 作为 JSONL 文件形态的 real adapter。外部 Runtime 最终准备用哪种消息中间件（Redis Pub/Sub、NATS、Kafka、gRPC stream）？我好提前做适配。
3. **真实仿真 fixture**：是否有现成的 MuJoCo / Isaac Sim 场景和机器人模型可以接入 Dashboard 做集成测试？目前只有 JSON fixture。
4. **Provider Router 实现**：`rosclaw-provider` 是否有独立 repo 或接口定义？Dashboard 的 `/api/mcp/call` 现在只能列出 mock provider，需要真实路由契约。
5. **是否继续补 dashboard 内部能力**：在 L3 真实任务还跑不通的情况下，是否优先把 dashboard 内的 Know、Event Bus Monitor、Provider Health、E2E 补齐，还是先等外部模块 ready？
6. **PR 合并时机**：PR #1 目前可干净合并、测试通过。用户之前要求“不用你合并”。是否保持 open，等待外部模块一起验收后再合并？
7. **FEEDBACK 文件处理**：`FEEDBACK` 文件内容为空（仅 1 行）。是否需要我在其中补充本次验收缺口，还是它由你维护？

---

## 7. 下一步建议

### 短期（Dashboard 内部可闭环）

1. 新增 Know 知识库页面与 API（若决定放在 dashboard）。
2. 补齐 Event Bus Monitor 过滤/统计能力，或增加 Kafka/Redis/NATS adapter。
3. 补齐 Provider Health 页面（schema、latency 趋势、错误日志）。
4. 跑通 Playwright E2E 测试。

### 中期（需外部模块配合）

1. 与 Runtime 团队确认 event bus 协议，完成订阅对接。
2. 与 Sandbox 团队确认 `sandbox_result` / `replay_id` 输出格式，让 Dashboard 回放真实 sandbox replay。
3. 与 Provider 团队确认 provider router API，替换 mock provider。

### 长期（验收日必备）

1. 至少跑通 1 个真实场景（建议先 A 小车 PID 或 B 机械臂 reach）。
2. 生成一份完整的 `ROSClaw v1.0 Acceptance Report`（按指南第八节模板），Dashboard 已具备生成器，只需真实运行数据。

---

## 8. 联系方式 / 需要我做什么

如果你希望我：

- 继续补齐 dashboard 内部能力（Know / Event Bus Monitor / Provider Health / E2E），请指定优先级。
- 等待外部模块 ready 后再集成，请告知 expected timeline。
- 授权合并 PR #1，请明确说明（之前你要求不合并）。
- 将当前优化工作更新到 PR #1 或创建新 PR，请告知。
- 生成更详细的模块对接文档或 OpenAPI 契约，我可以继续写。
