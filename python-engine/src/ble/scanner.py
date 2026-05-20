"""BLE 扫描器 — 封装 bleak.BleakScanner"""

from __future__ import annotations

import logging

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from ..core.events import EventBus

logger = logging.getLogger(__name__)

# 广播信道频率 → 信道号映射
FREQ_TO_CHANNEL = {
    2402: 37,
    2426: 38,
    2480: 39,
}


class BleScanner:
    """BLE 被动扫描器，把每个广播包转为 BleEvent 并发布到事件总线。"""

    def __init__(self, event_bus: EventBus, active: bool = True):
        self._event_bus = event_bus
        self._scanner: BleakScanner | None = None
        self._running = False
        self._active = active

    # ── 生命周期 ──

    async def start(self) -> None:
        self._scanner = BleakScanner(
            detection_callback=self._on_detection,
            scanning_mode="active" if self._active else "passive",
        )
        self._running = True
        await self._scanner.start()
        logger.info("BLE scanner started (mode=%s)", "active" if self._active else "passive")

    async def stop(self) -> None:
        self._running = False
        if self._scanner:
            await self._scanner.stop()
            logger.info("BLE scanner stopped")

    # ── 回调 ──

    async def _on_detection(self, device: BLEDevice, ad_data: AdvertisementData):
        from .models import BleEvent
        from .parser import parse_advertisement

        parsed = parse_advertisement(device, ad_data)

        event = BleEvent(
            mac=device.address,
            name=parsed.get("name", "Unknown"),
            rssi=ad_data.rssi,
            tx_power=ad_data.tx_power,
            channel=parsed.get("channel", 0),
            manufacturer_id=parsed.get("manufacturer_id", ""),
            manufacturer_data=parsed.get("manufacturer_data"),
            service_uuids=ad_data.service_uuids or [],
        )
        await self._event_bus.publish("ble:advertisement", event)

    @property
    def running(self) -> bool:
        return self._running


# ── 单例 ──

_scanner_instance: BleScanner | None = None


def get_scanner(event_bus: EventBus) -> BleScanner:
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = BleScanner(event_bus)
    return _scanner_instance
