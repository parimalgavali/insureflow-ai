package com.insureflow.api.claims;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimDocument;
import com.insureflow.api.claims.domain.ClaimEvent;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimNote;
import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.domain.ClaimType;
import com.insureflow.api.claims.repository.ClaimDocumentRepository;
import com.insureflow.api.claims.repository.ClaimEventRepository;
import com.insureflow.api.claims.repository.ClaimNoteRepository;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.policy.domain.Customer;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.domain.PolicyType;
import com.insureflow.api.policy.repository.CustomerRepository;
import com.insureflow.api.policy.repository.PolicyRepository;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
class ClaimRepositoryTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private PolicyRepository policyRepository;

    @Autowired
    private ClaimRepository claimRepository;

    @Autowired
    private ClaimEventRepository claimEventRepository;

    @Autowired
    private ClaimNoteRepository claimNoteRepository;

    @Autowired
    private ClaimDocumentRepository claimDocumentRepository;

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.test.database.replace", () -> "none");
    }

    @Test
    void savesAndFindsClaimTimelineNotesAndDocuments() {
        Customer customer = new Customer();
        customer.setCustomerNumber("CUST-CLAIM-1001");
        customer.setFirstName("Jordan");
        customer.setLastName("Lee");
        customer.setEmail("jordan.lee@example.test");
        customer.setCountry("US");
        customerRepository.save(customer);

        Policy policy = new Policy();
        policy.setCustomer(customer);
        policy.setPolicyNumber("POL-CLAIM-1001");
        policy.setPolicyType(PolicyType.PERSONAL_AUTO);
        policy.setStatus(PolicyStatus.ACTIVE);
        policy.setEffectiveDate(LocalDate.of(2026, 1, 1));
        policy.setExpirationDate(LocalDate.of(2027, 1, 1));
        policy.setPremiumAmount(new BigDecimal("1300.00"));
        policy.setCurrency("USD");
        policyRepository.save(policy);

        Claim claim = new Claim();
        claim.setPolicy(policy);
        claim.setCustomer(customer);
        claim.setClaimNumber("CLM-20260625-000001");
        claim.setClaimType(ClaimType.AUTO_COLLISION);
        claim.setStatus(ClaimStatus.SUBMITTED);
        claim.setLossDate(LocalDate.of(2026, 6, 24));
        claim.setReportedAt(Instant.parse("2026-06-25T10:15:30Z"));
        claim.setLossLocation("Columbus, OH");
        claim.setDescription("Rear-end collision at a stop light.");
        claim.setEstimatedLossAmount(new BigDecimal("9000.00"));
        claimRepository.save(claim);

        ClaimEvent event = new ClaimEvent();
        event.setClaim(claim);
        event.setEventType(ClaimEventType.FNOL_SUBMITTED);
        event.setEventSource("SYSTEM");
        event.setDescription("FNOL submitted");
        event.setPayload(Map.of("channel", "API"));
        claimEventRepository.save(event);

        ClaimNote note = new ClaimNote();
        note.setClaim(claim);
        note.setNoteType("GENERAL");
        note.setBody("Customer is available after 5 PM.");
        claimNoteRepository.save(note);

        ClaimDocument document = new ClaimDocument();
        document.setClaim(claim);
        document.setDocumentType("FNOL_STATEMENT");
        document.setFileName("fnol-statement.txt");
        document.setStorageUri("memory://fnol-statement.txt");
        document.setContentType("text/plain");
        document.setExtractedMetadata(Map.of("source", "test"));
        claimDocumentRepository.save(document);

        assertThat(claimRepository.findByClaimNumber("CLM-20260625-000001")).isPresent();
        assertThat(claimRepository.countByClaimNumberStartingWith("CLM-20260625")).isEqualTo(1);
        assertThat(claimEventRepository.findByClaimClaimNumberOrderByCreatedAtAsc("CLM-20260625-000001")).hasSize(1);
        assertThat(claimNoteRepository.findByClaimClaimNumberOrderByCreatedAtDesc("CLM-20260625-000001")).hasSize(1);
        assertThat(claimDocumentRepository.findByClaimClaimNumberOrderByUploadedAtDesc("CLM-20260625-000001")).hasSize(1);
    }
}
