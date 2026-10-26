package com.insureflow.api;

import com.insureflow.api.ai.triage.config.AiTriageProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;

@SpringBootApplication
@EnableConfigurationProperties(AiTriageProperties.class)
public class InsureFlowApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(InsureFlowApiApplication.class, args);
    }
}
