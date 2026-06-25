package com.insureflow.api.ai.triage.service;

import com.insureflow.api.ai.triage.api.dto.TriageScoreRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimDocument;
import com.insureflow.api.claims.domain.ClaimEvent;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimType;
import com.insureflow.api.claims.repository.ClaimDocumentRepository;
import com.insureflow.api.claims.repository.ClaimEventRepository;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.repository.CoverageRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;

@Service
public class ClaimTriageFeatureAssembler {

    private final CoverageRepository coverageRepository;
    private final ClaimDocumentRepository claimDocumentRepository;
    private final ClaimEventRepository claimEventRepository;
    private final ClaimRepository claimRepository;

    public ClaimTriageFeatureAssembler(
            CoverageRepository coverageRepository,
            ClaimDocumentRepository claimDocumentRepository,
            ClaimEventRepository claimEventRepository,
            ClaimRepository claimRepository) {
        this.coverageRepository = coverageRepository;
        this.claimDocumentRepository = claimDocumentRepository;
        this.claimEventRepository = claimEventRepository;
        this.claimRepository = claimRepository;
    }

    public TriageScoreRequest assemble(Claim claim) {
        Optional<Coverage> coverage = coverageRepository.findByPolicyAndCoverageType(
                claim.getPolicy(), coverageTypeForClaimType(claim.getClaimType()));
        CoverageSnapshot coverageSnapshot = latestCoverageSnapshot(claim.getClaimNumber());
        long policyAgeDays = Math.max(0, ChronoUnit.DAYS.between(
                claim.getPolicy().getEffectiveDate(), claim.getLossDate()));

        return new TriageScoreRequest(
                claim.getId().toString(),
                claim.getClaimNumber(),
                new TriageScoreRequest.PolicyFeatures(
                        claim.getPolicy().getPolicyType().name(),
                        policyAgeDays,
                        coverage.map(Coverage::getLimitAmount).orElse(BigDecimal.ZERO),
                        coverage.map(Coverage::getDeductibleAmount).orElse(BigDecimal.ZERO),
                        coverageSnapshot.covered(),
                        coverageSnapshot.reasons()),
                new TriageScoreRequest.ClaimFeatures(
                        claim.getClaimType().name(),
                        claim.getEstimatedLossAmount() == null ? BigDecimal.ZERO : claim.getEstimatedLossAmount(),
                        containsAny(claim.getDescription(), "injury", "injured", "medical", "ambulance", "hospital"),
                        containsAny(claim.getDescription(), "third party", "other driver", "pedestrian", "passenger"),
                        hasPoliceReport(claim.getClaimNumber()),
                        lossReportDelayDays(claim),
                        priorClaimsCount(claim)),
                new TriageScoreRequest.TextFeatures(claim.getDescription()));
    }

    private CoverageSnapshot latestCoverageSnapshot(String claimNumber) {
        return claimEventRepository.findByClaimClaimNumberOrderByCreatedAtAsc(claimNumber).stream()
                .filter(event -> event.getEventType() == ClaimEventType.COVERAGE_VALIDATED)
                .reduce((first, second) -> second)
                .map(ClaimEvent::getPayload)
                .map(payload -> new CoverageSnapshot(
                        Boolean.TRUE.equals(payload.get("covered")),
                        stringList(payload.get("reasons"))))
                .orElse(new CoverageSnapshot(true, List.of()));
    }

    private boolean hasPoliceReport(String claimNumber) {
        return claimDocumentRepository.findByClaimClaimNumberOrderByUploadedAtDesc(claimNumber).stream()
                .map(ClaimDocument::getDocumentType)
                .anyMatch("POLICE_REPORT"::equals);
    }

    private long lossReportDelayDays(Claim claim) {
        LocalDate reportedDate = claim.getReportedAt().atZone(ZoneOffset.UTC).toLocalDate();
        return Math.max(0, ChronoUnit.DAYS.between(claim.getLossDate(), reportedDate));
    }

    private long priorClaimsCount(Claim claim) {
        return claimRepository.countByCustomerIdAndReportedAtBefore(claim.getCustomer().getId(), claim.getReportedAt());
    }

    private CoverageType coverageTypeForClaimType(ClaimType claimType) {
        return switch (claimType) {
            case AUTO_COLLISION -> CoverageType.COLLISION;
            case AUTO_COMPREHENSIVE -> CoverageType.COMPREHENSIVE;
            case BODILY_INJURY -> CoverageType.BODILY_INJURY;
            case PROPERTY_DAMAGE -> CoverageType.PROPERTY_DAMAGE;
            case HOME_WATER_DAMAGE -> CoverageType.WATER_DAMAGE;
            case HOME_FIRE -> CoverageType.FIRE;
            case THEFT -> CoverageType.THEFT;
        };
    }

    private boolean containsAny(String text, String... keywords) {
        String normalized = text == null ? "" : text.toLowerCase(Locale.ROOT);
        for (String keyword : keywords) {
            if (normalized.contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    @SuppressWarnings("unchecked")
    private List<String> stringList(Object value) {
        if (value instanceof List<?> values) {
            return (List<String>) values;
        }
        return List.of();
    }

    private record CoverageSnapshot(boolean covered, List<String> reasons) {}
}
