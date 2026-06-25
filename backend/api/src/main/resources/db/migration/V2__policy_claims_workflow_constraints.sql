CREATE TABLE claim_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    adjuster_id UUID REFERENCES adjusters(id),
    note_type VARCHAR(80) NOT NULL,
    body TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_claim_notes_claim_id_created_at ON claim_notes(claim_id, created_at);
CREATE INDEX idx_coverages_policy_type ON coverages(policy_id, coverage_type);
