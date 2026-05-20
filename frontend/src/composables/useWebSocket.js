import { ref, onUnmounted } from 'vue'

/**
 * WebSocket 连接管理 + 自动重连（指数退避）
 *
 * @param {string} path  WebSocket 路径，如 '/ws/ble'
 * @returns {{ lastMessage, send, connected }}
 */
export function useWebSocket(path) {
  const lastMessage = ref(null)
  const connected = ref(false)
  let ws = null
  let reconnectTimer = null
  let reconnectDelay = 1000 // 从 1s 开始

  function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.host}${path}`

    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      reconnectDelay = 1000
    }

    ws.onmessage = (event) => {
      try {
        lastMessage.value = JSON.parse(event.data)
      } catch {
        lastMessage.value = event.data
      }
    }

    ws.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 1.5, 30000)
      connect()
    }, reconnectDelay)
  }

  function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function disconnect() {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) {
      ws.onclose = null // 防止触发重连
      ws.close()
    }
  }

  connect()
  onUnmounted(disconnect)

  return { lastMessage, send, connected }
}
