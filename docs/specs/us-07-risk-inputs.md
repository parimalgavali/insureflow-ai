# US-07: Explain when risk cannot be calculated

As a customer, I want to know when a risk signal lacks required information, so missing answers are not mistaken for low risk.

- Require a valid incident date, known event type, explicit third-party/police/witness answers, policy product and nonnegative finite deductible.
- For a collision involving another party, also require whether the party is known. “No” counts as an answer.
- Skip scoring when inputs are missing. Show “Not enough information” and list the details needed, in English and German.
- Keep scoring failures separate: show temporarily unavailable, without an old score.
- Coverage guidance and human review remain possible when risk inputs are missing.
- Revalidate saved cards so legacy default-based scores do not appear as current results.
- Always show that the signal is guidance reviewed by a human. This gate does not establish statistical reliability; remaining defaults and model limitations are in the model card.

Validation covers each missing input, false answers, invalid policy/date inputs, no model call on incomplete facts, legacy cards, correction/restore flows, scoring failures, and UI availability updates.
