<template>
  <div class="card">
    <h3>📍 设备信号分布 (RSSI 雷达)</h3>
    <v-chart :option="option" style="height:280px" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ devices: Array })

const option = computed(() => {
  const devs = props.devices || []
  if (devs.length === 0) {
    return {
      title: { text: '暂无设备数据', left: 'center', top: 'center', textStyle: { color: '#484f58', fontSize: 14 } },
      backgroundColor: 'transparent',
    }
  }

  // 按 RSSI 分桶统计
  const bins = {}
  for (const d of devs) {
    const bucket = Math.floor(d.rssi_mean / 5) * 5
    bins[bucket] = (bins[bucket] || 0) + 1
  }

  const bucketKeys = Object.keys(bins).map(Number).sort((a, b) => a - b)
  const xLabels = bucketKeys.map(k => k + ' dBm')
  const yValues = bucketKeys.map(k => bins[k])

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `RSSI: ${p.name}<br/>设备数: ${p.value}`
      },
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLabel: { color: '#8b949e', fontSize: 10, rotate: 30 },
      axisTick: { show: false },
      name: 'RSSI (dBm)',
      nameTextStyle: { color: '#8b949e', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: '设备数',
      nameTextStyle: { color: '#8b949e', fontSize: 10 },
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#21262d' } },
    },
    series: [{
      type: 'bar',
      data: yValues,
      barWidth: '70%',
      itemStyle: {
        color: (params) => {
          const rssi = bucketKeys[params.dataIndex]
          if (rssi >= -50) return '#3fb950'
          if (rssi >= -70) return '#d2991d'
          return '#f85149'
        },
        borderRadius: [4, 4, 0, 0],
      },
    }],
    backgroundColor: 'transparent',
  }
})
</script>

<style scoped>
.card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; }
.card h3 { margin-bottom: 10px; font-size: .95rem; color: #8b949e; }
</style>
