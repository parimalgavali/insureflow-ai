package com.insureflow.api.humanreview;

import java.time.Instant;
import java.util.UUID;

public record HumanReviewResponse(
        UUID id,
        String claimNumber,
        UUID reviewerAdjusterId,
        HumanReviewDecision decision,
        String overrideReason,
        String notes,
        Instant reviewedAt) {

    static HumanReviewResponse from(HumanReview humanReview) {
        return new HumanReviewResponse(
                humanReview.getId(),
                humanReview.getClaim().getClaimNumber(),
                humanReview.getReviewerAdjuster().getId(),
                humanReview.getDecision(),
                humanReview.getOverrideReason(),
                humanReview.getNotes(),
                humanReview.getReviewedAt());
    }
}
