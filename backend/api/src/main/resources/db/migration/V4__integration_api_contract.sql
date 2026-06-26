CREATE TABLE integration_events (
    id UUID PRIMARY KEY,
    source_system VARCHAR(120) NOT NULL,
    event_type VARCHAR(120) NOT NULL,
    external_reference VARCHAR(160) NOT NULL,
    status VARCHAR(40) NOT NULL,
    claim_number VARCHAR(60),
    policy_number VARCHAR(60),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_integration_events_source_reference
    ON integration_events(source_system, external_reference);

CREATE INDEX idx_integration_events_claim_number
    ON integration_events(claim_number);

CREATE INDEX idx_integration_events_policy_number
    ON integration_events(policy_number);

CREATE TABLE claim_reserves (
    id UUID PRIMARY KEY,
    claim_id UUID NOT NULL REFERENCES claims(id),
    external_reference VARCHAR(160) NOT NULL,
    source_system VARCHAR(120) NOT NULL,
    coverage_code VARCHAR(80) NOT NULL,
    reserve_amount NUMERIC(14, 2) NOT NULL CHECK (reserve_amount >= 0),
    currency VARCHAR(3) NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_claim_reserves_claim_id
    ON claim_reserves(claim_id);

CREATE INDEX idx_claim_reserves_source_reference
    ON claim_reserves(source_system, external_reference);
