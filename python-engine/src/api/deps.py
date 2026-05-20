"""FastAPI 依赖注入 — 获取引擎单例"""

from ..core.events import event_bus
from ..ble.scanner import get_scanner
from ..ble.analyzer import get_analyzer
from ..csi.loader import get_loader


def get_event_bus():
    return event_bus


def get_ble_scanner():
    return get_scanner(event_bus)


def get_ble_analyzer():
    return get_analyzer(event_bus)


def get_csi_loader():
    return get_loader(event_bus)
