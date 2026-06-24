package com.insureflow.api.database;

import static org.assertj.core.api.Assertions.assertThat;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.util.HashSet;
import java.util.Set;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class FlywayMigrationTest {

    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Test
    void flywayCreatesCoreInsuranceTables() throws Exception {
        Flyway.configure()
                .dataSource(postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword())
                .locations("classpath:db/migration")
                .load()
                .migrate();

        Set<String> tableNames = new HashSet<>();
        try (Connection connection = DriverManager.getConnection(
                        postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
                ResultSet resultSet = connection
                        .createStatement()
                        .executeQuery("""
                                select table_name
                                from information_schema.tables
                                where table_schema = 'public'
                                """)) {
            while (resultSet.next()) {
                tableNames.add(resultSet.getString("table_name"));
            }
        }

        assertThat(tableNames)
                .containsAll(Set.of(
                        "customers",
                        "policies",
                        "coverages",
                        "claims",
                        "claim_documents",
                        "claim_events",
                        "adjusters",
                        "ai_triage_results",
                        "human_reviews",
                        "audit_logs",
                        "model_versions",
                        "prompt_versions"));
    }
}
