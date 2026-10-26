package com.insureflow.api.integration.api.dto;

import com.insureflow.api.claims.domain.ClaimStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record IntegrationClaimStatusUpdateRequest(
        @NotBlank String sourceSystem,
        @NotBlank String externalReference,
        @NotNull ClaimStatus targetStatus,
        @NotBlank String reason) {}
