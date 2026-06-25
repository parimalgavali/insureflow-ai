package com.insureflow.api.claims;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.claims.repository.ClaimEventRepository;
import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class FnolWorkflowIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Autowired
    private ClaimEventRepository claimEventRepository;

    @Test
    void successfulFnolCreatesSubmittedClaimAndTimelineEvents() {
        createAutoPolicy("CUST-FNOL-1001", "POL-FNOL-1001", "COLLISION");
        post("/policies/POL-FNOL-1001/activate", Map.of());

        ResponseEntity<Map<String, Object>> response = submitFnol("POL-FNOL-1001", "AUTO_COLLISION");

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody())
                .containsEntry("policyNumber", "POL-FNOL-1001")
                .containsEntry("claimType", "AUTO_COLLISION")
                .containsEntry("status", "SUBMITTED");
        assertThat((String) response.getBody().get("claimNumber")).startsWith("CLM-20260625-");
        assertThat(coverageValidation(response)).containsEntry("covered", true);

        String claimNumber = (String) response.getBody().get("claimNumber");
        assertThat(claimEventRepository.findByClaimClaimNumberOrderByCreatedAtAsc(claimNumber))
                .extracting(event -> event.getEventType().name())
                .containsExactly("FNOL_SUBMITTED", "COVERAGE_VALIDATED");
    }

    @Test
    void unknownPolicyReturns404() {
        ResponseEntity<Map<String, Object>> response = submitFnol("POL-FNOL-MISSING", "AUTO_COLLISION");

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getBody()).containsEntry("message", "Policy POL-FNOL-MISSING was not found");
    }

    @Test
    void inactivePolicyCreatesClaimWithCoverageIssue() {
        createAutoPolicy("CUST-FNOL-1002", "POL-FNOL-1002", "COLLISION");

        ResponseEntity<Map<String, Object>> response = submitFnol("POL-FNOL-1002", "AUTO_COLLISION");

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(coverageValidation(response)).containsEntry("covered", false);
        assertThat(reasons(response)).contains("POLICY_NOT_ACTIVE_ON_LOSS_DATE");
    }

    @Test
    void missingCoverageCreatesClaimWithCoverageIssue() {
        createAutoPolicy("CUST-FNOL-1003", "POL-FNOL-1003", "COMPREHENSIVE");
        post("/policies/POL-FNOL-1003/activate", Map.of());

        ResponseEntity<Map<String, Object>> response = submitFnol("POL-FNOL-1003", "AUTO_COLLISION");

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(reasons(response)).contains("COVERAGE_NOT_INCLUDED");
    }

    private void createAutoPolicy(String customerNumber, String policyNumber, String coverageType) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Taylor",
                "lastName", "Nguyen",
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
                "coverageCode", coverageType,
                "coverageName", coverageType + " Coverage",
                "coverageType", coverageType,
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[]"));
    }

    private ResponseEntity<Map<String, Object>> submitFnol(String policyNumber, String claimType) {
        return post("/claims/fnol", Map.of(
                "policyNumber", policyNumber,
                "claimType", claimType,
                "lossDate", "2026-06-24",
                "reportedAt", "2026-06-25T10:15:30Z",
                "lossLocation", "Columbus, OH",
                "description", "Rear-end collision at a stop light.",
                "estimatedLossAmount", new BigDecimal("9000.00")));
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }

    @SuppressWarnings("unchecked")
    private List<String> reasons(ResponseEntity<Map<String, Object>> response) {
        return (List<String>) coverageValidation(response).get("reasons");
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> coverageValidation(ResponseEntity<Map<String, Object>> response) {
        return (Map<String, Object>) response.getBody().get("coverageValidation");
    }
}
