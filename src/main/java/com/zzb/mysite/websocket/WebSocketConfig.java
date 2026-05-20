package com.zzb.mysite.websocket;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final CsiWebSocketHandler csiHandler;
    private final BleWebSocketHandler bleHandler;

    public WebSocketConfig(CsiWebSocketHandler csiHandler, BleWebSocketHandler bleHandler) {
        this.csiHandler = csiHandler;
        this.bleHandler = bleHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(csiHandler, "/ws/csi")
                .setAllowedOrigins("*");
        registry.addHandler(bleHandler, "/ws/ble")
                .setAllowedOrigins("*");
    }
}
