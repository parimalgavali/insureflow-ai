package com.insureflow.api.database;

import static org.assertj.core.api.Assertions.assertThat;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
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
                        "claim_notes",
                        "adjusters",
                        "ai_triage_results",
                        "human_reviews",
                        "audit_logs",
                        "model_versions",
                        "prompt_versions"));

        Set<String> aiTriageResultColumnNames = new HashSet<>();
        try (Connection connection = DriverManager.getConnection(
                        postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
                ResultSet resultSet = connection
                        .createStatement()
                        .executeQuery("""
                                select column_name
                                from information_schema.columns
                                where table_schema = 'public'
                                  and table_name = 'ai_triage_results'
                                """)) {
            while (resultSet.next()) {
                aiTriageResultColumnNames.add(resultSet.getString("column_name"));
            }
        }

        assertThat(aiTriageResultColumnNames)
                .containsAll(Set.of(
                        "model_name",
                        "model_version",
                        "result_sequence",
                        "severity_label",
                        "fraud_risk_label",
                        "litigation_risk_label",
                        "human_review_required"));
    }

    @Test
    void v3BackfillsTriageContractFromExistingScores() throws Exception {
        String schema = "triage_contract_" + UUID.randomUUID().toString().replace("-", "");
        String jdbcUrl = postgres.getJdbcUrl() + "&currentSchema=" + schema;

        try (Connection connection =
                        DriverManager.getConnection(postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
                Statement statement = connection.createStatement()) {
            statement.execute("create schema " + schema);
        }

        Flyway.configure()
                .dataSource(jdbcUrl, postgres.getUsername(), postgres.getPassword())
                .schemas(schema)
                .locations("classpath:db/migration")
                .target("2")
                .load()
                .migrate();

        try (Connection connection = DriverManager.getConnection(jdbcUrl, postgres.getUsername(), postgres.getPassword());
                Statement statement = connection.createStatement()) {
            statement.execute("""
                    insert into customers (id, customer_number, first_name, last_name, email)
                    values ('00000000-0000-0000-0000-000000000001', 'CUST-V3-1001', 'Avery', 'Stone',
                            'avery.stone@example.test')
                    """);
            statement.execute("""
                    insert into policies (
                        id, customer_id, policy_number, policy_type, status, effective_date, expiration_date,
                        premium_amount
                    )
                    values (
                        '00000000-0000-0000-0000-000000000002',
                        '00000000-0000-0000-0000-000000000001',
                        'POL-V3-1001',
                        'PERSONAL_AUTO',
                        'ACTIVE',
                        '2026-01-01',
                        '2027-01-01',
                        1250.00
                    )
                    """);
            statement.execute("""
                    insert into claims (
                        id, policy_id, customer_id, claim_number, claim_type, status, loss_date, reported_at,
                        description
                    )
                    values (
                        '00000000-0000-0000-0000-000000000003',
                        '00000000-0000-0000-0000-000000000002',
                        '00000000-0000-0000-0000-000000000001',
                        'CLM-V3-1001',
                        'AUTO_COLLISION',
                        'SUBMITTED',
                        '2026-06-24',
                        '2026-06-25T10:15:30Z',
                        'Score-only row before V3'
                    )
                    """);
            statement.execute("""
                    insert into ai_triage_results (
                        id, claim_id, severity_score, fraud_risk_score, litigation_risk_score, recommended_queue
                    )
                    values (
                        '00000000-0000-0000-0000-000000000004',
                        '00000000-0000-0000-0000-000000000003',
                        0.7000,
                        0.3500,
                        0.3499,
                        'STANDARD'
                    )
                    """);
        }

        Flyway.configure()
                .dataSource(jdbcUrl, postgres.getUsername(), postgres.getPassword())
                .schemas(schema)
                .locations("classpath:db/migration")
                .load()
                .migrate();

        try (Connection connection = DriverManager.getConnection(jdbcUrl, postgres.getUsername(), postgres.getPassword());
                ResultSet resultSet = connection
                        .createStatement()
                        .executeQuery("""
                                select severity_label,
                                       fraud_risk_label,
                                       litigation_risk_label,
                                       human_review_required,
                                       result_sequence
                                from ai_triage_results
                                where id = '00000000-0000-0000-0000-000000000004'
                                """)) {
            assertThat(resultSet.next()).isTrue();
            assertThat(resultSet.getString("severity_label")).isEqualTo("HIGH");
            assertThat(resultSet.getString("fraud_risk_label")).isEqualTo("MEDIUM");
            assertThat(resultSet.getString("litigation_risk_label")).isEqualTo("LOW");
            assertThat(resultSet.getBoolean("human_review_required")).isTrue();
            assertThat(resultSet.getLong("result_sequence")).isPositive();
        }
    }
}
