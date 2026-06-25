package com.insureflow.api.ai.triage.api.dto;

public record TriageScoreResponse(
        String claimId,
        String claimNumber,
        String modelName,
        String modelVersion,
        TriageScoreBlock severity,
        TriageScoreBlock fraud,
        TriageScoreBlock litigation,
        String recommendedQueue,
        boolean humanReviewRequired,
        String explanation) {}
