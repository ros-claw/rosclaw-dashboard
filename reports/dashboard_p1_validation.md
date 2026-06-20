# ROSClaw Dashboard P1 Validation Report

> Physical Trace Viewer + Acceptance Gap Closure 验证报告
> Commit: `1cae574310cbad405bbd10ea93bc6b7261bce941`
> Date: 2026-06-21

## 1. 本次开发范围

本次 PR 在 **Dashboard → Physical Trace Viewer** P1 能力之上，进一步补齐《ROSClaw_v1.0_深入验收指南》中可在 dashboard repo 内闭环的 L0/L2/L4/L5 验收差距：系统状态聚合、MCP 工具网关、Memory 失败解释、How 恢复建议、Forge bundle 生成与校验。

### 1.1 后端能力

| 能力 | 说明 | 关键文件 |
| --- | --- | --- |
| 运行索引 | 扫描 `ROSCLAW_PRACTICE_DIR/<run_id>/manifest.json` 与 `timeline.jsonl` / `events/*.jsonl` | `apps/api/src/services/run_indexer.py` |
| 运行列表/详情 | `GET /api/runs`、`GET /api/runs/{run_id}` | `apps/api/src/routers/runs.py` |
| 事件查询 | `GET /api/runs/{run_id}/events`，支持 track、severity、entity、tag、时间窗口、全文搜索 | `apps/api/src/routers/runs.py` |
| 失败分析 | `GET /api/runs/{run_id}/failures`、`GET /api/runs/{run_id}/events/search`（关联事件） | `apps/api/src/routers/runs.py` |
| 回放清单 | `GET /api/runs/{run_id}/replay`：统一返回 media、curves、trajectory、sandbox_states、tracks | `apps/api/src/routers/runs.py` |
| 静态资源 | `GET /api/runs/{run_id}/media/{path:path}`、curves、trajectory 接口 | `apps/api/src/routers/runs.py` |
| 导出任务 | `POST /api/export`、`GET /api/export/{job_id}`、`GET /api/export`，支持 rlds / lerobot / failure_case / skill_candidate | `apps/api/src/routers/export.py`、`apps/api/src/services/export_jobs.py` |
| 实时事件 | WebSocket `/api/runs/live` 推送新增 trace 事件 | `apps/api/src/routers/runs.py` |
| **系统状态** | `GET /api/status` 聚合 runtime、event_bus、seekdb、registry、mcp_gateway、provider_router、sandbox、practice、memory、dashboard 健康状态 | `apps/api/src/routers/status.py` |
| **MCP 工具网关** | `GET /api/mcp/tools`、`POST /api/mcp/call`，提供 `list_robots`、`list_providers`、`run_sandbox_task`、`query_memory`、`explain_failure`、`compile_asset_bundle` | `apps/api/src/routers/mcp.py` |
| **Memory 解释** | `POST /api/memory/explain` 读取运行失败、生成“发生了什么/为什么失败”的语义解释并写入 episodic memory | `apps/api/src/routers/memory.py` |
| **How 恢复** | `POST /api/how/recovery` 基于失败类型生成恢复建议与参数补丁并写入 procedural memory | `apps/api/src/routers/how.py` |
| **Forge 生成/校验** | `POST /api/forge/compile`、`POST /api/forge/validate`、`GET /api/forge/bundles`：生成 MCP server / skill package / provider manifest / e-URDF patch / sandbox spec bundle，执行 Critic 校验并 staging | `apps/api/src/routers/forge.py` |

### 1.2 前端能力

