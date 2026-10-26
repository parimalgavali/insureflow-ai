package com.insureflow.api.policy.api.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

public record CoverageCheckRequest(
        @NotBlank String claimType,
        @NotNull LocalDate lossDate,
        @NotNull @DecimalMin("0.00") BigDecimal estimatedLossAmount) {}
