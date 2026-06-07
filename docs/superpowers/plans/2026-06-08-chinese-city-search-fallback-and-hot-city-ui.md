# Chinese City Search Fallback And Hot City UI Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.
**Goal:** Make common Chinese city names searchable through a backend alias fallback, switch the dashboard default city to Chengdu, and label hot-city options clearly in the Vue selector.
**Architecture:** Keep Open-Meteo as the only upstream geocoding source, add a small alias retry layer inside the backend client, and keep the frontend structure unchanged by updating only the route view state and the city-selector rendering contract.
**Tech Stack:** FastAPI, pytest, Vue 3, TypeScript, Element Plus, Vitest
---
## File map
- Modify: D:\codex\job\backend\app\services\open_meteo_client.py
- Modify: D:\codex\job\backend\tests\test_open_meteo_client.py
- Modify: D:\codex\job\frontend\src\views\DashboardPage.vue
- Modify: D:\codex\job\frontend\src\views\DashboardPage.test.ts
- Modify: D:\codex\job\frontend\src\components\dashboard\CitySelector.vue
- Modify: D:\codex\job\frontend\src\types\dashboard.ts
- Modify: D:\codex\job\frontend\src\composables\useDashboardQuery.ts
## Component map
- DashboardPage.vue: keeps page-level state, owns the hot-city list, and passes city options into the selector.
- CitySelector.vue: renders the remote city search input and the hot-city tag UI.
- OpenMeteoClient: owns upstream geocoding fallback behavior.
### Task 1: Backend alias fallback
- [ ] Write a failing pytest covering ?? -> Chengdu alias fallback after the original Chinese query returns no results.
- [ ] Run the targeted backend test and confirm it fails for the expected reason.
- [ ] Add a focused Chinese city alias map and a single retry path in OpenMeteoClient.
- [ ] Re-run the targeted backend test and confirm it passes.
### Task 2: Frontend hot-city defaults
- [ ] Write failing Vitest assertions for default city ?? and hot-city option tagging.
- [ ] Run the targeted frontend test and confirm it fails for the expected reason.
- [ ] Update the dashboard hot-city seed data, selector contract, and fallback city text.
- [ ] Re-run the targeted frontend test and confirm it passes.
### Task 3: Regression verification
- [ ] Run backend tests for open_meteo_client.
- [ ] Run frontend dashboard view tests.
- [ ] If both sides are green, summarize the exact changed files and remaining caveats.