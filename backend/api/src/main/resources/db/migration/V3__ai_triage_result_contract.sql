ALTER TABLE ai_triage_results
    ADD COLUMN result_sequence BIGSERIAL,
    ADD COLUMN model_name VARCHAR(120),
    ADD COLUMN model_version VARCHAR(80),
    ADD COLUMN severity_label VARCHAR(40),
    ADD COLUMN fraud_risk_label VARCHAR(40),
    ADD COLUMN litigation_risk_label VARCHAR(40),
    ADD COLUMN human_review_required BOOLEAN;

UPDATE ai_triage_results
SET model_name = 'rule-based-triage',
    model_version = 'rules-v1',
    severity_label = CASE
        WHEN severity_score >= 0.7000 THEN 'HIGH'
        WHEN severity_score >= 0.3500 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    fraud_risk_label = CASE
        WHEN fraud_risk_score >= 0.7000 THEN 'HIGH'
        WHEN fraud_risk_score >= 0.3500 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    litigation_risk_label = CASE
        WHEN litigation_risk_score >= 0.7000 THEN 'HIGH'
        WHEN litigation_risk_score >= 0.3500 THEN 'MEDIUM'
        ELSE 'LOW'
    END,
    human_review_required = severity_score >= 0.7000
        OR fraud_risk_score >= 0.7000
        OR litigation_risk_score >= 0.7000;

ALTER TABLE ai_triage_results
    ALTER COLUMN model_name SET NOT NULL,
    ALTER COLUMN model_name SET DEFAULT 'rule-based-triage',
    ALTER COLUMN model_version SET NOT NULL,
    ALTER COLUMN model_version SET DEFAULT 'rules-v1',
    ALTER COLUMN severity_label SET NOT NULL,
    ALTER COLUMN severity_label SET DEFAULT 'LOW',
    ALTER COLUMN fraud_risk_label SET NOT NULL,
    ALTER COLUMN fraud_risk_label SET DEFAULT 'LOW',
    ALTER COLUMN litigation_risk_label SET NOT NULL,
    ALTER COLUMN litigation_risk_label SET DEFAULT 'LOW',
    ALTER COLUMN human_review_required SET NOT NULL,
    ALTER COLUMN human_review_required SET DEFAULT false;

CREATE INDEX idx_ai_triage_results_claim_id_created_at
    ON ai_triage_results(claim_id, created_at DESC, result_sequence DESC);
