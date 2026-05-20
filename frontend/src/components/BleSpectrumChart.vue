<template>
  <div class="card">
    <h3>📊 37 / 38 / 39 信道占用率</h3>
    <v-chart :option="option" style="height:280px" autoresize />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ channelUsage: Object })

const option = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      const p = params[0]
      return `${p.name.replace('\n', ' ')}<br/>占用率: ${(p.value * 100).toFixed(1)}%`
    },
  },
  grid: { left: 55, right: 20, top: 20, bottom: 50 },
  xAxis: {
    type: 'category',
    data: ['CH37\n2402MHz', 'CH38\n2426MHz', 'CH39\n2480MHz'],
    axisLabel: { color: '#8b949e', fontSize: 11, lineHeight: 16 },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 1,
    name: '占用率',
    nameTextStyle: { color: '#8b949e', fontSize: 10 },
    axisLabel: { color: '#8b949e', formatter: (v) => (v * 100).toFixed(0) + '%' },
    splitLine: { lineStyle: { color: '#21262d' } },
  },
  series: [{
    type: 'bar',
    data: [
      { value: props.channelUsage?.['37'] || 0, itemStyle: itemStyle(0) },
      { value: props.channelUsage?.['38'] || 0, itemStyle: itemStyle(1) },
      { value: props.channelUsage?.['39'] || 0, itemStyle: itemStyle(2) },
    ],
    barWidth: '40%',
    barCategoryGap: '30%',
  }],
  backgroundColor: 'transparent',
}))

function itemStyle(i) {
  const v = [props.channelUsage?.['37'] || 0, props.channelUsage?.['38'] || 0, props.channelUsage?.['39'] || 0][i]
  const color = v > 0.5 ? '#f85149' : v > 0.3 ? '#d2991d' : '#3fb950'
  return { color, borderRadius: [4, 4, 0, 0] }
}
</script>

<style scoped>
.card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; }
.card h3 { margin-bottom: 10px; font-size: .95rem; color: #8b949e; }
</style>
