package com.insureflow.api.claims.domain;

import com.insureflow.api.shared.domain.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.Map;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "claim_documents")
public class ClaimDocument extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "claim_id", nullable = false)
    private Claim claim;

    @Column(name = "document_type", nullable = false, length = 80)
    private String documentType;

    @Column(name = "file_name", nullable = false)
    private String fileName;

    @Column(name = "storage_uri", nullable = false)
    private String storageUri;

    @Column(name = "content_type", length = 120)
    private String contentType;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "extracted_metadata", nullable = false, columnDefinition = "jsonb")
    private Map<String, Object> extractedMetadata = Map.of();

    @Column(name = "uploaded_at", nullable = false)
    private Instant uploadedAt;

    @PrePersist
    void setUploadedAt() {
        if (uploadedAt == null) {
            uploadedAt = Instant.now();
        }
    }

    public Claim getClaim() {
        return claim;
    }

    public void setClaim(Claim claim) {
        this.claim = claim;
    }

    public String getDocumentType() {
        return documentType;
    }

    public void setDocumentType(String documentType) {
        this.documentType = documentType;
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public String getStorageUri() {
        return storageUri;
    }

    public void setStorageUri(String storageUri) {
        this.storageUri = storageUri;
    }

    public String getContentType() {
        return contentType;
    }

    public void setContentType(String contentType) {
        this.contentType = contentType;
    }

    public Map<String, Object> getExtractedMetadata() {
        return extractedMetadata;
    }

    public void setExtractedMetadata(Map<String, Object> extractedMetadata) {
        this.extractedMetadata = extractedMetadata;
    }

    public Instant getUploadedAt() {
        return uploadedAt;
    }
}
