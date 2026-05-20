package com.zzb.mysite.client;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

/**
 * 非阻塞 HTTP 客户端 → Python FastAPI 引擎。
 *
 * 设计：
 *  - 通过 WebClient 连接 Python SSE 端点
 *  - 每条 SSE event 回调给注册的 Consumer
 *  - 支持同时订阅 BLE 和 CSI 两个流
 */
@Component
public class PythonClient {

    private static final Logger log = LoggerFactory.getLogger(PythonClient.class);

    private final WebClient webClient;
    private final ObjectMapper objectMapper;

    private final List<Disposable> subscriptions = new CopyOnWriteArrayList<>();

    public PythonClient(
            @Value("${python.engine.base-url:http://localhost:8765}") String baseUrl,
            ObjectMapper objectMapper
    ) {
        this.webClient = WebClient.builder().baseUrl(baseUrl).build();
        this.objectMapper = objectMapper;
    }

    /**
     * 订阅 Python SSE 流。
     *
     * @param ssePath  SSE 端点路径，如 "/ble/events/stream"
     * @param callback 每条事件回调
     */
    public void subscribe(String ssePath, Consumer<JsonNode> callback) {
        Flux<ServerSentEvent<String>> eventFlux = webClient.get()
                .uri(ssePath)
                .retrieve()
                .bodyToFlux(
                        new org.springframework.core.ParameterizedTypeReference<ServerSentEvent<String>>() {}
                );

        Disposable sub = eventFlux.subscribe(
                event -> {
                    try {
                        String data = event.data();
                        if (data != null && !data.isBlank()) {
                            JsonNode node = objectMapper.readTree(data);
                            callback.accept(node);
                        }
                    } catch (Exception e) {
                        log.warn("Failed to parse SSE event from {}: {}", ssePath, e.getMessage());
                    }
                },
                error -> log.error("SSE stream error [{}]: {}", ssePath, error.getMessage()),
                () -> log.info("SSE stream completed: {}", ssePath)
        );
        subscriptions.add(sub);
        log.info("Subscribed to Python SSE: {}", ssePath);
    }

    /**
     * POST 调用 Python REST 端点。
     */
    public Map<String, Object> post(String path, Object body) {
        try {
            String response = webClient.post()
                    .uri(path)
                    .bodyValue(body)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            return response != null
                    ? objectMapper.readValue(response, new TypeReference<Map<String, Object>>() {})
                    : Map.of();
        } catch (Exception e) {
            log.error("POST {} failed: {}", path, e.getMessage());
            return Map.of();
        }
    }

    /**
     * GET 调用 Python REST 端点。
     */
    public Map<String, Object> get(String path) {
        try {
            String response = webClient.get()
                    .uri(path)
                    .retrieve()
                    .bodyToMono(String.class)
                    .block();
            return response != null
                    ? objectMapper.readValue(response, new TypeReference<Map<String, Object>>() {})
                    : Map.of();
        } catch (Exception e) {
            log.error("GET {} failed: {}", path, e.getMessage());
            return Map.of();
        }
    }

    /**
     * 取消所有 SSE 订阅。
     */
    public void shutdown() {
        subscriptions.forEach(Disposable::dispose);
        subscriptions.clear();
        log.info("All SSE subscriptions cleared");
    }
}
