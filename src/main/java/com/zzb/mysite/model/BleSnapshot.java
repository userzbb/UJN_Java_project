package com.zzb.mysite.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "ble_snapshot")
public class BleSnapshot {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Instant timestamp;

    private int deviceCount;

    private int channel37Count;

    private int channel38Count;

    private int channel39Count;

    @Column(columnDefinition = "TEXT")
    private String rssiHistogramJson;

    public BleSnapshot() {}

    // ── Getters / Setters ──

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }

    public int getDeviceCount() { return deviceCount; }
    public void setDeviceCount(int deviceCount) { this.deviceCount = deviceCount; }

    public int getChannel37Count() { return channel37Count; }
    public void setChannel37Count(int channel37Count) { this.channel37Count = channel37Count; }

    public int getChannel38Count() { return channel38Count; }
    public void setChannel38Count(int channel38Count) { this.channel38Count = channel38Count; }

    public int getChannel39Count() { return channel39Count; }
    public void setChannel39Count(int channel39Count) { this.channel39Count = channel39Count; }

    public String getRssiHistogramJson() { return rssiHistogramJson; }
    public void setRssiHistogramJson(String rssiHistogramJson) { this.rssiHistogramJson = rssiHistogramJson; }
}
