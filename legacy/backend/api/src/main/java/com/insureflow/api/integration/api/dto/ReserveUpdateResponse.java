package com.insureflow.api.integration.api.dto;

import java.math.BigDecimal;
import java.util.UUID;

public record ReserveUpdateResponse(
        String claimNumber,
        String coverageCode,
        BigDecimal reserveAmount,
        String currency,
        String reason,
        UUID reserveId,
        UUID integrationEventId) {}
