package com.insureflow.api.claims.repository;

import com.insureflow.api.claims.domain.ClaimDocument;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ClaimDocumentRepository extends JpaRepository<ClaimDocument, UUID> {

    List<ClaimDocument> findByClaimClaimNumberOrderByUploadedAtDesc(String claimNumber);
}
