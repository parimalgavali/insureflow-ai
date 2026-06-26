package com.insureflow.api.integration.api.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public record ReserveUpdateRequest(
        @NotBlank String sourceSystem,
        @NotBlank String externalReference,
        @NotBlank String coverageCode,
        @NotNull @DecimalMin("0.00") BigDecimal reserveAmount,
        @NotBlank @Size(min = 3, max = 3) String currency,
        @NotBlank String reason) {}
