package com.insureflow.api.governance;

import com.insureflow.api.shared.domain.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "model_versions")
public class ModelVersion extends BaseEntity {

    @Column(name = "model_name", nullable = false, length = 120)
    private String modelName;

    @Column(nullable = false, length = 80)
    private String version;

    @Column(name = "model_type", nullable = false, length = 80)
    private String modelType;

    @Column(name = "artifact_uri")
    private String artifactUri;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> metrics = Map.of();

    @Column(nullable = false)
    private boolean active;

    public String getModelName() {
        return modelName;
    }

    public String getVersion() {
        return version;
    }

    public String getModelType() {
        return modelType;
    }

    public String getArtifactUri() {
        return artifactUri;
    }

    public Map<String, Object> getMetrics() {
        return metrics;
    }

    public boolean isActive() {
        return active;
    }
}
