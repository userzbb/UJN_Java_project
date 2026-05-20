"""全局配置（环境变量优先，否则用默认值）"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    # ── Server ──
    host: str = field(default_factory=lambda: os.getenv("ENGINE_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(os.getenv("ENGINE_PORT", "8765")))

    # ── Data directories ──
    csi_data_dir: Path = field(default_factory=lambda: Path(
        os.getenv("CSI_DATA_DIR", str(Path(__file__).resolve().parents[3] / "datasets"))
    ))

    # ── BLE ──
    ble_scan_duration_default: float = 0.0   # 0 = 持续扫描直到手动停止
    ble_active_scan: bool = True              # Active scan → 请求更多广播数据

    # ── CSI ──
    csi_default_speed: float = 1.0            # 播放速度 1x
    csi_motion_window: int = 50               # 运动检测滑动窗口（帧数）
    csi_motion_threshold: float = 2.0         # 运动告警阈值（方差比）
    csi_baseline_frames: int = 200            # 基准方差校准帧数

    # ── SSE ──
    sse_queue_size: int = 1024
    sse_keepalive_sec: int = 15

    # ── CORS ──
    cors_origins: list[str] = field(default_factory=lambda: [
        "http://localhost:8080",
        "http://localhost:5173",
    ])


config = Config()
