ALTER TABLE ai_triage_results
    ADD COLUMN model_name VARCHAR(120) NOT NULL DEFAULT 'rule-based-triage',
    ADD COLUMN model_version VARCHAR(80) NOT NULL DEFAULT 'rules-v1',
    ADD COLUMN severity_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN fraud_risk_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN litigation_risk_label VARCHAR(40) NOT NULL DEFAULT 'LOW',
    ADD COLUMN human_review_required BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX idx_ai_triage_results_claim_id_created_at
    ON ai_triage_results(claim_id, created_at DESC);
