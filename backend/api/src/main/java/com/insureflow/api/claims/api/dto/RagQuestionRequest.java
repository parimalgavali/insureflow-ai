package com.insureflow.api.claims.api.dto;

import jakarta.validation.constraints.NotBlank;

public record RagQuestionRequest(@NotBlank String question) {}
