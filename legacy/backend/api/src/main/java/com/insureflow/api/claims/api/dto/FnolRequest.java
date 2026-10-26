package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.ClaimType;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

public record FnolRequest(
        @NotBlank String policyNumber,
        @NotNull ClaimType claimType,
        @NotNull LocalDate lossDate,
        @NotNull Instant reportedAt,
        String lossLocation,
        @NotBlank String description,
        @NotNull @DecimalMin("0.00") BigDecimal estimatedLossAmount) {}
