"""Feature selection for the Kaggle vehicle-fraud data and the ClaimFacts -> row mapping.

Only columns that can be *observed in a ClaimPilot conversation or policy record* are used;
everything else would be a training-time-only signal that gets a constant default at inference.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

TARGET = "FraudFound"
SOURCE_FILE = "data/raw/kaggle/carclaims.csv"

# Never used — fairness (protected attributes) or identifiers.
EXCLUDED_FAIRNESS = ["Sex", "MaritalStatus", "Age", "AgeOfPolicyHolder"]
EXCLUDED_IDS = ["PolicyNumber", "RepNumber"]
# Never used — not observable from a conversation + seed policy, so they would be a constant.
EXCLUDED_UNOBSERVABLE = [
    "Make",
    "Year",
    "PolicyType",
    "AgentType",
    "NumberOfSuppliments",
    "AddressChange-Claim",
    "NumberOfCars",
    "DriverRating",
    # claim-filing calendar fields: no plausible causal signal, only noise in explanations
    "WeekOfMonth",
    "WeekOfMonthClaimed",
    "DayOfWeekClaimed",
    "MonthClaimed",
]
EXCLUDED = EXCLUDED_FAIRNESS + EXCLUDED_IDS + EXCLUDED_UNOBSERVABLE

CATEGORICAL = [
    "Month",
    "DayOfWeek",
    "AccidentArea",
    "Fault",
    "VehicleCategory",
    "VehiclePrice",
    "Days:Policy-Accident",
    "Days:Policy-Claim",
    "PastNumberOfClaims",
    "AgeOfVehicle",
    "PoliceReportFiled",
    "WitnessPresent",
    "BasePolicy",
]
NUMERIC = ["Deductible"]
FEATURES = CATEGORICAL + NUMERIC

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEDUCTIBLES = [300, 400, 500, 700]

# Documented defaults for facts the conversation cannot (yet) supply.
DEFAULTS: dict[str, Any] = {
    "AccidentArea": "Urban",
    "VehicleCategory": "Sedan",
    "VehiclePrice": "20,000 to 29,000",
    "Days:Policy-Accident": "more than 30",
    "Days:Policy-Claim": "more than 30",
    "PastNumberOfClaims": "none",
    "AgeOfVehicle": "more than 7",
    "PoliceReportFiled": "No",
    "WitnessPresent": "No",
    "Fault": "Policy Holder",
    "BasePolicy": "All Perils",
}

PRODUCT_TO_BASE_POLICY = {
    "haftpflicht": "Liability",  # third-party liability only
    "teilkasko": "Collision",  # nearest available category; see model card
    "vollkasko": "All Perils",
}

THIRD_PARTY_FAULT_EVENTS = {
    "hit_and_run",
    "theft",
    "vandalism",
    "weather",
    "animal",
    "fire",
    "glass",
}


def load_frame(path: str = SOURCE_FILE) -> pd.DataFrame:
    return pd.read_csv(path)


def split_xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) with only FEATURES; raises if an excluded column sneaks in."""
    leaked = [c for c in EXCLUDED if c in FEATURES]
    if leaked:
        raise ValueError(f"excluded columns in FEATURES: {leaked}")
    x = frame[FEATURES].copy()
    for col in CATEGORICAL:
        x[col] = x[col].astype(str)
    y = (frame[TARGET] == "Yes").astype(int)
    return x, y


def _age_of_vehicle(years: int | None) -> str:
    if years is None:
        return DEFAULTS["AgeOfVehicle"]
    if years <= 0:
        return "new"
    if years >= 8:
        return "more than 7"
    return f"{max(years, 2)} years"


def _deductible(eur: float) -> int:
    return min(DEDUCTIBLES, key=lambda d: abs(d - eur))


def _yes_no(flag: bool | None, default: str) -> str:
    if flag is None:
        return default
    return "Yes" if flag else "No"


def facts_to_features(facts: Any, policy: Any, today: date | None = None) -> dict[str, Any]:
    """Map ClaimFacts + PolicyContext (duck-typed) onto one model row.

    Unknown facts fall back to DEFAULTS, so a sparse conversation yields a *baseline* score,
    not a high one.
    """
    today = today or date.today()
    row: dict[str, Any] = dict(DEFAULTS)

    incident = None
    if getattr(facts, "incident_date", None):
        try:
            incident = date.fromisoformat(facts.incident_date)
        except ValueError:
            incident = None
    incident = incident or today
    row["Month"] = MONTHS[incident.month - 1]
    row["DayOfWeek"] = DAYS[incident.weekday()]

    event = getattr(facts, "event_type", "unknown")
    third_party = getattr(facts, "third_party_involved", None)
    if event in THIRD_PARTY_FAULT_EVENTS or (
        event == "collision" and third_party and getattr(facts, "third_party_known", None)
    ):
        row["Fault"] = "Third Party"

    row["PoliceReportFiled"] = _yes_no(getattr(facts, "police_report_filed", None), "No")
    row["WitnessPresent"] = _yes_no(getattr(facts, "witnesses", None), "No")

    row["BasePolicy"] = PRODUCT_TO_BASE_POLICY.get(getattr(policy, "product", ""), "All Perils")
    row["Deductible"] = _deductible(float(getattr(policy, "deductible_eur", 300.0) or 300.0))
    row["AgeOfVehicle"] = _age_of_vehicle(getattr(policy, "vehicle_age_years", None))
    return {k: row[k] for k in FEATURES}


def row_frame(row: dict[str, Any]) -> pd.DataFrame:
    frame = pd.DataFrame([row], columns=FEATURES)
    for col in CATEGORICAL:
        frame[col] = frame[col].astype(str)
    return frame
