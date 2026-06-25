package com.insureflow.api.claims.api.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public record CreateClaimDocumentRequest(
        @NotBlank String documentType,
        @NotBlank String fileName,
        @NotBlank String storageUri,
        String contentType,
        Map<String, Object> extractedMetadata) {}
