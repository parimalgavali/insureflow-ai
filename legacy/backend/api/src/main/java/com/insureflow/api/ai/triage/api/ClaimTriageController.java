package com.insureflow.api.ai.triage.api;

import com.insureflow.api.ai.triage.api.dto.ClaimTriageResponse;
import com.insureflow.api.ai.triage.service.ClaimTriageService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/claims")
class ClaimTriageController {

    private final ClaimTriageService claimTriageService;

    ClaimTriageController(ClaimTriageService claimTriageService) {
        this.claimTriageService = claimTriageService;
    }

    @PostMapping("/{claimNumber}/triage")
    ClaimTriageResponse runTriage(@PathVariable String claimNumber) {
        return claimTriageService.runTriage(claimNumber);
    }

    @GetMapping("/{claimNumber}/triage")
    ClaimTriageResponse getLatestTriage(@PathVariable String claimNumber) {
        return claimTriageService.getLatestTriage(claimNumber);
    }
}
