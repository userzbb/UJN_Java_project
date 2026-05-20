package com.zzb.mysite.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "csi_alert")
public class CsiAlert {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Instant timestamp;

    private double motionScore;

    private int frameIndex;

    @Column(columnDefinition = "TEXT")
    private String subcarrierSnapshotJson;

    public CsiAlert() {}

    // ── Getters / Setters ──

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Instant getTimestamp() { return timestamp; }
    public void setTimestamp(Instant timestamp) { this.timestamp = timestamp; }

    public double getMotionScore() { return motionScore; }
    public void setMotionScore(double motionScore) { this.motionScore = motionScore; }

    public int getFrameIndex() { return frameIndex; }
    public void setFrameIndex(int frameIndex) { this.frameIndex = frameIndex; }

    public String getSubcarrierSnapshotJson() { return subcarrierSnapshotJson; }
    public void setSubcarrierSnapshotJson(String subcarrierSnapshotJson) { this.subcarrierSnapshotJson = subcarrierSnapshotJson; }
}
