package com.insureflow.api.integration.domain;

import com.insureflow.api.shared.domain.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Table;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "integration_events")
public class IntegrationEvent extends BaseEntity {

    @Column(name = "source_system", nullable = false, length = 120)
    private String sourceSystem;

    @Column(name = "event_type", nullable = false, length = 120)
    private String eventType;

    @Column(name = "external_reference", nullable = false, length = 160)
    private String externalReference;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 40)
    private IntegrationEventStatus status;

    @Column(name = "claim_number", length = 60)
    private String claimNumber;

    @Column(name = "policy_number", length = 60)
    private String policyNumber;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> payload = Map.of();

    public String getSourceSystem() {
        return sourceSystem;
    }

    public void setSourceSystem(String sourceSystem) {
        this.sourceSystem = sourceSystem;
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public String getExternalReference() {
        return externalReference;
    }

    public void setExternalReference(String externalReference) {
        this.externalReference = externalReference;
    }

    public IntegrationEventStatus getStatus() {
        return status;
    }

    public void setStatus(IntegrationEventStatus status) {
        this.status = status;
    }

    public String getClaimNumber() {
        return claimNumber;
    }

    public void setClaimNumber(String claimNumber) {
        this.claimNumber = claimNumber;
    }

    public String getPolicyNumber() {
        return policyNumber;
    }

    public void setPolicyNumber(String policyNumber) {
        this.policyNumber = policyNumber;
    }

    public Map<String, Object> getPayload() {
        return payload;
    }

    public void setPayload(Map<String, Object> payload) {
        this.payload = payload;
    }
}
