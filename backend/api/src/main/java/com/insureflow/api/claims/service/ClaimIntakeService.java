package com.insureflow.api.claims.service;

import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.FnolRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.policy.api.dto.CoverageCheckRequest;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.repository.PolicyRepository;
import com.insureflow.api.policy.service.CoverageValidationService;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ClaimIntakeService {

    private final PolicyRepository policyRepository;
    private final ClaimRepository claimRepository;
    private final ClaimNumberGenerator claimNumberGenerator;
    private final CoverageValidationService coverageValidationService;
    private final ClaimTimelineService claimTimelineService;

    public ClaimIntakeService(
            PolicyRepository policyRepository,
            ClaimRepository claimRepository,
            ClaimNumberGenerator claimNumberGenerator,
            CoverageValidationService coverageValidationService,
            ClaimTimelineService claimTimelineService) {
        this.policyRepository = policyRepository;
        this.claimRepository = claimRepository;
        this.claimNumberGenerator = claimNumberGenerator;
        this.coverageValidationService = coverageValidationService;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional
    public ClaimResponse submit(FnolRequest request) {
        Policy policy = policyRepository
                .findByPolicyNumber(request.policyNumber())
                .orElseThrow(() -> new ResourceNotFoundException("Policy " + request.policyNumber() + " was not found"));

        CoverageCheckResponse coverageValidation = coverageValidationService.validate(
                request.policyNumber(),
                new CoverageCheckRequest(
                        request.claimType().name(), request.lossDate(), request.estimatedLossAmount()));

        Claim claim = new Claim();
        claim.setPolicy(policy);
        claim.setCustomer(policy.getCustomer());
        claim.setClaimNumber(nextClaimNumber(request));
        claim.setClaimType(request.claimType());
        claim.setStatus(ClaimStatus.SUBMITTED);
        claim.setLossDate(request.lossDate());
        claim.setReportedAt(request.reportedAt());
        claim.setLossLocation(request.lossLocation());
        claim.setDescription(request.description());
        claim.setEstimatedLossAmount(request.estimatedLossAmount());
        Claim savedClaim = claimRepository.save(claim);

        claimTimelineService.record(
                savedClaim,
                ClaimEventType.FNOL_SUBMITTED,
                "SYSTEM",
                "FNOL submitted",
                Map.of("policyNumber", request.policyNumber(), "claimType", request.claimType().name()));
        claimTimelineService.record(
                savedClaim,
                ClaimEventType.COVERAGE_VALIDATED,
                "SYSTEM",
                "Coverage validated",
                Map.of(
                        "covered",
                        coverageValidation.covered(),
                        "reasons",
                        coverageValidation.reasons(),
                        "warnings",
                        coverageValidation.warnings()));

        return ClaimResponse.from(savedClaim, coverageValidation);
    }

    private String nextClaimNumber(FnolRequest request) {
        var reportedDate = request.reportedAt().atZone(ZoneOffset.UTC).toLocalDate();
        String prefix = "CLM-" + java.time.format.DateTimeFormatter.BASIC_ISO_DATE.format(reportedDate);
        long existingClaims = claimRepository.countByClaimNumberStartingWith(prefix);
        return claimNumberGenerator.generate(reportedDate, existingClaims);
    }
}
