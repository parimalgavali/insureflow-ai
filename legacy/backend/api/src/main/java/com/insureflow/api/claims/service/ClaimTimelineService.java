package com.insureflow.api.claims.service;

import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.claims.domain.ClaimEvent;
import com.insureflow.api.claims.domain.ClaimEventType;
import com.insureflow.api.claims.repository.ClaimEventRepository;
import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class ClaimTimelineService {

    private final ClaimEventRepository claimEventRepository;

    public ClaimTimelineService(ClaimEventRepository claimEventRepository) {
        this.claimEventRepository = claimEventRepository;
    }

    public ClaimEvent record(
            Claim claim, ClaimEventType eventType, String eventSource, String description, Map<String, Object> payload) {
        ClaimEvent event = new ClaimEvent();
        event.setClaim(claim);
        event.setEventType(eventType);
        event.setEventSource(eventSource);
        event.setDescription(description);
        event.setPayload(payload);
        return claimEventRepository.save(event);
    }
}
