import { ref, onMounted, onUnmounted } from 'vue'

/**
 * ECharts 实例生命周期管理 + resize 监听
 *
 * @param {import('vue').Ref} chartRef  template ref
 * @returns {{ chartInstance }}
 */
export function useECharts(chartRef) {
  const chartInstance = ref(null)

  let resizeObserver = null

  onMounted(() => {
    if (chartRef.value) {
      chartInstance.value = chartRef.value
    }
    resizeObserver = new ResizeObserver(() => {
      chartInstance.value?.resize?.()
    })
    if (chartRef.value?.$el) {
      resizeObserver.observe(chartRef.value.$el)
    }
  })

  onUnmounted(() => {
    resizeObserver?.disconnect()
    chartInstance.value?.dispose?.()
  })

  return { chartInstance }
}
