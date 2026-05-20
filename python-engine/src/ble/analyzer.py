"""BLE 分析器 — 设备聚合 + 信道占用统计 + 快照生成"""

from __future__ import annotations

import logging
import time
from collections import defaultdict

from ..core.events import EventBus
from .models import BleDevice, BleEvent, BleSnapshot

logger = logging.getLogger(__name__)

SNAPSHOT_INTERVAL_SEC = 300  # 5 分钟


class BleAnalyzer:
    """维护设备列表和信道统计，定期生成快照。"""

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self.devices: dict[str, BleDevice] = {}
        self.channel_counts: dict[int, int] = defaultdict(int)  # {37: N, 38: N, 39: N}
        self._rssi_samples: list[int] = []
        self._last_snapshot_ts: float = time.monotonic()

        # 订阅 BLE 事件
        event_bus.subscribe("ble:advertisement", self._on_advertisement)

    async def _on_advertisement(self, event: BleEvent) -> None:
        # ── 更新设备聚合 ──
        if event.mac in self.devices:
            self.devices[event.mac].update_rssi(event.rssi)
        else:
            self.devices[event.mac] = BleDevice(
                mac=event.mac,
                name=event.name,
                rssi_mean=float(event.rssi),
                rssi_max=event.rssi,
                rssi_min=event.rssi,
                channel_distribution={event.channel: 1},
                packet_count=1,
            )

        self.devices[event.mac].channel_distribution[event.channel] = (
            self.devices[event.mac].channel_distribution.get(event.channel, 0) + 1
        )

        # ── 信道计数 ──
        if event.channel != 0:
            self.channel_counts[event.channel] += 1

        # ── RSSI 样本（用于直方图） ──
        self._rssi_samples.append(event.rssi)

        # ── 周期快照 ──
        now = time.monotonic()
        if now - self._last_snapshot_ts >= SNAPSHOT_INTERVAL_SEC:
            await self._take_snapshot()
            self._last_snapshot_ts = now

    async def _take_snapshot(self) -> None:
        top = sorted(
            self.devices.values(),
            key=lambda d: d.rssi_mean,
            reverse=True,
        )[:10]

        snapshot = BleSnapshot(
            total_devices=len(self.devices),
            channel_37_count=self.channel_counts.get(37, 0),
            channel_38_count=self.channel_counts.get(38, 0),
            channel_39_count=self.channel_counts.get(39, 0),
            rssi_histogram=_compute_histogram(self._rssi_samples),
            top_devices=[d.mac for d in top],
        )
        await self._event_bus.publish("ble:snapshot", snapshot)

    # ── 查询方法 ──

    def get_devices(self, min_rssi: int = -100) -> list[dict]:
        """返回设备列表（去除信号极弱的）。"""
        return [
            self._device_to_dict(d)
            for d in self.devices.values()
            if d.rssi_mean >= min_rssi
        ]

    def get_channel_usage(self) -> dict:
        total = sum(self.channel_counts.values())
        if total == 0:
            return {"37": 0.0, "38": 0.0, "39": 0.0, "total": 0}
        return {
            "37": round(self.channel_counts[37] / total, 4),
            "38": round(self.channel_counts[38] / total, 4),
            "39": round(self.channel_counts[39] / total, 4),
            "total": total,
        }

    def get_summary(self) -> dict:
        return {
            "devices": len(self.devices),
            "total_packets": sum(d.packet_count for d in self.devices.values()),
            "channel_counts": dict(self.channel_counts),
        }

    # ── 内部 ──

    @staticmethod
    def _device_to_dict(d: BleDevice) -> dict:
        return {
            "mac": d.mac,
            "name": d.name,
            "rssi_mean": round(d.rssi_mean, 1),
            "rssi_max": d.rssi_max,
            "rssi_min": d.rssi_min,
            "first_seen": d.first_seen,
            "last_seen": d.last_seen,
            "packet_count": d.packet_count,
        }


def _compute_histogram(samples: list[int], bin_width: int = 5) -> list[int]:
    """计算 RSSI 分布直方图，bin_width=5 dBm。"""
    if not samples:
        return []
    bins: dict[int, int] = defaultdict(int)
    for rssi in samples:
        bin_key = (rssi // bin_width) * bin_width
        bins[bin_key] += 1
    return [bins[k] for k in sorted(bins)]


# ── 单例 ──

_analyzer_instance: BleAnalyzer | None = None


def get_analyzer(event_bus: EventBus) -> BleAnalyzer:
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = BleAnalyzer(event_bus)
    return _analyzer_instance
