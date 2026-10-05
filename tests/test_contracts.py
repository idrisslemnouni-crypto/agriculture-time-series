import numpy as np
import pandas as pd
import pytest

from agriforecast.modeling import fold, predict, residual_radius


def test_horizon_boundary_purged_by_target_date():
    origins = pd.date_range("2020-12-20", periods=30)
    d = pd.DataFrame({"origin": origins, "target_date": origins + pd.Timedelta(days=7)})
    train, val = fold(d, 2021)
    assert train.target_date.max() < val.origin.min()
    assert train.origin.max() <= pd.Timestamp("2020-12-24")


def test_finite_sample_residual_quantile():
    assert residual_radius(np.arange(10), 0.9) == 9
    with pytest.raises(ValueError):
        residual_radius([float("nan")])


def test_persistence_uses_current_measurement_only():
    d = pd.DataFrame({"SOIL_MOISTURE_10_DAILY": [0.2, 0.3], "target": [0.8, 0.9]})
    np.testing.assert_equal(predict({"kind": "persistence"}, d), [0.2, 0.3])


def test_seasonal_target_day_and_leap_day_index():
    d = pd.DataFrame({"target_date": pd.to_datetime(["2024-12-31"])})
    assert predict({"kind": "seasonal_climatology", "climatology": list(range(366))}, d)[0] == 365


def test_actual_predictions_physical_and_purged():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    if not (root / "reports/test-predictions.csv").exists():
        pytest.skip("Executed results unavailable")
    d = pd.read_csv(root / "reports/test-predictions.csv", parse_dates=["origin", "target_date"])
    assert (d.target_date - d.origin).dt.days.equals(d.horizon_days)
    assert d.selected_prediction.between(0, 1).all()
    assert (d.lower <= d.upper).all()
    b = pd.read_csv(
        root / "reports/backtest.csv", parse_dates=["train_target_max", "first_validation_origin"]
    )
    assert (b.train_target_max < b.first_validation_origin).all()
