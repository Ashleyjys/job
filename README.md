# 空气质量 / 天气联动分析看板

## 1. 项目概述
这是一个面向城市环境监测场景的 AI 应用开发项目，用于实现空气质量与天气联动分析看板，打通“外部数据接入 -> 工作流编排 -> 算法分析 -> 前端可视化展示”的完整链路。

本项目由我个人独立完成。我在需求拆解、架构设计、前后端实现、测试补充与文档交付过程中，结合 AI Skills / Agent 工作流提升研发效率，重点体现 AI 应用落地、服务编排、工程化交付与独立推进能力。

当前版本重点完成：
- 可配置工作流定义
- FastAPI 看板编排服务
- 同仓库独立 FastAPI 模拟算法服务
- Vue 3 + TypeScript + Vite + Element Plus 前端看板
- Open-Meteo 实时天气 / AQI 数据接入
- 远端算法服务优先、后端本地规则兜底
- 企业项目常见交付文档

## 当前阶段与真实状态
当前项目已进入“验证与交付”阶段，主体功能链路已经落地，并已补齐当前环境下的关键验证：

- 后端主链路与测试已验证通过
- 前端业务页面、接口联调与类型系统已完成
- 前端源码已通过 TypeScript 与 Vue 类型检查
- 前端 `npm run test` 已通过
- 前端 `npm run build` 已通过

因此，当前版本已经具备较完整的开发验收证据，可继续进入演示优化、增强功能或最终汇报整理阶段。

## 2. 目录结构
- `docs/`：项目章程、业务范围、架构、接口、测试、交付清单等文档
- `backend/`：看板编排服务、工作流加载、上游适配、看板接口与测试
- `algorithm_service/`：独立 FastAPI 模拟算法服务与测试
- `frontend/`：Vue 3 + Element Plus 看板前端
- `workflows/`：YAML 工作流配置
- `skills/`：本项目使用的 AI 技能说明

## 3. 技术栈
- 前端：Vue 3 + TypeScript + Vite + Element Plus
- 后端：FastAPI
- 工作流配置：YAML
- 图表：ECharts
- 测试：pytest + Vitest
- 文档：Markdown

## 4. 本地运行
### 4.1 启动算法服务
在项目根目录执行：

```powershell
conda create -y -p .\.condaenv python=3.12 fastapi pydantic pydantic-settings uvicorn pytest httpx pyyaml
cd algorithm_service
..\.condaenv\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

### 4.2 启动后端
在项目根目录执行：

```powershell
cd ..\backend
..\.condaenv\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.3 启动前端
在前端目录执行：

```powershell
cd frontend
npm install
npm run dev
```

### 4.4 本地开发连接方式
- 前端默认通过 Vite 开发代理访问后端，请求路径为 `/api/*`
- 当前代理配置位于 `frontend/vite.config.ts`，默认转发到 `http://localhost:8000`
- 因此前端本地开发时，通常不需要额外设置 `VITE_API_BASE_URL`
- 如果你希望前端直连后端，或者部署到非同源环境，可以在 `frontend/.env.local` 中覆盖：

```env
VITE_API_BASE_URL=http://localhost:8000
```

- 如果前后端最终通过同一域名下的反向代理部署，建议保留为：

```env
VITE_API_BASE_URL=/api
```

### 4.5 跨域说明
- 后端已经启用 CORS，中间件配置位于 `backend/app/main.py`
- 允许来源通过 `CORS_ALLOW_ORIGINS` 配置，默认包含本地常用地址：
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://localhost:4173`
  - `http://127.0.0.1:4173`
- 如果你更换了前端端口或域名，需要同步更新后端的 `CORS_ALLOW_ORIGINS`

默认访问地址：
- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- 后端健康检查：`http://localhost:8000/health`

## 5. 测试命令
### 5.1 算法服务测试
```powershell
cd algorithm_service
..\.condaenv\python.exe -m pytest tests -v
```

### 5.2 后端测试
```powershell
cd backend
..\.condaenv\python.exe -m pytest tests -v
```

### 5.3 前端测试
```powershell
cd frontend
npm run test
```

补充说明：
- 当前机器可执行：

```powershell
node .\node_modules\typescript\bin\tsc --noEmit
node .\node_modules\vue-tsc\bin\vue-tsc.js --noEmit
```

- 当前版本下，`npm run test` 与 `npm run build` 也已可以通过。
- 若后续在其他机器执行时出现 `spawn EPERM`，优先判断为环境限制，而非直接判断为前端业务代码错误。

## 6. 当前实现范围
当前骨架版本已支持：
- 按城市触发看板查询
- 读取 `workflows/main.yaml`
- 使用请求参数覆盖工作流中的预测天数、异常检测开关、风险阈值与风险权重（含 `pm10Weight`）
- 通过 Open-Meteo Geocoding / Weather / Air Quality API 获取真实数据
- 当上游失败时按配置回退到本地 mock 数据
- 通过独立算法服务执行风险评分与异常检测
- 工作流中的 `analysisTimeoutMs` 会驱动远端算法服务调用超时
- 当算法服务不可用时，风险评分与异常检测统一回退到后端本地规则
- 返回统一的 `DashboardViewModel`
- 前端基于 Element Plus 渲染指标卡、风险面板、状态面板与未来天气视图

## 6.1 前端 UI 复用说明
- 当前前端采用公开 UI 组件库 `Element Plus` 进行界面复用
- 主要复用组件包括表单、输入框、按钮、卡片、标签、提示区和栅格布局
- 复用来源与适配方式的完整说明见 [docs/04-figma-reuse.md](docs/04-figma-reuse.md)

