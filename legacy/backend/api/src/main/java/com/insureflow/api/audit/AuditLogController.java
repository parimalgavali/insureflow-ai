package com.insureflow.api.audit;

import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/audit")
class AuditLogController {

    private final AuditLogRepository auditLogRepository;

    AuditLogController(AuditLogRepository auditLogRepository) {
        this.auditLogRepository = auditLogRepository;
    }

    @GetMapping("/entity/{entityType}/{entityId}")
    List<AuditLogResponse> byEntity(@PathVariable String entityType, @PathVariable UUID entityId) {
        return auditLogRepository.findByEntityTypeAndEntityIdOrderByCreatedAtDesc(entityType, entityId).stream()
                .map(AuditLogResponse::from)
                .toList();
    }

    @GetMapping("/events")
    List<AuditLogResponse> events(
            @RequestParam(required = false) String entityType,
            @RequestParam(required = false) String actorId,
            @RequestParam(required = false) String action,
            @RequestParam(required = false) String correlationId,
            @RequestParam(defaultValue = "50") int limit) {
        int cappedLimit = Math.max(1, Math.min(limit, 100));
        String normalizedEntityType = normalize(entityType);
        String normalizedActorId = normalize(actorId);
        String normalizedAction = normalize(action);
        String normalizedCorrelationId = normalize(correlationId);
        return auditLogRepository.findAll(Sort.by(Sort.Direction.DESC, "createdAt")).stream()
                .filter(log -> matches(normalizedEntityType, log.getEntityType()))
                .filter(log -> matches(normalizedActorId, log.getActorId()))
                .filter(log -> normalizedAction == null || log.getAction().contains(normalizedAction))
                .filter(log -> matches(normalizedCorrelationId, log.getCorrelationId()))
                .limit(cappedLimit)
                .map(AuditLogResponse::from)
                .toList();
    }

    private String normalize(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        return value.trim();
    }

    private boolean matches(String filter, String value) {
        return filter == null || filter.equals(value);
    }
}
