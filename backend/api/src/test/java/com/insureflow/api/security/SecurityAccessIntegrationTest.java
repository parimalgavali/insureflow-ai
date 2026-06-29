package com.insureflow.api.security;

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
import org.springframework.boot.test.web.client.TestRestTemplate;

class SecurityAccessIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private final TestRestTemplate client = new TestRestTemplate();

    @Test
    void protectedApiRejectsRequestsWithoutToken() {
        ResponseEntity<Map<String, Object>> response = client.exchange(
                baseUrl + "/claims/CLM-DOES-NOT-EXIST", HttpMethod.GET, HttpEntity.EMPTY, MAP_RESPONSE);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void actuatorHealthAndPrometheusMetricsArePublicForLocalScraping() {
        ResponseEntity<String> health = client.exchange(
                "http://localhost:" + port + "/actuator/health",
                HttpMethod.GET,
                HttpEntity.EMPTY,
                String.class);
        ResponseEntity<String> metrics = client.exchange(
                "http://localhost:" + port + "/actuator/prometheus",
                HttpMethod.GET,
                HttpEntity.EMPTY,
                String.class);

        assertThat(health.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(health.getBody()).contains("\"status\":\"UP\"");
        assertThat(metrics.getStatusCode()).as(metrics.getBody()).isEqualTo(HttpStatus.OK);
        assertThat(metrics.getBody()).contains("jvm_memory_used_bytes");
    }

    @Test
    void rolesControlBackendIntegrationAndGovernanceAccess() {
        String adjusterToken = token("adjuster-user", "ADJUSTER");
        String integrationToken = token("integration-client", "INTEGRATION");
        String auditorToken = token("audit-user", "AUDITOR");
        String adminToken = token("admin-user", "ADMIN");

        assertThat(getMap("/claims/CLM-DOES-NOT-EXIST", adjusterToken).getStatusCode())
                .isEqualTo(HttpStatus.NOT_FOUND);

        assertThat(getMap("http://localhost:" + port + "/integration/v1/claims/CLM-DOES-NOT-EXIST", integrationToken)
                        .getStatusCode())
                .isEqualTo(HttpStatus.NOT_FOUND);

        assertThat(getList("/governance/model-versions", integrationToken).getStatusCode())
                .isEqualTo(HttpStatus.FORBIDDEN);

        assertThat(getList("/governance/model-versions", auditorToken).getStatusCode())
                .isEqualTo(HttpStatus.OK);

        assertThat(getMap("http://localhost:" + port + "/integration/v1/claims/CLM-DOES-NOT-EXIST", adminToken)
                        .getStatusCode())
                .isEqualTo(HttpStatus.NOT_FOUND);
    }

    private String token(String subject, String role) {
        ResponseEntity<Map<String, Object>> response = client.exchange(
                baseUrl + "/auth/dev-token",
                HttpMethod.POST,
                new HttpEntity<>(Map.of("subject", subject, "roles", List.of(role))),
                MAP_RESPONSE);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        return (String) response.getBody().get("token");
    }

    private ResponseEntity<Map<String, Object>> getMap(String pathOrUrl, String token) {
        String url = pathOrUrl.startsWith("http") ? pathOrUrl : baseUrl + pathOrUrl;
        return client.exchange(url, HttpMethod.GET, authEntity(token), MAP_RESPONSE);
    }

    private ResponseEntity<List<Map<String, Object>>> getList(String path, String token) {
        return client.exchange(baseUrl + path, HttpMethod.GET, authEntity(token), LIST_RESPONSE);
    }

    private HttpEntity<Void> authEntity(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return new HttpEntity<>(headers);
    }
}
