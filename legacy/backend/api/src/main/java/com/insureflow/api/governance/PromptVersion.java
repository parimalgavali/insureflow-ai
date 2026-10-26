package com.insureflow.api.governance;

import com.insureflow.api.shared.domain.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;

@Entity
@Table(name = "prompt_versions")
public class PromptVersion extends BaseEntity {

    @Column(name = "prompt_name", nullable = false, length = 120)
    private String promptName;

    @Column(nullable = false, length = 80)
    private String version;

    @Column(nullable = false, columnDefinition = "text")
    private String template;

    @Column(name = "model_name", length = 120)
    private String modelName;

    @Column(nullable = false)
    private boolean active;

    public String getPromptName() {
        return promptName;
    }

    public String getVersion() {
        return version;
    }

    public String getTemplate() {
        return template;
    }

    public String getModelName() {
        return modelName;
    }

    public boolean isActive() {
        return active;
    }
}
