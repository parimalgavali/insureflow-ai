package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.ClaimReserve;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimReserveRepository extends JpaRepository<ClaimReserve, UUID> {
    List<ClaimReserve> findByClaimClaimNumberOrderByCreatedAtDesc(String claimNumber);
}
