# Nixtla anomaly detection minimal design

## Goal
在尽量少改动现有项目的前提下，把异常检测从“纯本地规则”升级为“Nixtla 优先、本地规则回退”的混合方案，并保持前端契约稳定。

## Scope
- 保留现有 Open-Meteo 数据获取链路。
- 保留现有 `AnomalyResult` 返回结构，避免前端重写。
- 新增 Nixtla HTTP 适配层，仅接入异常检测，不先引入预测能力。
- 无 `NIXTLA_API_KEY`、第三方失败、超时或返回异常时，自动回退到当前本地异常检测逻辑。
- 同步补充环境变量和文档说明。

## Why this path
- 与当前项目最贴合：已有 AQI 小时级序列，直接可映射到第三方时序异常检测。
- 改动最小：前端基本不变，后端只增强分析实现。
- 面试更好讲：第三方算法 API + 内部统一接口 + fallback。

## Architecture
1. `dashboard_service` 仍负责拿到天气与空气质量数据并组装视图模型。
2. `detect_anomaly()` 改为调用新的 Nixtla 客户端函数；客户端内部根据配置决定：
   - 有 key：调用 Nixtla online anomaly detection
   - 无 key 或调用失败：回退本地规则
3. `/api/v1/analysis/detect-anomaly` 自动继承新逻辑，因此对外仍是内部统一算法接口。
4. `score_risk()` 暂时保留本地实现，避免一次性扩大范围。

## API behavior
- 成功命中 Nixtla：返回标准 `AnomalyResult`，`status="ok"`。
- 回退本地规则：返回标准 `AnomalyResult`，`status="degraded"`，并在 dashboard notice 中可选提示三方降级。
- `enableDetection=false`：直接跳过，不调用三方。

## Minimal file changes
- Modify: `D:\codex\job\backend\app\config.py`
- Add: `D:\codex\job\backend\app\services\nixtla_client.py`
- Modify: `D:\codex\job\backend\app\services\analysis_service.py`
- Modify: `D:\codex\job\backend\tests\test_analysis_service.py`
- Add: `D:\codex\job\backend\tests\test_nixtla_client.py`
- Modify: `D:\codex\job\.env.example`
- Modify: `D:\codex\job\README.md`
- Modify: `D:\codex\job\docs\03-api-spec.md`

## Success criteria
- 不配置 `NIXTLA_API_KEY` 时，现有测试仍通过，异常检测走本地回退。
- 配置 key 时，可调用 Nixtla 端点并把结果映射回现有 `AnomalyResult`。
- 前端无需改字段即可继续展示异常信息。
