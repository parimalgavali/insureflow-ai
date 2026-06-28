package com.insureflow.api.governance;

import java.util.Map;
import java.util.UUID;

public record ModelVersionResponse(
        UUID id,
        String modelName,
        String version,
        String modelType,
        String artifactUri,
        Map<String, Object> metrics,
        boolean active) {

    static ModelVersionResponse from(ModelVersion modelVersion) {
        return new ModelVersionResponse(
                modelVersion.getId(),
                modelVersion.getModelName(),
                modelVersion.getVersion(),
                modelVersion.getModelType(),
                modelVersion.getArtifactUri(),
                modelVersion.getMetrics(),
                modelVersion.isActive());
    }
}
