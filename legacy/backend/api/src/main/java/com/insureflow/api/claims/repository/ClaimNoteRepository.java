package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.ClaimNote;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimNoteRepository extends JpaRepository<ClaimNote, UUID> {

    List<ClaimNote> findByClaimClaimNumberOrderByCreatedAtDesc(String claimNumber);
}
