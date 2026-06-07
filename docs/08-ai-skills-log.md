# AI Skills 使用记录（AI Skills Log）

## 1. 文档目标
本文档用于记录本项目在需求整理、方案设计、编码辅助、测试补充、故障定位与交付文档同步过程中 AI 的实际参与情况，满足题目中“必须包含 AI Skills 使用记录”的要求。

## 2. 记录范围与原则
- 记录范围覆盖：需求拆解、文档生成、后端实现、前端实现、测试补充、联调排障、交付文档修订。
- 每条记录明确区分：AI 输出、人工确认、人工修订后的最终落地文件。
- AI 参与记录用于追踪产出来源，不替代人工对业务正确性、代码质量和最终交付结果的责任。
- 涉及中文文档和代码文件时，统一按 UTF-8 保存，并在写入后执行回读校验。

## 3. 本阶段实际使用记录

| 日期 | 阶段 | AI 方法 / Skills 方向 | 输入目标 | 主要产出 | 落地文件 | 采纳情况 | 人工修订情况 |
|---|---|---|---|---|---|---|---|
| 2026-06-07 | 需求拆解 | 结构化需求整理 | 将 `test.md` 整理为可直接提供给 AI 的企业化执行脚本 | 输出“先总框架、后逐步搭建、同步生成规范文档”的实施方式 | `ai_workflow_script.md` | 直接采纳 | 后续根据技术选型与阶段进展补充内容 |
| 2026-06-07 | 业务选型 | 方案评估与范围冻结 | 评估“空气质量 / 天气联动分析看板”是否适合作为项目业务场景 | 明确该方案适合用于 MVP，且便于稳定接入外部数据与展示完整主链路 | `docs/00-project-charter.md`、`docs/01-business-scope.md` | 直接采纳 | 用户确认场景后继续推进 |
| 2026-06-07 | 架构设计 | 分层设计与文档生成 | 基于既定场景输出系统架构、数据链路、工作流与接口契约 | 形成前端、后端、工作流、外部数据源、分析逻辑之间的边界定义 | `docs/02-architecture.md`、`docs/03-api-spec.md`、`docs/05-workflow-design.md`、`docs/06-data-contract.md`、`workflows/main.yaml` | 直接采纳 | 人工确认技术栈为 Vue 3 + FastAPI + YAML + ECharts |
| 2026-06-07 | 后端骨架实现 | 服务拆分与最小主链路搭建 | 建立 FastAPI 骨架、工作流加载器、看板查询接口与统一返回模型 | 完成 `router / schema / service` 基本分层与 MVP 主链路 | `backend/app/main.py`、`backend/app/routers/`、`backend/app/schemas/dashboard.py`、`backend/app/services/workflow_loader.py`、`backend/app/services/dashboard_service.py` | 直接采纳 | 人工确认保留本地 mock fallback 作为降级方案 |
| 2026-06-07 | 上游集成 | 适配层设计 | 将天气、空气质量、地理编码能力接入 Open-Meteo，并统一为内部模型 | 建立上游 API 到内部契约的标准化适配 | `backend/app/services/open_meteo_client.py` | 直接采纳 | 人工确认以 Open-Meteo 作为 MVP 上游 |
| 2026-06-07 | 前端骨架实现 | Vue 3 + TypeScript + Composition API | 搭建看板页面、城市选择、指标卡、风险面板、状态面板和 API 调用封装 | 完成可运行的前端页面骨架并打通查询链路 | `frontend/src/views/DashboardPage.vue`、`frontend/src/components/dashboard/`、`frontend/src/composables/useDashboardQuery.ts`、`frontend/src/services/api.ts` | 直接采纳 | 前端保持轻页面、逻辑下沉至 composable |
| 2026-06-07 | 测试补充 | 测试优先与验证闭环 | 为核心链路补充 pytest / Vitest 用例，验证接口、工作流配置、API URL 拼装等 | 建立最小回归测试集 | `backend/tests/`、`frontend/src/services/__tests__/api.test.ts`、`frontend/src/components/dashboard/__tests__/MetricCards.test.ts` | 直接采纳 | 人工通过测试结果进行验收 |
| 2026-06-07 | 编码问题修复 | 文件编码排查 | 处理中文文档与页面文案出现乱码的问题 | 明确终端显示乱码与文件内容损坏的区别，建立 UTF-8 回读校验流程 | `ai_workflow_script.md`、`docs/*.md`、前端相关 Vue 文件 | 直接采纳 | 后续写入改为“写后回读验证” |
| 2026-06-07 | 联调排障 | `systematic-debugging` 思路 | 排查页面报错 `Failed to fetch` 的根因 | 确认是跨域预检失败，补上后端 CORS 与前端 Vite 代理链路 | `backend/app/main.py`、`backend/app/config.py`、`backend/tests/test_dashboard_router.py`、`frontend/vite.config.ts`、`frontend/src/services/api.ts` | 直接采纳 | 人工确认保留“本地代理优先、直连可选”的运行方式 |
| 2026-06-07 | 交付文档同步 | 交付文档维护 | 将当前实现状态同步到运行与部署说明中 | 统一本地运行、环境变量、CORS、常见问题排查说明 | `README.md`、`.env.example`、`docs/10-deployment-runbook.md` | 直接采纳 | 人工确认说明与当前实现一致 |

## 4. 人工修订与质量控制记录
- 用户人工确认了业务场景、技术栈、目录位置与“直接执行”的推进方式。
- 在文档编码问题暴露后，调整为“写入后使用 UTF-8 回读校验”的策略，避免仅凭 PowerShell 终端显示结果判断文件质量。
- 对运行说明、环境变量与跨域策略进行了人工复核，确保 `README.md`、`.env.example`、`docs/10-deployment-runbook.md` 保持一致。
- AI 输出的代码和文档均经过人工确认后再纳入当前交付版本。

## 5. 本阶段 AI 参与带来的价值
- 快速完成了从题目要求到企业化实施脚本的结构化拆解。
- 在保持分层清晰的前提下，加速了文档、后端、前端与测试骨架的同步搭建。
- 在联调阶段帮助快速定位 `Failed to fetch` 的根因，避免停留在表象修补。
- 在交付阶段推动文档、实现与运行方式保持一致，降低阶段验收成本。

## 6. 当前限制与后续补充建议
当前 AI 参与记录已经覆盖到“框架设计 + 骨架搭建 + 实时上游接入 + 联调修复”阶段，但仍建议在后续阶段继续补充：
- ECharts 趋势图接入记录；
- 独立算法服务 / 风险评分接口替换记录；
- 更完整的异常处理、日志、缓存、限流与部署自动化记录；
- 下一轮代码审查后的问题闭环记录。

## 7. 当前阶段状态说明
截至 2026-06-07，本文档已从“规划期记录”更新为“真实实施记录”，能够反映当前项目在 MVP 阶段的 AI 参与轨迹与落地结果。
