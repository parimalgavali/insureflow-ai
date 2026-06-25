package com.insureflow.api.claims;

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

class ClaimOperationsIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void managesClaimTimelineStatusNotesAndDocuments() {
        String claimNumber = createSubmittedClaim("CUST-OPS-1001", "POL-OPS-1001");

        ResponseEntity<Map<String, Object>> fetched = getMap("/claims/" + claimNumber);
        assertThat(fetched.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(fetched.getBody()).containsEntry("claimNumber", claimNumber);

        ResponseEntity<List<Map<String, Object>>> initialEvents = getList("/claims/" + claimNumber + "/events");
        assertThat(initialEvents.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(initialEvents.getBody())
                .extracting(event -> event.get("eventType"))
                .containsExactly("FNOL_SUBMITTED", "COVERAGE_VALIDATED");

        ResponseEntity<Map<String, Object>> statusChange = post("/claims/" + claimNumber + "/status", Map.of(
                "targetStatus", "UNDER_REVIEW",
                "reason", "Initial adjuster review"));
        assertThat(statusChange.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(statusChange.getBody()).containsEntry("status", "UNDER_REVIEW");

        ResponseEntity<Map<String, Object>> invalidTransition = post("/claims/" + claimNumber + "/status", Map.of(
                "targetStatus", "PAID",
                "reason", "Cannot jump to paid"));
        assertThat(invalidTransition.getStatusCode()).isEqualTo(HttpStatus.UNPROCESSABLE_ENTITY);
        assertThat((String) invalidTransition.getBody().get("message")).contains("Invalid claim status transition");

        ResponseEntity<Map<String, Object>> note = post("/claims/" + claimNumber + "/notes", Map.of(
                "noteType", "GENERAL",
                "body", "Customer uploaded repair estimate."));
        assertThat(note.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(note.getBody()).containsEntry("noteType", "GENERAL");

        ResponseEntity<List<Map<String, Object>>> notes = getList("/claims/" + claimNumber + "/notes");
        assertThat(notes.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(notes.getBody()).hasSize(1);

        ResponseEntity<Map<String, Object>> document = post("/claims/" + claimNumber + "/documents", Map.of(
                "documentType", "REPAIR_INVOICE",
                "fileName", "repair-invoice.txt",
                "storageUri", "memory://repair-invoice.txt",
                "contentType", "text/plain",
                "extractedMetadata", Map.of("vendor", "Example Auto Body")));
        assertThat(document.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(document.getBody()).containsEntry("documentType", "REPAIR_INVOICE");

        ResponseEntity<List<Map<String, Object>>> documents = getList("/claims/" + claimNumber + "/documents");
        assertThat(documents.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(documents.getBody()).hasSize(1);

        ResponseEntity<List<Map<String, Object>>> finalEvents = getList("/claims/" + claimNumber + "/events");
        assertThat(finalEvents.getBody())
                .extracting(event -> event.get("eventType"))
                .contains("STATUS_CHANGED", "NOTE_ADDED", "DOCUMENT_ADDED");
    }

    private String createSubmittedClaim(String customerNumber, String policyNumber) {
        post("/customers", Map.of(
                "customerNumber", customerNumber,
                "firstName", "Morgan",
                "lastName", "Rivera",
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
                "exclusions", "[]"));
        post("/policies/" + policyNumber + "/activate", Map.of());
        ResponseEntity<Map<String, Object>> fnol = post("/claims/fnol", Map.of(
                "policyNumber", policyNumber,
                "claimType", "AUTO_COLLISION",
                "lossDate", "2026-06-24",
                "reportedAt", "2026-06-25T10:15:30Z",
                "lossLocation", "Columbus, OH",
                "description", "Rear-end collision at a stop light.",
                "estimatedLossAmount", new BigDecimal("9000.00")));
        return (String) fnol.getBody().get("claimNumber");
    }

    private ResponseEntity<Map<String, Object>> post(String path, Map<String, Object> request) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.POST, new HttpEntity<>(request), MAP_RESPONSE);
    }

    private ResponseEntity<Map<String, Object>> getMap(String path) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.GET, HttpEntity.EMPTY, MAP_RESPONSE);
    }

    private ResponseEntity<List<Map<String, Object>>> getList(String path) {
        return restTemplate.exchange(baseUrl + path, HttpMethod.GET, HttpEntity.EMPTY, LIST_RESPONSE);
    }
}
