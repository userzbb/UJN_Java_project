# 开发进度报告

> 更新日期：2026-05-20 | 首次提交 `2feb2ee`

## 总体进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 1: 基础设施 | 已完成 | Docker Compose + Maven + pyproject.toml + package.json |
| Phase 2: Python DSP 引擎 | 已完成 | BLE 扫描/分析 + CSI 加载/处理/检测 + SSE 流 |
| Phase 3: Spring Boot 网关 | 已完成 | REST API + WebSocket + JPA 持久化 + WebClient SSE 消费 |
| Phase 4: 前端 | 已完成 | Vue 3 + ECharts，BLE/CSI 两个面板共 8 个组件 |

**总代码量**：77 个文件，约 4,939 行源代码。

---

## 已实现功能

### 1. BLE 频谱感知子系统

| 功能 | 状态 | 备注 |
|------|------|------|
| 蓝牙设备实时扫描 | 已完成 | bleak.BleakScanner，回调推送至事件总线 |
| AD Structure 解析 | 已完成 | 解析设备名、厂商、TX Power |
| 设备去重与聚合 | 已完成 | MAC 地址去重，RSSI min/max/mean 统计 |
| 周期性快照 | 已完成 | 每 10s 生成 BLE 快照，写入 PostgreSQL |
| 设备列表 API | 已完成 | `GET /api/ble/devices` 返回当前设备列表 |
| 信道占用率 API | 已完成 | `GET /api/ble/channel/usage` 返回 CH37/38/39 统计 |
| 扫描控制 | 已完成 | `POST /api/ble/scan/start` / `/api/ble/scan/stop` |
| SSE 实时流 | 已完成 | `GET /ble/events/stream` → Spring Boot WebClient → WebSocket |
| 设备表 | 已完成 | MAC、名称、RSSI avg、包数、最近活跃时间 |
| 信道占用率柱状图 | 已完成 | CH37/38/39 三柱，颜色阈值：>50% 红 / >30% 黄 / 绿 |
| RSSI 分布直方图 | 已完成 | 5 dBm 分桶，颜色编码（强信号绿 / 弱信号红） |

**已知限制**：Windows 上 bleak 底层使用 WinRT API，不暴露 BLE 广播信道索引，信道占用率始终显示 0%。Linux/macOS 无此问题。

### 2. WiFi CSI 人体感知子系统

| 功能 | 状态 | 备注 |
|------|------|------|
| 数据集列表 | 已完成 | 可列出 `datasets/` 目录下所有可用数据集 |
| 数据集加载与播放 | 已完成 | 加载 .csi/.mat/.csv 文件，逐帧推送 |
| 合成数据降级 | 已完成 | 无数据集时自动生成 200 帧合成数据用于演示 |
| 播放控制 | 已完成 | 启动/暂停/停止/跳帧/调速 (0.1x-5x) |
| 进度查询 | 已完成 | 返回当前帧、总帧数、播放状态 |
| 子载波幅度提取 | 已完成 | CSIKit 解析复数矩阵 → 幅度 |
| Hampel 滤波 | 已完成 | 离群值去除 |
| 滑动窗口运动检测 | 已完成 | 方差阈值检测，生成运动告警 |
| 告警持久化 | 已完成 | 运动分数 > 阈值自动写入 csi_alert 表 |
| SSE 实时流 | 已完成 | 每帧 CSI 数据 + 运动检测结果推送 |
| 子载波热力图 | 已完成 | 60 帧滑动窗口，5 色渐变视觉映射 |
| 运动分数曲线 | 已完成 | 平滑折线 + 面积渐变 + 阈值标记线 |
| 告警事件列表 | 已完成 | 时间/帧号/分数/严重级别 |

**已知限制**：需要将真实 CSI 数据集（SignFi / Widar3.0 / NTU-Fi）下载到 `datasets/` 目录才能非合成演示。目前使用合成数据（200 帧，帧 80-130 有人工运动扰动）。

