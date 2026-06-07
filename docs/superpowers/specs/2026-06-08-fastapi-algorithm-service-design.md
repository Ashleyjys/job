# FastAPI 模拟算法服务设计

## 目标
在尽量少改动当前项目结构与前端契约的前提下，基于现有代码新增一个同仓库独立运行的 FastAPI 模拟算法服务，将风险评分与异常检测从看板编排服务中抽离为独立 HTTP 能力。

## 背景与动机
当前项目已经具备：
- Open-Meteo 数据接入；
- 风险评分与异常检测规则；
- 前端看板展示与后端编排接口；
- `analysis` 领域接口与测试基础。

但现状里分析逻辑仍主要以内聚在当前后端代码中的函数形式存在。为了更贴合题目中“算法接口为网络可调用 HTTP/WebSocket 接口”的要求，同时保持改动可控，本方案采用“同仓库新增独立 FastAPI 服务”的方式，把现有分析规则快速包装成可独立启动的模拟算法服务。

## 范围
本次设计只覆盖以下内容：
- 在仓库中新增 `algorithm_service` 独立目录；
- 提供独立 FastAPI 应用；
- 暴露两个算法接口：
  - `POST /score-risk`
  - `POST /detect-anomaly`
- 当前 `backend` 通过 HTTP 调用该算法服务；
- 算法服务不可用时，`backend` 回退到本地规则；
- 保持前端字段和主要页面逻辑不变。

本次不做：
- 数据库存储；
- 鉴权与租户隔离；
- 服务发现、容器编排、复杂部署；
- 算法模型训练；
- 大规模重构现有工作流系统。

## 总体结构
调整后，仓库中将有两个后端服务：

1. `backend`
- 角色：看板编排服务
- 负责：
  - 接收前端请求；
  - 调用 Open-Meteo 获取天气与空气质量数据；
  - 组装算法请求；
  - 通过 HTTP 调用算法服务；
  - 汇总结果并返回 `DashboardViewModel`。

2. `algorithm_service`
- 角色：模拟算法服务
- 负责：
  - 接收风险评分请求；
  - 接收异常检测请求；
  - 基于当前规则逻辑输出结果；
  - 保持简单、可独立测试、可独立启动。

## 目录设计
建议新增以下目录：

- `D:\codex\job\algorithm_service\app\main.py`
- `D:\codex\job\algorithm_service\app\routers\analysis.py`
- `D:\codex\job\algorithm_service\app\schemas\analysis.py`
- `D:\codex\job\algorithm_service\app\services\analysis_engine.py`
- `D:\codex\job\algorithm_service\tests\test_analysis_router.py`
- `D:\codex\job\algorithm_service\tests\test_analysis_engine.py`
- `D:\codex\job\algorithm_service\requirements.txt`

设计原则是直接复用你当前 `backend` 的分析领域模型和规则思路，不额外抽出共享 Python 包，避免为了“复用”引入更大结构调整。

## 接口设计
### 1. 风险评分
- 方法：`POST`
- 路径：`/score-risk`
- 输入：与当前 `AnalysisRiskRequest` 保持一致
- 输出：与当前 `RiskScoreResult` 保持一致

### 2. 异常检测
- 方法：`POST`
- 路径：`/detect-anomaly`
- 输入：与当前 `AnalysisAnomalyRequest` 保持一致
- 输出：与当前 `AnomalyResult` 保持一致

这样做的目的，是让当前 `backend` 的已有 schema 和前端数据契约尽量不变，只新增一个 HTTP 调用边界。

## 后端改造方式
`backend` 的改造遵循“最小侵入”原则：

### 保留的内容
- `dashboard` 查询接口保持不变；
- Open-Meteo 适配器保持不变；
- 前端调用路径保持不变；
- 风险/异常结果结构保持不变；
- 当前本地规则实现保留，作为 fallback。

### 新增的内容
- 在 `backend` 新增一个算法服务 HTTP client；
- 增加算法服务地址配置，例如：
  - `ALGORITHM_SERVICE_BASE_URL=http://localhost:8100`
  - `ALGORITHM_SERVICE_TIMEOUT_MS=2000`
- `dashboard_service` 在构造分析请求后，不再优先直接调本地函数，而是先走 HTTP 调用。

### 回退逻辑
- 如果算法服务调用成功：使用远端结果；
- 如果算法服务连接失败、超时、返回 5xx 或返回非法结构：
  - 回退到当前 `backend` 本地规则；
  - 将 `analysis` 状态标记为 `degraded`；
  - 其他天气和 AQI 数据仍正常返回。

## 数据流
目标数据流如下：

1. 前端请求 `backend` 的 `/api/v1/dashboard/query`；
2. `backend` 获取城市位置、天气数据、空气质量数据；
3. `backend` 组装：
   - `AnalysisRiskRequest`
   - `AnalysisAnomalyRequest`
4. `backend` 调用 `algorithm_service`：
   - `POST /score-risk`
   - `POST /detect-anomaly`
5. `algorithm_service` 返回评分与异常结果；
6. `backend` 组装统一展示模型并返回前端；
7. 若第 4 步失败，则第 5 步改为本地 fallback 逻辑。

## 为什么这是当前最优解
相对几种替代方案，这个方案最均衡：

### 对比“继续挂在同一个 FastAPI 应用里”
- 优点：改动少
- 缺点：很难证明“算法服务是独立网络接口”

### 对比“完全拆成独立仓库”
- 优点：边界更干净
- 缺点：对当前项目改动、文档、启动方式和测试影响更大

### 本方案的优势
- 服务边界足够清晰；
- 仍在同仓库，便于提交和讲解；
- 不需要大改前端；
- 符合题目要求；
- 面试时容易讲出“编排服务 + 算法服务 + fallback”这条工程故事线。

## 测试策略
### algorithm_service 测试
- 路由测试：验证两个 HTTP 接口响应结构；
- 规则测试：验证高风险评分、异常突增、关闭检测等行为。

### backend 测试
- HTTP client 成功调用算法服务；
- 算法服务失败时 fallback 到本地规则；
- `sourceStatus.analysis` 在远端失败时为 `degraded`；
- 看板返回结构不变。

### 前端测试
- 原有前端测试尽量不动；
- 只要展示契约不变，前端主要做回归验证即可。

## 运行方式
本次实现后，开发时需要两个服务：

1. 启动算法服务
- 例如：`http://localhost:8100`

2. 启动看板后端
- 例如：`http://localhost:8000`

3. 启动前端
- 例如：`http://localhost:5173`

如果算法服务未启动，系统仍可依赖本地 fallback 跑通主流程。

## 面试表述建议
这个设计特别适合校招面试时这样描述：
- 数据服务和算法服务职责分离；
- 算法能力通过独立 HTTP 服务暴露；
- 编排层负责调用外部数据和内部算法，再统一组装页面模型；
- 对远端算法服务失败做了降级，保证系统在演示环境下可用。

## 成功标准
完成后应满足：
- 同仓库存在可独立启动的 FastAPI 模拟算法服务；
- `backend` 能通过 HTTP 成功调用算法服务；
- 算法服务失败时系统仍可回退本地规则；
- 前端页面和现有主要接口契约不需要大改；
- 测试可以覆盖远端成功与 fallback 两条路径。
