package com.insureflow.api.claims.domain;

import com.insureflow.api.policy.domain.Customer;
import com.insureflow.api.policy.domain.Policy;
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
import java.time.Instant;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "claims")
public class Claim extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "policy_id", nullable = false)
    private Policy policy;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    @Column(name = "assigned_adjuster_id")
    private UUID assignedAdjusterId;

    @Column(name = "claim_number", nullable = false, unique = true, length = 60)
    private String claimNumber;

    @Enumerated(EnumType.STRING)
    @Column(name = "claim_type", nullable = false, length = 80)
    private ClaimType claimType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 60)
    private ClaimStatus status;

    @Column(name = "loss_date", nullable = false)
    private LocalDate lossDate;

    @Column(name = "reported_at", nullable = false)
    private Instant reportedAt;

    @Column(name = "loss_location")
    private String lossLocation;

    @Column(nullable = false)
    private String description;

    @Column(name = "estimated_loss_amount", precision = 14, scale = 2)
    private BigDecimal estimatedLossAmount;

    @Column(length = 40)
    private String severity;

    public Policy getPolicy() {
        return policy;
    }

    public void setPolicy(Policy policy) {
        this.policy = policy;
    }

    public Customer getCustomer() {
        return customer;
    }

    public void setCustomer(Customer customer) {
        this.customer = customer;
    }

    public UUID getAssignedAdjusterId() {
        return assignedAdjusterId;
    }

    public void setAssignedAdjusterId(UUID assignedAdjusterId) {
        this.assignedAdjusterId = assignedAdjusterId;
    }

    public String getClaimNumber() {
        return claimNumber;
    }

    public void setClaimNumber(String claimNumber) {
        this.claimNumber = claimNumber;
    }

    public ClaimType getClaimType() {
        return claimType;
    }

    public void setClaimType(ClaimType claimType) {
        this.claimType = claimType;
    }

    public ClaimStatus getStatus() {
        return status;
    }

    public void setStatus(ClaimStatus status) {
        this.status = status;
    }

    public LocalDate getLossDate() {
        return lossDate;
    }

    public void setLossDate(LocalDate lossDate) {
        this.lossDate = lossDate;
    }

    public Instant getReportedAt() {
        return reportedAt;
    }

    public void setReportedAt(Instant reportedAt) {
        this.reportedAt = reportedAt;
    }

    public String getLossLocation() {
        return lossLocation;
    }

    public void setLossLocation(String lossLocation) {
        this.lossLocation = lossLocation;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public BigDecimal getEstimatedLossAmount() {
        return estimatedLossAmount;
    }

    public void setEstimatedLossAmount(BigDecimal estimatedLossAmount) {
        this.estimatedLossAmount = estimatedLossAmount;
    }

    public String getSeverity() {
        return severity;
    }

    public void setSeverity(String severity) {
        this.severity = severity;
    }
}
