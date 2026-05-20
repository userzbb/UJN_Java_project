# 01 — 项目技术栈与架构

## 1. 项目概述

**无线环境感知与信号分析平台** 是一个面向通信工程的 Web 实时信号分析系统。平台整合两大子系统：

- **WiFi CSI 人体感知**：利用 Intel AX200 网卡提取 802.11 物理层信道状态信息（CSI），通过分析子载波幅度/相位变化实现被动人体运动检测。
- **BLE 频谱感知**：利用笔记本蓝牙适配器扫描 BLE 广播信道，分析周围蓝牙设备的信号强度分布、信道占用率和设备活动规律。

项目定位：通信工程课程设计 / 毕业设计级复杂度，展示完整的全栈工程能力与通信系统理论基础。

---

## 2. 技术栈总览

| 层 | 技术选型 | 版本 | 选型理由 |
|---|---|---|---|
| **前端框架** | Vue 3 (Composition API) | 3.5+ | 组件化拆分 BLE/CSI 面板，单文件组件可维护性好 |
| **前端构建** | Vite | 8+ | Rolldown (Rust) 统一打包，构建输出直写 Spring Boot static/ |
| **图表可视化** | ECharts | 5+ | 原生热力图/雷达图/流式更新，适合信号可视化 |
| **后端框架** | Spring Boot | 4.0.6 | Java 生态主力，WebSocket + JPA 开箱即用 |
| **数据库访问** | Spring Data JPA (Hibernate) | — | 4 张表操作简单，不需要手写 SQL |
| **数据库** | PostgreSQL | 17 | 支持 JSON 字段存储 CSI 快照 |
| **DSP 引擎** | Python FastAPI | 0.115+ | 异步框架，SSE 流式响应原生支持 |
| **Python 包管理** | uv (pip 替代) | latest | 比 pip 快 10-100x，lockfile 可复现 |
| **BLE 扫描** | bleak | 0.22+ | 跨平台 BLE 库，Windows/Linux/macOS 均可用 |
| **CSI 解析** | CSIKit (PyPI) | 2.4+ | Python 原生解析 .csi / .mat / .csv 格式 |
| **科学计算** | numpy + scipy | latest | FFT、滤波、统计计算，.mat 文件读取 |
| **实时通信** | WebSocket + SSE | — | WebSocket 推前端，SSE 从 Python 拉到后端 |
| **容器化** | Docker Compose | — | PostgreSQL 一键部署 |
| **Java 版本** | Java 17 (LTS) | 17 | Spring Boot 4.x 最低要求 |

---

## 3. 系统架构

### 3.1 三层服务架构

```
┌──────────────────────────────────────────────────────────────────┐
│                        浏览器 (前端)                                │
│                                                                   │
│  Vue 3 + ECharts                   WebSocket 客户端                │
│  ┌────────────┐ ┌────────────┐     ws://host:8080/ws/csi          │
│  │ BlePanel   │ │ CsiPanel   │     ws://host:8080/ws/ble           │
│  └────────────┘ └────────────┘                                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │ WebSocket (实时推送)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Spring Boot (:8080)                           │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐   │
│  │ WebSocket 层     │  │ REST Controller  │  │ JPA Repository │   │
│  │ CsiHandler      │  │ CsiController   │  │ BleSnapshot   │   │
│  │ BleHandler      │  │ BleController   │  │ CsiAlert      │   │
│  └────────┬────────┘  └────────┬─────────┘  │ DeviceInfo    │   │
│           │                    │             │ AppSettings   │   │
│           │         ┌──────────┴─────────┐   └───────┬────────┘   │
│           │         │ PythonClient.java  │           │            │
│           │         │ (WebClient 非阻塞)  │           │            │
│           │         └──────────┬─────────┘           │            │
└───────────┼────────────────────┼─────────────────────┼────────────┘
            │                    │ SSE (流式接收)       │ JDBC
            │                    ▼                     ▼
┌───────────┴───────────────────────────────────────┴────────────┐
│                                                                    │
│  ┌─────────────────────────┐       ┌───────────────────────────┐ │
│  │  Python FastAPI (:8765) │       │  PostgreSQL (:5432)       │ │
│  │                         │       │                           │ │
│  │  src/ble/scanner.py    │       │  Docker Compose 管理       │ │
│  │  src/ble/parser.py     │       │  4 张表，数据量小           │ │
│  │  src/ble/analyzer.py   │       │                           │ │
│  │  src/csi/watcher.py    │       │                           │ │
│  │  src/csi/parser.py     │       │                           │ │
│  │  src/csi/processor.py  │       │                           │ │
│  │  src/csi/detector.py   │       │                           │ │
│  └─────────────────────────┘       └───────────────────────────┘ │
│            ▲                                                      │
│            │ BLE HCI (操作系统蓝牙栈)                                │
│            │ CSI 数据集文件 (.csi / .mat / .csv)                      │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流详解

#### BLE 数据流

```
笔记本蓝牙适配器
    │ (HCI 层，操作系统原生支持)
    ▼
