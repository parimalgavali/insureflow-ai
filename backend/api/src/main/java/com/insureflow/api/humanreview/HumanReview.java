package com.insureflow.api.humanreview;

import com.insureflow.api.adjusters.Adjuster;
import com.insureflow.api.ai.triage.domain.AiTriageResult;
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
import java.time.Instant;

@Entity
@Table(name = "human_reviews")
public class HumanReview extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "claim_id", nullable = false)
    private Claim claim;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "ai_triage_result_id")
    private AiTriageResult aiTriageResult;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "reviewer_adjuster_id", nullable = false)
    private Adjuster reviewerAdjuster;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 80)
    private HumanReviewDecision decision;

    @Column(name = "override_reason", columnDefinition = "text")
    private String overrideReason;

    @Column(columnDefinition = "text")
    private String notes;

    @Column(name = "reviewed_at", nullable = false)
    private Instant reviewedAt = Instant.now();

    public Claim getClaim() {
        return claim;
    }

    public void setClaim(Claim claim) {
        this.claim = claim;
    }

    public AiTriageResult getAiTriageResult() {
        return aiTriageResult;
    }

    public void setAiTriageResult(AiTriageResult aiTriageResult) {
        this.aiTriageResult = aiTriageResult;
    }

    public Adjuster getReviewerAdjuster() {
        return reviewerAdjuster;
    }

    public void setReviewerAdjuster(Adjuster reviewerAdjuster) {
        this.reviewerAdjuster = reviewerAdjuster;
    }

    public HumanReviewDecision getDecision() {
        return decision;
    }

    public void setDecision(HumanReviewDecision decision) {
        this.decision = decision;
    }

    public String getOverrideReason() {
        return overrideReason;
    }

    public void setOverrideReason(String overrideReason) {
        this.overrideReason = overrideReason;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public Instant getReviewedAt() {
        return reviewedAt;
    }
}
