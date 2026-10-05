"""Forecast baselines, purged expanding folds and historical residual intervals."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from agriforecast.data import FEATURES

METHODS = ["persistence", "seasonal_climatology", "ridge", "random_forest"]


def metrics(y, prediction):
    return {
        "rmse": float(root_mean_squared_error(y, prediction)),
        "mae": float(mean_absolute_error(y, prediction)),
        "r2": float(r2_score(y, prediction)),
        "n": len(y),
    }


def fold(table: pd.DataFrame, year: int):
    boundary = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year, month=12, day=31)
    train = table[table.target_date < boundary]
    validation = table[(table.origin >= boundary) & (table.target_date <= end)]
    if train.empty or validation.empty or not train.target_date.max() < validation.origin.min():
        raise ValueError("Invalid or unpurged temporal fold")
    return train, validation


def fit(method, train):
    if method == "persistence":
        return {"kind": method, "model": None}
    if method == "seasonal_climatology":
        # Fit to each observed target day, not an origin-day shifted seasonal label.
        unique = train[["target_date", "target"]].drop_duplicates("target_date")
        day = unique.target_date.dt.dayofyear.to_numpy()
        values = unique.target.to_numpy()
        daily = []
        for d in range(1, 367):
            distance = np.minimum(abs(day - d), 366 - abs(day - d))
            local = values[distance <= 15]
            daily.append(float(local.mean()) if len(local) else float(values.mean()))
        return {"kind": method, "climatology": daily, "model": None}
    if method == "ridge":
        model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=1.0))
    elif method == "random_forest":
        model = make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestRegressor(
                n_estimators=160, max_depth=12, min_samples_leaf=5, n_jobs=2, random_state=42
            ),
        )
    else:
        raise ValueError("Unknown forecasting method")
    model.fit(train[FEATURES], train.target)
    return {"kind": method, "model": model}


def predict(state, table):
    if state["kind"] == "persistence":
        return table.SOIL_MOISTURE_10_DAILY.to_numpy()
    if state["kind"] == "seasonal_climatology":
        return np.array(state["climatology"])[table.target_date.dt.dayofyear.to_numpy() - 1]
    return np.clip(state["model"].predict(table[FEATURES]), 0, 1)


def residual_radius(errors, quantile=0.9):
    errors = np.asarray(errors, dtype=float)
    if (
        errors.ndim != 1
        or len(errors) == 0
        or not np.isfinite(errors).all()
        or not 0 < quantile < 1
    ):
        raise ValueError("Finite residuals and quantile in (0,1) required")
    rank = min(int(np.ceil((len(errors) + 1) * quantile)), len(errors))
    return float(np.sort(np.abs(errors))[rank - 1])
