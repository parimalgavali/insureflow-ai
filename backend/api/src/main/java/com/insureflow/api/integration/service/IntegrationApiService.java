package com.insureflow.api.integration.service;

import com.insureflow.api.claims.api.dto.ChangeClaimStatusRequest;
import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.FnolRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimReserve;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.claims.repository.ClaimReserveRepository;
import com.insureflow.api.claims.service.ClaimIntakeService;
import com.insureflow.api.claims.service.ClaimTimelineService;
import com.insureflow.api.claims.service.ClaimWorkflowService;
import com.insureflow.api.integration.api.dto.ClaimTriagedWebhookRequest;
import com.insureflow.api.integration.api.dto.ClaimTriagedWebhookResponse;
import com.insureflow.api.integration.api.dto.IntegrationClaimCreateRequest;
import com.insureflow.api.integration.api.dto.IntegrationClaimResponse;
import com.insureflow.api.integration.api.dto.IntegrationClaimStatusUpdateRequest;
import com.insureflow.api.integration.api.dto.IntegrationCoverageRequest;
import com.insureflow.api.integration.api.dto.IntegrationPolicySyncResponse;
import com.insureflow.api.integration.api.dto.PolicySyncRequest;
import com.insureflow.api.integration.api.dto.ReserveUpdateRequest;
import com.insureflow.api.integration.api.dto.ReserveUpdateResponse;
import com.insureflow.api.integration.domain.IntegrationEvent;
import com.insureflow.api.policy.api.dto.AddCoverageRequest;
import com.insureflow.api.policy.api.dto.CreateCustomerRequest;
import com.insureflow.api.policy.api.dto.CreatePolicyRequest;
import com.insureflow.api.policy.api.dto.PolicyResponse;
import com.insureflow.api.policy.service.PolicyManagementService;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class IntegrationApiService {

    private final PolicyManagementService policyManagementService;
    private final ClaimIntakeService claimIntakeService;
    private final ClaimWorkflowService claimWorkflowService;
    private final ClaimRepository claimRepository;
    private final ClaimReserveRepository claimReserveRepository;
    private final ClaimTimelineService claimTimelineService;
    private final IntegrationEventService integrationEventService;

    public IntegrationApiService(
            PolicyManagementService policyManagementService,
            ClaimIntakeService claimIntakeService,
            ClaimWorkflowService claimWorkflowService,
            ClaimRepository claimRepository,
            ClaimReserveRepository claimReserveRepository,
            ClaimTimelineService claimTimelineService,
            IntegrationEventService integrationEventService) {
        this.policyManagementService = policyManagementService;
        this.claimIntakeService = claimIntakeService;
        this.claimWorkflowService = claimWorkflowService;
        this.claimRepository = claimRepository;
        this.claimReserveRepository = claimReserveRepository;
        this.claimTimelineService = claimTimelineService;
        this.integrationEventService = integrationEventService;
    }

    @Transactional
    public IntegrationPolicySyncResponse syncPolicy(PolicySyncRequest request) {
        policyManagementService.createCustomer(new CreateCustomerRequest(
                request.customer().customerNumber(),
                request.customer().firstName(),
                request.customer().lastName(),
                request.customer().email(),
                request.customer().phone(),
                request.customer().addressLine1(),
                request.customer().addressLine2(),
                request.customer().city(),
                request.customer().state(),
                request.customer().postalCode(),
                request.customer().country()));

        PolicyResponse policy = policyManagementService.createPolicy(new CreatePolicyRequest(
                request.customer().customerNumber(),
                request.policy().policyNumber(),
                request.policy().policyType(),
                request.policy().effectiveDate(),
                request.policy().expirationDate(),
                request.policy().premiumAmount(),
                request.policy().currency()));

        for (IntegrationCoverageRequest coverage : request.coverages()) {
            policyManagementService.addCoverage(policy.policyNumber(), new AddCoverageRequest(
                    coverage.coverageCode(),
                    coverage.coverageName(),
                    coverage.coverageType(),
                    coverage.limitAmount(),
                    coverage.deductibleAmount(),
                    coverage.effectiveDate(),
                    coverage.expirationDate(),
                    coverage.exclusions()));
        }

        PolicyResponse finalPolicy = request.policy().activate()
                ? policyManagementService.activate(policy.policyNumber())
                : policyManagementService.getPolicy(policy.policyNumber());

        IntegrationEvent event = integrationEventService.recordCompleted(
                request.sourceSystem(),
                "POLICY_SYNC",
                request.externalReference(),
                null,
                finalPolicy.policyNumber(),
                Map.of(
                        "customerNumber", finalPolicy.customerNumber(),
                        "coverageCount", finalPolicy.coverages().size(),
                        "status", finalPolicy.status().name()));

        return new IntegrationPolicySyncResponse(
                finalPolicy.policyNumber(),
                finalPolicy.customerNumber(),
                finalPolicy.status(),
                finalPolicy.coverages().size(),
                event.getId());
    }

    @Transactional
    public IntegrationClaimResponse createClaim(IntegrationClaimCreateRequest request) {
        ClaimResponse claim = claimIntakeService.submit(new FnolRequest(
                request.claim().policyNumber(),
                request.claim().claimType(),
                request.claim().lossDate(),
                request.claim().reportedAt(),
                request.claim().lossLocation(),
                request.claim().description(),
                request.claim().estimatedLossAmount()));

        IntegrationEvent event = integrationEventService.recordCompleted(
                request.sourceSystem(),
                "CLAIM_CREATE",
                request.externalReference(),
                claim.claimNumber(),
                claim.policyNumber(),
                Map.of("status", claim.status().name(), "claimType", claim.claimType().name()));

        return toIntegrationClaimResponse(claim, event);
    }

    @Transactional(readOnly = true)
    public IntegrationClaimResponse getClaim(String claimNumber) {
        return toIntegrationClaimResponse(claimWorkflowService.getClaim(claimNumber), null);
    }

    @Transactional
    public IntegrationClaimResponse changeClaimStatus(
            String claimNumber, IntegrationClaimStatusUpdateRequest request) {
        ClaimResponse claim = claimWorkflowService.changeStatus(
                claimNumber, new ChangeClaimStatusRequest(request.targetStatus(), request.reason()));

        IntegrationEvent event = integrationEventService.recordCompleted(
                request.sourceSystem(),
                "CLAIM_STATUS_UPDATE",
                request.externalReference(),
                claim.claimNumber(),
                claim.policyNumber(),
                Map.of("status", claim.status().name(), "reason", request.reason()));

        return toIntegrationClaimResponse(claim, event);
    }

    @Transactional
    public ReserveUpdateResponse updateReserve(String claimNumber, ReserveUpdateRequest request) {
        Claim claim = claimRepository
                .findByClaimNumber(claimNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + claimNumber + " was not found"));

        ClaimReserve reserve = new ClaimReserve();
        reserve.setClaim(claim);
        reserve.setExternalReference(request.externalReference());
        reserve.setSourceSystem(request.sourceSystem());
        reserve.setCoverageCode(request.coverageCode());
        reserve.setReserveAmount(request.reserveAmount());
        reserve.setCurrency(request.currency());
        reserve.setReason(request.reason());
        ClaimReserve savedReserve = claimReserveRepository.save(reserve);

        claimTimelineService.record(
                claim,
                ClaimEventType.RESERVE_UPDATED,
                request.sourceSystem(),
                "Claim reserve updated",
                Map.of(
                        "externalReference", request.externalReference(),
                        "coverageCode", request.coverageCode(),
                        "reserveAmount", request.reserveAmount(),
                        "currency", request.currency(),
                        "reason", request.reason()));

        IntegrationEvent event = integrationEventService.recordCompleted(
                request.sourceSystem(),
                "CLAIM_RESERVE_UPDATE",
                request.externalReference(),
                claimNumber,
                claim.getPolicy().getPolicyNumber(),
                Map.of(
                        "coverageCode", request.coverageCode(),
                        "reserveAmount", request.reserveAmount(),
                        "currency", request.currency()));

        return new ReserveUpdateResponse(
                claimNumber,
                savedReserve.getCoverageCode(),
                savedReserve.getReserveAmount(),
                savedReserve.getCurrency(),
                savedReserve.getReason(),
                savedReserve.getId(),
                event.getId());
    }

    @Transactional
    public ClaimTriagedWebhookResponse acknowledgeClaimTriaged(ClaimTriagedWebhookRequest request) {
        Claim claim = claimRepository
                .findByClaimNumber(request.claimNumber())
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + request.claimNumber() + " was not found"));

        IntegrationEvent event = integrationEventService.recordAccepted(
                request.sourceSystem(),
                "CLAIM_TRIAGED_WEBHOOK",
                request.externalReference(),
                request.claimNumber(),
                claim.getPolicy().getPolicyNumber(),
                Map.of(
                        "severityLabel", request.severityLabel(),
                        "fraudRiskLabel", request.fraudRiskLabel(),
                        "recommendedQueue", request.recommendedQueue(),
                        "humanReviewRequired", request.humanReviewRequired()));

        return new ClaimTriagedWebhookResponse(true, request.claimNumber(), event.getId());
    }

    private IntegrationClaimResponse toIntegrationClaimResponse(ClaimResponse claim, IntegrationEvent event) {
        return new IntegrationClaimResponse(
                claim.claimNumber(),
                claim.status(),
                claim.claimType(),
                claim.lossDate(),
                claim.reportedAt(),
                claim.estimatedLossAmount(),
                Map.of("policyNumber", claim.policyNumber(), "customerNumber", claim.customerNumber()),
                event == null ? null : event.getId());
    }
}
