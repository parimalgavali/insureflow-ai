package com.insureflow.api.integration.api.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record IntegrationClaimCreateRequest(
        @NotBlank String sourceSystem,
        @NotBlank String externalReference,
        @NotNull @Valid IntegrationFnolRequest claim) {}
