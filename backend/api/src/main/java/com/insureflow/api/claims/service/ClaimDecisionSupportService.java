package com.insureflow.api.claims.service;

import com.insureflow.api.ai.triage.domain.AiTriageResult;
import com.insureflow.api.ai.triage.repository.AiTriageResultRepository;
import com.insureflow.api.claims.api.dto.DocumentWorkspaceResponse;
import com.insureflow.api.claims.api.dto.RagQuestionRequest;
import com.insureflow.api.claims.api.dto.RagQuestionResponse;
import com.insureflow.api.claims.api.dto.RagSourceResponse;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimDocument;
import com.insureflow.api.claims.domain.ClaimType;
import com.insureflow.api.claims.repository.ClaimDocumentRepository;
import com.insureflow.api.policy.api.dto.CoverageCheckResponse;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ClaimDecisionSupportService {

    private static final Map<ClaimType, List<String>> REQUIRED_DOCUMENTS = Map.of(
            ClaimType.AUTO_COLLISION, List.of("DAMAGE_PHOTOS", "REPAIR_INVOICE", "POLICE_REPORT"),
            ClaimType.AUTO_COMPREHENSIVE, List.of("DAMAGE_PHOTOS", "REPAIR_ESTIMATE"),
            ClaimType.BODILY_INJURY, List.of("MEDICAL_NOTE", "POLICE_REPORT"),
            ClaimType.PROPERTY_DAMAGE, List.of("DAMAGE_PHOTOS", "REPAIR_ESTIMATE"),
            ClaimType.HOME_WATER_DAMAGE, List.of("DAMAGE_PHOTOS", "REPAIR_ESTIMATE"),
            ClaimType.HOME_FIRE, List.of("DAMAGE_PHOTOS", "FIRE_REPORT", "REPAIR_ESTIMATE"),
            ClaimType.THEFT, List.of("POLICE_REPORT", "INVENTORY_LIST"));

    private final ClaimWorkflowService claimWorkflowService;
    private final ClaimDocumentRepository claimDocumentRepository;
    private final AiTriageResultRepository aiTriageResultRepository;

    public ClaimDecisionSupportService(
            ClaimWorkflowService claimWorkflowService,
            ClaimDocumentRepository claimDocumentRepository,
            AiTriageResultRepository aiTriageResultRepository) {
        this.claimWorkflowService = claimWorkflowService;
        this.claimDocumentRepository = claimDocumentRepository;
        this.aiTriageResultRepository = aiTriageResultRepository;
    }

    @Transactional(readOnly = true)
    public DocumentWorkspaceResponse getDocumentWorkspace(String claimNumber) {
        Claim claim = claimWorkflowService.findClaim(claimNumber);
        List<ClaimDocument> documents = claimDocumentRepository.findByClaimClaimNumberOrderByUploadedAtDesc(claimNumber);
        Set<String> received = new LinkedHashSet<>();
        documents.stream()
                .sorted(Comparator.comparing(ClaimDocument::getUploadedAt))
                .forEach(document -> received.add(document.getDocumentType()));
        List<String> required = REQUIRED_DOCUMENTS.getOrDefault(claim.getClaimType(), List.of("DAMAGE_PHOTOS"));
        List<String> missing = required.stream().filter(document -> !received.contains(document)).toList();

        List<String> highlights = new ArrayList<>();
        highlights.add("Received " + received.size() + " document type(s) for live backend review.");
        if (claim.getEstimatedLossAmount() != null) {
            highlights.add("Estimated loss amount is " + claim.getEstimatedLossAmount() + ".");
        }
        if (missing.isEmpty()) {
            highlights.add("Required document set is complete for the current claim type.");
        } else {
            highlights.add("Missing document request recommended: " + String.join(", ", missing) + ".");
        }

        return new DocumentWorkspaceResponse(
                List.copyOf(received),
                missing,
                highlights,
                List.of(
                        new DocumentWorkspaceResponse.SummarySection(
                                "Claim overview",
                                "Live document workspace for " + claim.getClaimNumber() + " (" + claim.getClaimType() + ")."),
                        new DocumentWorkspaceResponse.SummarySection(
                                "Recommended next action",
                                missing.isEmpty()
                                        ? "Continue adjuster review with the received document set."
                                        : "Request " + String.join(", ", missing) + " before final workflow movement.")));
    }

    @Transactional(readOnly = true)
    public RagQuestionResponse answerQuestion(String claimNumber, RagQuestionRequest request) {
        Claim claim = claimWorkflowService.findClaim(claimNumber);
        CoverageCheckResponse coverage = claimWorkflowService
                .getClaim(claimNumber)
                .coverageValidation();
        AiTriageResult triage = aiTriageResultRepository
                .findByClaimClaimNumberOrderByCreatedAtDescResultSequenceDesc(claimNumber)
                .stream()
                .findFirst()
                .orElse(null);

        String normalized = request.question().toLowerCase(Locale.ROOT);
        String answer;
        String sectionTitle;
        if (normalized.contains("cover") || normalized.contains("coverage")) {
            boolean covered = coverage != null && coverage.covered();
            answer = covered
                    ? "Based on the live coverage validation snapshot, this collision loss appears potentially covered when reviewed against the active policy context. Human review is still required before any claim decision."
                    : "The live coverage validation snapshot does not confirm coverage. Request adjuster review before any workflow movement.";
            sectionTitle = "Coverage Validation";
        } else if (normalized.contains("document") || normalized.contains("missing")) {
            DocumentWorkspaceResponse workspace = getDocumentWorkspace(claimNumber);
            answer = workspace.missingDocuments().isEmpty()
                    ? "The live document workspace does not show required documents missing for this claim type."
                    : "The live document workspace indicates these missing documents: "
                            + String.join(", ", workspace.missingDocuments()) + ".";
            sectionTitle = "Document Workspace";
        } else {
            answer = "I can answer from live claim, coverage, document, and triage evidence. The current claim status is "
                    + claim.getStatus() + ".";
            sectionTitle = "Claim Context";
        }

        if (triage != null) {
            answer += " Latest AI triage recommended queue: " + triage.getRecommendedQueue() + ".";
        }

        return new RagQuestionResponse(
                request.question(),
                answer,
                "MEDIUM",
                true,
                List.of(new RagSourceResponse(
                        "CLAIM-" + claim.getClaimNumber(),
                        "CLAIM-" + claim.getClaimNumber() + "-LIVE-CONTEXT",
                        "CLAIM_CONTEXT",
                        sectionTitle,
                        1,
                        0.72)));
    }
}
