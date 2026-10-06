import numpy as np
import pandas as pd
import pytest

from agriforecast.data import features


def calendar():
    frame = pd.DataFrame({"station": "station-A", "date": pd.date_range("2024-01-01", periods=20)})
    for name in [
        "SOIL_MOISTURE_5_DAILY",
        "SOIL_MOISTURE_10_DAILY",
        "P_DAILY_CALC",
        "T_DAILY_AVG",
        "RH_DAILY_AVG",
        "SOLARAD_DAILY",
    ]:
        frame[name] = np.arange(len(frame), dtype=float)
    return frame


@pytest.mark.parametrize("horizon", [1, 7])
def test_target_is_observation_on_exact_future_calendar_day(horizon):
    actual = features(calendar(), horizon)
    assert (actual.target_date - actual.origin).eq(pd.Timedelta(days=horizon)).all()
    np.testing.assert_equal(actual.target.iloc[:-horizon], np.arange(horizon, 20))
    assert actual.target.iloc[-horizon:].isna().all()


@pytest.mark.parametrize("bad_horizon", [True, False, 0, 1.5])
def test_horizon_requires_positive_nonboolean_integer(bad_horizon):
    with pytest.raises(ValueError, match="horizon"):
        features(calendar(), bad_horizon)


@pytest.mark.parametrize("bad_station", [None, "", "   "])
def test_missing_station_cannot_silently_drop_observations(bad_station):
    frame = calendar()
    frame.loc[2, "station"] = bad_station
    with pytest.raises(ValueError, match="station"):
        features(frame)


@pytest.mark.parametrize("fault", ["NaT", "gap", "duplicate", "intraday", "string", "empty"])
def test_invalid_calendar_cannot_create_a_misaligned_target(fault):
    frame = calendar()
    if fault == "NaT":
        frame.loc[19, "date"] = pd.NaT
    elif fault == "gap":
        frame = frame.drop(index=2)
    elif fault == "duplicate":
        frame.loc[2, "date"] = frame.loc[1, "date"]
    elif fault == "intraday":
        frame["date"] += pd.Timedelta(hours=12)
    elif fault == "string":
        frame["date"] = frame.date.astype(str)
    else:
        frame = frame.iloc[:0]
    with pytest.raises(ValueError, match="calendar"):
        features(frame)
