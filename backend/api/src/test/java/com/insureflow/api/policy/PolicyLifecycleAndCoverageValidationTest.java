package com.insureflow.api.policy;

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

class PolicyLifecycleAndCoverageValidationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void draftPolicyActivatesAndCancelledPolicyCannotActivateAgain() {
        createAutoPolicyWithCollisionCoverage("CUST-LIFE-1001", "POL-LIFE-1001");

        ResponseEntity<Map<String, Object>> activated = post("/policies/POL-LIFE-1001/activate", Map.of());
        assertThat(activated.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(activated.getBody()).containsEntry("status", "ACTIVE");

        ResponseEntity<Map<String, Object>> cancelled = post("/policies/POL-LIFE-1001/cancel", Map.of());
        assertThat(cancelled.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(cancelled.getBody()).containsEntry("status", "CANCELLED");

        ResponseEntity<Map<String, Object>> reactivated = post("/policies/POL-LIFE-1001/activate", Map.of());
        assertThat(reactivated.getStatusCode()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY);
        assertThat(reactivated.getBody()).containsEntry("message", "Only DRAFT policies can be activated");
    }

    @Test
    void activePolicyWithMatchingCoverageReturnsCovered() {
        createAutoPolicyWithCollisionCoverage("CUST-LIFE-1002", "POL-LIFE-1002");
        post("/policies/POL-LIFE-1002/activate", Map.of());

        ResponseEntity<Map<String, Object>> response = post("/policies/POL-LIFE-1002/coverage-check", Map.of(
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-01",
                "estimatedLossAmount", new BigDecimal("9000.00")));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody())
                .containsEntry("covered", true)
                .containsEntry("policyStatus", "ACTIVE")
                .containsEntry("coverageType", "COLLISION");
        assertThat((List<?>) response.getBody().get("reasons")).isEmpty();
        assertThat((List<?>) response.getBody().get("warnings")).isEmpty();
    }

    @Test
    void expiredPolicyReturnsNotCoveredReason() {
        createAutoPolicyWithCollisionCoverage("CUST-LIFE-1003", "POL-LIFE-1003");
        post("/policies/POL-LIFE-1003/activate", Map.of());
        post("/policies/POL-LIFE-1003/expire", Map.of());

        ResponseEntity<Map<String, Object>> response = post("/policies/POL-LIFE-1003/coverage-check", Map.of(
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-01",
                "estimatedLossAmount", new BigDecimal("9000.00")));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsEntry("covered", false);
        assertThat(stringList(response, "reasons"))
                .contains("POLICY_NOT_ACTIVE_ON_LOSS_DATE");
    }

    @Test
    void overLimitClaimReturnsCoveredWithWarning() {
        createAutoPolicyWithCollisionCoverage("CUST-LIFE-1004", "POL-LIFE-1004");
        post("/policies/POL-LIFE-1004/activate", Map.of());

        ResponseEntity<Map<String, Object>> response = post("/policies/POL-LIFE-1004/coverage-check", Map.of(
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-01",
                "estimatedLossAmount", new BigDecimal("40000.00")));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsEntry("covered", true);
        assertThat(stringList(response, "warnings"))
                .contains("ESTIMATED_LOSS_EXCEEDS_LIMIT");
    }

    @Test
    void coverageOutsideCoverageDatesReturnsNotCoveredReason() {
        createAutoPolicyWithFutureCollisionCoverage("CUST-LIFE-1006", "POL-LIFE-1006");
        post("/policies/POL-LIFE-1006/activate", Map.of());

        ResponseEntity<Map<String, Object>> response = post("/policies/POL-LIFE-1006/coverage-check", Map.of(
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-01",
                "estimatedLossAmount", new BigDecimal("9000.00")));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).containsEntry("covered", false);
        assertThat(stringList(response, "reasons"))
                .contains("COVERAGE_NOT_ACTIVE_ON_LOSS_DATE");
    }

    @Test
    void activePolicyCanRenewIntoDraftPolicyWithCopiedCoverage() {
        createAutoPolicyWithCollisionCoverage("CUST-LIFE-1005", "POL-LIFE-1005");
        post("/policies/POL-LIFE-1005/activate", Map.of());

        ResponseEntity<Map<String, Object>> renewed = post("/policies/POL-LIFE-1005/renew", Map.of());

        assertThat(renewed.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(renewed.getBody()).containsEntry("status", "DRAFT");
        assertThat((String) renewed.getBody().get("policyNumber")).startsWith("POL-LIFE-1005-REN");
        assertThat((Iterable<?>) renewed.getBody().get("coverages")).hasSize(1);
    }

    private void createAutoPolicyWithCollisionCoverage(String customerNumber, String policyNumber) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Riley",
                "lastName", "Morgan",
                "email", customerNumber.toLowerCase() + "@example.test",
                "country", "US"));

        post("/policies", Map.of(
                "customerNumber", customerNumber,
                "policyNumber", policyNumber,
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1500.00"),
                "currency", "USD"));

        post("/policies/" + policyNumber + "/coverages", Map.of(
                "coverageCode", "COLLISION",
                "coverageName", "Collision Coverage",
                "coverageType", "COLLISION",
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[\"racing\"]"));
    }

    private void createAutoPolicyWithFutureCollisionCoverage(String customerNumber, String policyNumber) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Riley",
                "lastName", "Morgan",
                "email", customerNumber.toLowerCase() + "@example.test",
                "country", "US"));

        post("/policies", Map.of(
                "customerNumber", customerNumber,
                "policyNumber", policyNumber,
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1500.00"),
                "currency", "USD"));

        post("/policies/" + policyNumber + "/coverages", Map.of(
                "coverageCode", "COLLISION",
                "coverageName", "Collision Coverage",
                "coverageType", "COLLISION",
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-07-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[\"racing\"]"));
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }

    @SuppressWarnings("unchecked")
    private List<String> stringList(ResponseEntity<Map<String, Object>> response, String key) {
        return (List<String>) response.getBody().get(key);
    }
}
