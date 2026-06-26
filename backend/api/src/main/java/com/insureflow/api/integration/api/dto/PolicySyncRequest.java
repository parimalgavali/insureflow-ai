package com.insureflow.api.integration.api.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record PolicySyncRequest(
        @NotBlank String sourceSystem,
        @NotBlank String externalReference,
        @NotNull @Valid IntegrationCustomerRequest customer,
        @NotNull @Valid IntegrationPolicyRequest policy,
        @NotEmpty List<@Valid IntegrationCoverageRequest> coverages) {}
