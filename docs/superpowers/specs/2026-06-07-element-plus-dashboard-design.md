# Element Plus 看板重构设计

- 日期：2026-06-07
- 范围：仅调整前端展示层
- 目标：在保持现有页面内容与数据流 1:1 不变的前提下，将当前自定义看板 UI 重构为基于 `Element Plus` 的组件实现。

## 1. 目标

本次重构的核心目标，是将前端从“Vue 3 + 自定义组件 / 自定义样式”的实现方式，调整为“Vue 3 + 公开 UI 组件库 `Element Plus`”的实现方式。

这样做的目的，是满足题目中“复用公开 UI 组件库”的要求，同时不改变当前已经完成的业务场景、接口契约和页面信息结构。

本次重构完成后，应满足以下结果：
- 页面仍展示相同的内容区块，且顺序保持不变。
- 项目能够明确体现对 `Element Plus` 组件的复用，而不是仅使用自定义 HTML / CSS。
- 数据流、composable、接口层保持不变。
- 项目文档能够清楚说明组件库来源、适配方式和复用映射关系。

## 2. 非目标

本次重构不包含以下内容：
- 后端改动
- API 契约改动
- 新增看板功能
- 工作流逻辑调整
- 与当前自定义视觉做像素级一致复刻
- 在 `Element Plus` 之上再额外构建一套独立设计系统

## 3. 当前状态

当前前端使用的是 Vue 3 单文件组件与自定义样式：
- `D:\codex\job\frontend\src\views\DashboardPage.vue`
- `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`
- `D:\codex\job\frontend\src\components\dashboard\MetricCards.vue`
- `D:\codex\job\frontend\src\components\dashboard\RiskPanel.vue`
- `D:\codex\job\frontend\src\components\dashboard\StatusPanel.vue`
- `D:\codex\job\frontend\src\styles.css`

当前页面结构已经稳定，应完整保留：
1. 顶部标题 / 说明区
2. 城市查询区
3. 指标卡片区
4. 风险面板
5. 系统状态面板
6. 未来天气区

## 4. 选定方案

本次采用的方案是：在保持页面内容 1:1 不变的前提下，将当前展示组件替换为 `Element Plus` 对应组件实现。

选择该方案的原因：
- 对现有可运行项目影响最小，风险最低
- 最能直接证明“复用公开 UI 组件库”
- 对业务逻辑和测试影响最小
- 最方便在交付文档中说明来源与复用关系

本次明确不采用的方案：
- 全量视觉重设计：超出当前任务范围
- 只做局部混合接入：题目证明力度较弱

## 5. 架构与边界

### 5.1 分层保持不变

本次重构后，整体架构仍保持当前分层：
- 视图层：页面编排与区块顺序
- 组件层：聚焦单一职责的看板 UI 区块
- composable 层：数据加载、loading、error 状态管理
- service 层：API 地址构造与网络请求
- type 层：`DashboardViewModel` 等类型定义

### 5.2 改动边界

本次改动严格限定在前端展示层。

原则上保持不变的文件：
- `D:\codex\job\frontend\src\composables\useDashboardQuery.ts`
- `D:\codex\job\frontend\src\services\api.ts`
- `D:\codex\job\frontend\src\types\dashboard.ts`

