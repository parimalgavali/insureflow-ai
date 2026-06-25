package com.insureflow.api.ai.triage;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.http.HttpMethod.POST;
import static org.springframework.test.web.client.ExpectedCount.once;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withServerError;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import com.insureflow.api.ai.triage.api.dto.TriageScoreRequest;
import com.insureflow.api.ai.triage.api.dto.TriageScoreResponse;
import com.insureflow.api.ai.triage.client.RestTriageClient;
import com.insureflow.api.ai.triage.config.AiTriageProperties;
import com.insureflow.api.ai.triage.domain.TriageRiskLabel;
import com.insureflow.api.shared.error.AiServiceUnavailableException;
import com.insureflow.api.shared.error.BusinessRuleViolationException;
import java.math.BigDecimal;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;
import org.springframework.test.web.client.MockRestServiceServer;

class RestTriageClientTest {

    private MockRestServiceServer server;
    private RestTriageClient client;

    @BeforeEach
    void setUp() {
        RestClient.Builder restClientBuilder = RestClient.builder();
        server = MockRestServiceServer.bindTo(restClientBuilder).build();
        client = new RestTriageClient(restClientBuilder, new AiTriageProperties("https://triage.example"));
    }

    @Test
    void scorePostsRequestAndParsesResponse() {
        server.expect(once(), requestTo("https://triage.example/ai/v1/triage/score"))
                .andExpect(method(POST))
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(content().json("""
                        {
                          "claimId": "claim-123",
                          "claimNumber": "CLM-2026-0001",
                          "policyFeatures": {
                            "policyType": "AUTO",
                            "policyAgeDays": 730,
                            "coverageLimitAmount": 50000.00,
                            "deductibleAmount": 500.00,
                            "coverageValid": true,
                            "coverageReasons": []
                          },
                          "claimFeatures": {
                            "claimType": "AUTO_COLLISION",
                            "estimatedLossAmount": 12500.00,
                            "injuryReported": true,
                            "thirdPartyInvolved": true,
                            "policeReportAvailable": false,
                            "lossReportDelayDays": 2,
                            "priorClaimsCount": 1
                          },
                          "textFeatures": {
                            "lossDescription": "Rear-end collision with soft tissue injury"
                          }
                        }
                        """))
                .andRespond(withSuccess("""
                        {
                          "claimId": "claim-123",
                          "claimNumber": "CLM-2026-0001",
                          "modelName": "rules-triage",
                          "modelVersion": "2026.06.1",
                          "severity": {
                            "label": "HIGH",
                            "score": 0.82,
                            "reasonCodes": ["INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE"]
                          },
                          "fraud": {
                            "label": "LOW",
                            "score": 0.18,
                            "reasonCodes": ["PROMPT_REPORTING"]
                          },
                          "litigation": {
                            "label": "MEDIUM",
                            "score": 0.46,
                            "reasonCodes": ["THIRD_PARTY_INVOLVED"]
                          },
                          "recommendedQueue": "COMPLEX_CLAIMS",
                          "humanReviewRequired": true,
                          "explanation": "Injury and high estimated loss require review."
                        }
                        """, MediaType.APPLICATION_JSON));

        TriageScoreResponse response = client.score(request());

        assertThat(response.claimId()).isEqualTo("claim-123");
        assertThat(response.claimNumber()).isEqualTo("CLM-2026-0001");
        assertThat(response.modelName()).isEqualTo("rules-triage");
        assertThat(response.modelVersion()).isEqualTo("2026.06.1");
        assertThat(response.severity().label()).isEqualTo(TriageRiskLabel.HIGH);
        assertThat(response.severity().score()).isEqualByComparingTo("0.82");
        assertThat(response.severity().reasonCodes()).containsExactly("INJURY_REPORTED", "HIGH_ESTIMATED_DAMAGE");
        assertThat(response.fraud().label()).isEqualTo(TriageRiskLabel.LOW);
        assertThat(response.fraud().score()).isEqualByComparingTo("0.18");
        assertThat(response.fraud().reasonCodes()).containsExactly("PROMPT_REPORTING");
        assertThat(response.litigation().label()).isEqualTo(TriageRiskLabel.MEDIUM);
        assertThat(response.litigation().score()).isEqualByComparingTo("0.46");
        assertThat(response.litigation().reasonCodes()).containsExactly("THIRD_PARTY_INVOLVED");
        assertThat(response.recommendedQueue()).isEqualTo("COMPLEX_CLAIMS");
        assertThat(response.humanReviewRequired()).isTrue();
        assertThat(response.explanation()).isEqualTo("Injury and high estimated loss require review.");
        server.verify();
    }

    @Test
    void scoreThrowsWhenAiServiceReturnsEmptyResponse() {
        server.expect(once(), requestTo("https://triage.example/ai/v1/triage/score"))
                .andExpect(method(POST))
                .andRespond(withSuccess("", MediaType.APPLICATION_JSON));

        assertThatThrownBy(() -> client.score(request()))
                .isInstanceOf(BusinessRuleViolationException.class)
                .hasMessage("AI triage service returned an empty response");
        server.verify();
    }

    @Test
    void scoreWrapsAiServiceFailures() {
        server.expect(once(), requestTo("https://triage.example/ai/v1/triage/score"))
                .andExpect(method(POST))
                .andRespond(withServerError());

        assertThatThrownBy(() -> client.score(request()))
                .isInstanceOf(AiServiceUnavailableException.class)
                .hasMessage("AI triage service is unavailable");
        server.verify();
    }

    private TriageScoreRequest request() {
        return new TriageScoreRequest(
                "claim-123",
                "CLM-2026-0001",
                new TriageScoreRequest.PolicyFeatures(
                        "AUTO",
                        730,
                        new BigDecimal("50000.00"),
                        new BigDecimal("500.00"),
                        true,
                        List.of()),
                new TriageScoreRequest.ClaimFeatures(
                        "AUTO_COLLISION",
                        new BigDecimal("12500.00"),
                        true,
                        true,
                        false,
                        2,
                        1),
                new TriageScoreRequest.TextFeatures("Rear-end collision with soft tissue injury"));
    }
}
