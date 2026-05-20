<template>
  <div class="ble-panel">
    <div class="controls">
      <button @click="startScan" :disabled="scanning" class="btn start">▶ 启动扫描</button>
      <button @click="stopScan" :disabled="!scanning" class="btn stop">⏹ 停止</button>
      <span class="info">设备数: {{ deviceCount }} | 总包数: {{ totalPackets }}</span>
    </div>

    <div class="charts">
      <BleSpectrumChart :channel-usage="channelUsage" />
      <BleDeviceRadar :devices="devices" />
    </div>

    <BleDeviceTable :devices="devices" />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useWebSocket } from '../composables/useWebSocket.js'
import BleSpectrumChart from './BleSpectrumChart.vue'
import BleDeviceRadar from './BleDeviceRadar.vue'
import BleDeviceTable from './BleDeviceTable.vue'

const { lastMessage, send, connected } = useWebSocket('/ws/ble')
const scanning = ref(false)
const deviceCount = ref(0)
const totalPackets = ref(0)
const channelUsage = ref({ '37': 0, '38': 0, '39': 0 })
const devices = ref([])

watch(lastMessage, (msg) => {
  if (!msg) return
  const type = msg.event_type

  if (type === 'ble:advertisement') {
    totalPackets.value++
  }

  if (type === 'ble:advertisement' || type === 'ble:snapshot') {
    // 从 REST API 拉设备列表（避免每次解析 SSE 重建）
    fetchDevices()
    fetchChannelUsage()
  }
})

async function fetchDevices() {
  try {
    const res = await fetch('/api/ble/devices')
    const data = await res.json()
    if (data.data?.devices) {
      devices.value = data.data.devices
      deviceCount.value = data.data.devices.length
    }
  } catch {}
}

async function fetchChannelUsage() {
  try {
    const res = await fetch('/api/ble/channel/usage')
    const data = await res.json()
    if (data.data) channelUsage.value = data.data
  } catch {}
}

function startScan() {
  send({ target: 'ble', action: 'start' })
  scanning.value = true
  fetch('/api/ble/scan/start', { method: 'POST' })
}

function stopScan() {
  send({ target: 'ble', action: 'stop' })
  scanning.value = false
  fetch('/api/ble/scan/stop', { method: 'POST' })
}
</script>

<style scoped>
.ble-panel { display: flex; flex-direction: column; gap: 20px; }

.controls { display: flex; align-items: center; gap: 12px; }
.btn {
  padding: 8px 18px; border-radius: 6px; border: 1px solid #30363d;
  background: #21262d; color: #c9d1d9; cursor: pointer; font-size: 0.9rem;
}
.btn.start { border-color: #238636; color: #3fb950; }
.btn.stop { border-color: #da3633; color: #f85149; }
.btn:disabled { opacity: .4; cursor: not-allowed; }
.info { color: #8b949e; font-size: .85rem; margin-left: auto; }

.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 800px) { .charts { grid-template-columns: 1fr; } }
</style>
