package com.insureflow.api.policy.api.dto;

import com.insureflow.api.policy.domain.PolicyType;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.time.LocalDate;

public record CreatePolicyRequest(
        @NotBlank String customerNumber,
        @NotBlank String policyNumber,
        @NotNull PolicyType policyType,
        @NotNull LocalDate effectiveDate,
        @NotNull LocalDate expirationDate,
        @NotNull @DecimalMin("0.00") BigDecimal premiumAmount,
        @NotBlank String currency) {}
