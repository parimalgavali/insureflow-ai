package com.insureflow.api.policy.service;

import com.insureflow.api.policy.api.dto.CoverageCheckRequest;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.repository.CoverageRepository;
import com.insureflow.api.policy.repository.PolicyRepository;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CoverageValidationService {

    private final PolicyRepository policyRepository;
    private final CoverageRepository coverageRepository;

    public CoverageValidationService(PolicyRepository policyRepository, CoverageRepository coverageRepository) {
        this.policyRepository = policyRepository;
        this.coverageRepository = coverageRepository;
    }

    @Transactional(readOnly = true)
    public CoverageCheckResponse validate(String policyNumber, CoverageCheckRequest request) {
        Policy policy = policyRepository
                .findByPolicyNumber(policyNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Policy " + policyNumber + " was not found"));

        CoverageType requiredCoverage = coverageTypeForClaimType(request.claimType());
        List<String> reasons = new ArrayList<>();
        List<String> warnings = new ArrayList<>();

        if (policy.getStatus() != PolicyStatus.ACTIVE
                || request.lossDate().isBefore(policy.getEffectiveDate())
                || !request.lossDate().isBefore(policy.getExpirationDate())) {
            reasons.add("POLICY_NOT_ACTIVE_ON_LOSS_DATE");
        }

        Coverage coverage = coverageRepository.findByPolicyAndCoverageType(policy, requiredCoverage).orElse(null);
        if (coverage == null) {
            reasons.add("COVERAGE_NOT_INCLUDED");
            return new CoverageCheckResponse(
                    false,
                    policy.getStatus(),
                    requiredCoverage,
                    null,
                    null,
                    "[]",
                    reasons,
                    warnings);
        }

        if (request.estimatedLossAmount().compareTo(coverage.getLimitAmount()) > 0) {
            warnings.add("ESTIMATED_LOSS_EXCEEDS_LIMIT");
        }

        return new CoverageCheckResponse(
                reasons.isEmpty(),
                policy.getStatus(),
                requiredCoverage,
                coverage.getLimitAmount(),
                coverage.getDeductibleAmount(),
                coverage.getExclusions(),
                reasons,
                warnings);
    }

    private CoverageType coverageTypeForClaimType(String claimType) {
        return switch (claimType) {
            case "AUTO_COLLISION" -> CoverageType.COLLISION;
            case "AUTO_COMPREHENSIVE" -> CoverageType.COMPREHENSIVE;
            case "BODILY_INJURY" -> CoverageType.BODILY_INJURY;
            case "PROPERTY_DAMAGE" -> CoverageType.PROPERTY_DAMAGE;
            case "HOME_WATER_DAMAGE" -> CoverageType.WATER_DAMAGE;
            case "HOME_FIRE" -> CoverageType.FIRE;
            case "THEFT" -> CoverageType.THEFT;
            default -> throw new IllegalArgumentException("Unsupported claimType " + claimType);
        };
    }
}
