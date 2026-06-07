# Dashboard Query Parameters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在前端页面增加可真实影响当前请求结果的参数配置区，包括天气预测天数、空气质量预测天数和异常检测开关。

**Architecture:** 保持现有 Element Plus 页面结构不变，在查询表单中加入参数控件；父页面持有参数状态，提交后通过 composable 传给 API 调用层，确保参数真实进入请求 payload。

**Tech Stack:** Vue 3、TypeScript、Element Plus、Vitest、@vue/test-utils

---

## 文件职责

- `D:\codex\job\frontend\src\types\dashboard.ts`：新增前端查询表单参数类型
- `D:\codex\job\frontend\src\components\dashboard\CitySelector.vue`：升级为“城市 + 参数配置 + 提交”的查询组件
- `D:\codex\job\frontend\src\views\DashboardPage.vue`：持有参数状态并提交完整查询对象
- `D:\codex\job\frontend\src\composables\useDashboardQuery.ts`：将真实参数传入 `queryDashboard`
- `D:\codex\job\frontend\src\components\dashboard\__tests__\CitySelector.test.ts`：补参数区渲染与完整提交契约测试
- `D:\codex\job\frontend\src\composables\__tests__\useDashboardQuery.test.ts`：验证 composable 会把参数真实传入请求层
- `D:\codex\job\README.md`：如有必要，补一句当前前端支持工作流参数配置

## 任务 1：先补失败测试

- [ ] 更新 `CitySelector.test.ts`，要求组件渲染两个参数选择控件和一个异常检测开关。
- [ ] 更新 `CitySelector.test.ts`，要求提交事件携带完整 payload：`city`、`forecastDays`、`aqForecastDays`、`enableAnomalyDetection`。
- [ ] 新增 `useDashboardQuery.test.ts`，要求 `loadDashboard()` 调用 `queryDashboard()` 时带上页面选择的真实参数。
- [ ] 运行这些测试并确认失败原因与新需求一致。

## 任务 2：实现参数数据结构

- [ ] 在 `types/dashboard.ts` 中新增共享的查询表单参数类型。
- [ ] 确保该类型可同时供视图层、查询组件和 composable 使用。

## 任务 3：升级查询组件

- [ ] 将 `CitySelector.vue` 从单一城市输入升级为完整查询表单。
- [ ] 增加 `forecastDays`、`aqForecastDays`、`enableAnomalyDetection` 的双向绑定。
- [ ] 提交时发出完整 payload，并对城市值继续做 `trim()` 处理。

## 任务 4：连通页面与请求层

- [ ] 在 `DashboardPage.vue` 中增加参数状态并提供默认值：7、5、true。
- [ ] 让页面通过组件绑定把参数传给 `CitySelector.vue`。
- [ ] 把 `refreshDashboard()` 改为接收完整查询对象。
- [ ] 把 `useDashboardQuery.ts` 改为接收完整查询参数，并真实传入 `queryDashboard()`。

## 任务 5：验证与文档同步

- [ ] 运行前端测试并确认通过。
- [ ] 运行前端构建并确认通过。
- [ ] 如有必要，在 `README.md` 中补充“支持工作流参数配置”的说明。
