package com.insureflow.api.policy.repository;

import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.Policy;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CoverageRepository extends JpaRepository<Coverage, UUID> {

    List<Coverage> findByPolicyPolicyNumber(String policyNumber);

    Optional<Coverage> findByPolicyAndCoverageType(Policy policy, CoverageType coverageType);
}
