package com.zzb.mysite.controller;

import com.zzb.mysite.client.PythonClient;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/ble")
public class BleController {

    private final PythonClient pythonClient;

    public BleController(PythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    @PostMapping("/scan/start")
    public Map<String, Object> startScan() {
        Map<String, Object> resp = pythonClient.get("/ble/scan/start");
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/scan/stop")
    public Map<String, Object> stopScan() {
        Map<String, Object> resp = pythonClient.get("/ble/scan/stop");
        return Map.of("status", "ok", "data", resp);
    }

    @GetMapping("/status")
    public Map<String, Object> getStatus() {
        Map<String, Object> resp = pythonClient.get("/ble/status");
        return Map.of("status", "ok", "data", resp);
    }

    @GetMapping("/devices")
    public Map<String, Object> getDevices() {
        Map<String, Object> resp = pythonClient.get("/ble/devices");
        return Map.of("status", "ok", "data", resp);
    }

    @GetMapping("/channel/usage")
    public Map<String, Object> getChannelUsage() {
        Map<String, Object> resp = pythonClient.get("/ble/channel/usage");
        return Map.of("status", "ok", "data", resp);
    }
}
