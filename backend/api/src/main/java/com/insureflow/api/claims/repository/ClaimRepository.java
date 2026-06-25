package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.Claim;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimRepository extends JpaRepository<Claim, UUID> {

    Optional<Claim> findByClaimNumber(String claimNumber);

    long countByClaimNumberStartingWith(String claimNumberPrefix);
}