Python bleak.BleakScanner
    │ scan 回调：每发现一个广播包触发
    ▼
ble/scanner.py → ble/parser.py
    │ 解析 AD Structure → 提取 MAC / Name / RSSI / Channel / TxPower / Manufacturer
    ▼
ble/analyzer.py
    │ 实时统计：信道占用率、设备 RSSI 分布
    │ 周期生成 BleSnapshot（每 5 分钟）
    ▼
stream/sse.py → SSE 流
    │ 每个广播包封装为一个 JSON event
    ▼
Spring Boot PythonClient (WebClient)
    │ 接收 SSE → 解析 Flux<ServerSentEvent>
    ▼
BleWebSocketHandler
    │ 转发到 WebSocket 频道 /ws/ble
    ▼
前端 BlePanel
    │ ECharts 实时更新：频谱柱状图、设备雷达、设备列表
    │
    │ (同时，周期快照通过 REST API 写入 PostgreSQL)
    ▼
PostgreSQL: ble_snapshot 表
```

#### CSI 数据流

```
公开 CSI 数据集 (本地 python-engine/datasets/)
    │ 用户在前端选择数据集（SignFi / Widar3.0 / 自定义）
    │ Spring Boot 转发加载请求到 Python
    ▼
csi/loader.py
    │ 加载指定数据集的所有 .csi 文件到内存
    │ 按时间戳排序帧序列，支持调速/跳转/循环
    ▼
csi/parser.py (CSIKit)
    │ 解析 .csi 文件 → numpy 复数矩阵 [N_tx × N_rx × N_subcarriers]
    │ 提取时间戳、RSSI、带宽等元数据
    ▼
csi/processor.py
    │ 计算：幅度 = |H|, 相位 = ∠H
    │ 去噪：Hampel 滤波去除异常子载波
    │ 归一化：消除 AGC 增益波动
    ▼
csi/detector.py
    │ 滑动窗口计算 CSI 幅度方差
    │ 阈值判断：var > threshold → motion_detected = true
    ▼
stream/sse.py → SSE 流
    │ 每帧封装为 JSON event（含子载波幅度数组 + 运动分数）
    ▼
Spring Boot PythonClient
    │ 接收 SSE → 解析 Flux<ServerSentEvent>
    ▼
CsiWebSocketHandler
    │ 转发到 WebSocket 频道 /ws/csi
    │
    │ (运动告警 → REST API → PostgreSQL)
    ▼
前端 CsiPanel
    │ Canvas 实时绘制子载波幅度热力图
    │ 运动检测分数曲线实时更新
