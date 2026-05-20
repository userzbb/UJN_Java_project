# 04 — WiFi CSI 技术细节

## 1. CSI 物理层原理

### 1.1 什么是 CSI

CSI（Channel State Information，信道状态信息）是无线通信物理层对信道频率响应的细粒度估计。WiFi 接收端对每个 OFDM 子载波独立估计信道响应，得到一组复数：

```
H(f_k) = Y(f_k) / X(f_k)          (频域信道估计)

其中: Y(f_k) = 接收到的子载波 f_k 上的符号
      X(f_k) = 发送端的长训练序列 (LTF, 已知)
      k      = 子载波编号
```

LTF（Long Training Field）是发送端在 WiFi 帧前置的已知导频符号，接收端用它做信道估计。

### 1.2 公开 CSI 数据集

本平台使用学术界公开 CSI 数据集进行分析，无需实时采集硬件。CSIKit 支持多种数据格式。

| 数据集 | 场景 | CSI 格式 | 子载波数 | 采集硬件 |
|--------|------|----------|:-------:|----------|
| **SignFi** | 手语手势识别 (150 种手势) | .csi | 30 | Intel 5300 |
| **Widar3.0** | 手势/人体活动识别 | .csi | 30 | Intel 5300 |
| **NTU-Fi** | 人体身份识别（多人） | .csi | 30 | Intel 5300 |
| **Custom .csi** | 用户自行下载/采集的数据集 | .csi | 可变 | 取决于来源 |

平台内置 SignFi 子集作为默认演示数据，其他数据集可下载后导入。

### 1.3 CSI 矩阵

一次 CSI 测量的输出是一个 4 维矩阵：

```
CSI[t] ∈ C^(N_tx × N_rx × N_subcarriers)

N_tx  = 2  (发射天线)
N_rx  = 2  (接收天线)
N_sub  = 256 (802.11n/ac, 20MHz) 或 996 (802.11ax, 80MHz)

每个 H[i,j,k] 是一个复数:
    |H| : 子载波幅度 (0~1, 归一化后)
    ∠H  : 子载波相位 (-π ~ π)

每帧 CSI 数据量:
    256 × 2 × 2 × 8 bytes ≈ 8 KB (complex64, per frame)
    996 × 2 × 2 × 8 bytes ≈ 31 KB (80MHz HE frame)
```

---

## 2. CSI 数据集加载

### 2.1 工作流程

```
公开 CSI 数据集 (本地存储)
    │
    │ python-engine/datasets/
    │   ├── signfi/
    │   │   ├── user1_gesture1.csi
    │   │   ├── user1_gesture2.csi
    │   │   └── ...
    │   ├── widar3/
    │   └── custom/               # 用户自行放置的数据集
    │
    ▼
用户在前端选择数据集 → 后端调用 Python /csi/load
    │
    ▼
csi/loader.py
    │
    │ 1. 扫描数据集目录，列出所有 .csi 文件
    │ 2. 按时间戳排序帧序列
    │ 3. 按配置的播放速度逐帧读取
    │ 4. 每帧 → CSIKit 解析 → 发布到 event_bus
    │
    ▼
csi/parser.py (CSIKit) 解析 → 推送到事件总线 → SSE → 前端实时渲染
```

### 2.2 数据集导入

```
1. 内置数据集
   · SignFi 子集随项目提供（python-engine/datasets/signfi/）
   · 用户可直接在前端选择使用

2. 外部数据集导入（两种方式）
   · 方式 A：手动下载 .csi 文件放到 python-engine/datasets/custom/ 目录
   · 方式 B：通过前端上传 .csi 文件 → Spring Boot 接收 → 存储到 Python datasets 目录

3. 支持的格式
   · .csi  (PicoScenes / Intel 5300 格式, CSIKit 解析)
   · .mat  (MATLAB 格式, scipy.io.loadmat 读取)
   · .csv  (CSV 导出格式, numpy/pandas 读取)
```

### 2.3 播放控制

前端提供类似视频播放器的控制：

| 控制 | 参数 | 说明 |
|------|------|------|
| 数据集选择 | dataset_name | 下拉列表，列出可用数据集 |
| 播放速度 | 0.1x – 10x | 1x = 实时（按帧时间戳间隔），10x = 10 倍速 |
| 进度条 | frame_index / total_frames | 可拖拽跳转到任意帧 |
| 暂停/继续 | — | 暂停推送，继续恢复 |
| 循环播放 | on/off | 播完后自动从头开始 |

---

## 3. CSIKit 解析

### 3.1 .csi 文件格式

PicoScenes .csi 文件是二进制格式，包含帧头元数据 + CSI 复数矩阵。CSIKit 库屏蔽了这个复杂性：

