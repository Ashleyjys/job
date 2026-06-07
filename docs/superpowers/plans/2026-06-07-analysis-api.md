# Analysis API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dedicated analysis endpoints inside the existing FastAPI project for risk scoring and anomaly detection, then make the dashboard workflow consume the analysis domain instead of inline rule helpers.

**Architecture:** Keep a single FastAPI process, but split the analysis capability into its own schema, service, and router. The dashboard domain remains the orchestration layer for location resolution and upstream weather / AQI fetching, while the new analysis domain owns risk and anomaly calculations and their API contracts.

**Tech Stack:** FastAPI, Pydantic, pytest, existing workflow YAML configuration

---

### Task 1: Define analysis domain schemas

**Files:**
- Create: `backend/app/schemas/analysis.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_analysis_service.py`

- [ ] Define request / response schemas for `score-risk` and `detect-anomaly`
- [ ] Reuse existing dashboard domain primitives where reasonable, but keep analysis contracts explicit
- [ ] Include request models for weather summary, air quality summary, optional rules, and hourly AQI points

### Task 2: Add failing service-level tests for analysis rules

**Files:**
- Create: `backend/tests/test_analysis_service.py`
- Modify: none
- Test: `backend/tests/test_analysis_service.py`

- [ ] Add test for risk score output and threshold mapping
- [ ] Add test for anomaly detection when AQI delta crosses threshold
- [ ] Add test for anomaly disabled / insufficient data branches
- [ ] Run only the new file and confirm failure before implementation

### Task 3: Implement analysis service

**Files:**
- Create: `backend/app/services/analysis_service.py`
- Test: `backend/tests/test_analysis_service.py`

- [ ] Implement risk scoring logic in a dedicated service function
- [ ] Implement anomaly detection logic in a dedicated service function
- [ ] Keep output aligned with current `RiskScoreResult` and `AnomalyResult` semantics
- [ ] Run service tests and make them pass

### Task 4: Add failing router tests for analysis endpoints

**Files:**
- Create: `backend/tests/test_analysis_router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_analysis_router.py`

- [ ] Add test for `POST /api/v1/analysis/score-risk`
- [ ] Add test for `POST /api/v1/analysis/detect-anomaly`
- [ ] Confirm router tests fail before endpoint implementation

### Task 5: Implement analysis router and register it

**Files:**
- Create: `backend/app/routers/analysis.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_analysis_router.py`

- [ ] Expose risk scoring endpoint
- [ ] Expose anomaly detection endpoint
- [ ] Register analysis router in the FastAPI app
- [ ] Re-run router tests and make them pass

### Task 6: Refactor dashboard service to consume analysis domain

**Files:**
- Modify: `backend/app/services/dashboard_service.py`
- Modify: `backend/tests/test_dashboard_service.py`
- Modify: `backend/tests/test_dashboard_router.py`
- Test: `backend/tests/test_dashboard_service.py`, `backend/tests/test_dashboard_router.py`

- [ ] Replace inline `_build_risk_result()` usage with analysis service call
- [ ] Replace inline `_build_anomaly_result()` usage with analysis service call
- [ ] Remove obsolete inline helper functions after migration
- [ ] Preserve current workflow option behavior and fallback behavior
- [ ] Update tests to assert the dashboard still returns valid analysis output

### Task 7: Sync docs and run full verification

**Files:**
- Modify: `docs/03-api-spec.md`
- Modify: `docs/02-architecture.md`
- Modify: `docs/06-data-contract.md`
- Test: `backend/tests`, `frontend` test/build commands

- [ ] Update API spec with real analysis endpoints and request / response bodies
- [ ] Update architecture / data-contract docs to reflect analysis domain split
- [ ] Run `..\.condaenv\python.exe -m pytest tests -v` in `backend`
- [ ] Run `npm run test -- --run` in `frontend`
- [ ] Run `npm run build` in `frontend`
