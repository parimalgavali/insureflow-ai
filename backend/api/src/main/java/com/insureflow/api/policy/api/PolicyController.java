package com.insureflow.api.policy.api;

import com.insureflow.api.policy.api.dto.AddCoverageRequest;
import com.insureflow.api.policy.api.dto.CoverageResponse;
import com.insureflow.api.policy.api.dto.CreatePolicyRequest;
import com.insureflow.api.policy.api.dto.PolicyResponse;
import com.insureflow.api.policy.service.PolicyManagementService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/policies")
class PolicyController {

    private final PolicyManagementService service;

    PolicyController(PolicyManagementService service) {
        this.service = service;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    PolicyResponse createPolicy(@Valid @RequestBody CreatePolicyRequest request) {
        return service.createPolicy(request);
    }

    @GetMapping("/{policyNumber}")
    PolicyResponse getPolicy(@PathVariable String policyNumber) {
        return service.getPolicy(policyNumber);
    }

    @PostMapping("/{policyNumber}/coverages")
    @ResponseStatus(HttpStatus.CREATED)
    CoverageResponse addCoverage(
            @PathVariable String policyNumber, @Valid @RequestBody AddCoverageRequest request) {
        return service.addCoverage(policyNumber, request);
    }
}
