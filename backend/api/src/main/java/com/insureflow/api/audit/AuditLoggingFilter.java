package com.insureflow.api.audit;

import com.insureflow.api.security.JwtPrincipal;
import com.insureflow.api.security.JwtService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
public class AuditLoggingFilter extends OncePerRequestFilter {

    private static final UUID NIL_UUID = UUID.fromString("00000000-0000-0000-0000-000000000000");

    private final AuditLogRepository auditLogRepository;
    private final JwtService jwtService;

    public AuditLoggingFilter(AuditLogRepository auditLogRepository, JwtService jwtService) {
        this.auditLogRepository = auditLogRepository;
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            filterChain.doFilter(request, response);
        } finally {
            if (!shouldSkip(request)) {
                auditLogRepository.save(toAuditLog(request, response));
            }
        }
    }

    private boolean shouldSkip(HttpServletRequest request) {
        String path = request.getRequestURI();
        return path.equals("/api/v1/health")
                || path.startsWith("/swagger-ui")
                || path.startsWith("/v3/api-docs")
                || path.equals("/api/v1/auth/dev-token");
    }

    private AuditLog toAuditLog(HttpServletRequest request, HttpServletResponse response) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        JwtPrincipal principal = authentication != null && authentication.getPrincipal() instanceof JwtPrincipal jwt
                ? jwt
                : principalFromHeader(request);
        AuditLog auditLog = new AuditLog();
        auditLog.setActorType(principal == null ? "ANONYMOUS" : "USER");
        auditLog.setActorId(principal == null ? null : principal.subject());
        auditLog.setAction(request.getMethod() + " " + request.getRequestURI());
        auditLog.setEntityType(entityType(request.getRequestURI()));
        auditLog.setEntityId(NIL_UUID);
        auditLog.setCorrelationId((String) request.getAttribute(CorrelationIdFilter.ATTRIBUTE));
        auditLog.setAfterState(Map.of(
                "method", request.getMethod(),
                "path", request.getRequestURI(),
                "status", response.getStatus(),
                "sourceIp", request.getRemoteAddr()));
        return auditLog;
    }

    private JwtPrincipal principalFromHeader(HttpServletRequest request) {
        String authorization = request.getHeader("Authorization");
        if (authorization == null || !authorization.startsWith("Bearer ")) {
            return null;
        }
        try {
            return jwtService.validate(authorization.substring(7));
        } catch (RuntimeException exception) {
            return null;
        }
    }

    private String entityType(String path) {
        String[] parts = path.split("/");
        if (parts.length > 3 && "api".equals(parts[1])) {
            return parts[3].toUpperCase();
        }
        if (parts.length > 2 && "integration".equals(parts[1])) {
            return "INTEGRATION";
        }
        return "UNKNOWN";
    }
}
