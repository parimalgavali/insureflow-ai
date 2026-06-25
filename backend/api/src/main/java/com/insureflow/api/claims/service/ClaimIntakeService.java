package com.insureflow.api.claims.service;

import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.FnolRequest;
import com.insureflow.api.policy.api.dto.CoverageCheckRequest;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import com.insureflow.api.policy.service.CoverageValidationService;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.stereotype.Service;

@Service
public class ClaimIntakeService {

    private final CoverageValidationService coverageValidationService;
    private final ClaimIntakeAttemptService claimIntakeAttemptService;

    public ClaimIntakeService(
            CoverageValidationService coverageValidationService,
            ClaimIntakeAttemptService claimIntakeAttemptService) {
        this.coverageValidationService = coverageValidationService;
        this.claimIntakeAttemptService = claimIntakeAttemptService;
    }

    public ClaimResponse submit(FnolRequest request) {
        CoverageCheckResponse coverageValidation = coverageValidationService.validate(
                request.policyNumber(),
                new CoverageCheckRequest(
                        request.claimType().name(), request.lossDate(), request.estimatedLossAmount()));

        DataIntegrityViolationException collision = null;
        for (int attempt = 0; attempt < 2; attempt++) {
            try {
                return claimIntakeAttemptService.submitAttempt(request, coverageValidation);
            } catch (DataIntegrityViolationException exception) {
                collision = exception;
            }
        }
        throw collision;
    }
}
