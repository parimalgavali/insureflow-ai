# System Context

InsureFlow AI simulates property and casualty insurance policy and claims workflows in a cloud-native portfolio system. It is inspired by enterprise insurance core-system patterns while remaining independent of any official vendor implementation.

The primary users are:

- Adjusters who review claims, documents, coverage context, AI triage signals, and timeline events.
- Senior adjusters who handle escalations, overrides, and complex claim review.
- Underwriters who need policy and coverage context.
- Admins who manage system configuration, auditability, and governance.
- Customers who submit first notice of loss details in later phases.
- External systems that exchange policy, claim, reserve, and status updates through integration APIs.

AI supports triage, document extraction, claim summarization, and grounded assistance over claim and policy information. These AI features are decision-support signals only.

Humans make final insurance decisions. The system is designed to preserve review, override, and audit trails for responsible AI governance.
