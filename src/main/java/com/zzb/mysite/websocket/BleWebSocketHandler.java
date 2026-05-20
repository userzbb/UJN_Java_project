package com.zzb.mysite.websocket;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.zzb.mysite.client.PythonClient;
import com.zzb.mysite.model.BleSnapshot;
import com.zzb.mysite.repository.BleSnapshotRepository;
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
public class BleWebSocketHandler extends TextWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(BleWebSocketHandler.class);

    private final Set<WebSocketSession> sessions = new CopyOnWriteArraySet<>();
    private final PythonClient pythonClient;
    private final ObjectMapper objectMapper;
    private final BleSnapshotRepository snapshotRepository;

    private boolean pythonSubscribed = false;

    public BleWebSocketHandler(
            PythonClient pythonClient,
            ObjectMapper objectMapper,
            BleSnapshotRepository snapshotRepository
    ) {
        this.pythonClient = pythonClient;
        this.objectMapper = objectMapper;
        this.snapshotRepository = snapshotRepository;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.add(session);
        log.info("BLE WS client connected: {} (total: {})", session.getId(), sessions.size());

        if (!pythonSubscribed) {
            pythonClient.subscribe("/ble/events/stream", this::onPythonEvent);
            pythonSubscribed = true;
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        JsonNode cmd = objectMapper.readTree(message.getPayload());
        String action = cmd.has("action") ? cmd.get("action").asText() : "";
        String target = cmd.has("target") ? cmd.get("target").asText() : "";

        if ("ble".equals(target)) {
            switch (action) {
                case "start" -> pythonClient.get("/ble/scan/start");
                case "stop" -> pythonClient.get("/ble/scan/stop");
                default -> log.debug("Unknown BLE action: {}", action);
            }
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session);
        log.info("BLE WS client disconnected: {} (total: {})", session.getId(), sessions.size());
    }

    // ── 从 Python SSE 回调 → 广播给所有前端 ──

    private void onPythonEvent(JsonNode event) {
        try {
            // 快照持久化到 DB
            if (event.has("event_type") && "ble:snapshot".equals(event.get("event_type").asText())) {
                BleSnapshot snap = new BleSnapshot();
                snap.setTimestamp(Instant.now());
                snap.setDeviceCount(event.has("total_devices") ? event.get("total_devices").asInt() : 0);
                snap.setChannel37Count(event.has("channel_37_count") ? event.get("channel_37_count").asInt() : 0);
                snap.setChannel38Count(event.has("channel_38_count") ? event.get("channel_38_count").asInt() : 0);
                snap.setChannel39Count(event.has("channel_39_count") ? event.get("channel_39_count").asInt() : 0);
                snap.setRssiHistogramJson(event.has("rssi_histogram") ? event.get("rssi_histogram").toString() : "[]");
                snapshotRepository.save(snap);
            }

            // 广播
            String json = event.toString();
            TextMessage msg = new TextMessage(json);
            for (WebSocketSession s : sessions) {
                if (s.isOpen()) {
                    try {
                        s.sendMessage(msg);
                    } catch (Exception e) {
                        log.warn("Failed to send BLE WS msg to {}: {}", s.getId(), e.getMessage());
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing BLE event: {}", e.getMessage());
        }
    }
}
