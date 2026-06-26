package com.insureflow.api.integration.api.dto;

import com.insureflow.api.policy.domain.PolicyStatus;
import java.util.UUID;

public record IntegrationPolicySyncResponse(
        String policyNumber,
        String customerNumber,
        PolicyStatus status,
        int coverageCount,
        UUID integrationEventId) {}
