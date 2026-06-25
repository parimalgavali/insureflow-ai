package com.insureflow.api.ai.triage;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.ai.triage.client.TriageClient;
import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.ResourceAccessException;

class ClaimTriageFailureIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void runTriageReturnsServiceUnavailableWhenAiServiceCannotBeReached() {
        createAutoPolicy("CUST-TRIAGE-DOWN-1001", "POL-TRIAGE-DOWN-1001");
        post("/policies/POL-TRIAGE-DOWN-1001/activate", Map.of());
        String claimNumber = (String) submitFnol("POL-TRIAGE-DOWN-1001").getBody().get("claimNumber");

        ResponseEntity<Map<String, Object>> response =
                post("/claims/" + claimNumber + "/triage", Map.of());

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(response.getBody())
                .containsEntry("status", 503)
                .containsEntry("error", "Service Unavailable")
                .containsEntry("message", "AI triage service is unavailable");
    }

    private void createAutoPolicy(String customerNumber, String policyNumber) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Morgan",
                "lastName", "Lee",
                "email", customerNumber.toLowerCase() + "@example.test",
                "country", "US"));

        post("/policies", Map.of(
                "customerNumber", customerNumber,
                "policyNumber", policyNumber,
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1450.00"),
                "currency", "USD"));

        post("/policies/" + policyNumber + "/coverages", Map.of(
                "coverageCode", "COLLISION",
                "coverageName", "Collision Coverage",
                "coverageType", "COLLISION",
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[]"));
    }

    private ResponseEntity<Map<String, Object>> submitFnol(String policyNumber) {
        return post("/claims/fnol", Map.of(
                "policyNumber", policyNumber,
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-24",
                "reportedAt", "2026-06-25T10:15:30Z",
                "lossLocation", "Columbus, OH",
                "description", "Rear-end collision with reported injury.",
                "estimatedLossAmount", new BigDecimal("12000.00")));
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }

    @TestConfiguration
    static class UnavailableTriageClientConfiguration {

        @Bean
        @Primary
        TriageClient triageClient() {
            return request -> {
                throw new ResourceAccessException("Connection refused");
            };
        }
    }
}
