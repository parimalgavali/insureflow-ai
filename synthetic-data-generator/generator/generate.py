from __future__ import annotations

import random
import uuid
from datetime import date, timedelta

from generator.config import GeneratorConfig
from generator.documents import render_document
from generator.models import (
    AITriageLabel,
    Adjuster,
    Claim,
    ClaimDocument,
    ClaimEvent,
    ClaimNote,
    Coverage,
    Customer,
    GeneratedDataset,
    Payment,
    Policy,
    SyntheticDocument,
)
from generator.reference_data import (
    CITIES,
    CLAIM_STATUSES,
    CLAIM_TYPES,
    COVERAGE_TYPES,
    FIRST_NAMES,
    LAST_NAMES,
    PRODUCT_TYPES,
)
from generator.rules import score_fraud, score_litigation, score_severity


def _uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def _iso(base: date, days: int) -> str:
    return (base + timedelta(days=days)).isoformat()


def _choose(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _generate_customers(config: GeneratorConfig, rng: random.Random) -> list[Customer]:
    customers: list[Customer] = []
    for index in range(config.customers):
        first_name = _choose(rng, FIRST_NAMES)
        last_name = _choose(rng, LAST_NAMES)
        customer_number = index + 1
        customers.append(
            Customer(
                customer_id=_uuid(rng),
                first_name=first_name,
                last_name=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}{customer_number}@example.test",
                phone=f"+49-555-{customer_number:06d}",
                city=_choose(rng, CITIES),
                country="DE",
                date_of_birth=_iso(date(1960, 1, 1), rng.randint(7_000, 18_000)),
                created_at=_iso(date(2024, 1, 1), rng.randint(0, 730)),
            )
        )
    return customers


def _generate_adjusters(config: GeneratorConfig, rng: random.Random) -> list[Adjuster]:
    adjusters: list[Adjuster] = []
    for index in range(config.adjusters):
        adjusters.append(
            Adjuster(
                adjuster_id=_uuid(rng),
                employee_number=f"ADJ-{index + 1:04d}",
                first_name=_choose(rng, FIRST_NAMES),
                last_name=_choose(rng, LAST_NAMES),
                region=_choose(rng, CITIES),
                authority_limit_eur=rng.choice([10_000, 25_000, 50_000, 100_000]),
                active=True,
            )
        )
    return adjusters


def _generate_policies(
    config: GeneratorConfig,
    rng: random.Random,
    customers: list[Customer],
) -> tuple[list[Policy], list[Coverage]]:
    policies: list[Policy] = []
    coverages: list[Coverage] = []
    for index in range(config.policies):
        customer = customers[index % len(customers)]
        start_offset = rng.randint(0, 700)
        start_date = date(2024, 1, 1) + timedelta(days=start_offset)
        policy = Policy(
            policy_id=_uuid(rng),
            policy_number=f"POL-{2026}-{index + 1:06d}",
            customer_id=customer.customer_id,
            product_type=_choose(rng, PRODUCT_TYPES),
            status=rng.choice(["ACTIVE", "ACTIVE", "ACTIVE", "EXPIRED"]),
            start_date=start_date.isoformat(),
            end_date=(start_date + timedelta(days=365)).isoformat(),
            annual_premium_eur=rng.randint(480, 2_400),
            deductible_eur=rng.choice([150, 300, 500, 750, 1_000]),
            coverage_limit_eur=rng.choice([25_000, 50_000, 100_000, 250_000]),
        )
        policies.append(policy)

        for coverage_type in rng.sample(COVERAGE_TYPES, rng.randint(2, 4)):
            coverages.append(
                Coverage(
                    coverage_id=_uuid(rng),
                    policy_id=policy.policy_id,
                    coverage_type=coverage_type,
                    limit_eur=min(policy.coverage_limit_eur, rng.choice([10_000, 25_000, 50_000, 100_000])),
                    deductible_eur=policy.deductible_eur,
                    active=policy.status == "ACTIVE",
                )
            )
    return policies, coverages