```python
# csi/parser.py

import csikit

def parse_csi_file(filepath: str) -> list[CsiFrame]:
    """
    解析 PicoScenes .csi 文件。
    
    Returns:
        list of CsiFrame, 一个 .csi 文件可能包含多帧 CSI 测量
    """
    frames = []
    csi_data = csikit.read(filepath)
    
    for frame in csi_data.frames:
        csi_frame = CsiFrame(
            timestamp=frame.timestamp,
            rssi=frame.rssi,
            bandwidth=frame.bandwidth_mhz,      # 20/40/80
            n_subcarriers=frame.nsub,
            csi_matrix=frame.csi_matrix,        # numpy (2, 2, nsub) complex64
            source_mac=frame.source_mac,
            destination_mac=frame.dest_mac,
        )
        frames.append(csi_frame)
    
    return frames
```

### 3.2 注意：CSI 矩阵提取

```python
# CSIKit 返回的 csi_matrix 维度可能因版本而异
# 确保处理所有维度情况:
def normalize_csi_matrix(raw_csi: np.ndarray) -> np.ndarray:
    """
    统一 CSI 矩阵为 (N_tx, N_rx, N_subcarriers) 格式。
    """
    if raw_csi.ndim == 3:
        return raw_csi                    # 已经是标准格式
    elif raw_csi.ndim == 2:
        return raw_csi[np.newaxis, :, :]  # 添加 Tx 维度
    elif raw_csi.ndim == 1:
        return raw_csi[np.newaxis, np.newaxis, :]  # 单天线
    else:
        raise ValueError(f"Unexpected CSI matrix shape: {raw_csi.shape}")
```

---

## 4. CSI 信号处理

### 4.1 幅度提取

```python
# csi/processor.py

import numpy as np
from scipy.signal import medfilt

def extract_amplitude(csi_matrix: np.ndarray) -> np.ndarray:
    """
    提取 CSI 幅度。

    Input:  (N_tx, N_rx, N_sub) complex64 复数矩阵
    Output: (N_sub,) float64 幅度向量（所有天线链路的平均）
    """
    # 对所有 Tx-Rx 天线对取幅度
    amplitude_grid = np.abs(csi_matrix)          # (N_tx, N_rx, N_sub)
    # 拉平天线维度取平均
    amplitude = np.mean(amplitude_grid, axis=(0, 1))  # (N_sub,)
    return amplitude

def smooth_amplitude(amp: np.ndarray, window: int = 5) -> np.ndarray:
    """中值滤波去噪"""
    return medfilt(amp, kernel_size=window)
```

### 4.2 Hampel 异常值滤波

```python
def hampel_filter(
    signal: np.ndarray, 
    window: int = 7, 
    n_sigma: float = 3.0
) -> np.ndarray:
    """
    Hampel 滤波器：检测并替换异常值。

    对每个点，计算以其为中心的窗口内中位数和 MAD。
    如果该点偏离中位数超过 n_sigma * MAD，视为异常并替换为中位数。

    Args:
        signal: 输入信号 (subcarrier,)
        window: 滑动窗口大小 (奇数)
        n_sigma: 阈值倍数 (默认 3 → 3σ)

    Returns:
        滤波后的信号
    """
    half = window // 2
    n = len(signal)
    filtered = signal.copy()

    for i in range(half, n - half):
        local = signal[i - half:i + half + 1]
        median = np.median(local)
        mad = np.median(np.abs(local - median))

        if mad == 0:
            continue

        z_score = 0.6745 * (signal[i] - median) / mad
        if np.abs(z_score) > n_sigma:
            filtered[i] = median

    return filtered
```

### 4.3 归一化

```python
def normalize_csi(amplitude: np.ndarray) -> np.ndarray:
    """
    归一化 CSI 幅度，消除 AGC 增益波动。

    使用每个时间帧的幅度除以中位数。
    """
    median = np.median(amplitude)
    if median < 1e-10:
        return amplitude
    return amplitude / median
```

---

## 5. 运动检测算法

### 5.1 滑动窗口方差法

