package com.insureflow.api.claims.service;

import com.insureflow.api.claims.api.dto.ClaimDocumentResponse;
import com.insureflow.api.claims.api.dto.CreateClaimDocumentRequest;
import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimDocument;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.repository.ClaimDocumentRepository;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ClaimDocumentService {

    private final ClaimWorkflowService claimWorkflowService;
    private final ClaimDocumentRepository claimDocumentRepository;
    private final ClaimTimelineService claimTimelineService;

    public ClaimDocumentService(
            ClaimWorkflowService claimWorkflowService,
            ClaimDocumentRepository claimDocumentRepository,
            ClaimTimelineService claimTimelineService) {
        this.claimWorkflowService = claimWorkflowService;
        this.claimDocumentRepository = claimDocumentRepository;
        this.claimTimelineService = claimTimelineService;
    }

    @Transactional
    public ClaimDocumentResponse create(String claimNumber, CreateClaimDocumentRequest request) {
        Claim claim = claimWorkflowService.findClaim(claimNumber);
        ClaimDocument document = new ClaimDocument();
        document.setClaim(claim);
        document.setDocumentType(request.documentType());
        document.setFileName(request.fileName());
        document.setStorageUri(request.storageUri());
        document.setContentType(request.contentType());
        document.setExtractedMetadata(request.extractedMetadata() == null ? Map.of() : request.extractedMetadata());
        ClaimDocument savedDocument = claimDocumentRepository.save(document);
        claimTimelineService.record(
                claim,
                ClaimEventType.DOCUMENT_ADDED,
                "SYSTEM",
                "Claim document metadata added",
                Map.of("documentType", request.documentType(), "fileName", request.fileName()));
        return ClaimDocumentResponse.from(savedDocument);
    }

    @Transactional(readOnly = true)
    public List<ClaimDocumentResponse> list(String claimNumber) {
        claimWorkflowService.findClaim(claimNumber);
        return claimDocumentRepository.findByClaimClaimNumberOrderByUploadedAtDesc(claimNumber).stream()
                .map(ClaimDocumentResponse::from)
                .toList();
    }
}
