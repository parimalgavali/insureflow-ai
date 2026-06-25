package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.ClaimEvent;
import com.insureflow.api.claims.domain.ClaimEventType;
import java.time.Instant;
import java.util.Map;

public record ClaimEventResponse(
        ClaimEventType eventType,
        String eventSource,
        String description,
        Map<String, Object> payload,
        Instant createdAt) {

    public static ClaimEventResponse from(ClaimEvent event) {
        return new ClaimEventResponse(
                event.getEventType(),
                event.getEventSource(),
                event.getDescription(),
                event.getPayload(),
                event.getCreatedAt());
    }
}
