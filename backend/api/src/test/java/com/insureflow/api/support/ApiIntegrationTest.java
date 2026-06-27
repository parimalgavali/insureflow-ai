package com.insureflow.api.support;

import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import com.insureflow.api.security.InsureFlowRole;
import com.insureflow.api.security.JwtService;
import java.util.Set;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.annotation.DirtiesContext;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
public abstract class ApiIntegrationTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @LocalServerPort
    protected int port;

    @Autowired
    protected TestRestTemplate restTemplate;

    @Autowired(required = false)
    private JwtService jwtService;

    protected String baseUrl;

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @BeforeEach
    void setBaseUrl() {
        baseUrl = "http://localhost:" + port + "/api/v1";
        if (jwtService != null && restTemplate.getRestTemplate().getInterceptors().isEmpty()) {
            String token = jwtService.createToken("integration-test-admin", Set.of(InsureFlowRole.ADMIN));
            restTemplate.getRestTemplate().getInterceptors().add((request, body, execution) -> {
                if (!request.getHeaders().containsKey("Authorization")) {
                    request.getHeaders().setBearerAuth(token);
                }
                return execution.execute(request, body);
            });
        }
    }
}
