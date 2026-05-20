"""CSI 数据集加载器 — 从文件读取 + 逐帧播放"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from ..core.config import config
from ..core.events import EventBus
from .models import CsiFrame, CsiFrameEvent, DatasetInfo
from .parser import parse_csi_file
from .processor import CsiProcessor
from .detector import MotionDetector

logger = logging.getLogger(__name__)


class CsiLoader:
    """
    加载 CSI 数据集，逐帧推送到事件总线。
    支持播放控制：play / pause / seek / speed。
    """

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._frames: list[CsiFrame] = []
        self._current_idx = 0
        self._running = False
        self._speed = config.csi_default_speed
        self._task: asyncio.Task | None = None
        self._processor = CsiProcessor()
        self._detector = MotionDetector(
            window_size=config.csi_motion_window,
            threshold=config.csi_motion_threshold,
        )

    # ── 数据集发现 ──

    def list_datasets(self) -> list[dict]:
        """扫描 datasets/ 目录，列出可用数据集。"""
        ds_root = config.csi_data_dir
        if not ds_root.exists():
            logger.warning("CSI data dir not found: %s", ds_root)
            return []

        datasets = []
        for subdir in sorted(ds_root.iterdir()):
            if not subdir.is_dir():
                continue
            csi_files = list(subdir.glob("*.csi"))
            mat_files = list(subdir.glob("*.mat"))
            all_files = csi_files + mat_files
            if not all_files:
                continue

            total_size = sum(f.stat().st_size for f in all_files)
            datasets.append({
                "name": subdir.name,
                "file_count": len(all_files),
                "total_size_mb": round(total_size / 1e6, 2),
                "formats": list(set(f.suffix for f in all_files)),
            })
        return datasets

    # ── 加载 ──

    async def load(self, dataset_name: str) -> dict:
        """加载指定数据集的所有帧到内存。"""
        ds_dir = config.csi_data_dir / dataset_name
        if not ds_dir.exists():
            raise FileNotFoundError(f"Dataset not found: {dataset_name}")

        csi_files = sorted(ds_dir.glob("*.csi"))
        if not csi_files:
            raise ValueError(f"No .csi files found in dataset: {dataset_name}")

        self._frames = []
        for fpath in csi_files:
            logger.info("Loading %s ...", fpath.name)
            try:
                frames = parse_csi_file(str(fpath))
                self._frames.extend(frames)
            except Exception as exc:
                logger.error("Failed to parse %s: %s", fpath.name, exc)

        if not self._frames:
            raise ValueError(f"No valid frames in dataset: {dataset_name}")

        # 按时间戳排序
        self._frames.sort(key=lambda f: f.timestamp)
        self._current_idx = 0
        self._detector.reset()

        duration = (
            self._frames[-1].timestamp - self._frames[0].timestamp
            if len(self._frames) > 1 else 0.0
        )

        logger.info(
            "Loaded dataset '%s': %d frames, %.1f sec",
            dataset_name, len(self._frames), duration,
        )
        return {
            "dataset": dataset_name,
            "total_frames": len(self._frames),
            "duration_sec": round(duration, 1),
        }

    # ── 播放控制 ──

    async def play(self) -> None:
        """开始逐帧播放。"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._play_loop())

    async def _play_loop(self) -> None:
        """逐帧推送到事件总线。"""
        while self._running and self._current_idx < len(self._frames):
            frame = self._frames[self._current_idx]

            # 信号处理
            amplitude = self._processor.extract_amplitude(frame.csi_matrix)
            phase = self._processor.extract_phase(frame.csi_matrix)

            # 运动检测
            motion_result = self._detector.update(amplitude)

            # 构造事件
            event = CsiFrameEvent(
                timestamp=frame.timestamp,
                frame_index=self._current_idx,
                amplitude=amplitude.tolist(),
                phase=phase.tolist(),
                motion_score=motion_result.motion_score,
                motion_detected=motion_result.motion_detected,
            )
            await self._event_bus.publish("csi:frame", event)

            self._current_idx += 1

            # 按帧时间戳间隔 × speed 控制播放速率
            if self._running and self._current_idx < len(self._frames):
                dt = (
                    self._frames[self._current_idx].timestamp
                    - frame.timestamp
                )
                await asyncio.sleep(max(0.001, dt / self._speed))

    def pause(self) -> None:
        """暂停。"""
        self._running = False

    def seek(self, idx: int) -> None:
        """跳转到指定帧（0-indexed）。"""
        self._current_idx = max(0, min(idx, len(self._frames) - 1))

    def set_speed(self, speed: float) -> None:
        """设置播放速度 0.1 ~ 10x。"""
        self._speed = max(0.1, min(10.0, speed))

    async def stop(self) -> None:
        """停止播放。"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    # ── 状态查询 ──

    @property
    def playing(self) -> bool:
        return self._running

    @property
    def progress(self) -> dict:
        return {
            "current_frame": self._current_idx,
            "total_frames": len(self._frames),
            "speed": self._speed,
        }


# ── 单例 ──

_loader_instance: CsiLoader | None = None


def get_loader(event_bus: EventBus) -> CsiLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = CsiLoader(event_bus)
    return _loader_instance
