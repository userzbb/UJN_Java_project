"""CSI 文件解析 — CSIKit 封装"""

from __future__ import annotations

import logging

import numpy as np

from .models import CsiFrame

logger = logging.getLogger(__name__)


def parse_csi_file(filepath: str) -> list[CsiFrame]:
    """
    解析 .csi 文件 → CsiFrame 列表。

    使用 CSIKit 库处理多种 .csi 格式：
      - PicoScenes (Intel AX200/210, Intel 5300)
      - Nexmon (Broadcom)
      - Atheros
      - ESP32

    如果 CSIKit 不可用，fallback 到生成模拟 CSI 数据用于开发。
    """
    try:
        import csikit
        return _parse_with_csikit(filepath, csikit)
    except ImportError:
        logger.warning("CSIKit not installed — generating synthetic CSI data for dev")
        return _generate_synthetic_frames(filepath)


def _parse_with_csikit(filepath: str, csikit) -> list[CsiFrame]:
    """使用 CSIKit 解析真实 .csi 文件。"""
    frames = []
    csi_data = csikit.read(filepath)

    for frame in csi_data.frames:
        csi_matrix = _normalize_csi_matrix(frame.csi_matrix)
        csi_frame = CsiFrame(
            timestamp=getattr(frame, "timestamp", 0.0),
            rssi=getattr(frame, "rssi", 0),
            bandwidth=getattr(frame, "bandwidth_mhz", 20),
            n_subcarriers=csi_matrix.shape[-1],
            csi_matrix=csi_matrix.astype(np.complex64),
            source_mac=getattr(frame, "source_mac", ""),
            destination_mac=getattr(frame, "dest_mac", ""),
        )
        frames.append(csi_frame)

    return frames


def _normalize_csi_matrix(raw_csi: np.ndarray) -> np.ndarray:
    """统一 CSI 矩阵为 (N_tx, N_rx, N_subcarriers)。"""
    if raw_csi.ndim == 3:
        return raw_csi
    elif raw_csi.ndim == 2:
        return raw_csi[np.newaxis, :, :]
    elif raw_csi.ndim == 1:
        return raw_csi[np.newaxis, np.newaxis, :]
    else:
        raise ValueError(f"Unexpected CSI matrix shape: {raw_csi.shape}")


# ── 开发用合成数据生成 ──

def _generate_synthetic_frames(filepath: str) -> list[CsiFrame]:
    """
    当 CSIKit 不可用时，生成模拟 CSI 数据供开发使用。
    这允许在没有真实 CSI 数据集的环境下开发前端可视化。
    """
    import time

    n_frames = 200
    n_sub = 30  # Intel 5300 典型值
    frames = []

    base_ts = time.time() - n_frames * 0.02  # 20ms 帧间隔（50Hz）

    for i in range(n_frames):
        ts = base_ts + i * 0.02

        # 模拟多径信道：几个不同频率的正弦波叠加
        amplitude = np.zeros((1, 1, n_sub), dtype=np.complex64)
        for k in range(n_sub):
            # 基础幅度随子载波编号略有变化（模拟频率选择性衰落）
            base = 0.7 + 0.3 * np.sin(k / 5.0)
            # 加入时变扰动（模拟人体运动对部分子载波的影响）
            motion_perturb = 0.0
            if 80 <= i <= 130:  # 帧 80-130 模拟有人走动
                if 5 <= k <= 20:
                    motion_perturb = 0.3 * np.sin(i * 0.3 + k * 0.5)
            # 热噪声
            noise = 0.05 * (np.random.randn() + 1j * np.random.randn())

            amplitude[0, 0, k] = base + motion_perturb + noise

        frames.append(CsiFrame(
            timestamp=ts,
            rssi=-40 + int(10 * np.sin(i * 0.1)),
            bandwidth=20,
            n_subcarriers=n_sub,
            csi_matrix=amplitude.astype(np.complex64),
        ))

    logger.info(
        "Generated %d synthetic CSI frames from %s (dev mode)",
        n_frames, filepath,
    )
    return frames
