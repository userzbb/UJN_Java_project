package com.zzb.mysite.repository;

import com.zzb.mysite.model.DeviceInfo;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface DeviceInfoRepository extends JpaRepository<DeviceInfo, Long> {
    Optional<DeviceInfo> findByMac(String mac);
}
