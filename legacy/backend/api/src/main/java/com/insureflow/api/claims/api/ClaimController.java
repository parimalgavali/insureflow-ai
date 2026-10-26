package com.insureflow.api.claims.api;

import com.insureflow.api.claims.api.dto.ChangeClaimStatusRequest;
import com.insureflow.api.claims.api.dto.ClaimEventResponse;
import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.DocumentWorkspaceResponse;
import com.insureflow.api.claims.api.dto.RagQuestionRequest;
import com.insureflow.api.claims.api.dto.RagQuestionResponse;
import com.insureflow.api.claims.service.ClaimDecisionSupportService;
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
    private final ClaimDecisionSupportService claimDecisionSupportService;

    ClaimController(ClaimWorkflowService claimWorkflowService, ClaimDecisionSupportService claimDecisionSupportService) {
        this.claimWorkflowService = claimWorkflowService;
        this.claimDecisionSupportService = claimDecisionSupportService;
    }

    @GetMapping
    List<ClaimResponse> listClaims() {
        return claimWorkflowService.listClaims();
    }

    @GetMapping("/{claimNumber}")
    ClaimResponse getClaim(@PathVariable String claimNumber) {
        return claimWorkflowService.getClaim(claimNumber);
    }

    @GetMapping("/{claimNumber}/events")
    List<ClaimEventResponse> getEvents(@PathVariable String claimNumber) {
        return claimWorkflowService.getEvents(claimNumber);
    }

    @GetMapping("/{claimNumber}/document-workspace")
    DocumentWorkspaceResponse getDocumentWorkspace(@PathVariable String claimNumber) {
        return claimDecisionSupportService.getDocumentWorkspace(claimNumber);
    }

    @PostMapping("/{claimNumber}/rag-query")
    RagQuestionResponse answerRagQuestion(
            @PathVariable String claimNumber, @Valid @RequestBody RagQuestionRequest request) {
        return claimDecisionSupportService.answerQuestion(claimNumber, request);
    }

    @PostMapping("/{claimNumber}/status")
    ClaimResponse changeStatus(
            @PathVariable String claimNumber, @Valid @RequestBody ChangeClaimStatusRequest request) {
        return claimWorkflowService.changeStatus(claimNumber, request);
    }
}
