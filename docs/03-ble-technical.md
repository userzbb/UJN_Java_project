# 03 — BLE 技术细节

## 1. BLE 协议栈层次

```
┌──────────────────────────────────┐
│  Application (GATT Profile)     │  ← 你的平台不处理这层
├──────────────────────────────────┤
│  Host (GAP, GATT, ATT, SM, L2CAP)│
├──────────────────────────────────┤
│  Controller (HCI, Link Layer, PHY)│  ← bleak 在 HCI 层抓广播包
├──────────────────────────────────┤
│  Radio (2.4 GHz)                 │
└──────────────────────────────────┘
```

本平台只关注 **Advertising（广播）** 层：被动监听 BLE 设备发出的广播帧，不建立连接。这对应 GAP（Generic Access Profile）的 Broadcaster/Observer 角色。

---

## 2. 广播包类型

| ADV PDU Type | 名称 | 说明 | 本平台处理 |
|-------------|------|------|:---------:|
| 0x00 | ADV_IND | 可连接非定向广播（最常见） | ✅ |
| 0x01 | ADV_DIRECT_IND | 定向连接广播 | ✅ |
| 0x02 | ADV_NONCONN_IND | 不可连接非定向广播（Beacon 常用） | ✅ |
| 0x03 | SCAN_REQ | 扫描请求 | ❌ |
| 0x04 | SCAN_RSP | 扫描响应 | ✅ |
| 0x05 | CONNECT_IND | 连接请求 | ❌ |
| 0x06 | ADV_SCAN_IND | 可扫描非定向广播 | ✅ |

---

## 3. 广播包解析链路

### 3.1 bleak 回调

```python
# ble/scanner.py

from bleak import BleakScanner

async def on_advertisement(device: BLEDevice, advertisement_data: AdvertisementData):
    """
    bleak 回调: 每收到一个 BLE 广播包触发一次
    
    参数:
      device: BLEDevice — MAC 地址 + 名称
      advertisement_data: AdvertisementData — 解析后的 AD Structure
    """
    event = BleEvent(
        mac=device.address,
        name=device.name,
        rssi=advertisement_data.rssi,
        tx_power=advertisement_data.tx_power,
        manufacturer=extract_manufacturer(advertisement_data),
        # 信道推断 (见 3.2)
        channel=infer_channel(frequency_hz),
    )
    await event_bus.publish(event)
```

### 3.2 信道推断

bleak 在 Windows 上不直接暴露广播信道号（37/38/39），但可以从数据包频率推断：

```python
# ble/parser.py

CHANNEL_FREQ_MAP = {
    2402: 37,  # 2402 MHz
    2426: 38,  # 2426 MHz
    2480: 39,  # 2480 MHz
}

# 允许 ±1 MHz 容差（实际晶振误差远小于此）
def infer_channel(freq_hz):
    freq_mhz = round(freq_hz / 1_000_000)
    if abs(freq_mhz - 2402) <= 1:
        return 37
    elif abs(freq_mhz - 2426) <= 1:
        return 38
    elif abs(freq_mhz - 2480) <= 1:
        return 39
    return 0  # 未知信道（连接建立后跳到数据信道）
```

如果 bleak 平台不提供频率字段，使用 RSSI 差异启发式（同设备在 3 个信道上的 RSSI 通常不同，可通过聚类分离）。

### 3.3 AD Structure 解析

```python
# ble/parser.py

from bleak.uuids import uuid16_dict

def parse_ad_structures(ad_data: AdvertisementData) -> dict:
    """
    提取 AD Structure 关键字段。
    bleak 已做了基础解析，这里做二次提取和厂商特定处理。
    """
    result = {
        "flags": ad_data.flags,           # 0x01
        "name_complete": None,            # 0x09
        "tx_power": ad_data.tx_power,     # 0x0A
        "manufacturer_data": {},           # 0xFF
        "service_uuids": ad_data.service_uuids,
    }
    
    # 设备名称提取（优先 Complete，其次 Shortened）
    result["name"] = (
        ad_data.local_name                  # bleak 已处理 Complete/Shortened
        or extract_name_from_mfg(ad_data)   # Apple 设备藏在 Mfg Data 里
        or "Unknown"
    )
    
    # 厂商识别
    for company_id, data in ad_data.manufacturer_data.items():
        result["manufacturer_data"][hex(company_id)] = data.hex()
    
    return result
```

