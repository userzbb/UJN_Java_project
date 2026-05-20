"""异步事件总线 — 基于 asyncio.Queue 的发布/订阅模式"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

Callback = Callable[[Any], Coroutine[Any, Any, None]]


class EventBus:
    """轻量级异步事件总线。"""

    def __init__(self):
        self._subscribers: dict[str, list[Callback]] = defaultdict(list)
        self._queues: dict[str, asyncio.Queue] = {}

    # ── 订阅 ──

    def subscribe(self, event_type: str, callback: Callback) -> None:
        """注册回调，每次 publish(event_type) 时触发。"""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callback) -> None:
        """移除回调。"""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb is not callback
            ]

    # ── 发布 ──

    async def publish(self, event_type: str, payload: Any) -> None:
        """发布事件：通知所有订阅回调 + 写入队列（供 SSE 消费）。"""
        # 推送给订阅回调
        for cb in self._subscribers.get(event_type, []):
            try:
                await cb(payload)
            except Exception as exc:
                # 单个回调失败不应影响其他订阅者
                import logging
                logging.getLogger(__name__).warning(
                    "EventBus callback %s failed for %s: %s", cb.__name__, event_type, exc
                )

        # 放入队列供 SSE 拉取
        await self._put_queue(event_type, payload)

    async def publish_many(self, event_type: str, items: list[Any]) -> None:
        """批量发布。"""
        for item in items:
            await self.publish(event_type, item)

    # ── 队列 (SSE 消费端) ──

    def get_queue(self, event_type: str, maxsize: int = 1024) -> asyncio.Queue:
        """获取（或创建）事件队列，供 SSE endpoint 消费。"""
        if event_type not in self._queues:
            self._queues[event_type] = asyncio.Queue(maxsize=maxsize)
        return self._queues[event_type]

    async def _put_queue(self, event_type: str, payload: Any) -> None:
        q = self.get_queue(event_type)
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            # 丢弃最旧的事件（滑动窗口式）
            try:
                q.get_nowait()
                q.task_done()
                q.put_nowait(payload)
            except asyncio.QueueEmpty:
                pass


# 全局单例
event_bus = EventBus()
