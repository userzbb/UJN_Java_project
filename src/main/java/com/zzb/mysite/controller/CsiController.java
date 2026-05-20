package com.zzb.mysite.controller;

import com.zzb.mysite.client.PythonClient;
import com.zzb.mysite.repository.CsiAlertRepository;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/csi")
public class CsiController {

    private final PythonClient pythonClient;
    private final CsiAlertRepository csiAlertRepository;

    public CsiController(PythonClient pythonClient, CsiAlertRepository csiAlertRepository) {
        this.pythonClient = pythonClient;
        this.csiAlertRepository = csiAlertRepository;
    }

    @GetMapping("/datasets")
    public Map<String, Object> listDatasets() {
        Map<String, Object> resp = pythonClient.get("/csi/datasets");
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/load")
    public Map<String, Object> loadDataset(@RequestBody Map<String, Object> body) {
        Map<String, Object> resp = pythonClient.post("/csi/load", body);
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/stop")
    public Map<String, Object> stopPlayback() {
        Map<String, Object> resp = pythonClient.post("/csi/stop", Map.of());
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/pause")
    public Map<String, Object> pausePlayback() {
        Map<String, Object> resp = pythonClient.post("/csi/pause", Map.of());
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/seek")
    public Map<String, Object> seekFrame(@RequestBody Map<String, Object> body) {
        Map<String, Object> resp = pythonClient.post("/csi/seek", body);
        return Map.of("status", "ok", "data", resp);
    }

    @PostMapping("/speed")
    public Map<String, Object> setSpeed(@RequestBody Map<String, Object> body) {
        Map<String, Object> resp = pythonClient.post("/csi/speed", body);
        return Map.of("status", "ok", "data", resp);
    }

    @GetMapping("/progress")
    public Map<String, Object> getProgress() {
        Map<String, Object> resp = pythonClient.get("/csi/progress");
        return Map.of("status", "ok", "data", resp);
    }

    @GetMapping("/alerts")
    public Map<String, Object> getAlerts() {
        return Map.of("status", "ok", "alerts", csiAlertRepository.findTop50ByOrderByTimestampDesc());
    }
}
