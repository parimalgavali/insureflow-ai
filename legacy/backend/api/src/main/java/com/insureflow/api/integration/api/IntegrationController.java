package com.insureflow.api.integration.api;

import com.insureflow.api.integration.api.dto.ClaimTriagedWebhookRequest;
import com.insureflow.api.integration.api.dto.ClaimTriagedWebhookResponse;
import com.insureflow.api.integration.api.dto.IntegrationClaimCreateRequest;
import com.insureflow.api.integration.api.dto.IntegrationClaimResponse;
import com.insureflow.api.integration.api.dto.IntegrationClaimStatusUpdateRequest;
import com.insureflow.api.integration.api.dto.IntegrationPolicySyncResponse;
import com.insureflow.api.integration.api.dto.PolicySyncRequest;
import com.insureflow.api.integration.api.dto.ReserveUpdateRequest;
import com.insureflow.api.integration.api.dto.ReserveUpdateResponse;
import com.insureflow.api.integration.service.IntegrationApiService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/integration/v1")
class IntegrationController {

    private final IntegrationApiService integrationApiService;

    IntegrationController(IntegrationApiService integrationApiService) {
        this.integrationApiService = integrationApiService;
    }

    @PostMapping("/policies/sync")
    @ResponseStatus(HttpStatus.CREATED)
    IntegrationPolicySyncResponse syncPolicy(@Valid @RequestBody PolicySyncRequest request) {
        return integrationApiService.syncPolicy(request);
    }

    @PostMapping("/claims")
    @ResponseStatus(HttpStatus.CREATED)
    IntegrationClaimResponse createClaim(@Valid @RequestBody IntegrationClaimCreateRequest request) {
        return integrationApiService.createClaim(request);
    }

    @GetMapping("/claims/{claimNumber}")
    IntegrationClaimResponse getClaim(@PathVariable String claimNumber) {
        return integrationApiService.getClaim(claimNumber);
    }

    @PostMapping("/claims/{claimNumber}/status")
    IntegrationClaimResponse changeClaimStatus(
            @PathVariable String claimNumber, @Valid @RequestBody IntegrationClaimStatusUpdateRequest request) {
        return integrationApiService.changeClaimStatus(claimNumber, request);
    }

    @PostMapping("/claims/{claimNumber}/reserves")
    @ResponseStatus(HttpStatus.CREATED)
    ReserveUpdateResponse updateReserve(
            @PathVariable String claimNumber, @Valid @RequestBody ReserveUpdateRequest request) {
        return integrationApiService.updateReserve(claimNumber, request);
    }

    @PostMapping("/webhooks/claim-triaged")
    @ResponseStatus(HttpStatus.ACCEPTED)
    ClaimTriagedWebhookResponse acknowledgeClaimTriaged(@Valid @RequestBody ClaimTriagedWebhookRequest request) {
        return integrationApiService.acknowledgeClaimTriaged(request);
    }
}
