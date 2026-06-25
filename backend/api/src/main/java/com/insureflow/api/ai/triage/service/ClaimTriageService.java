package com.insureflow.api.ai.triage.service;

import com.insureflow.api.ai.triage.api.dto.ClaimTriageResponse;
import com.insureflow.api.ai.triage.api.dto.TriageScoreBlock;
import com.insureflow.api.ai.triage.api.dto.TriageScoreResponse;
import com.insureflow.api.ai.triage.client.TriageClient;
import com.insureflow.api.ai.triage.domain.AiTriageResult;
import com.insureflow.api.ai.triage.repository.AiTriageResultRepository;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.repository.ClaimRepository;
import com.insureflow.api.claims.service.ClaimTimelineService;
import com.insureflow.api.shared.error.AiServiceUnavailableException;
import com.insureflow.api.shared.error.ResourceNotFoundException;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClientException;

@Service
public class ClaimTriageService {

    private final ClaimRepository claimRepository;
    private final AiTriageResultRepository aiTriageResultRepository;
    private final ClaimTriageFeatureAssembler featureAssembler;
    private final TriageClient triageClient;
    private final ClaimTimelineService claimTimelineService;

    public ClaimTriageService(
            ClaimRepository claimRepository,
            AiTriageResultRepository aiTriageResultRepository,
            ClaimTriageFeatureAssembler featureAssembler,
            TriageClient triageClient,
            ClaimTimelineService claimTimelineService) {
        this.claimRepository = claimRepository;
        this.aiTriageResultRepository = aiTriageResultRepository;
        this.featureAssembler = featureAssembler;
        this.triageClient = triageClient;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional
    public ClaimTriageResponse runTriage(String claimNumber) {
        Claim claim = findClaim(claimNumber);
        TriageScoreResponse score = scoreClaim(claim);
        AiTriageResult result = aiTriageResultRepository.save(toEntity(claim, score));
        claimTimelineService.record(
                claim,
                ClaimEventType.TRIAGE_COMPLETED,
                "AI_TRIAGE",
                "AI triage completed",
                Map.of(
                        "severityLabel", score.severity().label().name(),
                        "fraudRiskLabel", score.fraud().label().name(),
                        "litigationRiskLabel", score.litigation().label().name(),
                        "recommendedQueue", score.recommendedQueue(),
                        "reasonCodes", reasonCodes(score)));
        return ClaimTriageResponse.from(result);
    }

    @Transactional(readOnly = true)
    public ClaimTriageResponse getLatestTriage(String claimNumber) {
        findClaim(claimNumber);
        return aiTriageResultRepository.findByClaimClaimNumberOrderByCreatedAtDescResultSequenceDesc(claimNumber)
                .stream()
                .findFirst()
                .map(ClaimTriageResponse::from)
                .orElseThrow(() -> new ResourceNotFoundException("No triage result found for claim " + claimNumber));
    }

    private Claim findClaim(String claimNumber) {
        return claimRepository
                .findByClaimNumber(claimNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Claim " + claimNumber + " was not found"));
    }

    private TriageScoreResponse scoreClaim(Claim claim) {
        try {
            return triageClient.score(featureAssembler.assemble(claim));
        } catch (RestClientException exception) {
            throw new AiServiceUnavailableException("AI triage service is unavailable", exception);
        }
    }

    private AiTriageResult toEntity(Claim claim, TriageScoreResponse score) {
        AiTriageResult result = new AiTriageResult();
        result.setClaim(claim);
        result.setModelName(score.modelName());
        result.setModelVersion(score.modelVersion());
        result.setSeverityScore(score.severity().score());
        result.setSeverityLabel(score.severity().label());
        result.setFraudRiskScore(score.fraud().score());
        result.setFraudRiskLabel(score.fraud().label());
        result.setLitigationRiskScore(score.litigation().score());
        result.setLitigationRiskLabel(score.litigation().label());
        result.setRecommendedQueue(score.recommendedQueue());
        result.setReasonCodes(reasonCodes(score));
        result.setExplanation(score.explanation());
        result.setHumanReviewRequired(score.humanReviewRequired());
        return result;
    }

    private List<String> reasonCodes(TriageScoreResponse score) {
        LinkedHashSet<String> codes = new LinkedHashSet<>();
        addReasonCodes(codes, score.severity());
        addReasonCodes(codes, score.fraud());
        addReasonCodes(codes, score.litigation());
        return List.copyOf(codes);
    }

    private void addReasonCodes(LinkedHashSet<String> codes, TriageScoreBlock block) {
        if (block.reasonCodes() != null) {
            codes.addAll(block.reasonCodes());
        }
    }
}