```python
# csi/detector.py

class MotionDetector:
    def __init__(self, window_size: int = 50, threshold: float = 2.0):
        """
        Args:
            window_size: 滑动窗口大小（按帧数，50 帧 @ 50Hz = 1 秒）
            threshold: 方差比阈值，超过此值触发 motion 事件
        """
        self.window_size = window_size
        self.threshold = threshold
        self.amplitude_buffer = []       # 滑动窗口存储
        self.baseline_var = None          # 基准方差（无人时的稳态方差）
        self.baseline_samples = 200       # 校准需要的帧数
    
    def update(self, amplitude: np.ndarray) -> MotionResult:
        """
        输入当前帧的子载波幅度向量，返回运动检测结果。
        
        Args:
            amplitude: (N_sub,) 当前帧子载波幅度
            
        Returns:
            MotionResult: motion_score, motion_detected, details
        """
        self.amplitude_buffer.append(amplitude)
        if len(self.amplitude_buffer) > self.window_size:
            self.amplitude_buffer.pop(0)
        
        if len(self.amplitude_buffer) < self.window_size:
            return MotionResult(motion_score=0.0, motion_detected=False, 
                                status="calibrating")
        
        # 计算当前窗口内所有子载波的帧间方差
        window_stack = np.stack(self.amplitude_buffer, axis=0)  # (W, N_sub)
        current_var = np.var(window_stack, axis=0).mean()       # 所有子载波平均方差
        
        # 校准：积累基准方差
        if self.baseline_var is None:
            self.baseline_var = current_var
            self.baseline_samples -= len(self.amplitude_buffer)
            return MotionResult(motion_score=0.0, motion_detected=False, 
                                status="calibrating")
        
        # 运动分数 = 当前方差 / 基准方差
        motion_score = current_var / max(self.baseline_var, 1e-12)
        motion_detected = motion_score > self.threshold
        
        # 缓慢更新基准（适应环境缓慢变化，如温湿度）
        self.baseline_var = 0.95 * self.baseline_var + 0.05 * current_var
        
        return MotionResult(
            motion_score=float(motion_score),
            motion_detected=motion_detected,
            status="active",
        )
```

### 5.2 为什么这个算法有效

```
场景: 一个人在 WiFi 路由器和你的笔记本之间走过

时间轴:
帧 #:    0        50       100      150      200      250
       ┌────────┬────────┬────────┬────────┬────────┬────────┐
       │ 无人   │ 无人   │ █ 走动 │ █ 走动 │ 无人   │ 无人   │
       └────────┴────────┴────────┴────────┴────────┴────────┘

方差:   1.0x     0.9x     5.3x     4.8x     1.1x     0.8x
告警:   ○        ○        ●        ●        ○        ○

观察: 人在场时方差暴增 5 倍，触发阈值 2.0x
```

**为什么人体反射会影响 CSI？**
- 人体 ≈ 70% 水 → 对 2.4/5 GHz 信号强反射
- 移动中的人体产生时变多径 → 子载波幅度随时间波动
- 256 个子载波中总有若干对当前多径变化敏感

---

## 6. 数据集加载器

```python
# csi/loader.py

import asyncio
import time
from pathlib import Path

class CsiLoader:
    """
    数据集加载器：读取公开 CSI 数据集文件，按时间戳排序后逐帧推送到事件总线。

    支持格式：.csi (CSIKit), .mat (scipy.io), .csv (numpy/pandas)
    支持播放速度控制 (0.1x ~ 10x)
    """

    def __init__(self, event_bus: EventBus, config: Config):
        self.event_bus = event_bus
        self.config = config
        self._frames: list[CsiFrame] = []  # 已加载的全部帧
        self._current_idx = 0
        self._running = False
        self._speed = 1.0
        self._task: asyncio.Task | None = None

    def list_datasets(self) -> list[dict]:
        """扫描 datasets/ 目录，返回可用数据集列表"""
        ds_root = Path(self.config.csi_data_dir)
        datasets = []
        for subdir in ds_root.iterdir():
            if subdir.is_dir():
                files = list(subdir.glob("*.csi")) + list(subdir.glob("*.mat"))
                datasets.append({
                    "name": subdir.name,
                    "file_count": len(files),
                    "total_size_mb": sum(f.stat().st_size for f in files) / 1e6,
                })
        return datasets

    async def load(self, dataset_name: str) -> dict:
        """加载指定数据集的所有帧到内存"""
        ds_dir = Path(self.config.csi_data_dir) / dataset_name
        csi_files = sorted(ds_dir.glob("*.csi"))

        self._frames = []
        for fpath in csi_files:
            frames = parse_csi_file(str(fpath))
            self._frames.extend(frames)

        # 按时间戳排序
        self._frames.sort(key=lambda f: f.timestamp)
        self._current_idx = 0
        return {
            "dataset": dataset_name,
            "total_frames": len(self._frames),
            "duration_sec": self._frames[-1].timestamp - self._frames[0].timestamp 
                if len(self._frames) > 1 else 0,
        }

    async def play(self):
        """开始逐帧播放，按 speed 控制间隔"""
        self._running = True
        self._task = asyncio.create_task(self._play_loop())

    async def _play_loop(self):
        while self._running and self._current_idx < len(self._frames):
            frame = self._frames[self._current_idx]
            await self.event_bus.publish("csi:frame", frame)
            self._current_idx += 1

            # 按帧时间戳间隔 × speed 等待
            if self._current_idx < len(self._frames):
                dt = self._frames[self._current_idx].timestamp - frame.timestamp
                await asyncio.sleep(max(0, dt / self._speed))

    def pause(self):
        self._running = False

    def seek(self, idx: int):
        """跳转到指定帧"""
        self._current_idx = max(0, min(idx, len(self._frames) - 1))

    def set_speed(self, speed: float):
        """设置播放速度 (0.1 ~ 10.0)"""
        self._speed = max(0.1, min(10.0, speed))

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
```

