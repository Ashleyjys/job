# 工作流设计说明（Workflow Design）

## 1. 文档目标
本文档定义“空气质量 / 天气联动分析看板”的可配置工作流，用于将：
- 数据获取
- 算法分析
- 视图模型组装
- 结果展示
串联为可编排、可追踪、可降级的执行链路。

## 1.1 当前实现边界
当前 MVP 已经落地的是：
- 使用 `workflows/main.yaml` 保存工作流输入、配置项与步骤定义
- 通过 `backend/app/services/workflow_loader.py` 对 YAML 进行加载与结构校验
- 由 `backend/app/services/dashboard_service.py` 按既定主链路执行真实编排

当前尚未落地的是：
- 通用的步骤执行引擎
- 基于 `steps` 图的动态调度
- 真正的运行时并行执行器

因此，本文档以下内容以“当前代码已实现的工作流行为”为主，同时保留 YAML 中对未来演进方向的表达。

## 2. 工作流设计原则
- 配置驱动，不把核心流程硬编码在单一函数中
- 上游数据获取与内部算法分析解耦
- 当前以服务层主链路编排为主，YAML 步骤定义作为流程契约与未来演进基础
- 支持条件分支和降级返回
- 支持参数化阈值和开关配置

## 3. 主工作流概览
**工作流名称**
- `main`

**工作流目标**
- 根据用户输入的城市或坐标，获取天气和空气质量信息，完成风险评分与异常检测，并返回前端展示模型。

**工作流模式**
- 配置驱动的顺序执行 + 条件分支 + 分析降级

## 4. 工作流主链路
```mermaid
flowchart TD
    A[接收前端请求] --> B[校验输入参数]
    B --> C{是否已提供坐标}
    C -- 否 --> D[调用地理编码接口]
    C -- 是 --> E[进入数据拉取阶段]
    D --> E
    E --> F[获取天气数据]
    F --> G[获取空气质量数据]
    G --> H[标准化并组装分析输入]
    H --> I[调用风险评分接口]
    I --> J[调用异常检测接口或本地检测逻辑]
    J --> K[组装展示模型]
    K --> L[返回响应]
```

## 5. 工作流分步骤说明

### Step 1：输入校验
**目标**
- 校验城市名、坐标、时区和工作流参数是否合法。

**输入**
- 前端请求体

**输出**
- 标准化请求对象

**校验项**
- 城市名与坐标不能同时为空
- 若提供坐标，纬度范围为 `[-90, 90]`，经度范围为 `[-180, 180]`
- `forecastDays` 建议为 `1-7`
- 风险阈值满足 `medium < high`

### Step 2：地理编码（条件步骤）
**触发条件**
- 当请求未直接提供坐标时执行

**目标**
- 将城市名转换为坐标与时区

**失败处理**
- 无结果时返回 `CITY_NOT_FOUND`
- 上游失败时返回可重试错误

### Step 3：天气与 AQI 拉取
**目标**
- 获取天气数据和空气质量数据，作为后续分析输入。

**当前实现方式**
- 先调用 `fetch_weather`
- 再调用 `fetch_air_quality`
- YAML 中保留了 `mode: parallel` 语义，当前主要用于表达目标流程，而不是由通用执行器实际并行调度

**超时控制**
- 每个上游请求独立超时
- 当地理编码、天气或空气质量任一步骤抛出 `HTTPError` 时，若 `ENABLE_MOCK_FALLBACK=true`，直接返回整页 mock 看板

### Step 4：数据标准化
**目标**
- 将上游响应字段映射为内部统一模型，避免上游字段直接污染业务逻辑和前端模型。

**标准化内容**
- 城市信息
- 当前天气摘要
- 当前 AQI 摘要
- 小时级时间序列
- 天级趋势摘要
- 数据源状态

**校验规则**
- 时间序列长度必须一致
- 数值字段缺失时给出默认值或标记不可用
- 上游单位统一写入元数据

### Step 5：风险评分
**目标**
- 对当前环境状态生成 `riskScore` 和 `riskLevel`

