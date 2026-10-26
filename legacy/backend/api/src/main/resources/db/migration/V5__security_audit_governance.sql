ALTER TABLE ai_triage_results
    ADD COLUMN input_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN output_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX idx_audit_logs_correlation_id ON audit_logs(correlation_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

INSERT INTO model_versions (id, model_name, version, model_type, artifact_uri, metrics, active)
VALUES
    (
        gen_random_uuid(),
        'rule-based-triage',
        'rules-v1',
        'RULES_ENGINE',
        'ai-services/triage-service',
        '{"purpose": "Transparent claim severity, fraud, and litigation triage"}'::jsonb,
        true
    ),
    (
        gen_random_uuid(),
        'ml-triage-baseline',
        'local-baseline-v1',
        'SCIKIT_LEARN',
        'ml/artifacts',
        '{"purpose": "Local synthetic-data severity and fraud-risk scoring"}'::jsonb,
        true
    )
ON CONFLICT (model_name, version) DO NOTHING;

INSERT INTO prompt_versions (id, prompt_name, version, template, model_name, active)
VALUES
    (
        gen_random_uuid(),
        'document-extraction',
        '2026-06-local-v1',
        'Extract structured claim document fields and return valid JSON.',
        'deterministic-local-provider',
        true
    ),
    (
        gen_random_uuid(),
        'rag-adjuster-answer',
        '2026-06-local-v1',
        'Answer adjuster questions using retrieved sources and cite evidence.',
        'deterministic-rag-local',
        true
    )
ON CONFLICT (prompt_name, version) DO NOTHING;
