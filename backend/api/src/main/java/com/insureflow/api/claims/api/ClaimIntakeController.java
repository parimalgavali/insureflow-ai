package com.insureflow.api.claims.api;

import com.insureflow.api.claims.api.dto.ClaimResponse;
import com.insureflow.api.claims.api.dto.FnolRequest;
import com.insureflow.api.claims.service.ClaimIntakeService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/claims")
class ClaimIntakeController {

    private final ClaimIntakeService claimIntakeService;

    ClaimIntakeController(ClaimIntakeService claimIntakeService) {
        this.claimIntakeService = claimIntakeService;
    }

    @PostMapping("/fnol")
    @ResponseStatus(HttpStatus.CREATED)
    ClaimResponse submitFnol(@Valid @RequestBody FnolRequest request) {
        return claimIntakeService.submit(request);
    }
}
