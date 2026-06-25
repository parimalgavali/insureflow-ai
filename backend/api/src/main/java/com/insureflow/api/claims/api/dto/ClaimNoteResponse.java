package com.insureflow.api.claims.api.dto;

import com.insureflow.api.claims.domain.ClaimNote;
import java.time.Instant;
import java.util.UUID;

public record ClaimNoteResponse(UUID adjusterId, String noteType, String body, Instant createdAt) {

    public static ClaimNoteResponse from(ClaimNote note) {
        return new ClaimNoteResponse(note.getAdjusterId(), note.getNoteType(), note.getBody(), note.getCreatedAt());
    }
}
