package com.insureflow.api.ai.triage.domain;

import com.insureflow.api.claims.domain.Claim;
import com.insureflow.api.shared.domain.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "ai_triage_results")
public class AiTriageResult extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "claim_id", nullable = false)
    private Claim claim;

    @Column(name = "model_name", nullable = false, length = 120)
    private String modelName = "rule-based-triage";

    @Column(name = "model_version", nullable = false, length = 80)
    private String modelVersion = "rules-v1";

    @Column(name = "severity_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal severityScore;

    @Enumerated(EnumType.STRING)
    @Column(name = "severity_label", nullable = false, length = 40)
    private TriageRiskLabel severityLabel;

    @Column(name = "fraud_risk_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal fraudRiskScore;

    @Enumerated(EnumType.STRING)
    @Column(name = "fraud_risk_label", nullable = false, length = 40)
    private TriageRiskLabel fraudRiskLabel;

    @Column(name = "litigation_risk_score", nullable = false, precision = 5, scale = 4)
    private BigDecimal litigationRiskScore;

    @Enumerated(EnumType.STRING)
    @Column(name = "litigation_risk_label", nullable = false, length = 40)
    private TriageRiskLabel litigationRiskLabel;

    @Column(name = "recommended_queue", nullable = false, length = 80)
    private String recommendedQueue;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "reason_codes", nullable = false, columnDefinition = "jsonb")
    private List<String> reasonCodes = new ArrayList<>();

    @Column(columnDefinition = "text")
    private String explanation;

    @Column(name = "human_review_required", nullable = false)
    private boolean humanReviewRequired;

    public Claim getClaim() {
        return claim;
    }

    public void setClaim(Claim claim) {
        this.claim = claim;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }

    public String getModelVersion() {
        return modelVersion;
    }

    public void setModelVersion(String modelVersion) {
        this.modelVersion = modelVersion;
    }

    public BigDecimal getSeverityScore() {
        return severityScore;
    }

    public void setSeverityScore(BigDecimal severityScore) {
        this.severityScore = severityScore;
    }

    public TriageRiskLabel getSeverityLabel() {
        return severityLabel;
    }

    public void setSeverityLabel(TriageRiskLabel severityLabel) {
        this.severityLabel = severityLabel;
    }

    public BigDecimal getFraudRiskScore() {
        return fraudRiskScore;
    }

    public void setFraudRiskScore(BigDecimal fraudRiskScore) {
        this.fraudRiskScore = fraudRiskScore;
    }

    public TriageRiskLabel getFraudRiskLabel() {
        return fraudRiskLabel;
    }

    public void setFraudRiskLabel(TriageRiskLabel fraudRiskLabel) {
        this.fraudRiskLabel = fraudRiskLabel;
    }

    public BigDecimal getLitigationRiskScore() {
        return litigationRiskScore;
    }

    public void setLitigationRiskScore(BigDecimal litigationRiskScore) {
        this.litigationRiskScore = litigationRiskScore;
    }

    public TriageRiskLabel getLitigationRiskLabel() {
        return litigationRiskLabel;
    }

    public void setLitigationRiskLabel(TriageRiskLabel litigationRiskLabel) {
        this.litigationRiskLabel = litigationRiskLabel;
    }

    public String getRecommendedQueue() {
        return recommendedQueue;
    }

    public void setRecommendedQueue(String recommendedQueue) {
        this.recommendedQueue = recommendedQueue;
    }

    public List<String> getReasonCodes() {
        return reasonCodes;
    }

    public void setReasonCodes(List<String> reasonCodes) {
        this.reasonCodes = reasonCodes;
    }

    public String getExplanation() {
        return explanation;
    }

    public void setExplanation(String explanation) {
        this.explanation = explanation;
    }

    public boolean isHumanReviewRequired() {
        return humanReviewRequired;
    }

    public void setHumanReviewRequired(boolean humanReviewRequired) {
        this.humanReviewRequired = humanReviewRequired;
    }
}
