package com.insureflow.api.humanreview;

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
@RequestMapping("/api/v1/claims/{claimNumber}/human-reviews")
class HumanReviewController {

    private final HumanReviewService humanReviewService;

    HumanReviewController(HumanReviewService humanReviewService) {
        this.humanReviewService = humanReviewService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    HumanReviewResponse create(
            @PathVariable String claimNumber, @Valid @RequestBody CreateHumanReviewRequest request) {
        return humanReviewService.create(claimNumber, request);
    }

    @GetMapping
    List<HumanReviewResponse> list(@PathVariable String claimNumber) {
        return humanReviewService.list(claimNumber);
    }
}
