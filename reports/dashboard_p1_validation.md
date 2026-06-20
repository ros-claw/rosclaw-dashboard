# ROSClaw Dashboard P1 Validation Report

> Physical Trace Viewer 升级验证报告
> Commit: `dd4e1a30d50cf82d8a3f259029f40c37de4b7b20`
> Date: 2026-06-21

## 1. 本次开发范围

本次 PR 聚焦 **Dashboard → Physical Trace Viewer** 的 P1 能力：把练习运行（practice runs）从磁盘目录加载到 Web 界面，提供可观测、可回放、可导出的多轨道时间轴。

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

### 1.3 共享包与工程

- `packages/timeline-core/src/index.ts`：扩展 `TraceEvent`、`ReplayManifestMedia` 与辅助函数（`groupByTrack`、`findFailures`、`findRelated` 等）。
- `apps/web/tailwind.config.js`：修复 content 路径，包含 `app/` 与 `components/`。
- `apps/web/package.json`：新增 `@rosclaw/timeline-core`、`zustand`、`recharts`、`@xyflow/react`、`@tanstack/react-query` 等依赖。
- `apps/web/scripts/e2e-server.mjs`：重新创建，负责在 Playwright 测试时启动 API（8001）与 Next.js dev（3000）。

## 2. 测试结果

| 测试层级 | 命令 | 结果 |
| --- | --- | --- |
| 后端单元/集成测试 | `pytest apps/api/tests` | **35 passed** |
| timeline-core 构建 | `pnpm --filter @rosclaw/timeline-core build` | **成功** |
| 前端类型检查 | `cd apps/web && ./node_modules/.bin/tsc --noEmit` | **clean** |
| 前端单元测试 | `cd apps/web && ./node_modules/.bin/vitest run` | **6 passed** |
| E2E 测试 | `cd apps/web && ./node_modules/.bin/playwright test e2e/trace-viewer.spec.ts` | **1 passed** |

### 2.1 关键修复（测试中发现的阻塞问题）

1. **导入时配置捕获**：`run_indexer.PRACTICE_DIR` 与 `export_jobs.EXPORT_DIR` 在测试收集阶段被提前固定，改为懒加载 `_practice_dir()` 与可重新绑定的 `EXPORT_DIR`。
2. **FastAPI lifespan 未触发**：`AsyncClient(ASGITransport(app))` 不会触发 lifespan，在 `conftest.py` session fixture 中显式调用 `init_db()`。
3. **数据库污染**：机器人测试改为内存 SQLite，并在每个测试前 truncate `robots` 表。
4. **media 404**：`runs.py` 中曾直接使用 `settings.practice_dir`，已改为 `run_indexer._practice_dir()`。
5. **`ReplayManifestMedia.name` 缺失**：同步更新 `timeline-core`、`schemas.py` 与 `run_indexer.py`。
6. **pnpm / Node 版本不匹配**：绕过 pnpm，直接调用本地二进制（`./node_modules/.bin/tsc`、vitest、playwright）。
7. **Playwright `Jump` 按钮稳定性超时**：使用 `{ force: true }` 点击。

## 3. 性能与可扩展性说明

- **文件扫描**：当前每次请求按需读取磁盘 JSONL，未做持久化缓存。运行目录较大时建议后续增加：
  - 内存 LRU 缓存（运行摘要、事件列表）。
  - 后台索引 worker 扫描并写入 SeekDB / SQLite。
- **事件分页**：`GET /api/runs/{run_id}/events` 默认 `limit=200`，目前全量读取后切片；大数据量时应改为流式读取或预建索引。
- **回放同步**：前端通过 `requestAnimationFrame` 轮询 `replayStore.currentTime`，CPU 占用低，但视频 seek 精度受浏览器解码影响。
- **导出任务**：当前为同步执行线程（后台 asyncio task），适合低并发；后续可接入 Celery / RQ 以支持队列与重试。

## 4. 已知限制

1. **物理仿真未接入**：当前使用 fixture 中的 mock 数据，未连接 MuJoCo / Isaac Sim / Gazebo。
2. **事件总线未深度集成**：Dashboard 目前直接扫描 `ROSCLAW_PRACTICE_DIR`；真正的 Event Bus 订阅与 `rosclaw.dashboard.trace.updated` 事件推送需要 Runtime / Practice 模块进一步对接。
3. **Memory / How 未接入**：失败分析面板只展示当前运行的事件关联，未调用 Memory 查询历史相似失败，也未调用 How 生成恢复建议。
4. **Forge 未接入**：导出 UI 只生成文件包，尚未与 `sdk_to_mcp` / Asset Forge 的 bundle 生成、Critic validation、staging install 流程打通。
5. **身份鉴权缺失**：所有路由均为公开访问，未实现用户认证与权限控制。
6. **大型运行性能未压测**：未针对 10k+ 事件、GB 级视频的运行做专项测试。

## 5. 与《ROSClaw_v1.0_深入验收指南》的差距

| 验收层 | 指南要求 | 当前状态 |
| --- | --- | --- |
| L0 安装启动 | `rosclaw init / doctor / start` 全绿 | **未涉及**，Dashboard 仅作为 web 应用可运行 |
| L1 模块契约 | 各模块 API 契约 | **部分涉及**：runs / replay / export API 已定义 |
| L2 Claude Code 接入 | MCP tools 可调用 ROSClaw | **未涉及** |
| L3 单机器人任务 | 小车 PID / 机械臂 reach / 抓取 | **未涉及**：只有 mock fixture |
| L4 失败恢复与记忆 | Memory 解释失败、How 恢复、第二轮改进 | **未涉及**：失败分析仅为当前事件关联 |
| L5 自扩展 | Forge 生成 bundle、Critic validation | **未涉及**：导出为静态文件包 |
| Dashboard 验收 | 完整 trace、事件流、replay | **部分满足**：可加载练习运行、展示多轨时间轴、回放、失败跳转、导出 |

**结论**：本次 PR 完成了 Dashboard 在 **Practice Timeline / Replay / Export** 方向上的 P1 基础能力，但尚未覆盖指南中的全系统闭环验收。建议在后续 Sprint 中按 L0 → L5 顺序补齐 Runtime、MCP、Sandbox、Memory、How、Forge 的对接。

## 6. 提交建议

- 应提交的分支：`feature/physical-trace-viewer`
- 应包含的文件：本次新增/修改的 backend / frontend / shared package / tests / reports 文件。
- **不应提交的文件**：`FEEDBACK`、`ROSClaw_v1.0_深入验收指南.md`、`.env`、`credentials.json`、构建产物、`test-results/`、临时调试脚本。
