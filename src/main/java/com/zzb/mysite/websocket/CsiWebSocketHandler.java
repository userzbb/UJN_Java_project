package com.zzb.mysite.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.zzb.mysite.client.PythonClient;
import com.zzb.mysite.model.CsiAlert;
import com.zzb.mysite.repository.CsiAlertRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.time.Instant;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;

@Component
public class CsiWebSocketHandler extends TextWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(CsiWebSocketHandler.class);

    private final Set<WebSocketSession> sessions = new CopyOnWriteArraySet<>();
    private final PythonClient pythonClient;
    private final ObjectMapper objectMapper;
    private final CsiAlertRepository alertRepository;

    private boolean pythonSubscribed = false;

    public CsiWebSocketHandler(
            PythonClient pythonClient,
            ObjectMapper objectMapper,
            CsiAlertRepository alertRepository
    ) {
        this.pythonClient = pythonClient;
        this.objectMapper = objectMapper;
        this.alertRepository = alertRepository;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.info("CSI WS client connected: {} (total: {})", session.getId(), sessions.size());

        // 第一个客户端连接时，订阅 Python SSE
        if (!pythonSubscribed) {
            pythonClient.subscribe("/csi/events/stream", this::onPythonEvent);
            pythonSubscribed = true;
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        // 前端可以通过 WebSocket 发送控制指令（如暂停、调速等）
        JsonNode cmd = objectMapper.readTree(message.getPayload());
        String action = cmd.has("action") ? cmd.get("action").asText() : "";
        String target = cmd.has("target") ? cmd.get("target").asText() : "";

        if ("csi".equals(target)) {
            switch (action) {
                case "pause" -> pythonClient.post("/csi/pause", null);
                case "stop" -> pythonClient.post("/csi/stop", null);
                case "seek" -> {
                    int frame = cmd.has("frame_index") ? cmd.get("frame_index").asInt() : 0;
                    pythonClient.post("/csi/seek", java.util.Map.of("frame_index", frame));
                }
                case "speed" -> {
                    double speed = cmd.has("speed") ? cmd.get("speed").asDouble() : 1.0;
                    pythonClient.post("/csi/speed", java.util.Map.of("speed", speed));
                }
                default -> log.debug("Unknown CSI action: {}", action);
            }
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.info("CSI WS client disconnected: {} (total: {})", session.getId(), sessions.size());
    }

    // ── 从 Python SSE 回调 → 广播给所有前端 ──

    private void onPythonEvent(JsonNode event) {
        try {
            // 如果有运动告警，持久化到 DB
            if (event.has("event_type") && "csi:alert".equals(event.get("event_type").asText())) {
                CsiAlert alert = new CsiAlert();
                alert.setTimestamp(Instant.now());
                alert.setMotionScore(event.has("motion_score") ? event.get("motion_score").asDouble() : 0);
                alert.setFrameIndex(event.has("frame_index") ? event.get("frame_index").asInt() : 0);
                alert.setSubcarrierSnapshotJson(event.toString());
                alertRepository.save(alert);
            }

            // 广播给所有前端 WebSocket 客户端
            String json = event.toString();
            TextMessage msg = new TextMessage(json);
            for (WebSocketSession s : sessions) {
                if (s.isOpen()) {
                    try {
                        s.sendMessage(msg);
                    } catch (Exception e) {
                        log.warn("Failed to send CSI WS msg to {}: {}", s.getId(), e.getMessage());
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing CSI event: {}", e.getMessage());
        }
    }
}
