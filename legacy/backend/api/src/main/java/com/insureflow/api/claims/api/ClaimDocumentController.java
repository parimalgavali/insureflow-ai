package com.insureflow.api.claims.api;

import com.insureflow.api.claims.api.dto.ClaimDocumentResponse;
import com.insureflow.api.claims.api.dto.CreateClaimDocumentRequest;
import com.insureflow.api.claims.service.ClaimDocumentService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/claims/{claimNumber}/documents")
class ClaimDocumentController {

    private final ClaimDocumentService claimDocumentService;

    ClaimDocumentController(ClaimDocumentService claimDocumentService) {
        this.claimDocumentService = claimDocumentService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    ClaimDocumentResponse createDocument(
            @PathVariable String claimNumber, @Valid @RequestBody CreateClaimDocumentRequest request) {
        return claimDocumentService.create(claimNumber, request);
    }

    @GetMapping
    List<ClaimDocumentResponse> listDocuments(@PathVariable String claimNumber) {
        return claimDocumentService.list(claimNumber);
    }
}
