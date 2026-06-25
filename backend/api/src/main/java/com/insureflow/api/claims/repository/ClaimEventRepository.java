package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.ClaimEvent;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimEventRepository extends JpaRepository<ClaimEvent, UUID> {

    List<ClaimEvent> findByClaimClaimNumberOrderByCreatedAtAsc(String claimNumber);
}
