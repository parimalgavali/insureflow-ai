package com.insureflow.api.policy.api.dto;

import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.CoverageType;
import java.math.BigDecimal;
import java.time.LocalDate;

public record CoverageResponse(
        String coverageCode,
        String coverageName,
        CoverageType coverageType,
        BigDecimal limitAmount,
        BigDecimal deductibleAmount,
        LocalDate effectiveDate,
        LocalDate expirationDate,
        String exclusions) {

    public static CoverageResponse from(Coverage coverage) {
        return new CoverageResponse(
                coverage.getCoverageCode(),
                coverage.getCoverageName(),
                coverage.getCoverageType(),
                coverage.getLimitAmount(),
                coverage.getDeductibleAmount(),
                coverage.getEffectiveDate(),
                coverage.getExpirationDate(),
                coverage.getExclusions());
    }
}
