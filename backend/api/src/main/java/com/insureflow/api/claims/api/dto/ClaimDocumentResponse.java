package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.ClaimDocument;
import java.time.Instant;
import java.util.Map;

public record ClaimDocumentResponse(
        String documentType,
        String fileName,
        String storageUri,
        String contentType,
        Map<String, Object> extractedMetadata,
        Instant uploadedAt) {

    public static ClaimDocumentResponse from(ClaimDocument document) {
        return new ClaimDocumentResponse(
                document.getDocumentType(),
                document.getFileName(),
                document.getStorageUri(),
                document.getContentType(),
                document.getExtractedMetadata(),
                document.getUploadedAt());
    }
}