**输入**
- 当前天气数据
- 当前 AQI 数据
- 风险阈值与权重参数

**输出**
- 风险分数
- 风险等级
- 关键影响因子
- 风险摘要

### Step 6：异常检测（可选步骤）
**目标**
- 对小时级趋势进行突变和极值检测

**触发开关**
- `enableAnomalyDetection = true`

**当前实现方式**
- 当前后端始终会构造异常检测输入
- 当 `enableAnomalyDetection=false` 时，远端算法服务或本地规则会返回“未启用检测 / 无异常”的结果
- 当前不是通过工作流执行器真正跳过该步骤，而是通过请求参数控制检测逻辑

**输出**
- `hasAnomaly`
- `anomalyFlags`
- `severity`
- `messages`

### Step 7：视图模型组装
**目标**
- 将标准化结果、风险结果和异常结果拼装为前端可直接渲染的统一 ViewModel

**组装内容**
- 页面头部城市信息
- 当前指标卡片
- 趋势图数据
- 风险面板
- 异常提示面板
- 数据源状态提示
- 降级说明

## 6. 条件分支与降级逻辑
### 6.1 地理编码失败
- 若 `ENABLE_MOCK_FALLBACK=true`，返回整页 mock 看板结果
- 若未开启 fallback，则直接返回错误

### 6.2 天气或 AQI 上游失败
- 当前实现不会保留部分成功结果
- 若 `ENABLE_MOCK_FALLBACK=true`，直接回退到整页 mock 看板结果
- mock 看板中的 `sourceStatus.weather / airQuality / analysis` 均标记为 `degraded`

### 6.3 分析接口失败
- 原始天气和 AQI 数据正常展示
- 风险评分与异常检测统一回退到 `backend` 本地规则
- `sourceStatus.analysis` 标记为 `degraded`

### 6.4 尚未落地的能力
- “天气成功 / AQI 失败”时继续展示局部真实结果
- 返回专门的错误页模型
- 由通用工作流引擎根据 `steps` 图做真实条件跳转和并行执行

## 7. 配置项设计
| 配置项 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| `workflow.id` | string | `main` | 工作流标识 |
| `workflow.enableAnomalyDetection` | boolean | `true` | 是否启用异常检测 |
| `workflow.defaultForecastDays` | integer | `7` | 天气预测天数 |
| `workflow.defaultAirQualityForecastDays` | integer | `5` | AQI 预测天数 |
| `upstream.weather.timeoutMs` | integer | `5000` | 天气接口超时 |
| `upstream.airQuality.timeoutMs` | integer | `5000` | AQI 接口超时 |
| `analysis.timeoutMs` | integer | `2000` | 算法接口超时 |
| `risk.highThreshold` | integer | `70` | 高风险阈值 |
| `risk.mediumThreshold` | integer | `40` | 中风险阈值 |

## 8. 工作流状态跟踪
建议每次执行生成 `workflowRunId`，并记录以下状态：
- `received`
- `validated`
- `location_resolved`
- `weather_fetched`
- `air_quality_fetched`
- `normalized`
- `risk_scored`
- `anomaly_checked`
- `assembled`
- `completed`
- `degraded`
- `failed`

## 9. 日志与可观测性建议
- 记录 `traceId`
- 记录 `workflowRunId`
- 记录上游耗时
- 记录降级原因
- 记录风险评分输入摘要，不记录敏感信息

## 10. YAML 工作流落地说明
本项目使用 `workflows/main.yaml` 描述工作流结构。

当前代码中的真实落地方式是：
- `workflow_loader.py` 负责加载并校验 YAML
- `dashboard_service.py` 负责执行主链路编排
- `steps` 字段当前主要用于表达工作流结构、配置项和后续扩展方向

因此，YAML 在当前版本中更接近“流程契约 + 配置来源”，而不是“已经完全由引擎驱动的运行时步骤图”。

## 11. 与前端交互关系
前端并不关心工作流内部细节，只通过：
- 城市选择
- 参数配置
- 触发查询
来驱动后端执行工作流。

前端只依赖最终的展示模型和数据源状态，不直接处理第三方原始响应结构。
