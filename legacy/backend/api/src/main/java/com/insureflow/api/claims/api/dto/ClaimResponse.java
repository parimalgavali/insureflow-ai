package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.domain.ClaimType;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

public record ClaimResponse(
        String claimNumber,
        String policyNumber,
        String customerNumber,
        ClaimType claimType,
        ClaimStatus status,
        LocalDate lossDate,
        Instant reportedAt,
        String lossLocation,
        String description,
        BigDecimal estimatedLossAmount,
        CoverageCheckResponse coverageValidation) {

    public static ClaimResponse from(Claim claim, CoverageCheckResponse coverageValidation) {
        return new ClaimResponse(
                claim.getClaimNumber(),
                claim.getPolicy().getPolicyNumber(),
                claim.getCustomer().getCustomerNumber(),
                claim.getClaimType(),
                claim.getStatus(),
                claim.getLossDate(),
                claim.getReportedAt(),
                claim.getLossLocation(),
                claim.getDescription(),
                claim.getEstimatedLossAmount(),
                coverageValidation);
    }
}
