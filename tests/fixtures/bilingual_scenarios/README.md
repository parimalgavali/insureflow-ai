# Difficult bilingual conversations

The four scenarios keep English, keep German, switch English to German, and switch German to English. Each recorded fixture has an `_expected.json` file containing the customer turns, language sequence, expected questions/answers and stable facts.

The first customer turn gives competing dates and amounts without confirming either, and leaves other-party involvement unknown. The second says "I don't know" / "Ich weiß nicht" and must not become a guessed date, amount or boolean. The third supplies confirmed core details while leaving witnesses unknown. The controlled composition flags conflicting evidence, which must force an Unclear card even if its proposed status was likely covered.

The API test then submits explicit corrections to date/amount/witnesses and checks the refreshed composition, scorer inputs and before/after history. A later explicit Not known correction clears the witness answer and removes the risk signal. This uses the actual correction controls' null contract; it does not claim that every ambiguous natural-language retraction is interpreted correctly by a live model.

Policy preparation/retrieval uses the fictional `../claim_types_policy.pdf`. All model responses are recorded, and risk scoring is an input-recording probe. These are reproducible application contracts, not live-model language/translation accuracy or real coverage evaluations.

Run with the test database configured:

```sh
uv run pytest tests/test_bilingual_conversations.py
```

The corresponding Vue tests switch a restored conversation's language without creating a new claim, erasing its transcript or changing its saved identifier. They check that the next message uses the selected language.
