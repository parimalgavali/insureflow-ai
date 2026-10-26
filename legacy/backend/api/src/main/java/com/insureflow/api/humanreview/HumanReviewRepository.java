package com.insureflow.api.humanreview;

import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HumanReviewRepository extends JpaRepository<HumanReview, UUID> {
    List<HumanReview> findByClaimClaimNumberOrderByReviewedAtDesc(String claimNumber);
}
