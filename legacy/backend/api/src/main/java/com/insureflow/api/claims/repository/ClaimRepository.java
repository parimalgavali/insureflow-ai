package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.Claim;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimRepository extends JpaRepository<Claim, UUID> {

    List<Claim> findAllByOrderByReportedAtDesc();

    Optional<Claim> findByClaimNumber(String claimNumber);

    long countByClaimNumberStartingWith(String claimNumberPrefix);

    long countByCustomerIdAndReportedAtBefore(UUID customerId, Instant reportedAt);
}
