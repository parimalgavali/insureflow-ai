package com.insureflow.api.claims.service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import org.springframework.stereotype.Component;

@Component
public class ClaimNumberGenerator {

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.BASIC_ISO_DATE;

    public String generate(LocalDate date, long existingClaimsForDate) {
        return "CLM-%s-%06d".formatted(DATE_FORMAT.format(date), existingClaimsForDate + 1);
    }
}