**为什么用播放器模式而不是 watch 模式？** 
- 数据集是静态文件，不需要实时监听文件系统变化
- 播放器模式支持调速/跳转/循环，用户体验更好
- 可以配合 SSE 实现流式推送到前端，既保留实时动画效果，又解耦了数据来源

---

## 7. FastAPI 路由

```python
# api/csi_routes.py

router = APIRouter(prefix="/csi", tags=["CSI"])

@router.get("/datasets")
async def list_datasets(loader: CsiLoader = Depends(get_loader)):
    """列出可用数据集"""
    datasets = loader.list_datasets()
    return {"datasets": datasets}

@router.post("/load")
async def load_dataset(
    body: dict,  # {"dataset": "signfi_sample", "speed": 1.0}
    loader: CsiLoader = Depends(get_loader),
):
    """加载数据集并开始播放"""
    info = await loader.load(body["dataset"])
    loader.set_speed(body.get("speed", 1.0))
    await loader.play()
    return {"status": "playing", **info}

@router.post("/stop")
async def stop_playback(loader: CsiLoader = Depends(get_loader)):
    """停止播放"""
    loader.stop()
    return {"status": "stopped"}

@router.post("/pause")
async def pause_playback(loader: CsiLoader = Depends(get_loader)):
    """暂停/继续"""
    loader.pause()
    return {"status": "paused"}

@router.post("/seek")
async def seek_frame(body: dict, loader: CsiLoader = Depends(get_loader)):
    """跳转到指定帧"""
    loader.seek(body["frame_index"])
    return {"status": "seeked", "frame": body["frame_index"]}

@router.post("/speed")
async def set_speed(body: dict, loader: CsiLoader = Depends(get_loader)):
    """设置播放速度 0.1x ~ 10x"""
    loader.set_speed(body["speed"])
    return {"status": "ok", "speed": body["speed"]}

@router.get("/events/stream")
async def event_stream(...) -> StreamingResponse:
    """SSE 端点: 实时流式推送 CSI 帧到 Spring Boot"""
    ...
```

---

## 8. 前端 CSI 可视化规范

### 8.1 子载波热力图

```
// CsiHeatmap.vue
// 使用 ECharts heatmap 类型

数据格式 (每帧一行):
[
  [frame_idx, subcarrier_idx, amplitude_value],
  [0, 0, 0.85], [0, 1, 0.92], ..., [0, 255, 0.78],
  [1, 0, 0.83], [1, 1, 0.90], ..., [1, 255, 0.55],  ← 人在时幅度下降
  ...
]

ECharts 配置:
{
  xAxis: { name: '子载波编号', min: 0, max: 255 },
  yAxis: { name: '帧序号 (时间 →)', inverse: true },
  visualMap: {
    min: 0, max: 1,
    inRange: { color: ['#0a1628', '#22c55e', '#eab308', '#ef4444'] }
    //             深蓝(低)    绿(中)     黄(中高)   红(高)
  },
  series: [{ type: 'heatmap', data: [...] }]
}

// 滚动窗口: 只显示最近 100 帧，自动滚动
```

### 8.2 运动检测曲线

```
// CsiMotionChart.vue

数据格式:
[
  { timestamp: 1234567890.1, motion_score: 0.95, threshold: 2.0 },
  { timestamp: 1234567890.2, motion_score: 1.05, threshold: 2.0 },
  ...
  { timestamp: 1234567891.5, motion_score: 5.30, threshold: 2.0 },  ← 有人!
  ...
]

ECharts 配置:
{
  xAxis: { type: 'time', name: '时间' },
  yAxis: { type: 'value', name: '运动分数' },
  series: [
    {
      name: 'Motion Score',
      type: 'line',
      data: [...],
      areaStyle: { opacity: 0.3 },
      markLine: {
        data: [{ yAxis: 2.0, name: '告警阈值', lineStyle: { color: '#ef4444' } }]
      }
    }
  ]
}
```

### 8.3 告警列表

```
// CsiAlertList.vue

表格字段:
| 时间 | 运动分数 | 持续帧数 | 操作 |
|------|---------|---------|------|
| 14:23:01 | 5.3 | 45 帧 | [查看 CSI 快照] |
| 14:15:22 | 3.1 | 12 帧 | [查看 CSI 快照] |

"查看 CSI 快照" → 弹窗显示该时刻的子载波幅度曲线图
```
