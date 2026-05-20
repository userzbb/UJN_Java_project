"""BLE 广播包解析 — AD Structure 二次提取 + 信道推断"""

from __future__ import annotations

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

# 常见 Company ID（蓝牙 SIG 分配）
WELL_KNOWN_COMPANY_IDS = {
    0x004C: "Apple Inc.",
    0x0006: "Microsoft",
    0x00E0: "Google",
    0x0075: "Samsung Electronics",
    0x0059: "Nordic Semiconductor",
    0x0131: "Xiaomi",
    0x02E5: "Huawei",
}

# 常见信道频率（MHz）→ 信道号
FREQ_TO_CHANNEL = {
    2402: 37,
    2426: 38,
    2480: 39,
}


def infer_channel_from_rssi(rssi: int) -> int:
    """
    当操作系统不提供频率信息时，用 RSSI 值做启发式推断。
    大部分蓝牙芯片在 3 个广播信道上发射功率相同，
    但接收端在不同频率上的天线增益可能不同导致 RSSI 偏差。

    实际中此方法不精确，建议从 hci 层获取频率。
    返回 0 表示未知。
    """
    # 此函数的精确版本需要访问 HCI 事件中的 channel_index 字段。
    # bleak 在 Windows 上可能不暴露这个字段。
    # 作为 fallback：默认返回 0 (unknown)
    return 0


def infer_channel(freq_hz: int | None) -> int:
    """根据频率（Hz）推断信道号。"""
    if freq_hz is None:
        return 0
    freq_mhz = round(freq_hz / 1_000_000)
    # 放宽到 ±2 MHz 容差
    for center, ch in FREQ_TO_CHANNEL.items():
        if abs(freq_mhz - center) <= 2:
            return ch
    return 0


def extract_name(device: BLEDevice, ad_data: AdvertisementData) -> str:
    """提取设备名称，优先级：bleak 解析 > 设备自身 > Unknown。"""
    if ad_data.local_name:
        return ad_data.local_name
    if device.name:
        return device.name
    return "Unknown"


def extract_manufacturer(ad_data: AdvertisementData) -> dict:
    """提取厂商信息。"""
    result = {"manufacturer_id": "", "manufacturer_data": None}
    if ad_data.manufacturer_data:
        for company_id, data in ad_data.manufacturer_data.items():
            result["manufacturer_id"] = f"0x{company_id:04X}"
            result["manufacturer_data"] = data.hex()
            break  # 通常只有一个
    return result


def parse_advertisement(
    device: BLEDevice, ad_data: AdvertisementData
) -> dict:
    """
    解析一个广播包，返回结构化字段。
    此函数不依赖 async，可在同步回调中安全调用。
    """
    mfg = extract_manufacturer(ad_data)

    return {
        "name": extract_name(device, ad_data),
        "manufacturer_id": mfg["manufacturer_id"],
        "manufacturer_data": mfg["manufacturer_data"],
        # 尝试从元数据获取频率（部分后端支持）
        "channel": _try_get_channel(ad_data, device),
    }


def _try_get_channel(ad_data: AdvertisementData, device: BLEDevice) -> int:
    """尝试从不同的可能数据源获取信道。"""
    # 1. 检查 advertisement data 中的 platform_data
    if hasattr(ad_data, "platform_data") and ad_data.platform_data:
        pd = ad_data.platform_data
        if isinstance(pd, dict):
            freq = pd.get("freq") or pd.get("frequency")
            if freq:
                return infer_channel(int(freq))

    # 2. 检查 BLEDevice 的 metadata
    if hasattr(device, "metadata") and device.metadata:
        freq = device.metadata.get("freq")
        if freq:
            return infer_channel(int(freq))

    # 3. RSSI fallback (不太可靠，标记为未知)
    return infer_channel_from_rssi(ad_data.rssi)
