<template>
  <div class="card">
    <h3>🚨 运动告警记录 ({{ alerts.length }})</h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>时间</th><th>帧索引</th><th>运动分数</th><th>状态</th></tr>
        </thead>
        <tbody>
          <tr v-for="(a, i) in alerts" :key="i" :class="{ active: a.motion_score >= 3.0 }">
            <td>{{ formatTime(a.timestamp || a.created_at) }}</td>
            <td class="mono">#{{ a.frame_index }}</td>
            <td :class="scoreClass(a.motion_score)">{{ a.motion_score?.toFixed(2) }}</td>
            <td>
              <span class="badge" :class="a.motion_score >= 3.0 ? 'badge-high' : 'badge-low'">
                {{ a.motion_score >= 3.0 ? '高' : '低' }}
              </span>
            </td>
          </tr>
          <tr v-if="alerts.length === 0">
            <td colspan="4" class="empty">尚无运动告警 — 加载数据集并播放后出现</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({ alerts: { type: Array, default: () => [] } })

function scoreClass(score) {
  if (score >= 4.0) return 'score-high'
  if (score >= 2.0) return 'score-mid'
  return 'score-low'
}

function formatTime(ts) {
  if (!ts) return '--'
  const d = new Date(ts * 1000 || ts)
  return d.toLocaleTimeString()
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
tr.active { background: rgba(248,81,73,0.06); }
.score-high { color: #f85149; }
.score-mid { color: #d2991d; }
.score-low { color: #3fb950; }
.badge {
  padding: 2px 8px; border-radius: 10px; font-size: .75rem; font-weight: 600;
}
.badge-high { background: rgba(248,81,73,0.2); color: #f85149; }
.badge-low { background: rgba(210,153,29,0.2); color: #d2991d; }
.empty { color: #484f58; text-align: center; padding: 24px; }
</style>
