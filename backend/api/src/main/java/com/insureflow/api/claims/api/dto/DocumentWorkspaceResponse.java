package com.insureflow.api.claims.api.dto;

import java.util.List;

public record DocumentWorkspaceResponse(
        List<String> receivedDocuments,
        List<String> missingDocuments,
        List<String> extractionHighlights,
        List<SummarySection> summarySections) {

    public record SummarySection(String title, String body) {}
}
