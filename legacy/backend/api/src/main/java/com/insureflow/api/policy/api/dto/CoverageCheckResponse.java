package com.insureflow.api.policy.api.dto;

import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.PolicyStatus;
import java.math.BigDecimal;
import java.util.List;

public record CoverageCheckResponse(
        boolean covered,
        PolicyStatus policyStatus,
        CoverageType coverageType,
        BigDecimal limitAmount,
        BigDecimal deductibleAmount,
        String exclusions,
        List<String> reasons,
        List<String> warnings) {}
