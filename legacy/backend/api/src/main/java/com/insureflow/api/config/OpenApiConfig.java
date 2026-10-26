package com.insureflow.api.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI insureFlowOpenApi() {
        return new OpenAPI()
                .info(new Info()
                        .title("InsureFlow AI API")
                        .version("0.1.0")
                        .description("Guidewire-inspired claims and policy intelligence API"));
    }
}
