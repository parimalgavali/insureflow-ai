package com.insureflow.api.audit;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public record AuditLogResponse(
        UUID id,
        String actorType,
        String actorId,
        String action,
        String entityType,
        UUID entityId,
        String correlationId,
        Map<String, Object> afterState,
        Instant createdAt) {

    static AuditLogResponse from(AuditLog auditLog) {
        return new AuditLogResponse(
                auditLog.getId(),
                auditLog.getActorType(),
                auditLog.getActorId(),
                auditLog.getAction(),
                auditLog.getEntityType(),
                auditLog.getEntityId(),
                auditLog.getCorrelationId(),
                auditLog.getAfterState(),
                auditLog.getCreatedAt());
    }
}
