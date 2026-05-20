package com.zzb.mysite.repository;

import com.zzb.mysite.model.CsiAlert;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface CsiAlertRepository extends JpaRepository<CsiAlert, Long> {
    List<CsiAlert> findTop50ByOrderByTimestampDesc();
}
