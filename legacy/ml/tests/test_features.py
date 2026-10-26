from insureflow_ml.features import FEATURE_COLUMNS, load_training_frame


def test_load_training_frame_builds_model_features(sample_data_dir):
    frame = load_training_frame(sample_data_dir)

    assert not frame.empty
    assert set(FEATURE_COLUMNS).issubset(frame.columns)
    assert {"severity_label", "fraud_label"}.issubset(frame.columns)
    assert set(frame["severity_label"]).issubset({"LOW", "MEDIUM", "HIGH"})
    assert set(frame["fraud_label"]).issubset({"LOW", "MEDIUM", "HIGH"})
    assert frame["loss_report_delay_days"].min() >= 0
    assert frame["policy_age_days"].min() >= 0
    assert frame["prior_claims_count"].min() >= 0
