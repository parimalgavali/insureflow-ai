package com.insureflow.api.claims.api;

import com.insureflow.api.claims.api.dto.ChangeClaimStatusRequest;
import com.insureflow.api.claims.api.dto.ClaimEventResponse;
import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.service.ClaimWorkflowService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/claims")
class ClaimController {

    private final ClaimWorkflowService claimWorkflowService;

    ClaimController(ClaimWorkflowService claimWorkflowService) {
        this.claimWorkflowService = claimWorkflowService;
    }

    @GetMapping("/{claimNumber}")
    ClaimResponse getClaim(@PathVariable String claimNumber) {
        return claimWorkflowService.getClaim(claimNumber);
    }

    @GetMapping("/{claimNumber}/events")
    List<ClaimEventResponse> getEvents(@PathVariable String claimNumber) {
        return claimWorkflowService.getEvents(claimNumber);
    }

    @PostMapping("/{claimNumber}/status")
    ClaimResponse changeStatus(
            @PathVariable String claimNumber, @Valid @RequestBody ChangeClaimStatusRequest request) {
        return claimWorkflowService.changeStatus(claimNumber, request);
    }
}
