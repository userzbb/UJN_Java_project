"""BLE API 路由"""

from fastapi import APIRouter, Depends

from .deps import get_ble_scanner, get_ble_analyzer, get_event_bus
from ..stream.sse import sse_event_generator

router = APIRouter(prefix="/ble", tags=["BLE"])


@router.get("/scan/start")
async def start_scan(scanner=Depends(get_ble_scanner)):
    """启动 BLE 持续扫描。"""
    await scanner.start()
    return {"status": "scanning", "message": "BLE scan started"}


@router.get("/scan/stop")
async def stop_scan(scanner=Depends(get_ble_scanner)):
    """停止 BLE 扫描。"""
    await scanner.stop()
    return {"status": "stopped", "message": "BLE scan stopped"}


@router.get("/status")
async def get_status(scanner=Depends(get_ble_scanner), analyzer=Depends(get_ble_analyzer)):
    """扫描状态 + 统计摘要。"""
    return {
        "scanning": scanner.running,
        "summary": analyzer.get_summary(),
    }


@router.get("/devices")
async def get_devices(analyzer=Depends(get_ble_analyzer)):
    """已发现的设备列表。"""
    return {"devices": analyzer.get_devices()}


@router.get("/channel/usage")
async def get_channel_usage(analyzer=Depends(get_ble_analyzer)):
    """37/38/39 信道占用统计。"""
    return analyzer.get_channel_usage()


@router.get("/events/stream")
async def ble_event_stream(eb=Depends(get_event_bus)):
    """
    SSE 端点：实时推送 BLE 广播事件和快照。
    Spring Boot 通过此端点接收实时数据。
    """
    return await sse_event_generator(
        eb,
        ["ble:advertisement", "ble:snapshot"],
    )
