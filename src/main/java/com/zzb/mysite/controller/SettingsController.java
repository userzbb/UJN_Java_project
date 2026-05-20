package com.zzb.mysite.controller;

import com.zzb.mysite.model.AppSettings;
import com.zzb.mysite.repository.AppSettingsRepository;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/settings")
public class SettingsController {

    private final AppSettingsRepository repo;

    public SettingsController(AppSettingsRepository repo) {
        this.repo = repo;
    }

    @GetMapping
    public Map<String, Object> getAll() {
        Map<String, String> settings = new HashMap<>();
        repo.findAll().forEach(s -> settings.put(s.getKey(), s.getValue()));
        return Map.of("status", "ok", "settings", settings);
    }

    @GetMapping("/{key}")
    public Map<String, Object> get(@PathVariable String key) {
        Optional<AppSettings> opt = repo.findById(key);
        return opt.map(s -> Map.of("status", "ok", "key", s.getKey(), "value", (Object) s.getValue()))
                .orElse(Map.of("status", "not_found"));
    }

    @PutMapping("/{key}")
    public Map<String, Object> set(@PathVariable String key, @RequestBody Map<String, String> body) {
        AppSettings s = new AppSettings(key, body.getOrDefault("value", ""));
        repo.save(s);
        return Map.of("status", "ok", "key", key);
    }
}
