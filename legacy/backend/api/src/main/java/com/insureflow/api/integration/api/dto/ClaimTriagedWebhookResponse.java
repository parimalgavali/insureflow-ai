package com.insureflow.api.integration.api.dto;

import java.util.UUID;

public record ClaimTriagedWebhookResponse(
        boolean accepted,
        String claimNumber,
        UUID integrationEventId) {}
