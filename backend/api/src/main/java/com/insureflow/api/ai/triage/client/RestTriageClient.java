package com.insureflow.api.ai.triage.client;

import com.insureflow.api.ai.triage.api.dto.TriageScoreRequest;
import com.insureflow.api.ai.triage.api.dto.TriageScoreResponse;
import com.insureflow.api.ai.triage.config.AiTriageProperties;
import com.insureflow.api.shared.error.AiServiceUnavailableException;
import com.insureflow.api.shared.error.BusinessRuleViolationException;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component
public class RestTriageClient implements TriageClient {

    private static final String SCORE_PATH = "/ai/v1/triage/score";

    private final RestClient restClient;

    public RestTriageClient(RestClient.Builder restClientBuilder, AiTriageProperties properties) {
        this.restClient = restClientBuilder
                .baseUrl(properties.baseUrl())
                .build();
    }

    @Override
    public TriageScoreResponse score(TriageScoreRequest request) {
        TriageScoreResponse response;
        try {
            response = restClient.post()
                    .uri(SCORE_PATH)
                    .body(request)
                    .retrieve()
                    .body(TriageScoreResponse.class);
        } catch (RestClientException exception) {
            throw new AiServiceUnavailableException("AI triage service is unavailable", exception);
        }

        if (response == null) {
            throw new BusinessRuleViolationException("AI triage service returned an empty response");
        }

        return response;
    }
}
