"""CSI 运动检测 — 滑动窗口方差法"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class MotionResult:
    motion_score: float
    motion_detected: bool
    status: str = "active"  # calibrating | active


class MotionDetector:
    """
    基于 CSI 子载波幅度方差的运动检测器。

    原理：
      无人时 CSI 幅度稳定（仅热噪声），方差低；
      人体反射产生新的多径 → 特定子载波幅度波动 → 帧间方差升高。

    算法：
      1. 滑动窗口收集 N 帧幅度
      2. 计算窗口内所有子载波的平均方差
      3. 方差 / 基准方差 > threshold → motion_detected
    """

    def __init__(self, window_size: int = 50, threshold: float = 2.0):
        self.window_size = window_size
        self.threshold = threshold
        self._buffer: list[np.ndarray] = []
        self._baseline_var: float | None = None  # 稳态基准方差
        self._baseline_samples_remaining: int = 200

    def reset(self) -> None:
        """重置状态（切换数据集时调用）。"""
        self._buffer.clear()
        self._baseline_var = None
        self._baseline_samples_remaining = 200

    def update(self, amplitude: np.ndarray) -> MotionResult:
        """
        输入当前帧的子载波幅度向量，返回检测结果。

        Args:
            amplitude: (N_sub,) 当前帧子载波幅度
        Returns:
            MotionResult
        """
        self._buffer.append(amplitude)
        if len(self._buffer) > self.window_size:
            self._buffer.pop(0)

        if len(self._buffer) < self.window_size:
            return MotionResult(motion_score=0.0, motion_detected=False, status="calibrating")

        # 计算窗口内帧间方差（所有子载波平均）
        stack = np.stack(self._buffer, axis=0)  # (W, N_sub)
        current_var = float(np.var(stack, axis=0).mean())

        # 校准阶段：积累基准方差
        if self._baseline_var is None:
            self._baseline_var = current_var
            self._baseline_samples_remaining -= 1
            return MotionResult(motion_score=0.0, motion_detected=False, status="calibrating")

        if self._baseline_samples_remaining > 0:
            # 继续用初期数据更新基准
            alpha = 0.1
            self._baseline_var = (1 - alpha) * self._baseline_var + alpha * current_var
            self._baseline_samples_remaining -= 1
            return MotionResult(motion_score=0.0, motion_detected=False, status="calibrating")

        # 计算运动分数
        if self._baseline_var < 1e-12:
            motion_score = 0.0
        else:
            motion_score = current_var / self._baseline_var

        motion_detected = motion_score > self.threshold

        # 缓慢更新基准（适应环境缓慢变化）
        self._baseline_var = 0.95 * self._baseline_var + 0.05 * current_var

        return MotionResult(
            motion_score=round(motion_score, 3),
            motion_detected=motion_detected,
            status="active",
        )
