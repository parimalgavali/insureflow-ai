package com.insureflow.api.ai.triage.client;

import com.insureflow.api.ai.triage.api.dto.TriageScoreRequest;
import com.insureflow.api.ai.triage.api.dto.TriageScoreResponse;

public interface TriageClient {

    TriageScoreResponse score(TriageScoreRequest request);
}
