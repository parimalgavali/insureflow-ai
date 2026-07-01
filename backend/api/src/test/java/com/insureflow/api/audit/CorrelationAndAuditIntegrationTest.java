package com.insureflow.api.audit;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.support.ApiIntegrationTest;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class CorrelationAndAuditIntegrationTest extends ApiIntegrationTest {

    private static final String NIL_UUID = "00000000-0000-0000-0000-000000000000";
    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void correlationIdIsReturnedOnErrorsAndProtectedRequestsAreAudited() {
        String adjusterToken = token("adjuster-audit-user", "ADJUSTER");
        String auditorToken = token("auditor-audit-user", "AUDITOR");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(adjusterToken);
        headers.set("X-Correlation-Id", "corr-phase-11-001");

        ResponseEntity<Map<String, Object>> missingClaim = restTemplate.exchange(
                baseUrl + "/claims/CLM-MISSING-AUDIT", HttpMethod.GET, new HttpEntity<>(headers), MAP_RESPONSE);

        assertThat(missingClaim.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(missingClaim.getHeaders().getFirst("X-Correlation-Id")).isEqualTo("corr-phase-11-001");
        assertThat(missingClaim.getBody()).containsEntry("correlationId", "corr-phase-11-001");

        ResponseEntity<List<Map<String, Object>>> auditLogs =
                restTemplate.exchange(
                        baseUrl + "/audit/entity/CLAIMS/" + NIL_UUID,
                        HttpMethod.GET,
                        authEntity(auditorToken),
                        LIST_RESPONSE);

        assertThat(auditLogs.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(auditLogs.getBody())
                .anySatisfy(log -> {
                    assertThat(log).containsEntry("actorId", "adjuster-audit-user");
                    assertThat(log).containsEntry("correlationId", "corr-phase-11-001");
                });
    }

    @Test
    void auditorCanSearchAuditEventsByActorEntityAndCorrelationId() {
        String adjusterToken = token("phase-19-adjuster", "ADJUSTER");
        String auditorToken = token("phase-19-auditor", "AUDITOR");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(adjusterToken);
        headers.set("X-Correlation-Id", "corr-phase-19-001");

        restTemplate.exchange(
                baseUrl + "/claims/CLM-PHASE-19-MISSING",
                HttpMethod.GET,
                new HttpEntity<>(headers),
                MAP_RESPONSE);

        ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                baseUrl
                        + "/audit/events?entityType=CLAIMS&actorId=phase-19-adjuster"
                        + "&correlationId=corr-phase-19-001&limit=10",
                HttpMethod.GET,
                authEntity(auditorToken),
                LIST_RESPONSE);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .anySatisfy(log -> {
                    assertThat(log).containsEntry("actorId", "phase-19-adjuster");
                    assertThat(log).containsEntry("entityType", "CLAIMS");
                    assertThat(log).containsEntry("correlationId", "corr-phase-19-001");
                });
    }

    private String token(String subject, String role) {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                baseUrl + "/auth/dev-token",
                HttpMethod.POST,
                new HttpEntity<>(Map.of("subject", subject, "roles", List.of(role))),
                MAP_RESPONSE);
        return (String) response.getBody().get("token");
    }

    private HttpEntity<Void> authEntity(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return new HttpEntity<>(headers);
    }
}
