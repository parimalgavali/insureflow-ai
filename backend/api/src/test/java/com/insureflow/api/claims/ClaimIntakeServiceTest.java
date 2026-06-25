package com.insureflow.api.claims;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.FnolRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimType;
import com.insureflow.api.claims.service.ClaimIntakeAttemptService;
import com.insureflow.api.claims.service.ClaimIntakeService;
import com.insureflow.api.policy.api.dto.CoverageCheckRequest;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import com.insureflow.api.policy.domain.CoverageType;
import com.insureflow.api.policy.domain.Customer;
import com.insureflow.api.policy.domain.Policy;
import com.insureflow.api.policy.domain.PolicyStatus;
import com.insureflow.api.policy.domain.PolicyType;
import com.insureflow.api.policy.service.CoverageValidationService;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

class ClaimIntakeServiceTest {

    @Test
    void retriesOnceWhenClaimNumberCollides() {
        CoverageValidationService coverageValidationService = new CoverageValidationService(null, null) {
            @Override
            public CoverageCheckResponse validate(String policyNumber, CoverageCheckRequest request) {
                return new CoverageCheckResponse(
                        true,
                        PolicyStatus.ACTIVE,
                        CoverageType.COLLISION,
                        new BigDecimal("25000.00"),
                        new BigDecimal("500.00"),
                        "[]",
                        List.of(),
                        List.of());
            }
        };
        AtomicInteger attempts = new AtomicInteger();
        ClaimIntakeAttemptService claimIntakeAttemptService = new ClaimIntakeAttemptService(null, null, null, null) {
            @Override
            public ClaimResponse submitAttempt(FnolRequest request, CoverageCheckResponse coverageValidation) {
                if (attempts.incrementAndGet() == 1) {
                    throw new DataIntegrityViolationException("duplicate claim number");
                }
                Customer customer = new Customer();
                customer.setCustomerNumber("CUST-RETRY-1001");
                Policy policy = new Policy();
                policy.setCustomer(customer);
                policy.setPolicyNumber(request.policyNumber());
                policy.setPolicyType(PolicyType.PERSONAL_AUTO);
                policy.setStatus(PolicyStatus.ACTIVE);
                policy.setEffectiveDate(LocalDate.of(2026, 1, 1));
                policy.setExpirationDate(LocalDate.of(2027, 1, 1));
                policy.setPremiumAmount(new BigDecimal("1500.00"));
                policy.setCurrency("USD");
                Claim claim = new Claim();
                claim.setPolicy(policy);
                claim.setCustomer(customer);
                claim.setClaimNumber("CLM-20260625-000002");
                claim.setClaimType(request.claimType());
                claim.setStatus(com.insureflow.api.claims.domain.ClaimStatus.SUBMITTED);
                claim.setLossDate(request.lossDate());
                claim.setReportedAt(request.reportedAt());
                claim.setDescription(request.description());
                claim.setEstimatedLossAmount(request.estimatedLossAmount());
                return ClaimResponse.from(claim, coverageValidation);
            }
        };

        ClaimIntakeService service = new ClaimIntakeService(
                coverageValidationService,
                claimIntakeAttemptService);

        ClaimResponse response = service.submit(new FnolRequest(
                "POL-RETRY-1001",
                ClaimType.AUTO_COLLISION,
                LocalDate.of(2026, 6, 24),
                Instant.parse("2026-06-25T10:15:30Z"),
                "Columbus, OH",
                "Rear-end collision at a stop light.",
                new BigDecimal("9000.00")));

        assertThat(response.claimNumber()).isEqualTo("CLM-20260625-000002");
        assertThat(attempts).hasValue(2);
    }
}
