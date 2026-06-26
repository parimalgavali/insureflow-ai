package com.insureflow.api.integration;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class IntegrationApiIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    @SuppressWarnings("unchecked")
    void supportsGuidewireStylePolicyClaimStatusReserveAndWebhookFlow() {
        String suffix = Long.toString(System.nanoTime());
        String customerNumber = "INT-CUST-" + suffix;
        String policyNumber = "INT-POL-" + suffix;

        ResponseEntity<Map<String, Object>> policySync = postIntegration("/policies/sync", Map.of(
                "sourceSystem", "PolicyCenter",
                "externalReference", "PC-POL-" + suffix,
                "customer", Map.of(
                        "customerNumber", customerNumber,
                        "firstName", "Avery",
                        "lastName", "Stone",
                        "email", "avery." + suffix + "@example.test",
                        "country", "US"),
                "policy", Map.of(
                        "policyNumber", policyNumber,
                        "policyType", "PERSONAL_AUTO",
                        "effectiveDate", "2026-01-01",
                        "expirationDate", "2027-01-01",
                        "premiumAmount", new BigDecimal("1425.00"),
                        "currency", "USD",
                        "activate", true),
                "coverages", List.of(Map.of(
                        "coverageCode", "COLLISION",
                        "coverageName", "Collision Coverage",
                        "coverageType", "COLLISION",
                        "limitAmount", new BigDecimal("30000.00"),
                        "deductibleAmount", new BigDecimal("500.00"),
                        "effectiveDate", "2026-01-01",
                        "expirationDate", "2027-01-01",
                        "exclusions", "[]"))));
        assertThat(policySync.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(policySync.getBody()).containsEntry("policyNumber", policyNumber);
        assertThat(policySync.getBody()).containsEntry("status", "ACTIVE");

        ResponseEntity<Map<String, Object>> claimCreate = postIntegration("/claims", Map.of(
                "sourceSystem", "ClaimCenter",
                "externalReference", "CC-CLAIM-" + suffix,
                "claim", Map.of(
                        "policyNumber", policyNumber,
                        "claimType", "AUTO_COLLISION",
                        "lossDate", "2026-06-24",
                        "reportedAt", "2026-06-25T10:15:30Z",
                        "lossLocation", "Columbus, OH",
                        "description", "Rear-end collision reported through integration API.",
                        "estimatedLossAmount", new BigDecimal("9200.00"))));
        assertThat(claimCreate.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        String claimNumber = (String) claimCreate.getBody().get("claimNumber");
        assertThat(claimNumber).startsWith("CLM-");

        ResponseEntity<Map<String, Object>> lookup = getIntegration("/claims/" + claimNumber);
        assertThat(lookup.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(lookup.getBody()).containsEntry("claimNumber", claimNumber);
        assertThat((Map<String, Object>) lookup.getBody().get("policy")).containsEntry("policyNumber", policyNumber);

        ResponseEntity<Map<String, Object>> statusUpdate = postIntegration("/claims/" + claimNumber + "/status", Map.of(
                "sourceSystem", "ClaimCenter",
                "externalReference", "CC-STATUS-" + suffix,
                "targetStatus", "UNDER_REVIEW",
                "reason", "Integration queue assignment"));
        assertThat(statusUpdate.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(statusUpdate.getBody()).containsEntry("status", "UNDER_REVIEW");

        ResponseEntity<Map<String, Object>> invalidStatus = postIntegration("/claims/" + claimNumber + "/status", Map.of(
                "sourceSystem", "ClaimCenter",
                "externalReference", "CC-STATUS-BAD-" + suffix,
                "targetStatus", "PAID",
                "reason", "Cannot jump directly to paid"));
        assertThat(invalidStatus.getStatusCode()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY);

        ResponseEntity<Map<String, Object>> reserve = postIntegration("/claims/" + claimNumber + "/reserves", Map.of(
                "sourceSystem", "ClaimCenter",
                "externalReference", "CC-RES-" + suffix,
                "coverageCode", "COLLISION",
                "reserveAmount", new BigDecimal("8500.00"),
                "currency", "USD",
                "reason", "Initial collision reserve"));
        assertThat(reserve.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(reserve.getBody()).containsEntry("claimNumber", claimNumber);
        assertThat(reserve.getBody()).containsEntry("reserveAmount", 8500.00);

        ResponseEntity<List<Map<String, Object>>> events = getApiList("/claims/" + claimNumber + "/events");
        assertThat(events.getBody())
                .extracting(event -> event.get("eventType"))
                .contains("STATUS_CHANGED", "RESERVE_UPDATED");

        ResponseEntity<Map<String, Object>> webhook = postIntegration("/webhooks/claim-triaged", Map.of(
                "sourceSystem", "TriageService",
                "externalReference", "TRIAGE-" + suffix,
                "claimNumber", claimNumber,
                "severityLabel", "HIGH",
                "fraudRiskLabel", "MEDIUM",
                "recommendedQueue", "SENIOR_ADJUSTER",
                "humanReviewRequired", true));
        assertThat(webhook.getStatusCode()).isEqualTo(HttpStatus.ACCEPTED);
        assertThat(webhook.getBody()).containsEntry("accepted", true);
        assertThat(webhook.getBody()).containsEntry("claimNumber", claimNumber);
    }

    @Test
    void rejectsInvalidIntegrationPayloadsWithConsistentValidationErrors() {
        ResponseEntity<Map<String, Object>> response = postIntegration("/policies/sync", Map.of(
                "sourceSystem", "",
                "externalReference", "",
                "coverages", List.of()));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).containsEntry("status", 400);
        assertThat((String) response.getBody().get("message")).contains("sourceSystem");
    }

    private ResponseEntity<Map<String, Object>> postIntegration(String path, Map<String, Object> request) {
        return restTemplate.exchange(
                "http://localhost:" + port + "/integration/v1" + path,
                HttpMethod.POST,
                new HttpEntity<>(request),
                MAP_RESPONSE);
    }

    private ResponseEntity<Map<String, Object>> getIntegration(String path) {
        return restTemplate.exchange(
                "http://localhost:" + port + "/integration/v1" + path, HttpMethod.GET, HttpEntity.EMPTY, MAP_RESPONSE);
    }

    private ResponseEntity<List<Map<String, Object>>> getApiList(String path) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.GET, HttpEntity.EMPTY, LIST_RESPONSE);
    }
}