## 6.2 PM10 权重使用说明
- 前端参数区已提供可选的 `PM10 权重` 输入项
- 默认留空，表示 `PM10` 不参与风险评分，保持当前默认评分口径不变
- 仅当用户显式填写数值时，前端才会向后端透传 `riskRules.pm10Weight`
- 该参数适合作为演示“算法参数可配置”的补充项，不建议在未同步调整其他权重前直接作为默认开启项

## 6.3 项目特色说明
- 本项目按个人独立完成方式推进，覆盖业务场景选型、工作流设计、前后端实现、测试补充与文档交付
- 在实现过程中结合 AI Skills / Agent 工作流，用于需求拆解、架构整理、编码辅助、测试补齐与文档同步
- AI 在本项目中承担开发协作角色，不替代人工对业务判断、代码质量与最终交付结果的责任
- 相关过程记录见 [docs/08-ai-skills-log.md](docs/08-ai-skills-log.md) 与 [docs/09-code-review-report.md](docs/09-code-review-report.md)

## 7. 后续建议
1. 将当前模拟算法服务升级为可插拔的真实模型服务
2. 接入 ECharts 折线图与地图热力层
3. 增加上游缓存、限流与更细粒度的降级策略
4. 增加契约测试、集成测试与部署脚本

## 8. 常见问题排查
### 8.1 页面提示 `Failed to fetch`
按以下顺序检查：

1. 后端是否已经启动，并能访问 `http://localhost:8000/health`
2. 前端是否通过 `npm run dev` 启动，且使用了 `frontend/vite.config.ts` 中的代理配置
3. 如果配置了 `VITE_API_BASE_URL`，确认该值是否正确
4. 如果前端不走代理而是直连后端，确认后端 `CORS_ALLOW_ORIGINS` 是否包含当前前端地址

### 8.2 中文在终端里显示异常
- PowerShell 终端显示乱码不一定代表文件内容损坏
- 当前项目文档文件统一按 UTF-8 保存
- 如需核对真实内容，优先使用支持 UTF-8 的编辑器直接打开文件

## 9. 交付物索引
为便于在 GitHub 上对照 [test.md](test.md) 快速查看材料，可以直接从这里进入：

- 源代码：[frontend/](frontend/)、[backend/](backend/)、[algorithm_service/](algorithm_service/)
- 配置文件：[.env.example](.env.example)、[workflows/main.yaml](workflows/main.yaml)
- 功能说明与设计思路：[docs/00-project-charter.md](docs/00-project-charter.md)、[docs/01-business-scope.md](docs/01-business-scope.md)
- 架构设计：[docs/02-architecture.md](docs/02-architecture.md)
- 算法接口与数据接口说明：[docs/03-api-spec.md](docs/03-api-spec.md)
- Figma / UI 复用说明：[docs/04-figma-reuse.md](docs/04-figma-reuse.md)
- 工作流设计与编排逻辑：[docs/05-workflow-design.md](docs/05-workflow-design.md)、[docs/12-api-call-flow.md](docs/12-api-call-flow.md)
- AI Skills 使用记录：[docs/08-ai-skills-log.md](docs/08-ai-skills-log.md)
- 代码审查报告：[docs/09-code-review-report.md](docs/09-code-review-report.md)
- 运行说明：[docs/10-deployment-runbook.md](docs/10-deployment-runbook.md)
- 交付检查清单：[docs/11-delivery-checklist.md](docs/11-delivery-checklist.md)
- Skills 文件：[skills/](skills/)

## 10. 与 `test.md` 要求的对应关系
| `test.md` 要求 | 仓库内对应材料 | 说明 |
| --- | --- | --- |
| 网络算法接口 | [algorithm_service/](algorithm_service/)、[docs/03-api-spec.md](docs/03-api-spec.md) | 提供独立 FastAPI 算法服务，包含风险评分与异常检测接口。 |
| 网络数据接口 | [backend/app/services/open_meteo_client.py](backend/app/services/open_meteo_client.py)、[docs/03-api-spec.md](docs/03-api-spec.md) | 接入 Open-Meteo Geocoding / Weather / Air Quality API。 |
| Figma / 前端复用 | [frontend/](frontend/)、[docs/04-figma-reuse.md](docs/04-figma-reuse.md) | 基于 Element Plus 组件体系完成界面复用，并说明来源与适配方式。 |
| 可配置工作流 | [workflows/main.yaml](workflows/main.yaml)、[docs/05-workflow-design.md](docs/05-workflow-design.md)、[docs/12-api-call-flow.md](docs/12-api-call-flow.md) | 工作流支持数据获取、算法处理、参数覆盖、超时控制与降级编排。 |
| 分层架构与可复用性 | [backend/app/services/](backend/app/services/)、[backend/app/routers/](backend/app/routers/)、[frontend/src/components/](frontend/src/components/)、[docs/02-architecture.md](docs/02-architecture.md) | 前后端按职责拆分，配置与业务逻辑分离，便于替换数据源或算法服务。 |
| AI Skills 运用 | [skills/](skills/)、[docs/08-ai-skills-log.md](docs/08-ai-skills-log.md) | 保留 Skills 文件与使用记录，覆盖 API 封装、工作流编排、前端映射与代码审查。 |
| 代码审查 | [docs/09-code-review-report.md](docs/09-code-review-report.md) | 记录审查角色、发现的问题以及对应修改。 |
| 运行说明 | [docs/10-deployment-runbook.md](docs/10-deployment-runbook.md)、[.env.example](.env.example) | 说明依赖安装、环境变量配置与本地启动方式。 |