```

### 3.3 通信协议对比

| 通道 | 协议 | 方向 | 数据格式 | 用途 |
|------|------|------|----------|------|
| 前端 ↔ Spring Boot | WebSocket | 双向 | JSON | 实时推送 BLE/CSI 事件 + 前端发送控制指令 |
| Spring Boot → Python | HTTP REST | 单向(请求) | JSON | 配置下发、控制指令（启动/停止扫描） |
| Python → Spring Boot | SSE | 单向(推送) | JSON (text/event-stream) | 持续推送扫描结果、解析事件 |
| Spring Boot ↔ PostgreSQL | JDBC | 双向 | SQL | 历史数据持久化 |

---

## 4. 项目目录结构

```
mysite/
│
├── frontend/                          # 前端项目（Vue 3 + Vite）
│   ├── package.json                   # npm 依赖声明
│   ├── vite.config.js                 # Vite 8 配置（输出到 ../src/main/resources/static/）
│   ├── index.html                     # 入口 HTML
│   └── src/
│       ├── main.js                    # Vue 应用创建 + ECharts 注册
│       ├── App.vue                    # 根组件（Tab 切换 CSI/BLE）
│       ├── composables/               # 组合式函数（可复用逻辑）
│       │   ├── useWebSocket.js        # WebSocket 连接管理 + 自动重连
│       │   └── useECharts.js          # ECharts 实例生命周期
│       └── components/
│           ├── DashboardHeader.vue    # 顶部导航栏（系统标题 + 启动/停止按钮）
│           ├── BlePanel.vue           # BLE 仪表盘主面板
│           ├── BleSpectrumChart.vue   # 37/38/39 信道占用柱状图
│           ├── BleDeviceRadar.vue     # 设备 RSSI 雷达分布图
│           ├── BleDeviceTable.vue     # 设备列表（MAC / Name / RSSI / 首次发现）
│           ├── CsiPanel.vue           # CSI 仪表盘主面板
│           ├── CsiHeatmap.vue         # 子载波幅度热力图（Canvas / ECharts heatmap）
│           ├── CsiMotionChart.vue     # 运动检测分数时序曲线
│           └── CsiAlertList.vue       # 告警事件列表
│
├── python-engine/                     # Python DSP 引擎
│   ├── pyproject.toml                 # uv 项目声明 + 依赖
│   ├── uv.lock                        # 依赖锁定文件
│   ├── main.py                        # FastAPI 入口（app 创建 + router 注册 + CORS）
│   └── src/
│       ├── __init__.py
│       ├── core/                      # 基础设施层
│       │   ├── __init__.py
│       │   ├── config.py              # 全局配置（端口、路径、采样率、阈值）
│       │   ├── events.py              # 异步事件总线（asyncio.Queue 实现发布/订阅）
│       │   └── models.py              # 共享基类 TimestampedEvent
│       ├── ble/                       # BLE 引擎模块
│       │   ├── __init__.py
│       │   ├── scanner.py             # bleak.BleakScanner 封装（启动/停止/回调）
│       │   ├── parser.py              # AD Structure 二进制解析
│       │   ├── analyzer.py            # 信道占用率 / RSSI 分布统计
│       │   └── models.py              # BleEvent, BleDevice, ChannelUsage
│       ├── csi/                       # CSI 引擎模块
│       │   ├── __init__.py
│       │   ├── watcher.py             # 目录监听（watchdog 文件系统事件）
│       │   ├── parser.py              # CSIKit 封装（.csi → numpy 矩阵）
│       │   ├── processor.py           # 子载波幅度/相位提取 + 去噪 + 归一化
│       │   ├── detector.py            # 滑动窗口方差检测 → 运动告警
│       │   └── models.py              # CsiEvent, CsiFrame, MotionAlert
│       ├── api/                       # FastAPI 路由层
│       │   ├── __init__.py
│       │   ├── ble_routes.py          # /ble/* REST 端点
│       │   ├── csi_routes.py          # /csi/* REST 端点
│       │   └── deps.py                # 依赖注入（获取引擎单例 + event_bus）
│       └── stream/                    # 流式输出层
│           ├── __init__.py
│           └── sse.py                 # SSE 流管理器（管理客户端订阅 + 事件广播）
│
├── src/
│   ├── main/
│   │   ├── java/com/zzb/mysite/
│   │   │   ├── MysiteApplication.java          # Spring Boot 入口
│   │   │   ├── websocket/
│   │   │   │   ├── WebSocketConfig.java        # WebSocket 端点注册
│   │   │   │   ├── CsiWebSocketHandler.java    # CSI WS 处理器（扩展 TextWebSocketHandler）
│   │   │   │   └── BleWebSocketHandler.java    # BLE WS 处理器
│   │   │   ├── controller/
│   │   │   │   ├── CsiController.java          # REST: CSI 会话列表、告警查询
│   │   │   │   ├── BleController.java          # REST: BLE 快照、设备历史
│   │   │   │   └── SettingsController.java     # REST: 平台配置 CRUD
│   │   │   ├── client/
│   │   │   │   └── PythonClient.java           # WebClient 封装 + SSE 流消费
│   │   │   ├── model/
│   │   │   │   ├── BleSnapshot.java            # JPA Entity: BLE 周期快照
│   │   │   │   ├── CsiAlert.java               # JPA Entity: CSI 运动告警
│   │   │   │   ├── DeviceInfo.java             # JPA Entity: 发现的蓝牙设备
│   │   │   │   └── AppSettings.java            # JPA Entity: 键值对配置
│   │   │   └── repository/
│   │   │       ├── BleSnapshotRepository.java
│   │   │       ├── CsiAlertRepository.java
│   │   │       ├── DeviceInfoRepository.java
│   │   │       └── AppSettingsRepository.java
│   │   └── resources/
│   │       ├── application.properties          # Spring 配置（端口、DB 连接、Python URL）
│   │       └── static/                         # 前端构建产物（Vite build 输出目标）
│   └── test/java/com/zzb/mysite/
│       └── MysiteApplicationTests.java         # Spring Boot 测试
│
├── docker-compose.yml               # PostgreSQL 容器定义
├── pom.xml                          # Maven 项目配置
└── docs/                            # 项目文档
    ├── 01-architecture.md           # 本文档：技术栈与架构
    ├── 02-features-and-principles.md # 功能与通信原理
    ├── 03-ble-technical.md          # BLE 技术细节
    └── 04-wifi-csi-technical.md     # WiFi CSI 技术细节
