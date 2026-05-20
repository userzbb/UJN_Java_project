package com.zzb.mysite.repository;

import com.zzb.mysite.model.BleSnapshot;
import org.springframework.data.jpa.repository.JpaRepository;
import java.time.Instant;
import java.util.List;

public interface BleSnapshotRepository extends JpaRepository<BleSnapshot, Long> {
    List<BleSnapshot> findByTimestampAfterOrderByTimestampDesc(Instant since);
    List<BleSnapshot> findTop24ByOrderByTimestampDesc();
}
