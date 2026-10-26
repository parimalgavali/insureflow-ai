package com.insureflow.api.ai.triage.api.dto;

import java.math.BigDecimal;
import java.util.List;

public record TriageScoreRequest(
        String claimId,
        String claimNumber,
        PolicyFeatures policyFeatures,
        ClaimFeatures claimFeatures,
        TextFeatures textFeatures) {

    public record PolicyFeatures(
            String policyType,
            long policyAgeDays,
            BigDecimal coverageLimitAmount,
            BigDecimal deductibleAmount,
            boolean coverageValid,
            List<String> coverageReasons) {}

    public record ClaimFeatures(
            String claimType,
            BigDecimal estimatedLossAmount,
            boolean injuryReported,
            boolean thirdPartyInvolved,
            boolean policeReportAvailable,
            long lossReportDelayDays,
            long priorClaimsCount) {}

    public record TextFeatures(String lossDescription) {}
}
