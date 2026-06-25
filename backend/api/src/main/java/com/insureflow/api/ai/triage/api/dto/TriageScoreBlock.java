package com.insureflow.api.ai.triage.api.dto;

import com.insureflow.api.ai.triage.domain.TriageRiskLabel;
import java.math.BigDecimal;
import java.util.List;

public record TriageScoreBlock(
        TriageRiskLabel label,
        BigDecimal score,
        List<String> reasonCodes) {}
