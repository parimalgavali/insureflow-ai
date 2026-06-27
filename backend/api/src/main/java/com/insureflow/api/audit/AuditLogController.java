package com.insureflow.api.audit;

import java.util.List;
import java.util.UUID;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
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
}
