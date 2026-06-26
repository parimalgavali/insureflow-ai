package com.insureflow.api.integration.api.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record ClaimTriagedWebhookRequest(
        @NotBlank String sourceSystem,
        @NotBlank String externalReference,
        @NotBlank String claimNumber,
        @NotBlank String severityLabel,
        @NotBlank String fraudRiskLabel,
        @NotBlank String recommendedQueue,
        @NotNull Boolean humanReviewRequired) {}