### 3.4 厂商识别（基于 Company ID）

```
常见蓝牙 SIG 分配的 Company ID:
  0x004C  — Apple Inc.
  0x0006  — Microsoft
  0x00E0  — Google
  0x0075  — Samsung Electronics
  0x0059  — Nordic Semiconductor
```

---

## 4. BLE 数据模型

```python
# ble/models.py

@dataclass
class BleEvent(TimestampedEvent):
    """
    单个 BLE 广播包事件。
    频率: 每秒几十到几百个（取决于环境设备密度）
    """
    mac: str              # MAC 地址 (e.g., "AA:BB:CC:DD:EE:FF")
    name: str             # 设备名称 (e.g., "AirPods Pro")
    rssi: int             # 接收信号强度 (dBm, 典型 -90 到 -20)
    tx_power: int | None  # 发射功率 (dBm, 部分设备提供)
    channel: int          # 广播信道 37/38/39
    manufacturer_id: str  # 厂商 ID
    manufacturer_data: str | None  # 厂商自定义数据 (hex)
    service_uuids: list[str]       # 服务 UUID


@dataclass
class BleDevice:
    """
    发现设备聚合信息。
    同一个 MAC 可能收到多次广播包，这里聚合统计。
    """
    mac: str
    name: str
    first_seen: float     # 首次发现时间 (Unix timestamp)
    last_seen: float      # 最近发现时间
    rssi_mean: float      # 平均 RSSI
    rssi_max: int
    rssi_min: int
    channel_distribution: dict[int, int]  # {37: N, 38: N, 39: N}
    packet_count: int     # 收到该设备的广播包总数


@dataclass
class BleSnapshot:
    """
    周期快照（每 5 分钟），写入 PostgreSQL。
    """
    timestamp: float
    total_devices: int
    channel_37_count: int
    channel_38_count: int
    channel_39_count: int
    rssi_histogram: list[int]  # RSSI 分布 (按 5dBm bin)
    top_devices: list[str]     # RSSI 最强的 10 个设备 MAC
```

---

## 5. 扫描器设计

```python
# ble/scanner.py

class BleScanner:
    def __init__(self, event_bus: EventBus, config: Config):
        self.scanner: BleakScanner | None = None
        self.event_bus = event_bus
        self.config = config
        self._running = False
    
    async def start(self):
        """启动 BLE 扫描"""
        self.scanner = BleakScanner(
            detection_callback=self._on_detection,
            scanning_mode="active",  # Active 模式: 发 SCAN_REQ 请求更多数据
        )
        self._running = True
        await self.scanner.start()
    
    async def stop(self):
        """停止 BLE 扫描"""
        self._running = False
        if self.scanner:
            await self.scanner.stop()
    
    async def _on_detection(self, device: BLEDevice, ad_data: AdvertisementData):
        """扫描回调: 解析 → 发布到事件总线"""
        event = BleEvent(
            mac=device.address,
            name=ad_data.local_name or device.name or "Unknown",
            rssi=ad_data.rssi,
            tx_power=ad_data.tx_power,
            channel=_infer_channel(ad_data),
            ...
        )
        await self.event_bus.publish("ble:advertisement", event)


# 单例工厂
_scanner: BleScanner | None = None

def get_scanner() -> BleScanner:
    global _scanner
    if _scanner is None:
        _scanner = BleScanner(event_bus=...)
    return _scanner
```

---

## 6. Analysis 分析器

