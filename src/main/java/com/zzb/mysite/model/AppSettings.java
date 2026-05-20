package com.zzb.mysite.model;

import jakarta.persistence.*;

@Entity
@Table(name = "app_settings")
public class AppSettings {

    @Id
    @Column(length = 128)
    private String key;

    @Column(columnDefinition = "TEXT")
    private String value;

    public AppSettings() {}

    public AppSettings(String key, String value) {
        this.key = key;
        this.value = value;
    }

    // ── Getters / Setters ──

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public String getValue() { return value; }
    public void setValue(String value) { this.value = value; }
}
