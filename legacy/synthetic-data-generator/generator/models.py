from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Customer:
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    city: str
    country: str
    date_of_birth: str
    created_at: str


@dataclass(frozen=True)
class Policy:
    policy_id: str
    policy_number: str
    customer_id: str
    product_type: str
    status: str
    start_date: str
    end_date: str
    annual_premium_eur: int
    deductible_eur: int
    coverage_limit_eur: int


@dataclass(frozen=True)
class Coverage:
    coverage_id: str
    policy_id: str
    coverage_type: str
    limit_eur: int
    deductible_eur: int
    active: bool


@dataclass(frozen=True)
class Claim:
    claim_id: str
    claim_number: str
    policy_id: str
    customer_id: str
    adjuster_id: str
    claim_type: str
    status: str
    loss_date: str
    reported_date: str
    loss_city: str
    description: str
    estimated_damage_eur: int
    injury_reported: bool
    third_party_involved: bool
    police_report_available: bool


@dataclass(frozen=True)
class ClaimDocument:
    document_id: str
    claim_id: str
    document_type: str
    received_at: str
    source: str


@dataclass(frozen=True)
class ClaimNote:
    note_id: str
    claim_id: str
    adjuster_id: str
    created_at: str
    note_type: str
    body: str


@dataclass(frozen=True)
class ClaimEvent:
    event_id: str
    claim_id: str
    event_type: str
    occurred_at: str
    actor: str
    description: str


@dataclass(frozen=True)
class Adjuster:
    adjuster_id: str
    employee_number: str
    first_name: str
    last_name: str
    region: str
    authority_limit_eur: int
    active: bool


@dataclass(frozen=True)
class Payment:
    payment_id: str
    claim_id: str
    amount_eur: int
    payment_date: str
    payment_type: str
    status: str


@dataclass(frozen=True)
class AITriageLabel:
    label_id: str
    claim_id: str
    severity_score: int
    severity_label: str
    fraud_score: int
    fraud_label: str
    litigation_score: int
    litigation_label: str
    reason_codes: str
    model_version: str


@dataclass(frozen=True)
class SyntheticDocument:
    document_id: str
    claim_id: str
    document_type: str
    text: str


@dataclass(frozen=True)
class GeneratedDataset:
    customers: list[Customer]
    policies: list[Policy]
    coverages: list[Coverage]
    claims: list[Claim]
    claim_documents: list[ClaimDocument]
    claim_notes: list[ClaimNote]
    claim_events: list[ClaimEvent]
    adjusters: list[Adjuster]
    payments: list[Payment]
    ai_triage_labels: list[AITriageLabel]
    documents: list[SyntheticDocument]
