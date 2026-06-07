# 运行与部署说明（Deployment Runbook）

## 1. 文档目标
本文档说明项目在本地演示环境下的安装、配置、启动、验证与常见排查方式。

## 2. 技术栈
- 前端：Vue 3 + TypeScript + Vite
- 后端：FastAPI
- 工作流配置：YAML
- 测试：pytest + Vitest

## 3. 环境准备
### 3.1 后端环境
```powershell
conda create -y -p .\.condaenv python=3.12 fastapi pydantic pydantic-settings uvicorn pytest httpx pyyaml
```

### 3.2 前端环境
```powershell
cd frontend
npm install
```

## 4. 启动步骤
### 4.1 启动算法服务
```powershell
cd algorithm_service
..\.condaenv\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8100
```

### 4.2 启动后端
```powershell
cd ..\backend
..\.condaenv\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.3 启动前端
```powershell
cd frontend
npm run dev
```

### 4.4 本地开发连接方式
- 前端默认通过 Vite 开发代理访问后端，请求路径为 `/api/*`
- 当前代理配置位于 `frontend/vite.config.ts`，默认转发到 `http://localhost:8000`
- 本地开发时建议将 `VITE_API_BASE_URL` 保持为 `/api`
- 如果需要让前端直连后端，或者部署到非同源环境，可在前端环境文件中覆盖：

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 4.5 跨域说明
- 后端已经启用 CORS，中间件配置位于 `backend/app/main.py`
- 允许来源通过 `CORS_ALLOW_ORIGINS` 配置，多个地址使用逗号分隔
- 默认允许的本地来源包括：
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
  - `http://localhost:4173`
  - `http://127.0.0.1:4173`
- 如果前端端口或域名发生变化，需要同步更新 `CORS_ALLOW_ORIGINS`

## 5. 骨架阶段验证
1. `GET /health` 返回 `{ "status": "ok" }`
2. `POST /api/v1/dashboard/query` 返回统一的看板视图模型
3. `POST http://localhost:8100/score-risk` 与 `POST http://localhost:8100/detect-anomaly` 可正常返回
4. 前端页面可以展示城市、指标卡、风险面板、系统状态与未来天气窗口
5. 请求中的 `forecastDays` 与 `enableAnomalyDetection` 会影响接口返回结果
6. 默认情况下后端会调用 Open-Meteo 上游接口与独立算法服务；若上游失败且 `ENABLE_MOCK_FALLBACK=true`，则回退到本地 mock 数据；若算法服务失败，则回退到后端本地规则

## 6. 测试命令
### 6.1 算法服务
```powershell
cd algorithm_service
..\.condaenv\python.exe -m pytest tests -v
```

### 6.2 后端
```powershell
cd backend
..\.condaenv\python.exe -m pytest tests -v
```

### 6.3 前端
```powershell
cd frontend
npm run test
```

## 7. 常见问题
### 7.1 fastapi 未安装
优先使用项目级 `.condaenv`，避免依赖全局 Python 或全局 pip 镜像配置。

### 7.2 中文乱码
所有文件统一使用 UTF-8 编码。避免通过 PowerShell 管道把中文字符串传给 Python 再写盘，否则终端编码可能先把中文替换成 `?`。

### 7.3 前端无法访问后端
检查：
- 前端是否通过 `npm run dev` 启动，并使用了 `frontend/vite.config.ts` 中的代理配置
- `VITE_API_BASE_URL` 是否与当前运行方式一致：
  - 本地代理模式：`/api`
  - 前端直连后端模式：`http://localhost:8000`
- 后端是否监听 `8000`
- 浏览器请求地址是否正确
- 如果前端直连后端，检查后端 `CORS_ALLOW_ORIGINS` 是否包含当前前端来源

### 7.4 上游接口访问失败
检查：
- 当前网络是否能访问 `api.open-meteo.com`
- 是否存在代理、证书或 DNS 问题
- `ENABLE_MOCK_FALLBACK` 是否开启
- 后端日志中是否出现上游超时或响应异常

### 7.5 页面提示 `Failed to fetch`
按以下顺序检查：

1. 后端是否已经启动，并能访问 `http://localhost:8000/health`
2. 前端是否通过 `npm run dev` 启动，且使用了 `frontend/vite.config.ts` 中的代理配置
3. 如果配置了 `VITE_API_BASE_URL`，确认该值是否正确
4. 如果前端不走代理而是直连后端，确认后端 `CORS_ALLOW_ORIGINS` 是否包含当前前端地址
