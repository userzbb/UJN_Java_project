<template>
  <div class="card">
    <h3>🔥 子载波幅度热力图</h3>
    <v-chart :option="option" style="height:300px" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  frames: { type: Array, default: () => [] },
  maxFrames: { type: Number, default: 60 },
})

const option = computed(() => {
  const data = (props.frames || [])
  if (data.length === 0) {
    return { title: { text: '等待数据...', left: 'center', top: 'center', textStyle: { color: '#484f58', fontSize: 14 } }, backgroundColor: 'transparent' }
  }

  const subcarrierCount = data[0]?.amplitude?.length || 30
  const heatmapData = []
  const xLabels = []

  data.forEach((f, i) => {
    xLabels.push(`#${f.frame_index}`)
    f.amplitude.forEach((amp, subIdx) => {
      heatmapData.push([i, subIdx, amp])
    })
  })

  return {
    tooltip: {
      position: 'top',
      formatter: (p) => {
        const m = p.data
        return `帧 #${xLabels[m[0]]}<br/>子载波 ${m[1]}<br/>幅度 ${m[2].toFixed(3)}`
      },
    },
    grid: { left: 60, right: 30, top: 10, bottom: 50 },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLabel: { color: '#8b949e', fontSize: 10, rotate: 45 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: Array.from({ length: subcarrierCount }, (_, i) => `SC${i}`),
      axisLabel: { color: '#8b949e', fontSize: 10 },
      splitLine: { show: false },
    },
    visualMap: {
      min: 0,
      max: 1,
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      inRange: { color: ['#0d1117', '#1f6feb', '#3fb950', '#d2991d', '#f85149'] },
      textStyle: { color: '#8b949e' },
    },
    series: [{
      type: 'heatmap',
      data: heatmapData,
      itemStyle: { borderColor: '#161b22', borderWidth: 1 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,.5)' } },
    }],
    backgroundColor: 'transparent',
  }
})
</script>

<style scoped>
.card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; }
.card h3 { margin-bottom: 10px; font-size: .95rem; color: #8b949e; }
</style>
