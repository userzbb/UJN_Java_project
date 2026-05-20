"""SSE 流管理器 — 从事件总线消费事件，格式化为 SSE 推送"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from starlette.responses import StreamingResponse

from ..core.events import EventBus

logger = logging.getLogger(__name__)


async def sse_event_generator(
    event_bus: EventBus,
    event_types: list[str],
    keepalive_sec: int = 15,
) -> StreamingResponse:
    """
    创建一个 SSE StreamingResponse，从事件总线消费指定类型的事件。

    用法（在 FastAPI 路由中）：
        return await sse_event_generator(event_bus, ["ble:advertisement", "ble:snapshot"])
    """
    # 为每个事件类型创建队列消费者
    queues = {et: event_bus.get_queue(et) for et in event_types}

    async def generate():
        last_keepalive = time.monotonic()
        while True:
            # 从所有队列轮询事件
            something_sent = False
            for event_type, queue in queues.items():
                try:
                    payload = queue.get_nowait()
                    yield _format_sse(event_type, payload)
                    something_sent = True
                except asyncio.QueueEmpty:
                    pass

            # 如果本周期没事件，发 keepalive 注释
            now = time.monotonic()
            if now - last_keepalive >= keepalive_sec:
                yield ": keepalive\n\n"
                last_keepalive = now

            # 如果没有事件，短暂等待后再检查
            if not something_sent:
                await asyncio.sleep(0.05)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # nginx 不缓冲
        },
    )


def _format_sse(event_type: str, payload) -> str:
    """将事件格式化为 SSE 文本。"""
    data = _serialize(payload)
    return f"event: {event_type}\ndata: {data}\n\n"


def _serialize(obj) -> str:
    """JSON 序列化，处理 dataclass/numpy/自定义类型。"""
    if hasattr(obj, "__dataclass_fields__"):
        return json.dumps(_dataclass_to_dict(obj), default=_json_default)
    if isinstance(obj, dict):
        return json.dumps(obj, default=_json_default)
    return json.dumps({"value": obj}, default=_json_default)


def _json_default(o):
    """JSON 序列化 fallback。"""
    import numpy as np
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    raise TypeError(f"Unserializable type: {type(o)}")


def _dataclass_to_dict(obj) -> dict:
    """将 dataclass 转为 dict，跳过不可序列化的字段。"""
    result = {}
    for field_name, field_def in obj.__dataclass_fields__.items():
        value = getattr(obj, field_name)
        # 跳过 numpy 数组（太大），子载波数据已经在专门的 amplitude/phase 字段里
        try:
            json.dumps({"test": value}, default=_json_default)
            result[field_name] = value
        except (TypeError, OverflowError):
            result[field_name] = str(type(value).__name__)
    return result
