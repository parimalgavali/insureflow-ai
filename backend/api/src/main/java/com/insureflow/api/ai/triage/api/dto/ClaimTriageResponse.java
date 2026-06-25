package com.insureflow.api.ai.triage.api.dto;

import com.insureflow.api.ai.triage.domain.AiTriageResult;
import com.insureflow.api.ai.triage.domain.TriageRiskLabel;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

public record ClaimTriageResponse(
        String claimNumber,
        String modelName,
        String modelVersion,
        BigDecimal severityScore,
        TriageRiskLabel severityLabel,
        BigDecimal fraudRiskScore,
        TriageRiskLabel fraudRiskLabel,
        BigDecimal litigationRiskScore,
        TriageRiskLabel litigationRiskLabel,
        String recommendedQueue,
        List<String> reasonCodes,
        boolean humanReviewRequired,
        String explanation,
        Instant createdAt) {

    public static ClaimTriageResponse from(AiTriageResult result) {
        return new ClaimTriageResponse(
                result.getClaim().getClaimNumber(),
                result.getModelName(),
                result.getModelVersion(),
                result.getSeverityScore(),
                result.getSeverityLabel(),
                result.getFraudRiskScore(),
                result.getFraudRiskLabel(),
                result.getLitigationRiskScore(),
                result.getLitigationRiskLabel(),
                result.getRecommendedQueue(),
                result.getReasonCodes(),
                result.isHumanReviewRequired(),
                result.getExplanation(),
                result.getCreatedAt());
    }
}