允许改动的文件：
- `D:\codex\job\frontend\src\main.ts`
- `D:\codex\job\frontend\src\styles.css`
- `D:\codex\job\frontend\src\views\DashboardPage.vue`
- `D:\codex\job\frontend\src\components\dashboard\` 下的展示组件
- 前端依赖与锁文件
- `D:\codex\job\docs\` 下的 Figma / UI 复用说明文档

## 6. 组件映射设计

### 6.1 `DashboardPage`

职责：负责页面整体编排、请求看板数据，并把视图模型切分后传递给子组件。

新的实现将使用 `Element Plus` 的布局能力搭建页面骨架，例如：
- `ElContainer`
- `ElMain`
- `ElRow`
- `ElCol`
- `ElSpace`

### 6.2 `CitySelector`

职责：收集城市输入，并向父组件发出提交事件。

需要保留的现有契约：
- `v-model` 城市值
- `submit` 事件

新的组件映射：
- `ElForm`
- `ElFormItem`
- `ElInput`
- `ElButton`

### 6.3 `MetricCards`

职责：根据 `MetricCardItem[]` 渲染 KPI 指标卡片。

需要保留的现有契约：
- `metrics` prop

新的组件映射：
- `ElRow`
- `ElCol`
- `ElCard`
- `ElTag`

### 6.4 `RiskPanel`

职责：展示风险分数、风险等级、摘要与关键因子。

需要保留的现有契约：
- `riskScore`
- `riskLevel`
- `summary`
- `primaryFactors`

新的组件映射：
- `ElCard`
- `ElTag`
- 卡片内部结构化文本区

### 6.5 `StatusPanel`

职责：展示数据源状态、notice 信息与异常提示。

需要保留的现有契约：
- `notices`
- `sourceStatus`
- `anomalyMessages`

新的组件映射：
- `ElCard`
- `ElTag` 用于数据源状态
- `ElAlert` 用于提示或异常强调
- 简单列表结构用于多条提示信息

### 6.6 未来天气区

职责：展示每日天气预测卡片。

该区域可以继续保留在 `DashboardPage.vue` 中内联实现，不额外增加组件数量；因为这次任务的重点是保持现有结构稳定，而不是继续拆分更多组件。

新的组件映射：
- 区域布局采用 `ElRow` / `ElCol`
- 每日天气卡片使用 `ElCard`

## 7. 样式策略

用户已经明确接受 `Element Plus` 默认风格，因此本次重构不再保留当前大面积自定义渐变卡片视觉。

本次样式策略如下：
- 将项目样式从“主导视觉风格”调整为“辅助页面排版”
- 保持 `Element Plus` 默认视觉可被明显识别
- 自定义 CSS 仅保留以下内容：
  - 页面最大宽度
  - 垂直间距
  - 标题层级
  - 风险分数与 KPI 数值等重点数字的强调样式

应移除或显著弱化的内容：
- 自定义 hero 渐变背景
- 自定义卡片底色与阴影体系
- 大量自定义 badge 视觉
- 会掩盖 `Element Plus` 复用事实的面板样式

## 8. 数据流

本次重构不改变数据流：
1. `DashboardPage.vue` 继续持有本地 `city` 状态。
2. `useDashboardQuery()` 继续通过现有 API 层请求数据。
3. 返回的 `DashboardViewModel` 继续通过 props 传给子组件。
4. 子组件继续只负责展示，不直接请求数据。

这一点很重要，因为本次任务是展示层重构，不是行为逻辑改造。

## 9. 加载态与错误态

当前行为需要完整保留：
- 请求中显示加载状态
- 请求失败时显示错误信息
- 请求成功后才渲染看板内容

UI 适配决定如下：
- 加载态使用 `ElSkeleton`，显示在看板主要内容区域附近
- 错误态使用 `ElAlert`，显示清晰的错误提示文案

## 10. 依赖接入与应用启动

前端将新增 `Element Plus` 依赖。

启动层预期改动：
- 在 `D:\codex\job\frontend\src\main.ts` 中注册 `Element Plus`
- 在启动入口中引入 `Element Plus` 所需样式

接入方式采用 Vue 3 + Vite 的标准做法，不引入额外架构层。

## 11. 文档更新方案

`D:\codex\job\docs\04-figma-reuse.md` 需要更新，以明确说明当前版本走的是“公开 UI 组件库复用”路径。

文档中需要明确以下内容：
- 来源：公开 UI 组件库 `Element Plus`
- 引用：`Element Plus` 官方安装文档与官方资源页中的设计资源入口
- 复用理由：为什么这种做法满足题目的复用要求
- 适配方式：在保留当前业务布局和数据结构的前提下，将输入、按钮、卡片、标签、提示区映射到 `Element Plus`
- 组件映射表：列出页面元素与具体 `Element Plus` 组件之间的对应关系

建议在文档中写出的映射关系包括：
- 城市输入区 -> `ElForm`、`ElInput`、`ElButton`
- KPI 指标卡 -> `ElCard`、`ElTag`
- 风险区 -> `ElCard`、`ElTag`
- 状态区 -> `ElCard`、`ElTag`、`ElAlert`
- 未来天气卡 -> `ElCard`

## 12. 测试策略

本次重构应尽量遵循测试先行的思路。

最小验证范围如下：
- 在重构前先补 `CitySelector` 的提交契约测试
- 在重构前先更新 `MetricCards` 的渲染测试
- 保持现有 API 工具测试继续通过
- 运行前端测试集
- 运行前端生产构建，确认 `Element Plus` 接入后编译通过

具体测试目标：
- `MetricCards` 测试继续证明指标名称和值在切换到 `Element Plus` 后仍能正确渲染
- `CitySelector` 测试应证明输入的城市值仍通过现有事件契约提交给父层
- 测试应聚焦“行为与内容是否保持不变”，而不是测试 `Element Plus` 内部实现细节

## 13. 风险与应对

### 风险 1：UI 结构在重构过程中发生漂移
应对：严格保持当前区块顺序和内容字段不变。

### 风险 2：页面看起来过于自定义，削弱组件库复用证明力度
应对：接受 `Element Plus` 默认视觉语言，避免过度覆写样式。

### 风险 3：代码已经改为组件库复用，但文档仍沿用 Figma-only 口径
应对：同步更新 `D:\codex\job\docs\04-figma-reuse.md`，明确改为“公开 UI 组件库复用说明”。

### 风险 4：测试因为 DOM 结构变化变得脆弱
应对：让测试聚焦文本、值与事件契约，不依赖旧版自定义 HTML 结构细节。

## 14. 验收标准

当以下条件全部满足时，本次设计视为完整：
- 前端已安装并注册 `Element Plus`
- 看板保留原有内容区块及其顺序，做到 1:1 保持
- 看板主要 UI 明确使用了 `Element Plus` 组件
- 现有数据流和 API 契约保持不变
- 前端测试通过
- 前端生产构建成功
- 复用文档明确说明来源、适配方式与组件映射关系

## 15. 实施顺序

1. 添加 `Element Plus` 依赖并完成入口注册。
2. 先补 / 更新测试。
3. 重构 `CitySelector`。
4. 重构 `MetricCards`。
5. 重构 `RiskPanel` 与 `StatusPanel`。
6. 重构 `DashboardPage` 的布局与未来天气区。
7. 精简 `styles.css`，只保留轻量布局样式。
8. 更新复用说明文档。
9. 运行测试与构建验证。

## 16. 备注

- 当前工作目录看起来不是 Git 仓库，因此本设计文档可以保存，但无法在当前状态下完成提交。
- 本次虽然已启用浏览器辅助，但设计阶段不需要额外的视觉选择页，文本确认已经足够。
