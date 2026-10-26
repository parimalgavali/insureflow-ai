package com.insureflow.api.governance;

import java.util.UUID;

public record PromptVersionResponse(
        UUID id,
        String promptName,
        String version,
        String template,
        String modelName,
        boolean active) {

    static PromptVersionResponse from(PromptVersion promptVersion) {
        return new PromptVersionResponse(
                promptVersion.getId(),
                promptVersion.getPromptName(),
                promptVersion.getVersion(),
                promptVersion.getTemplate(),
                promptVersion.getModelName(),
                promptVersion.isActive());
    }
}
