package com.insureflow.api.policy;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.policy.domain.Coverage;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.Customer;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.domain.PolicyType;
import com.insureflow.api.policy.repository.CoverageRepository;
import com.insureflow.api.policy.repository.CustomerRepository;
import com.insureflow.api.policy.repository.PolicyRepository;
import java.math.BigDecimal;
import java.time.LocalDate;
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
class PolicyRepositoryTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    private CustomerRepository customerRepository;

    @Autowired
    private PolicyRepository policyRepository;

    @Autowired
    private CoverageRepository coverageRepository;

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.test.database.replace", () -> "none");
    }

    @Test
    void savesAndFindsCustomerPolicyAndCoverage() {
        Customer customer = new Customer();
        customer.setCustomerNumber("CUST-1001");
        customer.setFirstName("Avery");
        customer.setLastName("Stone");
        customer.setEmail("avery.stone@example.test");
        customer.setPhone("555-0100");
        customer.setAddressLine1("100 Market Street");
        customer.setCity("Columbus");
        customer.setState("OH");
        customer.setPostalCode("43004");
        customer.setCountry("US");
        customerRepository.save(customer);

        Policy policy = new Policy();
        policy.setCustomer(customer);
        policy.setPolicyNumber("POL-AUTO-1001");
        policy.setPolicyType(PolicyType.PERSONAL_AUTO);
        policy.setStatus(PolicyStatus.DRAFT);
        policy.setEffectiveDate(LocalDate.of(2026, 1, 1));
        policy.setExpirationDate(LocalDate.of(2027, 1, 1));
        policy.setPremiumAmount(new BigDecimal("1280.00"));
        policy.setCurrency("USD");
        policyRepository.save(policy);

        Coverage coverage = new Coverage();
        coverage.setPolicy(policy);
        coverage.setCoverageCode("COLLISION");
        coverage.setCoverageName("Collision Coverage");
        coverage.setCoverageType(CoverageType.COLLISION);
        coverage.setLimitAmount(new BigDecimal("25000.00"));
        coverage.setDeductibleAmount(new BigDecimal("500.00"));
        coverage.setEffectiveDate(LocalDate.of(2026, 1, 1));
        coverage.setExpirationDate(LocalDate.of(2027, 1, 1));
        coverage.setExclusions("[\"racing\"]");
        coverageRepository.save(coverage);

        assertThat(customerRepository.findByCustomerNumber("CUST-1001"))
                .isPresent()
                .get()
                .extracting(Customer::getEmail)
                .isEqualTo("avery.stone@example.test");

        assertThat(policyRepository.findByPolicyNumber("POL-AUTO-1001"))
                .isPresent()
                .get()
                .extracting(Policy::getStatus)
                .isEqualTo(PolicyStatus.DRAFT);

        assertThat(coverageRepository.findByPolicyAndCoverageType(policy, CoverageType.COLLISION))
                .isPresent()
                .get()
                .satisfies(found -> {
                    assertThat(found.getLimitAmount()).isEqualByComparingTo("25000.00");
                    assertThat(found.getDeductibleAmount()).isEqualByComparingTo("500.00");
                });
    }
}
