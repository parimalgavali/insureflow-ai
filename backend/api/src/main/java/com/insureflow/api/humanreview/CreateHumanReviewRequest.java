package com.insureflow.api.humanreview;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public record CreateHumanReviewRequest(
        @NotNull UUID reviewerAdjusterId,
        @NotNull HumanReviewDecision decision,
        String overrideReason,
        String notes) {}
