# frontend-figma-mapper

## 用途
用于辅助把 Figma 设计元素映射为前端 Vue 组件实现，重点覆盖：
- 组件拆分
- 样式结构还原
- 交互行为适配
- 响应式布局处理

## 适用场景
- 顶部筛选栏映射
- KPI 指标卡片映射
- 趋势图容器映射
- 风险面板与异常面板映射

## 建议输入
- Figma 链接或截图
- 目标页面结构
- 交互要求
- 组件复用要求

## 期望输出
- Vue 组件拆分建议
- props / emits 设计建议
- 样式变量建议
- 与 Figma 的差异说明模板

## 本项目中的主要用途
- 将天气 / AQI 看板设计映射到 Vue 组件
- 为 `CitySelector`、`MetricCards`、`TrendChart`、`RiskPanel`、`AlertPanel` 提供拆分建议