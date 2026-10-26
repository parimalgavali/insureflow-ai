package com.insureflow.api.policy;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.support.ApiIntegrationTest;
import java.math.BigDecimal;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class PolicyApiIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void createsCustomerPolicyCoverageAndFetchesPolicy() {
        ResponseEntity<Map<String, Object>> customer = post("/customers", Map.of(
                "customerNumber", "CUST-API-1001",
                "firstName", "Maya",
                "lastName", "Chen",
                "email", "maya.chen@example.test",
                "phone", "555-0101",
                "addressLine1", "10 Lake Road",
                "city", "Madison",
                "state", "WI",
                "postalCode", "53703",
                "country", "US"));

        assertThat(customer.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(customer.getBody()).containsEntry("customerNumber", "CUST-API-1001");

        ResponseEntity<Map<String, Object>> policy = post("/policies", Map.of(
                "customerNumber", "CUST-API-1001",
                "policyNumber", "POL-API-1001",
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1400.00"),
                "currency", "USD"));

        assertThat(policy.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(policy.getBody())
                .containsEntry("policyNumber", "POL-API-1001")
                .containsEntry("status", "DRAFT");

        ResponseEntity<Map<String, Object>> coverage = post("/policies/POL-API-1001/coverages", Map.of(
                "coverageCode", "COLLISION",
                "coverageName", "Collision Coverage",
                "coverageType", "COLLISION",
                "limitAmount", new BigDecimal("25000.00"),
                "deductibleAmount", new BigDecimal("500.00"),
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "exclusions", "[\"racing\"]"));

        assertThat(coverage.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(coverage.getBody()).containsEntry("coverageType", "COLLISION");

        ResponseEntity<Map<String, Object>> fetched = restTemplate.exchange(
                baseUrl + "/policies/POL-API-1001", HttpMethod.GET, HttpEntity.EMPTY, MAP_RESPONSE);

        assertThat(fetched.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(fetched.getBody()).containsEntry("policyNumber", "POL-API-1001");
        assertThat(fetched.getBody()).containsEntry("customerNumber", "CUST-API-1001");
        assertThat((Iterable<?>) fetched.getBody().get("coverages")).hasSize(1);
    }

    @Test
    void creatingPolicyForUnknownCustomerReturns404() {
        ResponseEntity<Map<String, Object>> response = post("/policies", Map.of(
                "customerNumber", "CUST-MISSING",
                "policyNumber", "POL-MISSING-CUSTOMER",
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2026-01-01",
                "expirationDate", "2027-01-01",
                "premiumAmount", new BigDecimal("1400.00"),
                "currency", "USD"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getBody()).containsEntry("message", "Customer CUST-MISSING was not found");
    }

    @Test
    void creatingPolicyWithInvalidDatesReturns400() {
        post("/customers", Map.of(
                "customerNumber", "CUST-API-1002",
                "firstName", "Noah",
                "lastName", "Patel",
                "email", "noah.patel@example.test",
                "country", "US"));

        ResponseEntity<Map<String, Object>> response = post("/policies", Map.of(
                "customerNumber", "CUST-API-1002",
                "policyNumber", "POL-BAD-DATES",
                "policyType", "PERSONAL_AUTO",
                "effectiveDate", "2027-01-01",
                "expirationDate", "2026-01-01",
                "premiumAmount", new BigDecimal("1400.00"),
                "currency", "USD"));

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat((String) response.getBody().get("message")).contains("effectiveDate must be before expirationDate");
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }
}
