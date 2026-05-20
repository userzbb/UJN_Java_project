"""共享数据模型基类"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class TimestampedEvent:
    """所有事件的基类。"""
    timestamp: float = field(default_factory=time.time)
    event_type: str = ""