### 3. 基础设施

| 组件 | 状态 | 备注 |
|------|------|------|
| PostgreSQL 17 (Docker) | 已完成 | docker-compose.yml，端口 5432 |
| JPA 自动建表 | 已完成 | `ddl-auto=update`，4 张表自动创建 |
| PythonClient (WebClient) | 已完成 | 非阻塞 SSE 订阅 + REST GET/POST |
| WebSocket 网关 | 已完成 | `/ws/ble` + `/ws/csi` 两个端点 |
| 前端构建集成 | 已完成 | `vite build` → `src/main/resources/static/` |
| Vite 开发代理 | 已完成 | `/ws` 和 `/api` 代理到 Spring Boot :8080 |

### 4. 数据库表

| 表名 | 用途 | 字段 |
|------|------|------|
| `ble_snapshot` | BLE 周期性快照 | id, timestamp, device_count, channel_37/38/39_count |
| `csi_alert` | CSI 运动告警 | id, timestamp, motion_score, subcarrier_snapshot_json |
| `device_info` | 蓝牙设备信息 | id, mac, name, first_seen, last_seen, avg_rssi |
| `app_settings` | 应用配置键值存储 | key, value |

---

## 项目文件结构

```
mysite/
├── frontend/                          # Vue 3 + Vite + ECharts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.vue                    # 顶部导航 (BLE/CSI Tab 切换)
│       ├── main.js
│       ├── components/
│       │   ├── BlePanel.vue           # BLE 容器：控制栏 + 图表 + 表格
│       │   ├── BleSpectrumChart.vue   # 信道占用率柱状图
│       │   ├── BleDeviceRadar.vue     # RSSI 分布直方图
│       │   ├── BleDeviceTable.vue     # 设备列表表格
│       │   ├── CsiPanel.vue           # CSI 容器：播放控制 + 图表 + 告警
│       │   ├── CsiHeatmap.vue         # 子载波热力图
│       │   ├── CsiMotionChart.vue     # 运动分数折线图
│       │   └── CsiAlertList.vue       # 运动告警列表
│       └── composables/
│           ├── useWebSocket.js        # WebSocket 连接 + 自动重连
│           └── useECharts.js          # ECharts 实例生命周期管理
│
├── python-engine/                     # Python FastAPI DSP 引擎 (端口 :8765)
│   ├── main.py                        # 入口：创建 FastAPI app，注册路由，启动 uvicorn
│   ├── pyproject.toml                 # uv 依赖：fastapi, bleak, numpy, scipy, csikit
│   └── src/
│       ├── core/                      # 基础设施
│       │   ├── config.py              # 全局配置 (端口、路径、参数)
│       │   ├── events.py              # 异步事件总线 (asyncio.Queue pub/sub)
│       │   └── models.py              # 基类 TimestampedEvent
│       ├── ble/                       # BLE 引擎
│       │   ├── scanner.py             # bleak 蓝牙扫描器
│       │   ├── parser.py              # AD Structure 解析、信道推断
│       │   ├── analyzer.py            # 设备聚合、快照生成、信道统计
│       │   └── models.py              # BleEvent, BleDevice, BleSnapshot
│       ├── csi/                       # CSI 引擎
│       │   ├── loader.py              # 数据集加载 + 合成数据降级
│       │   ├── parser.py              # CSIKit 封装 (.csi → numpy 复数矩阵)
│       │   ├── processor.py           # 幅度提取、Hampel 滤波、归一化
│       │   ├── detector.py            # 滑动窗口方差 → 运动检测
│       │   └── models.py              # CsiFrame, CsiAlert, CsiDataset
│       ├── api/                       # FastAPI 路由
│       │   ├── ble_routes.py          # BLE REST + SSE 端点
│       │   ├── csi_routes.py          # CSI REST + SSE 端点
│       │   └── deps.py                # 单例依赖注入
│       └── stream/                    # SSE 流管理
│           └── sse.py                 # SSE 客户端订阅 + 推送
│
├── src/main/java/com/zzb/mysite/      # Spring Boot 4.0 (端口 :8080)
│   ├── MysiteApplication.java         # 启动类 + ObjectMapper Bean
│   ├── client/
│   │   └── PythonClient.java          # WebClient 封装：SSE 订阅 + REST 调用
│   ├── controller/
│   │   ├── BleController.java         # /api/ble/* 端点
│   │   ├── CsiController.java         # /api/csi/* 端点
│   │   └── SettingsController.java    # /api/settings 端点
│   ├── model/
│   │   ├── BleSnapshot.java
│   │   ├── CsiAlert.java
│   │   ├── DeviceInfo.java
│   │   └── AppSettings.java
│   ├── repository/                    # Spring Data JPA Repository × 4
│   └── websocket/
│       ├── WebSocketConfig.java       # 注册 /ws/ble 和 /ws/csi 端点
│       ├── BleWebSocketHandler.java   # BLE 通道：SSE → WebSocket 广播
│       └── CsiWebSocketHandler.java   # CSI 通道：SSE → WebSocket 广播
│
├── docker-compose.yml                 # PostgreSQL 17
├── pom.xml                            # Maven: Spring Boot + WebFlux + JPA + Jackson
└── docs/                              # 项目文档
    ├── 01-architecture.md
    ├── 02-features-and-principles.md
    ├── 03-ble-technical.md
    ├── 04-wifi-csi-technical.md
    └── 05-development-progress.md     # 本文件
```

