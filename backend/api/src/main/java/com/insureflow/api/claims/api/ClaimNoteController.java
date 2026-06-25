package com.insureflow.api.claims.api;

import com.insureflow.api.claims.api.dto.ClaimNoteResponse;
import com.insureflow.api.claims.api.dto.CreateClaimNoteRequest;
import com.insureflow.api.claims.service.ClaimNoteService;
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
@RequestMapping("/api/v1/claims/{claimNumber}/notes")
class ClaimNoteController {

    private final ClaimNoteService claimNoteService;

    ClaimNoteController(ClaimNoteService claimNoteService) {
        this.claimNoteService = claimNoteService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    ClaimNoteResponse createNote(
            @PathVariable String claimNumber, @Valid @RequestBody CreateClaimNoteRequest request) {
        return claimNoteService.create(claimNumber, request);
    }

    @GetMapping
    List<ClaimNoteResponse> listNotes(@PathVariable String claimNumber) {
        return claimNoteService.list(claimNumber);
    }
}
