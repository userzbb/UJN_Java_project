# 无线环境感知与信号分析平台

面向通信工程的 Web 实时仿真与信号分析平台，整合 **BLE 蓝牙频谱感知** 与 **WiFi CSI 人体运动检测** 两大子系统。无需 SDR 硬件即可进行有技术深度的无线通信实验与演示。

## 技术栈

| 层 | 方案 |
|---|---|
| 前端 | Vue 3 + Vite + ECharts 5 |
| 后端网关 | Spring Boot 4.0 + WebFlux + WebSocket |
| DSP 引擎 | Python FastAPI + bleak + CSIKit + numpy/scipy |
| 数据库 | PostgreSQL 17 (Docker Compose) |
| 实时通信 | 浏览器 ←WebSocket→ Spring Boot ←SSE→ Python |

## 功能概览

### BLE 频谱感知

- 笔记本蓝牙实时扫描周围 BLE 设备
- 设备去重聚合，RSSI 信号强度统计
- 信道 37/38/39 占用率分析（Linux/macOS）
- RSSI 分布直方图 + 实时设备列表
- 周期性快照持久化

### WiFi CSI 人体感知

- 公开 CSI 数据集加载与逐帧回放（支持 .csi / .mat / .csv）
- 子载波幅度热力图实时渲染
- 滑动窗口方差运动检测，自动生成告警
- 播放控制：启动/暂停/停止/跳帧/调速 (0.1x-5x)
- 无数据集时自动生成合成数据进行演示

## 快速开始

### 环境要求

- Java 17+
- Python 3.11+（[uv](https://github.com/astral-sh/uv) 包管理器）
- Node.js 20+
- Docker Desktop

### 启动步骤

```bash
# 1. 启动数据库
docker compose up -d

# 2. 启动 Python DSP 引擎
cd python-engine
uv sync
uv run main.py
# → 监听 http://localhost:8765

# 3. 构建前端（首次或前端代码变更时执行）
cd frontend
npm install
npm run build
cd ..

# 4. 启动 Spring Boot
./mvnw spring-boot:run
# → 访问 http://localhost:8080
```

### 前端开发模式（热重载）

```bash
cd frontend
npm run dev
# → 访问 http://localhost:5173
# Vite 自动代理 /api 和 /ws 到 Spring Boot :8080
```

## 项目结构

```
mysite/
├── frontend/                    # Vue 3 前端
│   └── src/
│       ├── components/          # 8 个 Vue 组件 (BLE + CSI 面板)
│       └── composables/         # useWebSocket / useECharts
├── python-engine/               # Python DSP 引擎 (端口 :8765)
│   └── src/
│       ├── core/                # 事件总线、配置、基础模型
│       ├── ble/                 # 蓝牙扫描、AD 解析、设备分析
│       ├── csi/                 # CSI 加载、解析、滤波、运动检测
│       ├── api/                 # FastAPI 路由
│       └── stream/              # SSE 流管理
├── src/main/java/com/zzb/mysite/  # Spring Boot (端口 :8080)
│   ├── client/                  # WebClient SSE 订阅
│   ├── controller/              # REST API
│   ├── model/                   # JPA 实体
│   ├── repository/              # Spring Data JPA
│   └── websocket/               # WebSocket 网关
├── docker-compose.yml           # PostgreSQL 17
└── docs/                        # 架构与开发文档
```

## 数据流

```
浏览器 ←─ WebSocket ─→ Spring Boot :8080 ←─ SSE ─→ Python :8765 ←─ bleak/CSIKit
  │                        │                           │
  │                        └── JPA ──→ PostgreSQL      │
  │                                                   │
  ECharts 实时渲染                                    蓝牙扫描 / CSI 回放
```

## 已知问题

- **Windows 信道占用率始终为 0%**：WinRT 蓝牙 API 不暴露广播信道索引。切换到 Linux/macOS 可获取真实的 CH37/38/39 分布。
- **CSI 真实数据集需手动下载**：自行下载 SignFi、Widar3.0 或 NTU-Fi 数据集，解压到 `datasets/` 目录。当前无数据集时自动使用合成数据演示。

## 开发文档

- [01-architecture.md](./docs/01-architecture.md) — 系统架构
- [02-features-and-principles.md](./docs/02-features-and-principles.md) — 功能与原理
- [03-ble-technical.md](./docs/03-ble-technical.md) — BLE 技术细节
- [04-wifi-csi-technical.md](./docs/04-wifi-csi-technical.md) — WiFi CSI 技术细节
- [05-development-progress.md](./docs/05-development-progress.md) — 开发进度