def _claim_description(
    rng: random.Random,
    claim_type: str,
    city: str,
    injury_reported: bool,
    third_party_involved: bool,
) -> str:
    legal_phrase = " Customer mentioned lawyer review." if injury_reported and rng.random() < 0.35 else ""
    third_party_phrase = " Another driver was involved." if third_party_involved else " No other party was involved."
    injury_phrase = " Injury symptoms were reported." if injury_reported else " No injuries were reported."
    return (
        f"{claim_type.replace('_', ' ').title()} reported in {city}."
        f"{third_party_phrase}{injury_phrase}{legal_phrase}"
    )


def _eligible_document_types(claim: Claim) -> list[str]:
    document_types = [
        "FNOL_STATEMENT",
        "REPAIR_INVOICE",
        "CUSTOMER_EMAIL",
        "ADJUSTER_NOTE",
    ]
    if claim.police_report_available:
        document_types.append("POLICE_REPORT")
    if claim.injury_reported:
        document_types.append("MEDICAL_REPORT")
    return document_types


def _generate_claims(
    config: GeneratorConfig,
    rng: random.Random,
    policies: list[Policy],
    adjusters: list[Adjuster],
) -> tuple[
    list[Claim],
    list[ClaimDocument],
    list[ClaimNote],
    list[ClaimEvent],
    list[Payment],
    list[AITriageLabel],
    list[SyntheticDocument],
]:
    claims: list[Claim] = []
    claim_documents: list[ClaimDocument] = []
    claim_notes: list[ClaimNote] = []
    claim_events: list[ClaimEvent] = []
    payments: list[Payment] = []
    ai_triage_labels: list[AITriageLabel] = []
    documents: list[SyntheticDocument] = []
    customer_claim_counts: dict[str, int] = {}

    for index in range(config.claims):
        policy = policies[index % len(policies)]
        adjuster = adjusters[index % len(adjusters)]
        policy_start = date.fromisoformat(policy.start_date)
        loss_date = policy_start + timedelta(days=rng.randint(1, 330))
        fnol_delay_days = rng.randint(0, 35)
        reported_date = loss_date + timedelta(days=fnol_delay_days)
        claim_type = _choose(rng, CLAIM_TYPES)
        injury_reported = claim_type == "BODILY_INJURY" or rng.random() < 0.18
        third_party_involved = rng.random() < 0.42
        police_report_available = rng.random() < 0.72
        estimated_damage = rng.randint(500, 45_000)
        status = _choose(rng, CLAIM_STATUSES)
        description = _claim_description(
            rng,
            claim_type,
            _choose(rng, CITIES),
            injury_reported,
            third_party_involved,
        )
        claim = Claim(
            claim_id=_uuid(rng),
            claim_number=f"CLM-{2026}-{index + 1:06d}",
            policy_id=policy.policy_id,
            customer_id=policy.customer_id,
            adjuster_id=adjuster.adjuster_id,
            claim_type=claim_type,
            status=status,
            loss_date=loss_date.isoformat(),
            reported_date=reported_date.isoformat(),
            loss_city=_choose(rng, CITIES),
            description=description,
            estimated_damage_eur=estimated_damage,
            injury_reported=injury_reported,
            third_party_involved=third_party_involved,
            police_report_available=police_report_available,
        )
        claims.append(claim)

        prior_claims_count = customer_claim_counts.get(policy.customer_id, 0)
        customer_claim_counts[policy.customer_id] = prior_claims_count + 1
        severity = score_severity(
            estimated_damage_eur=claim.estimated_damage_eur,
            injury_reported=claim.injury_reported,
            third_party_involved=claim.third_party_involved,
        )
        fraud = score_fraud(
            policy_age_days=(loss_date - policy_start).days,
            fnol_delay_days=fnol_delay_days,
            police_report_available=claim.police_report_available,
            prior_claims_count=prior_claims_count,
        )
        litigation = score_litigation(
            injury_reported=claim.injury_reported,
            description=claim.description,
            third_party_involved=claim.third_party_involved,
        )
        reason_codes = sorted(set(severity["reason_codes"] + fraud["reason_codes"] + litigation["reason_codes"]))
        ai_triage_labels.append(
            AITriageLabel(
                label_id=_uuid(rng),
                claim_id=claim.claim_id,
                severity_score=severity["score"],
                severity_label=severity["label"],
                fraud_score=fraud["score"],
                fraud_label=fraud["label"],
                litigation_score=litigation["score"],
                litigation_label=litigation["label"],
                reason_codes=";".join(reason_codes),
                model_version="rules-v1",
            )
        )

        eligible_document_types = _eligible_document_types(claim)
        document_types = rng.sample(eligible_document_types, rng.randint(1, min(3, len(eligible_document_types))))
        for document_type in document_types:
            claim_document = ClaimDocument(
                document_id=_uuid(rng),
                claim_id=claim.claim_id,
                document_type=document_type,
                received_at=reported_date.isoformat(),
                source=rng.choice(["CUSTOMER_PORTAL", "EMAIL", "ADJUSTER_UPLOAD"]),
            )
            claim_documents.append(claim_document)
            documents.append(render_document(claim, claim_document))

        claim_notes.append(
            ClaimNote(
                note_id=_uuid(rng),
                claim_id=claim.claim_id,
                adjuster_id=claim.adjuster_id,
                created_at=reported_date.isoformat(),
                note_type="INITIAL_REVIEW",
                body=f"Initial review created for {claim.claim_number} with status {claim.status}.",
            )
        )

        event_count = rng.randint(1, 4)
        for event_index in range(event_count):
            claim_events.append(
                ClaimEvent(
                    event_id=_uuid(rng),
                    claim_id=claim.claim_id,
                    event_type=rng.choice(["FNOL_RECEIVED", "ASSIGNED", "DOCUMENT_RECEIVED", "RESERVE_UPDATED"]),
                    occurred_at=(reported_date + timedelta(days=event_index)).isoformat(),
                    actor=rng.choice(["SYSTEM", "ADJUSTER", "CUSTOMER"]),
                    description=f"Claim event {event_index + 1} for {claim.claim_number}.",
                )
            )

        if status in {"APPROVED", "PAID"}:
            for payment_index in range(rng.randint(0, 2)):
                payments.append(
                    Payment(
                        payment_id=_uuid(rng),
                        claim_id=claim.claim_id,
                        amount_eur=max(100, min(estimated_damage, estimated_damage // (payment_index + 2))),
                        payment_date=(reported_date + timedelta(days=7 + payment_index * 14)).isoformat(),
                        payment_type=rng.choice(["INDEMNITY", "EXPENSE", "REPAIR_VENDOR"]),
                        status="PAID" if status == "PAID" else "APPROVED",
                    )
                )

    return claims, claim_documents, claim_notes, claim_events, payments, ai_triage_labels, documents


def generate_dataset(config: GeneratorConfig) -> GeneratedDataset:
    if min(config.customers, config.policies, config.claims, config.adjusters) < 1:
        raise ValueError("customers, policies, claims, and adjusters must all be at least 1")

    rng = random.Random(config.seed)
    customers = _generate_customers(config, rng)
    adjusters = _generate_adjusters(config, rng)
    policies, coverages = _generate_policies(config, rng, customers)
    claims, claim_documents, claim_notes, claim_events, payments, labels, documents = _generate_claims(
        config,
        rng,
        policies,
        adjusters,
    )

    return GeneratedDataset(
        customers=customers,
        policies=policies,
        coverages=coverages,
        claims=claims,
        claim_documents=claim_documents,
        claim_notes=claim_notes,
        claim_events=claim_events,
        adjusters=adjusters,
        payments=payments,
        ai_triage_labels=labels,
        documents=documents,
    )