| 能力 | 说明 | 关键文件 |
| --- | --- | --- |
| 运行列表 | `/runs` 页面，状态筛选、搜索、跳转 Trace Viewer | `apps/web/app/runs/page.tsx` |
| Trace Viewer | `/runs/[runId]` 页面，整合时间轴、回放、失败分析、导出 | `apps/web/app/runs/[runId]/page.tsx` |
| 多轨道时间轴 | task / agent / tool / provider / sandbox / runtime / robot / critic / memory / auto / failure | `apps/web/src/components/trace/TraceTimeline.tsx` |
| 失败分析面板 | 列出 failure 事件，支持 Jump 到时间点，展示关联事件 | `apps/web/src/components/trace/FailureAnalysisPanel.tsx` |
| 同步回放引擎 | Zustand ReplayClock：currentTime、playing、speed、seek、jumpToEvent | `apps/web/src/stores/replayStore.ts` |
| 回放面板 | Video、Curves（Recharts）、Trajectory、SandboxState | `apps/web/src/components/replay/*` |
| 导出 UI | RLDS / LeRobot / Failure Case / Skill Candidate 一键发起导出并轮询状态 | `apps/web/src/components/export/ExportPanel.tsx` |
| 实时模式 | 运行列表页可切换 Live，WebSocket 追加事件 | `apps/web/app/runs/page.tsx` |
| **系统状态卡片** | Robot Registry 首页展示 `/api/status` 整体健康度与模块网格 | `apps/web/app/page.tsx` |
| **失败分析增强** | FailureAnalysisPanel 新增 “Ask Memory” 与 “Get Recovery Hint” 按钮 | `apps/web/src/components/trace/FailureAnalysisPanel.tsx` |
| **Forge 页面** | `/forge` 页面：粘贴 SDK 描述、选择 target、编译并展示校验结果、列出已生成 bundle | `apps/web/app/forge/page.tsx` |

### 1.3 共享包与工程

- `packages/timeline-core/src/index.ts`：扩展 `TraceEvent`、`ReplayManifestMedia` 与辅助函数（`groupByTrack`、`findFailures`、`findRelated` 等）。
- `apps/web/tailwind.config.js`：修复 content 路径，包含 `app/` 与 `components/`。
- `apps/web/package.json`：新增 `@rosclaw/timeline-core`、`zustand`、`recharts`、`@xyflow/react`、`@tanstack/react-query` 等依赖。
- `apps/web/src/lib/api.ts`：新增 `status`、`mcp`、`how`、`forge` 客户端方法。
- `apps/web/src/components/DashboardShell.tsx`：导航栏新增 `Forge` 入口。

## 2. 测试结果

| 测试层级 | 命令 | 结果 |
| --- | --- | --- |
| 后端单元/集成测试 | `PYTHONPATH=src pytest apps/api/tests` | **46 passed** |
| timeline-core 构建 | `pnpm --filter @rosclaw/timeline-core build` | **成功** |
| 前端类型检查 | `cd apps/web && ./node_modules/.bin/tsc --noEmit` | **clean** |
| 前端单元测试 | `cd apps/web && ./node_modules/.bin/vitest run` | **6 passed** |
| E2E 测试 | `apps/web/e2e/trace-viewer.spec.ts` | **未配置**（当前仓库无 Playwright e2e 目录与 spec 文件） |

### 2.1 关键修复（测试中发现的阻塞问题）

1. **导入时配置捕获**：`run_indexer.PRACTICE_DIR` 与 `export_jobs.EXPORT_DIR` 在测试收集阶段被提前固定，改为懒加载 `_practice_dir()` 与可重新绑定的 `EXPORT_DIR`。
2. **FastAPI lifespan 未触发**：`AsyncClient(ASGITransport(app))` 不会触发 lifespan，在 `conftest.py` session fixture 中显式调用 `init_db()`。
3. **数据库污染**：机器人测试改为内存 SQLite，并在每个测试前 truncate `robots` 表。
4. **media 404**：`runs.py` 中曾直接使用 `settings.practice_dir`，已改为 `run_indexer._practice_dir()`。
5. **`ReplayManifestMedia.name` 缺失**：同步更新 `timeline-core`、`schemas.py` 与 `run_indexer.py`。
6. **pnpm / Node 版本不匹配**：绕过 pnpm，直接调用本地二进制（`./node_modules/.bin/tsc`、vitest、playwright）。
7. **Forge 校验绕过**：生成 `server.py` 时硬编码 safety 文本导致“应被拦截”的 bundle 通过校验；已移除硬编码注释，使校验真实依赖 SDK 输入是否包含 safety/firewall/approval/limit/constraint 关键词。
8. **Forge 安全用例失败**：安全 SDK 输入补充 safety 关键词，确保校验策略与安全用例一致。

## 3. 性能与可扩展性说明

- **文件扫描**：当前每次请求按需读取磁盘 JSONL，未做持久化缓存。运行目录较大时建议后续增加：
  - 内存 LRU 缓存（运行摘要、事件列表）。
  - 后台索引 worker 扫描并写入 SeekDB / SQLite。
