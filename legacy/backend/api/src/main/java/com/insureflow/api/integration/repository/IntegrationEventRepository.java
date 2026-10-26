package com.insureflow.api.integration.repository;

import com.insureflow.api.integration.domain.IntegrationEvent;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface IntegrationEventRepository extends JpaRepository<IntegrationEvent, UUID> {}
