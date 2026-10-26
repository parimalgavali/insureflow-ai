package com.insureflow.api.claims.api.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.UUID;

public record CreateClaimNoteRequest(UUID adjusterId, @NotBlank String noteType, @NotBlank String body) {}
