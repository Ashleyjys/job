# 代码审查报告（Code Review Report）

## 1. 文档目标
本文档用于记录当前 MVP 阶段已完成实现的代码审查结论、已验证证据、主要风险项与后续修订建议，满足题目中“必须包含代码审查记录”的要求。

## 2. 审查范围
本轮审查覆盖以下范围：
- 后端入口、路由、工作流加载、上游适配与看板服务；
- 前端请求封装、页面编排与关键展示组件；
- 跨域与本地开发代理链路；
- 已存在的 pytest / Vitest 测试；
- 与当前运行方式相关的交付文档。

重点文件包括：
- `backend/app/main.py`
- `backend/app/routers/dashboard.py`
- `backend/app/services/dashboard_service.py`
- `backend/app/services/open_meteo_client.py`
- `backend/app/services/mock_dashboard_data.py`
- `backend/app/services/workflow_loader.py`
- `frontend/src/services/api.ts`
- `frontend/src/composables/useDashboardQuery.ts`
- `frontend/src/views/DashboardPage.vue`
- `frontend/src/components/dashboard/StatusPanel.vue`
- `backend/tests/test_dashboard_router.py`

## 3. 审查证据
本轮审查基于以下已验证结果：
- 算法服务测试：`algorithm_service` 目录下执行 `..\.condaenv\python.exe -m pytest tests -v`，结果 `5 passed`
- 后端测试：`backend` 目录下执行 `..\.condaenv\python.exe -m pytest tests -v`，结果 `39 passed`
- 前端测试：`frontend` 目录下执行 `npm run test -- --run`，结果 `36 passed / 8 files`
- 前端类型检查：`tsc --noEmit` 与 `vue-tsc --noEmit` 通过
- 前端构建：`frontend` 目录下执行 `npm run build`，结果通过
- 本地跨域预检：`OPTIONS /api/v1/dashboard/query` 已返回 `200`，并带有正确的 CORS 头

## 4. 正向结论
本阶段实现有以下明显优点：
- 后端采用 `router / schema / service` 分层，主链路结构清晰；
- 工作流配置外置到 YAML，便于后续演化为可配置流程；
- Open-Meteo 上游数据已通过适配层归一化到内部契约，前端不直接依赖第三方字段；
- 独立算法服务接口已经拆分为单独的 FastAPI 服务，主服务可优先调用远端算法，再回退本地规则；
- 前端请求链路已统一为“本地代理优先、直连可选”，联调路径明确；
- 前端已经接入 ECharts 趋势图，并补齐了对应组件测试；
- 针对 `Failed to fetch` 的跨域问题已补上回归测试，避免同类问题再次回归；
- 运行说明、环境变量说明与部署说明已和当前实现同步。

## 5. 审查发现（按严重度排序）

| 编号 | 文件 / 模块 | 问题描述 | 风险等级 | 建议修复方案 | 当前状态 |
|---|---|---|---|---|---|
| CR-001 | `backend/app/services/dashboard_service.py` | 当前地理编码、天气或空气质量任一上游失败时，会在开启 fallback 的情况下直接回退为整页 mock 看板，无法保留部分真实上游结果，也不利于快速区分是哪一个上游先失败。 | P2 | 若后续希望更贴近企业级演示，可将天气、AQI 结果拆分为独立失败分支，保留部分成功数据，并在响应中显式标注失败源。 | 未修复 |
| CR-002 | `backend/app/services/workflow_loader.py`、`workflows/main.yaml`、`backend/app/services/dashboard_service.py` | 当前 YAML 已被加载和校验，但 `steps` 尚未形成通用执行引擎；如果文档把它描述为“真实并行调度器”，会高估当前系统能力。 | P2 | 在文档中明确“当前为配置契约 + 服务层编排”，若后续继续演进，再新增真正的步骤执行器。 | 文档已修正，代码未扩展 |
| CR-003 | `backend/app/routers/dashboard.py`、`frontend/src/services/api.ts`、`frontend/src/composables/useDashboardQuery.ts` | 当前错误返回和前端报错展示仍偏基础：前端主要显示 HTTP 状态或通用异常文本，未形成统一的企业化错误契约。 | P3 | 增加统一错误响应结构，例如 `traceId / code / message / details`，前端据此展示更可定位的信息。 | 未修复 |

## 6. 非阻塞性缺口说明
以下项目属于当前阶段尚未完成的增强项，不作为本轮阻塞性缺陷，但应在后续阶段继续推进：
- 地图热力层、更多对比图表与历史趋势扩展仍未完成；
- 当前独立算法服务仍为模拟算法服务，尚未替换为真实外部模型或第三方算法接口；
- 工作流 `steps` 仍未演进为真正的通用执行引擎；
- 生产化能力仍缺少更完整的日志、缓存、限流、监控与降级可观测性设计。

## 7. 审查结论
综合当前实现、测试结果与运行链路验证，可以得出以下结论：
- 当前交付物已经符合“总体框架 + 项目骨架 + 实时上游主链路 + 可运行联调”的阶段目标；
- 当前版本可以作为 MVP 演示与后续功能迭代的基线版本；
- 在进入下一阶段功能增强前，建议优先处理 `CR-001` 与 `CR-002`，以避免降级链路掩盖真实故障；
- 若目标从“课程 / 作业级 MVP”提升到“更接近企业项目的稳定演示版”，则应继续推进统一错误契约与更强的运行可观测性。

## 8. 后续审查建议
- 在扩展地图热力层与更多图表后，补做一次前端视图层专项审查；
- 在替换模拟算法服务后，补做一次接口契约与降级逻辑专项审查；
- 如果后续把 YAML `steps` 演进为真实执行引擎，补做一次工作流编排专项审查；
- 在新增缓存、限流与日志后，补做一次运行稳定性审查；
- 每次修复审查项后，回填本报告中的“当前状态”，形成闭环记录。
