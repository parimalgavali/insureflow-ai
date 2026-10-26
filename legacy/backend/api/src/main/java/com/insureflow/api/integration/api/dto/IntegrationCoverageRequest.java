package com.insureflow.api.integration.api.dto;

import com.insureflow.api.policy.domain.CoverageType;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

public record IntegrationCoverageRequest(
        @NotBlank String coverageCode,
        @NotBlank String coverageName,
        @NotNull CoverageType coverageType,
        @NotNull @DecimalMin("0.00") BigDecimal limitAmount,
        @NotNull @DecimalMin("0.00") BigDecimal deductibleAmount,
        @NotNull LocalDate effectiveDate,
        @NotNull LocalDate expirationDate,
        @NotBlank String exclusions) {}
