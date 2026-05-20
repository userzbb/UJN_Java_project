"""BLE 数据模型"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..core.models import TimestampedEvent


@dataclass
class BleEvent(TimestampedEvent):
    """单个 BLE 广播包事件。"""
    mac: str = ""
    name: str = "Unknown"
    rssi: int = -100
    tx_power: int | None = None
    channel: int = 0           # 37 / 38 / 39
    manufacturer_id: str = ""
    manufacturer_data: str | None = None
    service_uuids: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = "ble:advertisement"


@dataclass
class BleDevice:
    """聚合后的蓝牙设备信息。"""
    mac: str
    name: str
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    rssi_mean: float = 0.0
    rssi_max: int = -100
    rssi_min: int = -20
    channel_distribution: dict[int, int] = field(default_factory=lambda: {37: 0, 38: 0, 39: 0})
    packet_count: int = 0

    def update_rssi(self, rssi: int, alpha: float = 0.2) -> None:
        self.rssi_mean = alpha * rssi + (1 - alpha) * self.rssi_mean
        self.rssi_max = max(self.rssi_max, rssi)
        self.rssi_min = min(self.rssi_min, rssi)
        self.last_seen = time.time()
        self.packet_count += 1


@dataclass
class BleSnapshot(TimestampedEvent):
    """周期快照（每 5 分钟），写入 PostgreSQL。"""
    total_devices: int = 0
    channel_37_count: int = 0
    channel_38_count: int = 0
    channel_39_count: int = 0
    rssi_histogram: list[int] = field(default_factory=list)  # 按 5 dBm bin
    top_devices: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.event_type = "ble:snapshot"
