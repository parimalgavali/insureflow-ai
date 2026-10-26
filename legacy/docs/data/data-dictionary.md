# Synthetic Data Dictionary

All files are generated under a selected output directory, usually `data/synthetic` or `data/sample`.

## customers.csv

Customer master data. Key columns: `customer_id`, `first_name`, `last_name`, `email`, `phone`, `city`, `country`, `date_of_birth`, `created_at`.

## policies.csv

Motor policy records. Key columns: `policy_id`, `policy_number`, `customer_id`, `product_type`, `status`, `start_date`, `end_date`, `annual_premium_eur`, `deductible_eur`, `coverage_limit_eur`.

## coverages.csv

Policy coverage rows. Key columns: `coverage_id`, `policy_id`, `coverage_type`, `limit_eur`, `deductible_eur`, `active`.

## claims.csv

Claim header records. Key columns: `claim_id`, `claim_number`, `policy_id`, `customer_id`, `adjuster_id`, `claim_type`, `status`, `loss_date`, `reported_date`, `loss_city`, `description`, `estimated_damage_eur`, `injury_reported`, `third_party_involved`, `police_report_available`.

## claim_documents.csv

Structured document metadata. Key columns: `document_id`, `claim_id`, `document_type`, `received_at`, `source`.

## claim_notes.csv

Adjuster notes. Key columns: `note_id`, `claim_id`, `adjuster_id`, `created_at`, `note_type`, `body`.

## claim_events.csv

Claim timeline events. Key columns: `event_id`, `claim_id`, `event_type`, `occurred_at`, `actor`, `description`.

## adjusters.csv

Adjuster reference data. Key columns: `adjuster_id`, `employee_number`, `first_name`, `last_name`, `region`, `authority_limit_eur`, `active`.

## payments.csv

Synthetic claim payments for approved or paid claims. Key columns: `payment_id`, `claim_id`, `amount_eur`, `payment_date`, `payment_type`, `status`.

## ai_triage_labels.csv

Rule-generated triage labels. Key columns: `label_id`, `claim_id`, `severity_score`, `severity_label`, `fraud_score`, `fraud_label`, `litigation_score`, `litigation_label`, `reason_codes`, `model_version`.

## documents.jsonl

One synthetic text document per line. Key fields: `document_id`, `claim_id`, `document_type`, `text`.

## generation_summary.json

Generation metadata and counts. Key fields: `customers`, `policies`, `coverages`, `claims`, `claim_documents`, `claim_notes`, `claim_events`, `adjusters`, `payments`, `ai_triage_labels`, `documents`, `seed`.
