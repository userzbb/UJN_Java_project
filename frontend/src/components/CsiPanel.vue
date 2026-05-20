<template>
  <div class="csi-panel">
    <!-- ── 数据集选择 & 控制栏 ── -->
    <div class="controls">
      <select v-model="selectedDataset" class="dataset-select">
        <option value="">-- 选择数据集 --</option>
        <option v-for="ds in datasets" :key="ds.name" :value="ds.name">
          {{ ds.name }} ({{ ds.file_count }} 文件, {{ ds.total_size_mb }} MB)
        </option>
      </select>

      <button @click="loadAndPlay" :disabled="!selectedDataset || playing" class="btn play">▶ 加载播放</button>
      <button @click="pause" :disabled="!playing" class="btn pause">
        {{ paused ? '▶ 继续' : '⏸ 暂停' }}
      </button>
      <button @click="stop" :disabled="!playing && !paused" class="btn stop">⏹ 停止</button>

      <div class="speed-group">
        <label>速度</label>
        <input type="range" min="0.1" max="5" step="0.1" v-model.number="speed" @change="setSpeed" />
        <span class="speed-val">{{ speed }}x</span>
      </div>

      <div class="seek-group">
        <label>跳转帧</label>
        <input type="number" v-model.number="seekFrame" :max="totalFrames" min="0" class="seek-input" />
        <button @click="doSeek" class="btn seek" :disabled="!playing">跳转</button>
      </div>

      <span class="info">
        帧: {{ currentFrame }} / {{ totalFrames || '--' }}
        <span v-if="latestScore !== null" class="score" :class="scoreClass(latestScore)">
          | 运动: {{ latestScore.toFixed(2) }}
        </span>
      </span>
    </div>

    <!-- ── 进度条 ── -->
    <div class="progress-bar" v-if="totalFrames > 0">
      <div class="progress-fill" :style="{ width: (currentFrame / totalFrames * 100) + '%' }"></div>
    </div>

    <!-- ── 图表区域 ── -->
    <div class="charts">
      <CsiHeatmap :frames="frameWindow" />
      <CsiMotionChart :motion-data="motionData" :threshold="2.0" />
    </div>

    <!-- ── 告警列表 ── -->
    <CsiAlertList :alerts="alerts" />
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useWebSocket } from '../composables/useWebSocket.js'
import CsiHeatmap from './CsiHeatmap.vue'
import CsiMotionChart from './CsiMotionChart.vue'
import CsiAlertList from './CsiAlertList.vue'

const { lastMessage, send, connected } = useWebSocket('/ws/csi')

// ── 数据集 ──
const datasets = ref([])
const selectedDataset = ref('')

onMounted(async () => {
  try {
    const res = await fetch('/api/csi/datasets')
    const json = await res.json()
    // Spring Boot 包装: { status, data: { datasets: [...] } }
    const list = json.data?.datasets || json.datasets || []
    datasets.value = list
  } catch {}
})

// ── 播放状态 ──
const playing = ref(false)
const paused = ref(false)
const speed = ref(1.0)
const seekFrame = ref(0)
const currentFrame = ref(0)
const totalFrames = ref(0)
const latestScore = ref(null)

// ── 数据收集 ──
const frameWindow = ref([])   // 最近 60 帧（热力图）
const motionData = ref([])   // 最近 120 个运动分数
const alerts = ref([])

const MAX_HEATMAP_FRAMES = 60
const MAX_MOTION_POINTS = 120

watch(lastMessage, (msg) => {
  if (!msg) return

  const type = msg.event_type

  if (type === 'csi:frame') {
    currentFrame.value = msg.frame_index
    totalFrames.value = Math.max(totalFrames.value, msg.frame_index + 1)
    latestScore.value = msg.motion_score

    // 热力图滚动窗口
    const fw = [...frameWindow.value, msg]
    if (fw.length > MAX_HEATMAP_FRAMES) fw.splice(0, fw.length - MAX_HEATMAP_FRAMES)
    frameWindow.value = fw

    // 运动分数
    const md = [...motionData.value, { frame_index: msg.frame_index, motion_score: msg.motion_score }]
    if (md.length > MAX_MOTION_POINTS) md.splice(0, md.length - MAX_MOTION_POINTS)
    motionData.value = md
  }

  if (type === 'csi:alert') {
    alerts.value = [{ ...msg }, ...alerts.value].slice(0, 50)
  }
})

// ── 控制 ──
async function loadAndPlay() {
  if (!selectedDataset.value) return
  try {
    await fetch('/api/csi/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset: selectedDataset.value, speed: speed.value }),
    })
    playing.value = true
    paused.value = false
    frameWindow.value = []
    motionData.value = []
    alerts.value = []
    currentFrame.value = 0
    totalFrames.value = 0
  } catch {}
}

async function pause() {
  try {
    await fetch('/api/csi/pause', { method: 'POST' })
    paused.value = !paused.value
    playing.value = !paused.value
  } catch {}
}

async function stop() {
  try {
    await fetch('/api/csi/stop', { method: 'POST' })
    playing.value = false
    paused.value = false
    currentFrame.value = 0
  } catch {}
}

async function setSpeed() {
  try {
    await fetch('/api/csi/speed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speed: speed.value }),
    })
  } catch {}
}

async function doSeek() {
  try {
    await fetch('/api/csi/seek', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ frame_index: seekFrame.value }),
    })
  } catch {}
}

function scoreClass(score) {
  if (score >= 3.0) return 'score-high'
  if (score >= 2.0) return 'score-mid'
  return 'score-low'
}
</script>

<style scoped>
.csi-panel { display: flex; flex-direction: column; gap: 20px; }

/* ── 控制栏 ── */
.controls {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.dataset-select {
  background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
  border-radius: 6px; padding: 8px 12px; font-size: .85rem; min-width: 220px;
}
.btn {
  padding: 8px 16px; border-radius: 6px; border: 1px solid #30363d;
  background: #21262d; color: #c9d1d9; cursor: pointer; font-size: .85rem;
  white-space: nowrap;
}
.btn.play { border-color: #238636; color: #3fb950; }
.btn.pause { border-color: #d2991d; color: #d2991d; }
.btn.stop { border-color: #da3633; color: #f85149; }
.btn:disabled { opacity: .4; cursor: not-allowed; }

.speed-group, .seek-group {
  display: flex; align-items: center; gap: 6px;
}
.speed-group label, .seek-group label { color: #8b949e; font-size: .8rem; white-space: nowrap; }
.speed-group input[type="range"] { width: 80px; accent-color: #58a6ff; }
.speed-val { color: #c9d1d9; font-size: .8rem; min-width: 36px; }
.seek-input {
  width: 60px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
  border-radius: 4px; padding: 4px 8px; font-size: .8rem;
}
.btn.seek { padding: 4px 10px; font-size: .8rem; }

.info { color: #8b949e; font-size: .85rem; margin-left: auto; }
.score-high { color: #f85149; }
.score-mid { color: #d2991d; }
.score-low { color: #3fb950; }

/* ── 进度条 ── */
.progress-bar {
  height: 4px; background: #21262d; border-radius: 2px; overflow: hidden;
}
.progress-fill {
  height: 100%; background: linear-gradient(90deg, #1f6feb, #58a6ff);
  transition: width .3s ease;
}

/* ── 图表 ── */
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 900px) { .charts { grid-template-columns: 1fr; } }
</style>
