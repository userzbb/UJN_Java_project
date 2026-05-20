"""CSI 信号处理 — 幅度/相位提取 + Hampel 滤波 + 归一化"""

from __future__ import annotations

import numpy as np
from scipy.signal import medfilt


class CsiProcessor:
    """CSI 信号处理流水线。"""

    def __init__(self, hampel_window: int = 7, hampel_sigma: float = 3.0):
        self.hampel_window = hampel_window
        self.hampel_sigma = hampel_sigma

    # ── 幅度提取 ──

    def extract_amplitude(self, csi_matrix: np.ndarray) -> np.ndarray:
        """
        Input:  (N_tx, N_rx, N_sub) complex64
        Output: (N_sub,) float64, 所有天线链路平均
        """
        amp = np.abs(csi_matrix)  # (N_tx, N_rx, N_sub)
        amp_mean = np.mean(amp, axis=(0, 1))  # (N_sub,)
        return amp_mean

    # ── 相位提取 ──

    def extract_phase(self, csi_matrix: np.ndarray) -> np.ndarray:
        """
        Input:  (N_tx, N_rx, N_sub) complex64
        Output: (N_sub,) float64, 所有天线链路的平均相位 (radians)
        """
        phase = np.angle(csi_matrix)  # (-π, π)
        phase_mean = np.mean(phase, axis=(0, 1))
        return phase_mean

    # ── 去噪 ──

    def smooth_amplitude(self, amp: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """中值滤波平滑。"""
        if len(amp) < kernel_size:
            return amp
        return medfilt(amp, kernel_size=kernel_size)

    # ── Hampel 异常值滤波 ──

    def hampel_filter(self, signal: np.ndarray) -> np.ndarray:
        """
        Hampel 滤波器：检测并替换偏离中位数超过 n_sigma * MAD 的异常值。

        Args:
            signal: 1D 信号数组
        Returns:
            滤波后的数组
        """
        half = self.hampel_window // 2
        n = len(signal)

        if n < self.hampel_window:
            return signal  # 窗口太大，跳过

        filtered = signal.copy()
        for i in range(half, n - half):
            window = signal[i - half : i + half + 1]
            median = np.median(window)
            mad = np.median(np.abs(window - median))

            if mad < 1e-12:
                continue

            z = 0.6745 * (signal[i] - median) / mad
            if np.abs(z) > self.hampel_sigma:
                filtered[i] = median

        return filtered

    # ── 归一化 ──

    @staticmethod
    def normalize(amplitude: np.ndarray) -> np.ndarray:
        """按中位数归一化，消除 AGC 增益波动。"""
        median = np.median(amplitude)
        if median < 1e-10:
            return amplitude
        return amplitude / median

    # ── 流水线 ──

    def process(self, csi_matrix: np.ndarray) -> dict:
        """完整处理流水线：幅度 → 平滑 → Hampel → 归一化。"""
        amp = self.extract_amplitude(csi_matrix)
        amp = self.smooth_amplitude(amp)
        amp = self.hampel_filter(amp)
        amp = self.normalize(amp)
        phase = self.extract_phase(csi_matrix)
        return {"amplitude": amp, "phase": phase}