```python
# ble/analyzer.py

class BleAnalyzer:
    def __init__(self, event_bus: EventBus):
        self.devices: dict[str, BleDevice] = {}  # MAC → 聚合信息
        self.channel_counts: dict[int, int] = {37: 0, 38: 0, 39: 0}
        self._last_snapshot = time.monotonic()
        event_bus.subscribe("ble:advertisement", self._on_event)
    
    async def _on_event(self, event: BleEvent):
        # 更新设备聚合
        device = self.devices.get(event.mac)
        if device is None:
            device = BleDevice(
                mac=event.mac, name=event.name,
                first_seen=time.time(), last_seen=time.time(),
                rssi_mean=event.rssi, rssi_max=event.rssi, rssi_min=event.rssi,
                channel_distribution={event.channel: 1}, packet_count=1,
            )
            self.devices[event.mac] = device
        else:
            # 滑动平均更新 RSSI
            alpha = 0.2
            device.rssi_mean = alpha * event.rssi + (1-alpha) * device.rssi_mean
            device.last_seen = time.time()
            device.packet_count += 1
            device.channel_distribution[event.channel] = \
                device.channel_distribution.get(event.channel, 0) + 1
        
        # 更新信道计数
        self.channel_counts[event.channel] += 1
        
        # 周期快照
        if time.monotonic() - self._last_snapshot > 300:  # 5 分钟
            await self._take_snapshot()
            self._last_snapshot = time.monotonic()
    
    async def _take_snapshot(self):
        snapshot = BleSnapshot(
            timestamp=time.time(),
            total_devices=len(self.devices),
            channel_37_count=self.channel_counts[37],
            channel_38_count=self.channel_counts[38],
            channel_39_count=self.channel_counts[39],
            rssi_histogram=self._compute_rssi_histogram(),
            top_devices=sorted(self.devices, key=lambda m: self.devices[m].rssi_mean)[:10],
        )
        await self.event_bus.publish("ble:snapshot", snapshot)
```

---

## 7. FastAPI 路由

```python
# api/ble_routes.py

router = APIRouter(prefix="/ble", tags=["BLE"])

@router.get("/scan/start")
async def start_scan(scanner: BleScanner = Depends(get_scanner)):
    """启动 BLE 扫描，SSE 流开始推送数据"""
    await scanner.start()
    return {"status": "scanning", "message": "BLE scan started"}

@router.get("/scan/stop")
async def stop_scan(scanner: BleScanner = Depends(get_scanner)):
    """停止 BLE 扫描"""
    await scanner.stop()
    return {"status": "stopped", "message": "BLE scan stopped"}

@router.get("/devices")
async def get_devices(analyzer: BleAnalyzer = Depends(get_analyzer)):
    """获取当前发现的设备列表"""
    return {"devices": [device_to_dict(d) for d in analyzer.devices.values()]}

@router.get("/channel/usage")
async def get_channel_usage(analyzer: BleAnalyzer = Depends(get_analyzer)):
    """获取 37/38/39 信道占用率"""
    total = sum(analyzer.channel_counts.values())
    if total == 0:
        return {"channels": {37: 0, 38: 0, 39: 0}, "total": 0}
    return {
        "channels": {
            37: analyzer.channel_counts[37] / total,
            38: analyzer.channel_counts[38] / total,
            39: analyzer.channel_counts[39] / total,
        },
        "total": total,
    }

@router.get("/events/stream")
async def event_stream(...) -> StreamingResponse:
    """SSE 端点: 实时流式推送 BLE 事件到 Spring Boot"""
    ...
```

---

## 8. 前端可视化规范

### 8.1 信道占用柱状图

```javascript
// BleSpectrumChart.vue
// ECharts 配置
{
  xAxis: { data: ['CH37\n2402MHz', 'CH38\n2426MHz', 'CH39\n2480MHz'] },
  yAxis: { max: 100, name: '占用率 %' },
  series: [{
    type: 'bar',
    data: [0.35, 0.28, 0.37],  // 来自 WebSocket 实时更新
    itemStyle: {
      color: (params) => {
        // 根据占用率渐变: 绿 → 黄 → 红
        const ratio = params.value;
        if (ratio > 0.5) return '#ef4444';
        if (ratio > 0.3) return '#eab308';
        return '#22c55e';
      }
    }
  }]
}
```

### 8.2 设备雷达分布图

```javascript
// BleDeviceRadar.vue
// 以 RSSI 为半径，MAC 散点分布
{
  polar: {
    radius: ['20%', '80%']  // 内圈 = RSSI -90, 外圈 = RSSI -20
  },
  angleAxis: { max: 360 },      // 角度按设备数量分散
  radiusAxis: { max: -20, min: -90 },  // RSSI 范围
  series: [{
    type: 'scatter',
    coordinateSystem: 'polar',
    data: devices.map((d, i) => [i * (360 / devices.length), d.rssi_mean]),
    symbolSize: 10,
  }]
}
```