- **事件分页**：`GET /api/runs/{run_id}/events` 默认 `limit=200`，目前全量读取后切片；大数据量时应改为流式读取或预建索引。
- **回放同步**：前端通过 `requestAnimationFrame` 轮询 `replayStore.currentTime`，CPU 占用低，但视频 seek 精度受浏览器解码影响。
- **导出任务**：当前为同步执行线程（后台 asyncio task），适合低并发；后续可接入 Celery / RQ 以支持队列与重试。
- **MCP 网关**：当前为薄层 HTTP 代理，工具实现为内存/数据库查询；后续可由真实 `rosclaw` CLI / Runtime 暴露原生 MCP server 替代。
- **Memory / How**：当前为基于规则的字典匹配与参数补丁，适合覆盖常见失败模式；后续可接入 LLM-based 根因分析与策略生成。
- **Forge**：当前为模板生成 + 关键词 Critic 校验；后续应与真实 `sdk_to_mcp` / Asset Forge 编译器、签名与 staging install 流程对接。

## 4. 已知限制

1. **物理仿真未接入**：当前使用 fixture 中的 mock 数据，未连接 MuJoCo / Isaac Sim / Gazebo。
2. **事件总线未深度集成**：Dashboard 目前直接扫描 `ROSCLAW_PRACTICE_DIR`；真正的 Event Bus 订阅与 `rosclaw.dashboard.trace.updated` 事件推送需要 Runtime / Practice 模块进一步对接。
3. **身份鉴权缺失**：所有路由均为公开访问，未实现用户认证与权限控制。
4. **大型运行性能未压测**：未针对 10k+ 事件、GB 级视频的运行做专项测试。
5. **E2E 测试未建立**：仓库目前没有 Playwright e2e 目录与 spec，Trace Viewer 的端到端回归依赖手动验证。

## 5. 与《ROSClaw_v1.0_深入验收指南》的差距

| 验收层 | 指南要求 | 当前状态 |
| --- | --- | --- |
| L0 安装启动 | `rosclaw init / doctor / start` 全绿 | **部分涉及**：Dashboard 内提供 `/api/status` 聚合健康度，可展示 runtime / event_bus / seekdb / registry / mcp_gateway / sandbox / practice / memory / dashboard 模块状态；`rosclaw` CLI 本身的 init/doctor/start 不在本 repo 范围 |
| L1 模块契约 | 各模块 API 契约 | **部分涉及**：runs / replay / export / status / mcp / memory / how / forge API 已定义 |
| L2 Claude Code 接入 | MCP tools 可调用 ROSClaw | **已涉及**：`/api/mcp/tools` 与 `/api/mcp/call` 暴露 6 个稳定工具，Claude Code 可通过 HTTP 调用 |
| L3 单机器人任务 | 小车 PID / 机械臂 reach / 抓取 | **未涉及**：只有 mock fixture |
| L4 失败恢复与记忆 | Memory 解释失败、How 恢复、第二轮改进 | **已涉及**：`/api/memory/explain` 与 `/api/how/recovery` 基于失败事件生成解释与参数补丁并持久化到 Memory；UI 已提供入口 |
| L5 自扩展 | Forge 生成 bundle、Critic validation | **已涉及**：`/api/forge/compile` 生成 5 类 bundle，`/api/forge/validate` 执行 Critic 校验并拦截缺少 safety/firewall 约束的 bundle，通过校验后写入 staging |
| Dashboard 验收 | 完整 trace、事件流、replay | **基本满足**：可加载练习运行、展示多轨时间轴、回放、失败跳转、导出、系统状态、MCP 调用、Memory/How 分析、Forge 生成 |

**结论**：本次 PR 在 P1 Trace Viewer 基础上，闭环了 Dashboard 侧可实现的 L0 状态、L2 MCP 工具、L4 Memory/How、L5 Forge 验收能力。L3 真实机器人任务与物理仿真、以及 `rosclaw` CLI 本身的 L0 命令仍需要 Runtime / Embodiment / CLI 仓库后续补齐。

## 6. 提交建议

- 应提交的分支：`feature/physical-trace-viewer`
- 应包含的文件：本次新增/修改的 backend / frontend / shared package / tests / reports 文件。
- **不应提交的文件**：`FEEDBACK`、`ROSClaw_v1.0_深入验收指南.md`、`.env`、`credentials.json`、构建产物、`test-results/`、临时调试脚本。
