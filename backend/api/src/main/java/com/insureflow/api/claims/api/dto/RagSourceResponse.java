package com.insureflow.api.claims.api.dto;

public record RagSourceResponse(
        String documentId,
        String chunkId,
        String documentType,
        String sectionTitle,
        int pageNumber,
        double score) {}
