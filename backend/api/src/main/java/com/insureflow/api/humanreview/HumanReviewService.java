package com.insureflow.api.humanreview;

import com.insureflow.api.adjusters.Adjuster;
import com.insureflow.api.adjusters.AdjusterRepository;
import com.insureflow.api.ai.triage.domain.AiTriageResult;
import com.insureflow.api.ai.triage.repository.AiTriageResultRepository;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.claims.service.ClaimTimelineService;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class HumanReviewService {

    private final ClaimRepository claimRepository;
    private final AdjusterRepository adjusterRepository;
    private final AiTriageResultRepository aiTriageResultRepository;
    private final HumanReviewRepository humanReviewRepository;
    private final ClaimTimelineService claimTimelineService;

    public HumanReviewService(
            ClaimRepository claimRepository,
            AdjusterRepository adjusterRepository,
            AiTriageResultRepository aiTriageResultRepository,
            HumanReviewRepository humanReviewRepository,
            ClaimTimelineService claimTimelineService) {
        this.claimRepository = claimRepository;
        this.adjusterRepository = adjusterRepository;
        this.aiTriageResultRepository = aiTriageResultRepository;
        this.humanReviewRepository = humanReviewRepository;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional
    public HumanReviewResponse create(String claimNumber, CreateHumanReviewRequest request) {
        validate(request);
        Claim claim = claimRepository
                .findByClaimNumber(claimNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + claimNumber + " was not found"));
        Adjuster reviewer = adjusterRepository
                .findById(request.reviewerAdjusterId())
                .orElseThrow(() -> new ResourceNotFoundException("Adjuster " + request.reviewerAdjusterId() + " was not found"));
        AiTriageResult latestTriage = aiTriageResultRepository
                .findByClaimClaimNumberOrderByCreatedAtDescResultSequenceDesc(claimNumber)
                .stream()
                .findFirst()
                .orElse(null);

        HumanReview humanReview = new HumanReview();
        humanReview.setClaim(claim);
        humanReview.setReviewerAdjuster(reviewer);
        humanReview.setAiTriageResult(latestTriage);
        humanReview.setDecision(request.decision());
        humanReview.setOverrideReason(request.overrideReason());
        humanReview.setNotes(request.notes());
        HumanReview saved = humanReviewRepository.save(humanReview);

        claimTimelineService.record(
                claim,
                ClaimEventType.HUMAN_REVIEW_RECORDED,
                "HUMAN_REVIEW",
                "Human review recorded",
                Map.of(
                        "decision", request.decision().name(),
                        "overrideReason", request.overrideReason() == null ? "" : request.overrideReason()));
        return HumanReviewResponse.from(saved);
    }

    @Transactional(readOnly = true)
    public List<HumanReviewResponse> list(String claimNumber) {
        claimRepository
                .findByClaimNumber(claimNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + claimNumber + " was not found"));
        return humanReviewRepository.findByClaimClaimNumberOrderByReviewedAtDesc(claimNumber).stream()
                .map(HumanReviewResponse::from)
                .toList();
    }

    private void validate(CreateHumanReviewRequest request) {
        if (request.decision() == HumanReviewDecision.OVERRIDE_AI_RECOMMENDATION
                && (request.overrideReason() == null || request.overrideReason().isBlank())) {
            throw new IllegalArgumentException("overrideReason is required when overriding an AI recommendation");
        }
    }
}
