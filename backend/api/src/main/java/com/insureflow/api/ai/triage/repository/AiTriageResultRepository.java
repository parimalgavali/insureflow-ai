package com.insureflow.api.ai.triage.repository;

import com.insureflow.api.ai.triage.domain.AiTriageResult;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AiTriageResultRepository extends JpaRepository<AiTriageResult, UUID> {

    List<AiTriageResult> findByClaimClaimNumberOrderByCreatedAtDescResultSequenceDesc(String claimNumber);
}
