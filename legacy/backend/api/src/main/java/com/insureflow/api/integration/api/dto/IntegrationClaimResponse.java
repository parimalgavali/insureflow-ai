package com.insureflow.api.integration.api.dto;

import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.domain.ClaimType;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Map;
import java.util.UUID;

public record IntegrationClaimResponse(
        String claimNumber,
        ClaimStatus status,
        ClaimType claimType,
        LocalDate lossDate,
        Instant reportedAt,
        BigDecimal estimatedLossAmount,
        Map<String, Object> policy,
        UUID integrationEventId) {}
