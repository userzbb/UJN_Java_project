<template>
  <div class="card">
    <h3>📈 运动检测分数</h3>
    <v-chart :option="option" style="height:300px" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  motionData: { type: Array, default: () => [] },
  threshold: { type: Number, default: 2.0 },
})

const option = computed(() => {
  const data = props.motionData || []
  if (data.length === 0) {
    return { title: { text: '等待数据...', left: 'center', top: 'center', textStyle: { color: '#484f58', fontSize: 14 } }, backgroundColor: 'transparent' }
  }

  const xData = data.map(d => `#${d.frame_index}`)
  const yData = data.map(d => d.motion_score)

  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const p = params[0]
        return `帧 #${p.name}<br/>运动分数: ${p.value.toFixed(2)}${p.value >= props.threshold ? ' ⚠ 检测到运动' : ''}`
      },
    },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: { color: '#8b949e', fontSize: 10, rotate: 45 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '运动分数',
      nameTextStyle: { color: '#8b949e', fontSize: 11 },
      axisLabel: { color: '#8b949e' },
      splitLine: { lineStyle: { color: '#21262d' } },
    },
    series: [{
      type: 'line',
      data: yData,
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#58a6ff', width: 1.5 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(248,81,73,0.3)' },
            { offset: props.threshold / 10, color: 'rgba(248,81,73,0.15)' },
            { offset: 1, color: 'rgba(58,166,255,0.05)' },
          ],
        },
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#f85149', type: 'dashed', width: 1 },
        label: { formatter: `阈值 ${props.threshold}`, color: '#f85149', fontSize: 10 },
        data: [{ yAxis: props.threshold }],
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
