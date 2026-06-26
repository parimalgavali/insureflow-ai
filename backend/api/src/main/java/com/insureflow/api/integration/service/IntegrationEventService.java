package com.insureflow.api.integration.service;

import com.insureflow.api.integration.domain.IntegrationEvent;
import com.insureflow.api.integration.domain.IntegrationEventStatus;
import com.insureflow.api.integration.repository.IntegrationEventRepository;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class IntegrationEventService {

    private final IntegrationEventRepository integrationEventRepository;

    public IntegrationEventService(IntegrationEventRepository integrationEventRepository) {
        this.integrationEventRepository = integrationEventRepository;
    }

    public IntegrationEvent recordCompleted(
            String sourceSystem,
            String eventType,
            String externalReference,
            String claimNumber,
            String policyNumber,
            Map<String, Object> payload) {
        return record(
                sourceSystem,
                eventType,
                externalReference,
                IntegrationEventStatus.COMPLETED,
                claimNumber,
                policyNumber,
                payload);
    }

    public IntegrationEvent recordAccepted(
            String sourceSystem,
            String eventType,
            String externalReference,
            String claimNumber,
            String policyNumber,
            Map<String, Object> payload) {
        return record(
                sourceSystem,
                eventType,
                externalReference,
                IntegrationEventStatus.ACCEPTED,
                claimNumber,
                policyNumber,
                payload);
    }

    private IntegrationEvent record(
            String sourceSystem,
            String eventType,
            String externalReference,
            IntegrationEventStatus status,
            String claimNumber,
            String policyNumber,
            Map<String, Object> payload) {
        IntegrationEvent event = new IntegrationEvent();
        event.setSourceSystem(sourceSystem);
        event.setEventType(eventType);
        event.setExternalReference(externalReference);
        event.setStatus(status);
        event.setClaimNumber(claimNumber);
        event.setPolicyNumber(policyNumber);
        event.setPayload(payload);
        return integrationEventRepository.save(event);
    }
}
