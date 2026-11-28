from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from api.agent.schemas import ClaimCard, ClaimFacts, PolicyContext, RiskSignal
from ml.features import facts_to_features
from ml.predict import FraudScorer
from ml.risk_inputs import missing_risk_inputs


def complete(**patch):
    return ClaimFacts(
        **{
            "incident_date": "2026-10-25",
            "event_type": "collision",
            "third_party_involved": True,
            "third_party_known": False,
            "police_report_filed": False,
            "witnesses": False,
            **patch,
        }
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("incident_date", None),
        ("incident_date", "2026-02-30"),
        ("incident_date", "20261025"),
        ("event_type", "unknown"),
        ("third_party_involved", None),
        ("third_party_known", None),
        ("police_report_filed", None),
        ("witnesses", None),
    ],
)
def test_missing_inputs_prevent_prediction(field, value):
    model = Mock()
    scorer = FraudScorer({"model": model, "baseline": {}, "bands": {}, "version": "test"})
    facts = complete(**{field: value})
    assert field in missing_risk_inputs(facts, PolicyContext())
    assert scorer.score(facts, PolicyContext()) is None
    model.predict_proba.assert_not_called()


def test_false_is_known_and_third_party_identity_is_conditional():
    assert missing_risk_inputs(complete(), PolicyContext()) == []
    assert (
        missing_risk_inputs(
            complete(third_party_involved=False, third_party_known=None), PolicyContext()
        )
        == []
    )
    assert (
        missing_risk_inputs(complete(event_type="theft", third_party_known=None), PolicyContext())
        == []
    )


@pytest.mark.parametrize(
    "product,deductible,field",
    [
        ("unknown", 300, "policy_product"),
        ("vollkasko", None, "policy_deductible"),
        ("vollkasko", float("nan"), "policy_deductible"),
        ("vollkasko", -1, "policy_deductible"),
        ("vollkasko", True, "policy_deductible"),
    ],
)
def test_policy_inputs_are_checked(product, deductible, field):
    policy = SimpleNamespace(product=product, deductible_eur=deductible)
    assert field in missing_risk_inputs(complete(), policy)


def test_legacy_saved_signal_is_hidden_when_inputs_are_missing():
    card = ClaimCard.model_validate(
        {
            "facts": complete(police_report_filed=None).model_dump(),
            "policy": PolicyContext().model_dump(),
            "risk": RiskSignal(score=0.01, band="low", reasons=[]).model_dump(),
        }
    )
    assert card.risk is None
    assert card.risk_status == "insufficient_information"
    assert card.risk_missing == ["police_report_filed"]


@pytest.mark.parametrize("event", ["storm_hail", "wild_animal"])
def test_schema_event_names_use_the_documented_third_party_proxy(event):
    assert facts_to_features(complete(event_type=event), PolicyContext())["Fault"] == "Third Party"
