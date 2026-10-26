package com.insureflow.api.ai.triage.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.util.StringUtils;

@ConfigurationProperties(prefix = "insureflow.ai.triage")
public record AiTriageProperties(String baseUrl) {

    private static final String DEFAULT_BASE_URL = "http://localhost:8001";

    public AiTriageProperties {
        if (!StringUtils.hasText(baseUrl)) {
            baseUrl = DEFAULT_BASE_URL;
        }
    }
}