---

## 数据流架构

```
┌─────────────────────────────────────────────────────────────┐
│ 浏览器 (Vue 3 + ECharts)                                     │
│   ├── BlePanel ──WebSocket──► /ws/ble                       │
│   └── CsiPanel ──WebSocket──► /ws/csi                       │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Spring Boot :8080                                            │
│   ├── WebSocket Handlers (Ble/Csi) ──广播──► 前端            │
│   ├── PythonClient (WebClient) ──SSE──► Python :8765        │
│   └── JPA Repositories ──► PostgreSQL :5432                 │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Python FastAPI :8765                                         │
│   ├── EventBus (asyncio.Queue pub/sub)                       │
│   ├── BleScanner (bleak) ──► ble/*                           │
│   ├── CsiLoader (CSIKit) ──► csi/*                           │
│   └── SseManager ──SSE──► Spring Boot                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 启动方式

### 开发模式（推荐）

```bash
# 1. 数据库
docker compose up -d

# 2. Python 引擎
cd python-engine && uv sync && uv run main.py

# 3. Spring Boot
./mvnw spring-boot:run

# 4. 前端（可选，热重载开发）
cd frontend && npm run dev
# → 访问 http://localhost:5173 (Vite 代理 API 到 :8080)
```

### 集成模式（单端口）

```bash
# 1-3 同上
# 4. 构建前端到 Spring Boot static/
cd frontend && npm run build

# 访问 http://localhost:8080（Spring Boot 直接提供前端静态文件）
```

---

## 后续待办

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 高 | 下载真实 CSI 数据集 | 放置到 `datasets/` 目录，如 SignFi、Widar3.0 |
| 高 | CSI 数据集格式适配 | 当前仅支持 .csi 格式，需扩展 .mat (Widar) 和 .csv |
| 中 | BLE 信道区分 (Linux) | 在 Linux 上部署可拿到 CH37/38/39 真实数据 |
| 中 | 前端移动端适配 | 图表 grid 响应式，表格横向滚动 |
| 中 | 用户配置持久化 | SettingsController 对接前端设置面板 |
| 低 | 多数据集切换 | CSI 面板支持运行时切换不同数据集 |
| 低 | 数据导出 | 快照/告警导出为 CSV/JSON |
| 低 | 单元测试 | Python pytest + Java JUnit |
| 低 | Docker 化全栈部署 | 单个 docker-compose 启动全部 4 个服务 |
