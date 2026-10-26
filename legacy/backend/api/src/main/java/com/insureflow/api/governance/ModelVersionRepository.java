package com.insureflow.api.governance;

import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelVersionRepository extends JpaRepository<ModelVersion, UUID> {
    List<ModelVersion> findAllByOrderByModelNameAscVersionAsc();
}
