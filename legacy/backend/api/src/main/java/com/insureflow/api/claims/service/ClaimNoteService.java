package com.insureflow.api.claims.service;

import com.insureflow.api.claims.api.dto.ClaimNoteResponse;
import com.insureflow.api.claims.api.dto.CreateClaimNoteRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.domain.ClaimNote;
import com.insureflow.api.claims.repository.ClaimNoteRepository;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ClaimNoteService {

    private final ClaimWorkflowService claimWorkflowService;
    private final ClaimNoteRepository claimNoteRepository;
    private final ClaimTimelineService claimTimelineService;

    public ClaimNoteService(
            ClaimWorkflowService claimWorkflowService,
            ClaimNoteRepository claimNoteRepository,
            ClaimTimelineService claimTimelineService) {
        this.claimWorkflowService = claimWorkflowService;
        this.claimNoteRepository = claimNoteRepository;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional
    public ClaimNoteResponse create(String claimNumber, CreateClaimNoteRequest request) {
        Claim claim = claimWorkflowService.findClaim(claimNumber);
        ClaimNote note = new ClaimNote();
        note.setClaim(claim);
        note.setAdjusterId(request.adjusterId());
        note.setNoteType(request.noteType());
        note.setBody(request.body());
        ClaimNote savedNote = claimNoteRepository.save(note);
        claimTimelineService.record(
                claim,
                ClaimEventType.NOTE_ADDED,
                "SYSTEM",
                "Claim note added",
                Map.of("noteType", request.noteType()));
        return ClaimNoteResponse.from(savedNote);
    }

    @Transactional(readOnly = true)
    public List<ClaimNoteResponse> list(String claimNumber) {
        claimWorkflowService.findClaim(claimNumber);
        return claimNoteRepository.findByClaimClaimNumberOrderByCreatedAtDesc(claimNumber).stream()
                .map(ClaimNoteResponse::from)
                .toList();
    }
}
