package com.insureflow.api.humanreview;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;

class HumanReviewIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void overrideRequiresReasonAndPersistsHumanReview() {
        String token = token("human-review-adjuster", "ADJUSTER");
        UUID reviewerId = UUID.randomUUID();
        jdbcTemplate.update(
                """
                insert into adjusters (id, employee_number, first_name, last_name, email, role)
                values (?, ?, 'Riley', 'Shah', ?, 'SENIOR_ADJUSTER')
                """,
                reviewerId,
                "EMP-" + reviewerId,
                "riley." + reviewerId + "@example.test");

        String claimNumber = createSubmittedClaim(token);

        ResponseEntity<Map<String, Object>> missingReason = post(
                "/claims/" + claimNumber + "/human-reviews",
                Map.of(
                        "reviewerAdjusterId", reviewerId.toString(),
                        "decision", "OVERRIDE_AI_RECOMMENDATION",
                        "notes", "Override attempted without a reason."),
                token);
        assertThat(missingReason.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);

        ResponseEntity<Map<String, Object>> override = post(
                "/claims/" + claimNumber + "/human-reviews",
                Map.of(
                        "reviewerAdjusterId", reviewerId.toString(),
                        "decision", "OVERRIDE_AI_RECOMMENDATION",
                        "overrideReason", "Police report contradicts the AI triage summary.",
                        "notes", "Senior adjuster reviewed supporting documents."),
                token);
        assertThat(override.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(override.getBody())
                .containsEntry("claimNumber", claimNumber)
                .containsEntry("decision", "OVERRIDE_AI_RECOMMENDATION")
                .containsEntry("overrideReason", "Police report contradicts the AI triage summary.");

        ResponseEntity<List<Map<String, Object>>> reviews =
                restTemplate.exchange(
                        baseUrl + "/claims/" + claimNumber + "/human-reviews",
                        HttpMethod.GET,
                        authEntity(token),
                        LIST_RESPONSE);
        assertThat(reviews.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(reviews.getBody()).hasSize(1);
    }

    private String createSubmittedClaim(String token) {
        String suffix = Long.toString(System.nanoTime());
        post("/customers", Map.of(
                "customerNumber", "CUST-HR-" + suffix,
                "firstName", "Morgan",
                "lastName", "Rivera",
                "email", "morgan." + suffix + "@example.test",
                "country", "US"), token);
        post("/policies", Map.of(
                "customerNumber", "CUST-HR-" + suffix,
                "policyNumber", "POL-HR-" + suffix,
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1500.00"),
                "currency", "USD"), token);
        post("/policies/POL-HR-" + suffix + "/coverages", Map.of(
                "coverageCode", "COLLISION",
                "coverageName", "Collision Coverage",
                "coverageType", "COLLISION",
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[]"), token);
        post("/policies/POL-HR-" + suffix + "/activate", Map.of(), token);
        return (String) post("/claims/fnol", Map.of(
                "policyNumber", "POL-HR-" + suffix,
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-24",
                "reportedAt", "2026-06-25T10:15:30Z",
                "lossLocation", "Columbus, OH",
                "description", "Rear-end collision for human review.",
                "estimatedLossAmount", new BigDecimal("9000.00")), token).getBody().get("claimNumber");
    }

    private String token(String subject, String role) {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                baseUrl + "/auth/dev-token",
                HttpMethod.POST,
                new HttpEntity<>(Map.of("subject", subject, "roles", List.of(role))),
                MAP_RESPONSE);
        return (String) response.getBody().get("token");
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request, String token) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request, authHeaders(token)), MAP_RESPONSE);
    }

    private HttpEntity<Void> authEntity(String token) {
        return new HttpEntity<>(authHeaders(token));
    }

    private HttpHeaders authHeaders(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return headers;
    }
}
