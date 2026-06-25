package com.insureflow.api.policy.api.dto;

import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.domain.PolicyType;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public record PolicyResponse(
        String policyNumber,
        String customerNumber,
        PolicyType policyType,
        PolicyStatus status,
        LocalDate effectiveDate,
        LocalDate expirationDate,
        BigDecimal premiumAmount,
        String currency,
        List<CoverageResponse> coverages) {

    public static PolicyResponse from(Policy policy, List<Coverage> coverages) {
        return new PolicyResponse(
                policy.getPolicyNumber(),
                policy.getCustomer().getCustomerNumber(),
                policy.getPolicyType(),
                policy.getStatus(),
                policy.getEffectiveDate(),
                policy.getExpirationDate(),
                policy.getPremiumAmount(),
                policy.getCurrency(),
                coverages.stream().map(CoverageResponse::from).toList());
    }
}
