package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.ClaimStatus;
import jakarta.validation.constraints.NotNull;

public record ChangeClaimStatusRequest(@NotNull ClaimStatus targetStatus, String reason) {}
