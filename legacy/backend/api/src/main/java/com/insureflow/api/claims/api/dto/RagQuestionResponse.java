package com.insureflow.api.claims.api.dto;

import java.util.List;

public record RagQuestionResponse(
        String question,
        String answer,
        String confidence,
        boolean requiresHumanReview,
        List<RagSourceResponse> sources) {}
