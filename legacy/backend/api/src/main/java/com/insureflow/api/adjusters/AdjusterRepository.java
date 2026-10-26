package com.insureflow.api.adjusters;

import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AdjusterRepository extends JpaRepository<Adjuster, UUID> {}
