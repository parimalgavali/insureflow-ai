package com.insureflow.api.governance;

import static org.assertj.core.api.Assertions.assertThat;

import com.insureflow.api.support.ApiIntegrationTest;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

class GovernanceRegistryIntegrationTest extends ApiIntegrationTest {

    private static final ParameterizedTypeReference<Map<String, Object>> MAP_RESPONSE =
            new ParameterizedTypeReference<>() {};
    private static final ParameterizedTypeReference<List<Map<String, Object>>> LIST_RESPONSE =
            new ParameterizedTypeReference<>() {};

    @Test
    void auditorCanReadModelAndPromptRegistries() {
        String auditorToken = token("governance-auditor", "AUDITOR");

        ResponseEntity<List<Map<String, Object>>> models =
                restTemplate.exchange(baseUrl + "/governance/model-versions", HttpMethod.GET, authEntity(auditorToken), LIST_RESPONSE);
        ResponseEntity<List<Map<String, Object>>> prompts =
                restTemplate.exchange(baseUrl + "/governance/prompt-versions", HttpMethod.GET, authEntity(auditorToken), LIST_RESPONSE);

        assertThat(models.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(models.getBody())
                .extracting(model -> model.get("modelName"))
                .contains("rule-based-triage");

        assertThat(prompts.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(prompts.getBody())
                .extracting(prompt -> prompt.get("promptName"))
                .contains("document-extraction", "rag-adjuster-answer");
    }

    private String token(String subject, String role) {
        ResponseEntity<Map<String, Object>> response = restTemplate.exchange(
                baseUrl + "/auth/dev-token",
                HttpMethod.POST,
                new HttpEntity<>(Map.of("subject", subject, "roles", List.of(role))),
                MAP_RESPONSE);
        return (String) response.getBody().get("token");
    }

    private HttpEntity<Void> authEntity(String token) {
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        return new HttpEntity<>(headers);
    }
}
