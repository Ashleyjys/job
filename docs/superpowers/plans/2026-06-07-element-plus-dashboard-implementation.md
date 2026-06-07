# Element Plus Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前 Vue 3 自定义看板展示层改造为基于 `Element Plus` 的实现，同时保持页面内容、数据流与交互契约不变。

**Architecture:** 保持现有 composable、service、type 分层不变，仅替换展示层组件和页面布局。采用 `Element Plus` 的表单、卡片、标签、提示与栅格组件完成迁移，并同步更新测试与复用说明文档。

**Tech Stack:** Vue 3、TypeScript、Vite、Vitest、Element Plus、@vue/test-utils、jsdom

---

## 文件职责

- `D:\codex\job\frontend\package.json`：新增 `Element Plus` 与测试依赖
- `D:\codex\job\frontend\src\main.ts`：注册 `Element Plus` 并引入样式
- `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`：迁移为 `ElForm` / `ElInput` / `ElButton`
- `D:\codex\job\frontend\src\components\dashboard\MetricCards.vue`：迁移为 `ElCard` / `ElTag`
- `D:\codex\job\frontend\src\components\dashboard\RiskPanel.vue`：迁移为 `ElCard` / `ElTag`
- `D:\codex\job\frontend\src\components\dashboard\StatusPanel.vue`：迁移为 `ElCard` / `ElTag` / `ElAlert`
- `D:\codex\job\frontend\src\views\DashboardPage.vue`：迁移页面骨架、未来天气区与 loading/error 展示
- `D:\codex\job\frontend\src\styles.css`：精简为页面级排版样式
- `D:\codex\job\frontend\src\components\dashboard\__tests__\MetricCards.test.ts`：补充 Element Plus 迁移后的渲染断言
- `D:\codex\job\frontend\src\components\dashboard\__tests__\CitySelector.test.ts`：新增输入和提交契约测试
- `D:\codex\job\docs\04-figma-reuse.md`：更新为公开 UI 组件库复用说明

## 任务 1：准备依赖与测试基线

- [ ] 为 `MetricCards` 编写失败中的迁移测试：要求保留文本内容，并渲染出 Element Plus 卡片 / 标签特征。
- [ ] 为 `CitySelector` 编写失败中的交互测试：要求渲染出 Element Plus 表单控件，并在提交时继续发出裁剪后的城市值。
- [ ] 运行新增测试，确认它们在当前自定义组件实现下失败。
- [ ] 安装 `element-plus`、`@vue/test-utils`、`jsdom`。

## 任务 2：接入 Element Plus 启动层

- [ ] 更新 `package.json` 与锁文件。
- [ ] 在 `main.ts` 中引入 `Element Plus` 和 `element-plus/dist/index.css`。
- [ ] 注册 `app.use(ElementPlus)`。

## 任务 3：迁移基础输入与指标卡

- [ ] 将 `CitySelector.vue` 改写为 `ElForm` + `ElFormItem` + `ElInput` + `ElButton`，保留 `v-model` 与 `submit` 事件。
- [ ] 将 `MetricCards.vue` 改写为 `ElRow` + `ElCol` + `ElCard` + `ElTag`，保留 `metrics` prop。
- [ ] 运行对应组件测试，确认从失败转为通过。

## 任务 4：迁移风险区、状态区和页面骨架

- [ ] 将 `RiskPanel.vue` 改写为 `Element Plus` 卡片布局。
- [ ] 将 `StatusPanel.vue` 改写为 `Element Plus` 卡片、标签和提示区布局。
- [ ] 将 `DashboardPage.vue` 改写为 `Element Plus` 页面结构，保留原有区块顺序与字段。
- [ ] 使用 `ElSkeleton` 和 `ElAlert` 统一 loading/error 展示。

## 任务 5：整理样式与文档

- [ ] 精简 `styles.css`，移除会掩盖 Element Plus 默认风格的大面积自定义视觉。
- [ ] 更新 `docs/04-figma-reuse.md`，改为 Element Plus 公开 UI 组件库复用说明，并补充官方资源页与 Figma 资源入口引用。

## 任务 6：最终验证

- [ ] 运行前端测试集并确认通过。
- [ ] 运行前端生产构建并确认通过。
- [ ] 汇总改动文件、验证结果与剩余风险。
