package com.insureflow.api.ai.triage;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.ai.triage.domain.AiTriageResult;
import com.insureflow.api.ai.triage.domain.TriageRiskLabel;
import com.insureflow.api.ai.triage.repository.AiTriageResultRepository;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimStatus;
import com.insureflow.api.claims.domain.ClaimType;
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
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
class AiTriageResultRepositoryTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private PolicyRepository policyRepository;

    @Autowired
    private ClaimRepository claimRepository;

    @Autowired
    private AiTriageResultRepository aiTriageResultRepository;

    @Autowired
    private TestEntityManager entityManager;

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.test.database.replace", () -> "none");
    }

    @Test
    void findsTriageResultsByClaimNumberWithLatestFirstAndReasonCodesPreserved() throws Exception {
        Customer customer = new Customer();
        customer.setCustomerNumber("CUST-TRIAGE-1001");
        customer.setFirstName("Maya");
        customer.setLastName("Patel");
        customer.setEmail("maya.patel@example.test");
        customer.setCountry("US");
        customerRepository.save(customer);

        Policy policy = new Policy();
        policy.setCustomer(customer);
        policy.setPolicyNumber("POL-TRIAGE-1001");
        policy.setPolicyType(PolicyType.PERSONAL_AUTO);
        policy.setStatus(PolicyStatus.ACTIVE);
        policy.setEffectiveDate(LocalDate.of(2026, 1, 1));
        policy.setExpirationDate(LocalDate.of(2027, 1, 1));
        policy.setPremiumAmount(new BigDecimal("1250.00"));
        policy.setCurrency("USD");
        policyRepository.save(policy);

        Claim claim = new Claim();
        claim.setPolicy(policy);
        claim.setCustomer(customer);
        claim.setClaimNumber("CLM-TRIAGE-000001");
        claim.setClaimType(ClaimType.AUTO_COLLISION);
        claim.setStatus(ClaimStatus.SUBMITTED);
        claim.setLossDate(LocalDate.of(2026, 6, 24));
        claim.setReportedAt(Instant.parse("2026-06-25T10:15:30Z"));
        claim.setLossLocation("Columbus, OH");
        claim.setDescription("Rear-end collision at a stop light.");
        claim.setEstimatedLossAmount(new BigDecimal("9000.00"));
        claimRepository.save(claim);

        AiTriageResult firstResult = new AiTriageResult();
        firstResult.setClaim(claim);
        firstResult.setSeverityScore(new BigDecimal("0.2500"));
        firstResult.setSeverityLabel(TriageRiskLabel.LOW);
        firstResult.setFraudRiskScore(new BigDecimal("0.1000"));
        firstResult.setFraudRiskLabel(TriageRiskLabel.LOW);
        firstResult.setLitigationRiskScore(new BigDecimal("0.2000"));
        firstResult.setLitigationRiskLabel(TriageRiskLabel.LOW);
        firstResult.setRecommendedQueue("STANDARD");
        firstResult.setReasonCodes(List.of("LOW_IMPACT", "POLICY_ACTIVE"));
        firstResult.setExplanation("Low-risk claim.");
        aiTriageResultRepository.saveAndFlush(firstResult);

        Thread.sleep(5);

        AiTriageResult secondResult = new AiTriageResult();
        secondResult.setClaim(claim);
        secondResult.setSeverityScore(new BigDecimal("0.8200"));
        secondResult.setSeverityLabel(TriageRiskLabel.HIGH);
        secondResult.setFraudRiskScore(new BigDecimal("0.6500"));
        secondResult.setFraudRiskLabel(TriageRiskLabel.MEDIUM);
        secondResult.setLitigationRiskScore(new BigDecimal("0.7800"));
        secondResult.setLitigationRiskLabel(TriageRiskLabel.HIGH);
        secondResult.setRecommendedQueue("SPECIAL_INVESTIGATION");
        secondResult.setReasonCodes(List.of("HIGH_LOSS_AMOUNT", "ATTORNEY_REPRESENTED"));
        secondResult.setExplanation("Elevated triage risk.");
        secondResult.setHumanReviewRequired(true);
        aiTriageResultRepository.saveAndFlush(secondResult);
        entityManager.clear();

        List<AiTriageResult> results =
                aiTriageResultRepository.findByClaimClaimNumberOrderByCreatedAtDesc("CLM-TRIAGE-000001");

        assertThat(results).hasSize(2);
        assertThat(results.get(0).getId()).isEqualTo(secondResult.getId());
        assertThat(results.get(0).getReasonCodes()).containsExactly("HIGH_LOSS_AMOUNT", "ATTORNEY_REPRESENTED");
        assertThat(results.get(0).isHumanReviewRequired()).isTrue();
        assertThat(results.get(1).getId()).isEqualTo(firstResult.getId());
        assertThat(results.get(1).getReasonCodes()).containsExactly("LOW_IMPACT", "POLICY_ACTIVE");
    }
}
