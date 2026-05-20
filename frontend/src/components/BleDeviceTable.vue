<template>
  <div class="card">
    <h3>📋 已发现设备 ({{ devices.length }})</h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>MAC</th><th>名称</th><th>RSSI avg</th><th>包数</th><th>最近活跃</th></tr>
        </thead>
        <tbody>
          <tr v-for="d in sortedDevices" :key="d.mac">
            <td class="mono">{{ d.mac }}</td>
            <td>{{ d.name }}</td>
            <td :class="rssiClass(d.rssi_mean)">{{ d.rssi_mean }} dBm</td>
            <td>{{ d.packet_count }}</td>
            <td>{{ timeAgo(d.last_seen) }}</td>
          </tr>
          <tr v-if="devices.length === 0">
            <td colspan="5" class="empty">暂无设备 — 点击"启动扫描"开始</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ devices: Array })

const sortedDevices = computed(() =>
  [...(props.devices || [])].sort((a, b) => a.rssi_mean - b.rssi_mean)
)

function rssiClass(rssi) {
  if (rssi >= -50) return 'rssi-good'
  if (rssi >= -70) return 'rssi-ok'
  return 'rssi-weak'
}

function timeAgo(ts) {
  const s = (Date.now() / 1000) - ts
  if (s < 5) return '刚刚'
  if (s < 60) return Math.floor(s) + 's 前'
  return Math.floor(s / 60) + 'm 前'
}
</script>

<style scoped>
.card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; }
.card h3 { margin-bottom: 10px; font-size: .95rem; color: #8b949e; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid #21262d; }
th { color: #8b949e; font-weight: 500; }
.mono { font-family: 'Consolas', monospace; font-size: .8rem; }
.rssi-good { color: #3fb950; }
.rssi-ok { color: #d2991d; }
.rssi-weak { color: #f85149; }
.empty { color: #484f58; text-align: center; padding: 24px; }
</style>
