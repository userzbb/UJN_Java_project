package com.zzb.mysite.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "device_info")
public class DeviceInfo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String mac;

    private String name;

    private Instant firstSeen;

    private Instant lastSeen;

    private double avgRssi;

    public DeviceInfo() {}

    // ── Getters / Setters ──

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getMac() { return mac; }
    public void setMac(String mac) { this.mac = mac; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Instant getFirstSeen() { return firstSeen; }
    public void setFirstSeen(Instant firstSeen) { this.firstSeen = firstSeen; }

    public Instant getLastSeen() { return lastSeen; }
    public void setLastSeen(Instant lastSeen) { this.lastSeen = lastSeen; }

    public double getAvgRssi() { return avgRssi; }
    public void setAvgRssi(double avgRssi) { this.avgRssi = avgRssi; }
}