```

---

## 5. 启动流程

### 5.1 前置条件

- Java 17+
- Node.js 20+
- Python 3.11+ (通过 uv 管理)
- Docker Desktop (运行 PostgreSQL)
- CSI 数据集文件（内置 SignFi 子集，其他可从学术站点下载）

### 5.2 启动步骤

```bash
# 步骤 1: 启动 PostgreSQL
docker compose up -d

# 步骤 2: 安装 Python 依赖并启动 DSP 引擎
cd python-engine
uv sync
uv run main.py
# → FastAPI 运行在 http://localhost:8765
# → API 文档: http://localhost:8765/docs (Swagger UI)

# 步骤 3: 构建前端并启动 Spring Boot
cd ..
cd frontend
npm install
npm run build
# → dist/ 输出到 ../src/main/resources/static/

cd ..
./mvnw spring-boot:run
# → Spring Boot 运行在 http://localhost:8080
# → WebSocket: ws://localhost:8080/ws/csi
# → WebSocket: ws://localhost:8080/ws/ble

# 步骤 4: 打开浏览器
# http://localhost:8080
```

### 5.3 开发模式

```bash
# 前端开发（HMR 热更新）
cd frontend && npm run dev
# → Vite dev server 运行在 :5173
# → vite.config.js 配置 proxy 转发 /ws 到 :8080

# Spring Boot 开发（DevTools 热重载）
./mvnw spring-boot:run
# → spring-boot-devtools 加入 pom.xml

# Python 开发
cd python-engine && uv run uvicorn main:app --reload
# → 文件变更自动重载
```

---

## 6. 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                   单机部署 (开发/演示)                      │
│                                                          │
│  Docker:                                                 │
│  ┌──────────────────────┐                               │
│  │  PostgreSQL :5432    │                               │
│  └──────────────────────┘                               │
│                                                          │
│  本地进程:                                                │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │ Python     │  │ Spring Boot │  │ PostgreSQL       │  │
│  │ FastAPI    │  │ :8080       │  │ :5432           │  │
│  │ :8765      │  │             │  │                  │  │
│  └────────────┘  └─────────────┘  └──────────────────┘  │
│                                                          │
│  浏览器: http://localhost:8080                            │
└─────────────────────────────────────────────────────────┘
```

生产环境可扩展为 Docker Compose 全容器化部署，Java 和 Python 各一个 Dockerfile。

---

## 7. 安全与限制

| 项 | 说明 |
|---|---|
| **CORS** | Python FastAPI 仅允许来自 localhost:8080 的请求 |
| **WebSocket 限流** | 单客户端 BLE 事件推送频率上限 50 msg/s |
| **文件监听** | CSI watcher 仅监听配置的目录，不递归 |
| **数据库密码** | docker-compose.yml 中通过环境变量注入 |
| **数据集来源** | 使用公开学术数据集（SignFi/Widar3.0/NTU-Fi），非实时采集 |
