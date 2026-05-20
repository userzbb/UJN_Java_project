"""CSI 数据模型"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..core.models import TimestampedEvent


@dataclass
class CsiFrame:
    """单帧 CSI 测量。"""
    timestamp: float
    rssi: int = 0
    bandwidth: int = 20                     # MHz
    n_subcarriers: int = 30                 # Intel 5300 典型值
    csi_matrix: np.ndarray = field(         # (N_tx, N_rx, N_sub) complex64
        default_factory=lambda: np.array([])
    )
    source_mac: str = ""
    destination_mac: str = ""


@dataclass
class CsiFrameEvent(TimestampedEvent):
    """处理后推送到 SSE 的 CSI 帧事件。"""
    frame_index: int = 0
    timestamp: float = 0.0
    amplitude: list[float] = field(default_factory=list)     # 子载波幅度
    phase: list[float] = field(default_factory=list)          # 子载波相位
    motion_score: float = 0.0
    motion_detected: bool = False

    def __post_init__(self):
        self.event_type = "csi:frame"


@dataclass
class CsiAlert(TimestampedEvent):
    """运动告警。"""
    motion_score: float = 0.0
    frame_index: int = 0
    amplitude_snapshot: list[float] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = "csi:alert"


@dataclass
class DatasetInfo:
    """数据集元信息。"""
    name: str
    file_count: int = 0
    total_frames: int = 0
    duration_sec: float = 0.0
    total_size_mb: float = 0.0
