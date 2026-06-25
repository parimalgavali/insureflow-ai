package com.insureflow.api.claims;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.claims.service.ClaimNumberGenerator;
import java.time.LocalDate;
import org.junit.jupiter.api.Test;

class ClaimNumberGeneratorTest {

    @Test
    void formatsClaimNumberWithDateAndSequence() {
        ClaimNumberGenerator generator = new ClaimNumberGenerator();

        String claimNumber = generator.generate(LocalDate.of(2026, 6, 25), 0);

        assertThat(claimNumber).isEqualTo("CLM-20260625-000001");
    }

    @Test
    void incrementsSequenceAfterExistingClaimsForDate() {
        ClaimNumberGenerator generator = new ClaimNumberGenerator();

        String claimNumber = generator.generate(LocalDate.of(2026, 6, 25), 42);

        assertThat(claimNumber).isEqualTo("CLM-20260625-000043");
    }
}
