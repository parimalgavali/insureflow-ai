package com.insureflow.api.governance;

import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/governance")
class GovernanceController {

    private final ModelVersionRepository modelVersionRepository;
    private final PromptVersionRepository promptVersionRepository;

    GovernanceController(
            ModelVersionRepository modelVersionRepository,
            PromptVersionRepository promptVersionRepository) {
        this.modelVersionRepository = modelVersionRepository;
        this.promptVersionRepository = promptVersionRepository;
    }

    @GetMapping("/model-versions")
    List<ModelVersionResponse> modelVersions() {
        return modelVersionRepository.findAllByOrderByModelNameAscVersionAsc().stream()
                .map(ModelVersionResponse::from)
                .toList();
    }

    @GetMapping("/prompt-versions")
    List<PromptVersionResponse> promptVersions() {
        return promptVersionRepository.findAllByOrderByPromptNameAscVersionAsc().stream()
                .map(PromptVersionResponse::from)
                .toList();
    }
}
