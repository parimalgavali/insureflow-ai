package com.insureflow.api.claims.service;

import com.insureflow.api.claims.api.dto.ChangeClaimStatusRequest;
import com.insureflow.api.claims.api.dto.ClaimEventResponse;
import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEvent;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.repository.ClaimEventRepository;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.shared.error.BusinessRuleViolationException;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ClaimWorkflowService {

    private static final Map<ClaimStatus, Set<ClaimStatus>> ALLOWED_TRANSITIONS = Map.of(
            ClaimStatus.SUBMITTED, Set.of(ClaimStatus.UNDER_REVIEW, ClaimStatus.CLOSED),
            ClaimStatus.UNDER_REVIEW,
                    Set.of(ClaimStatus.PENDING_DOCUMENTS, ClaimStatus.APPROVED, ClaimStatus.DENIED, ClaimStatus.CLOSED),
            ClaimStatus.PENDING_DOCUMENTS, Set.of(ClaimStatus.UNDER_REVIEW, ClaimStatus.CLOSED),
            ClaimStatus.APPROVED, Set.of(ClaimStatus.PAYMENT_PENDING, ClaimStatus.CLOSED),
            ClaimStatus.PAYMENT_PENDING, Set.of(ClaimStatus.PAID, ClaimStatus.CLOSED),
            ClaimStatus.PAID, Set.of(ClaimStatus.CLOSED),
            ClaimStatus.DENIED, Set.of(ClaimStatus.CLOSED),
            ClaimStatus.CLOSED, Set.of());

    private final ClaimRepository claimRepository;
    private final ClaimEventRepository claimEventRepository;
    private final ClaimTimelineService claimTimelineService;

    public ClaimWorkflowService(
            ClaimRepository claimRepository,
            ClaimEventRepository claimEventRepository,
            ClaimTimelineService claimTimelineService) {
        this.claimRepository = claimRepository;
        this.claimEventRepository = claimEventRepository;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional(readOnly = true)
    public ClaimResponse getClaim(String claimNumber) {
        return ClaimResponse.from(findClaim(claimNumber), coverageValidationSnapshot(claimNumber).orElse(null));
    }

    @Transactional(readOnly = true)
    public List<ClaimResponse> listClaims() {
        return claimRepository.findAllByOrderByReportedAtDesc().stream()
                .map(claim -> ClaimResponse.from(claim, coverageValidationSnapshot(claim.getClaimNumber()).orElse(null)))
                .toList();
    }

    @Transactional(readOnly = true)
    public List<ClaimEventResponse> getEvents(String claimNumber) {
        findClaim(claimNumber);
        return claimEventRepository.findByClaimClaimNumberOrderByCreatedAtAsc(claimNumber).stream()
                .map(ClaimEventResponse::from)
                .toList();
    }

    @Transactional
    public ClaimResponse changeStatus(String claimNumber, ChangeClaimStatusRequest request) {
        Claim claim = findClaim(claimNumber);
        ClaimStatus currentStatus = claim.getStatus();
        if (!ALLOWED_TRANSITIONS.getOrDefault(currentStatus, Set.of()).contains(request.targetStatus())) {
            throw new BusinessRuleViolationException(
                    "Invalid claim status transition from " + currentStatus + " to " + request.targetStatus());
        }

        claim.setStatus(request.targetStatus());
        Claim savedClaim = claimRepository.save(claim);
        claimTimelineService.record(
                savedClaim,
                ClaimEventType.STATUS_CHANGED,
                "SYSTEM",
                "Claim status changed",
                Map.of("from", currentStatus.name(), "to", request.targetStatus().name(), "reason", reason(request)));
        return ClaimResponse.from(savedClaim, null);
    }

    Claim findClaim(String claimNumber) {
        return claimRepository
                .findByClaimNumber(claimNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + claimNumber + " was not found"));
    }

    private String reason(ChangeClaimStatusRequest request) {
        return request.reason() == null ? "" : request.reason();
    }

    @SuppressWarnings("unchecked")
    private Optional<CoverageCheckResponse> coverageValidationSnapshot(String claimNumber) {
        return claimEventRepository.findByClaimClaimNumberOrderByCreatedAtAsc(claimNumber).stream()
                .filter(event -> event.getEventType() == ClaimEventType.COVERAGE_VALIDATED)
                .reduce((first, second) -> second)
                .map(ClaimEvent::getPayload)
                .map(payload -> new CoverageCheckResponse(
                        Boolean.TRUE.equals(payload.get("covered")),
                        enumValue(PolicyStatus.class, payload.get("policyStatus")),
                        enumValue(CoverageType.class, payload.get("coverageType")),
                        decimalValue(payload.get("limitAmount")),
                        decimalValue(payload.get("deductibleAmount")),
                        stringValue(payload.get("exclusions")),
                        (List<String>) payload.getOrDefault("reasons", List.of()),
                        (List<String>) payload.getOrDefault("warnings", List.of())));
    }

    private <T extends Enum<T>> T enumValue(Class<T> enumType, Object value) {
        if (value == null) {
            return null;
        }
        return Enum.valueOf(enumType, value.toString());
    }

    private BigDecimal decimalValue(Object value) {
        if (value == null) {
            return null;
        }
        return new BigDecimal(value.toString());
    }

    private String stringValue(Object value) {
        return value == null ? null : value.toString();
    }
}
