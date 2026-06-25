package com.insureflow.api.ai.triage;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.ai.triage.api.dto.TriageScoreBlock;
import com.insureflow.api.ai.triage.api.dto.TriageScoreRequest;
import com.insureflow.api.ai.triage.api.dto.TriageScoreResponse;
import com.insureflow.api.ai.triage.client.TriageClient;
import com.insureflow.api.ai.triage.domain.TriageRiskLabel;
import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.List;
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

class ClaimTriageIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void runTriagePersistsResultAndRecordsTimelineEvent() {
        createAutoPolicy("CUST-TRIAGE-API-1001", "POL-TRIAGE-API-1001");
        post("/policies/POL-TRIAGE-API-1001/activate", Map.of());
        String claimNumber = (String) submitFnol("POL-TRIAGE-API-1001").getBody().get("claimNumber");

        ResponseEntity<Map<String, Object>> triageResponse =
                post("/claims/" + claimNumber + "/triage", Map.of());

        assertThat(triageResponse.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(triageResponse.getBody())
                .containsEntry("claimNumber", claimNumber)
                .containsEntry("severityLabel", "HIGH")
                .containsEntry("fraudRiskLabel", "LOW")
                .containsEntry("litigationRiskLabel", "MEDIUM")
                .containsEntry("recommendedQueue", "COMPLEX_CLAIMS")
                .containsEntry("humanReviewRequired", true);
        assertThat(reasonCodes(triageResponse))
                .containsExactly("INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE", "THIRD_PARTY_INVOLVED");

        ResponseEntity<List<Map<String, Object>>> events = restTemplate.exchange(
                baseUrl + "/claims/" + claimNumber + "/events",
                HttpMethod.GET,
                HttpEntity.EMPTY,
                LIST_MAP_RESPONSE);
        assertThat(events.getBody())
                .extracting(event -> event.get("eventType"))
                .contains("TRIAGE_COMPLETED");

        ResponseEntity<Map<String, Object>> fetchedTriage = restTemplate.exchange(
                baseUrl + "/claims/" + claimNumber + "/triage",
                HttpMethod.GET,
                HttpEntity.EMPTY,
                MAP_RESPONSE);
        assertThat(fetchedTriage.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(fetchedTriage.getBody())
                .containsEntry("claimNumber", claimNumber)
                .containsEntry("severityLabel", "HIGH")
                .containsEntry("recommendedQueue", "COMPLEX_CLAIMS");
    }

    private void createAutoPolicy(String customerNumber, String policyNumber) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Avery",
                "lastName", "Stone",
                "email", customerNumber.toLowerCase() + "@example.test",
                "country", "US"));

        post("/policies", Map.of(
                "customerNumber", customerNumber,
                "policyNumber", policyNumber,
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1550.00"),
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
                "description", "Rear-end collision with injury reported by the other driver.",
                "estimatedLossAmount", new BigDecimal("30000.00")));
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }

    @SuppressWarnings("unchecked")
    private List<String> reasonCodes(ResponseEntity<Map<String, Object>> response) {
        return (List<String>) response.getBody().get("reasonCodes");
    }

    @TestConfiguration
    static class StubTriageClientConfiguration {

        @Bean
        @Primary
        TriageClient triageClient() {
            return request -> new TriageScoreResponse(
                    request.claimId(),
                    request.claimNumber(),
                    "rule-based-triage",
                    "rules-v1",
                    new TriageScoreBlock(
                            TriageRiskLabel.HIGH,
                            new BigDecimal("0.8200"),
                            List.of("INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE")),
                    new TriageScoreBlock(TriageRiskLabel.LOW, new BigDecimal("0.1800"), List.of()),
                    new TriageScoreBlock(
                            TriageRiskLabel.MEDIUM,
                            new BigDecimal("0.4600"),
                            List.of("THIRD_PARTY_INVOLVED")),
                    "COMPLEX_CLAIMS",
                    true,
                    "Injury and high estimated damage require review.");
        }
    }
}
