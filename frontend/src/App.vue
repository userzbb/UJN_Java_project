<template>
  <div class="app">
    <header class="topbar">
      <h1>📡 无线环境感知与信号分析平台</h1>
      <span class="status-dot" :class="{ on: bleConnected || csiConnected }"></span>
    </header>

    <nav class="tabs">
      <button :class="{ active: activeTab === 'ble' }" @click="activeTab = 'ble'">
        🔵 BLE 频谱感知
      </button>
      <button :class="{ active: activeTab === 'csi' }" @click="activeTab = 'csi'">
        🟢 WiFi CSI 人体感知
      </button>
    </nav>

    <main class="main">
      <BlePanel v-if="activeTab === 'ble'" />
      <CsiPanel v-if="activeTab === 'csi'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import BlePanel from './components/BlePanel.vue'
import CsiPanel from './components/CsiPanel.vue'

const activeTab = ref('ble')
const bleConnected = ref(false)
const csiConnected = ref(false)
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #0d1117;
  color: #c9d1d9;
  min-height: 100vh;
}

.app { max-width: 1400px; margin: 0 auto; padding: 20px; }

.topbar {
  display: flex; align-items: center; gap: 12px;
  padding: 16px 0 20px;
  border-bottom: 1px solid #21262d;
}
.topbar h1 { font-size: 1.4rem; font-weight: 600; color: #f0f6fc; }
.status-dot {
  width: 10px; height: 10px; border-radius: 50%; background: #484f58;
}
.status-dot.on { background: #3fb950; box-shadow: 0 0 6px #3fb950; }

.tabs {
  display: flex; gap: 8px;
  padding: 16px 0;
  border-bottom: 1px solid #21262d;
}
.tabs button {
  padding: 8px 20px;
  border: 1px solid #30363d;
  border-radius: 8px;
  background: #161b22;
  color: #8b949e;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all .15s;
}
.tabs button:hover { border-color: #58a6ff; color: #c9d1d9; }
.tabs button.active {
  border-color: #1f6feb;
  background: #1f6feb22;
  color: #58a6ff;
}

.main { padding: 20px 0; }
</style>
