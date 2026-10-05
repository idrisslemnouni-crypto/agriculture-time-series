"""Execute validation-only selection and frozen future evaluation."""

import hashlib
import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from agriforecast.data import FEATURES, features, read_sources
from agriforecast.modeling import METHODS, fit, fold, metrics, predict, residual_radius


def run(root: Path):
    config = json.loads((root / "configs/default.json").read_text())
    data, evidence = read_sources(root)
    coverage = (
        data.assign(year=data.date.dt.year)
        .groupby("year")
        .agg(
            calendar_days=("date", "size"),
            observed_soil10_days=("SOIL_MOISTURE_10_DAILY", "count"),
        )
    )
    coverage["observed_fraction"] = coverage.observed_soil10_days / coverage.calendar_days
    (root / "reports").mkdir(exist_ok=True)
    coverage.to_csv(root / "reports/coverage.csv")
    all_results, backtest_rows, prediction_frames, artifacts = {}, [], [], {}
    for horizon in config["horizons_days"]:
        table = features(data, horizon).dropna(subset=["target", "SOIL_MOISTURE_10_DAILY"])
        pooled = {name: {"truth": [], "pred": []} for name in METHODS}
        for year in config["validation_years"]:
            train, val = fold(table, year)
            for method in METHODS:
                state = fit(method, train)
                p = predict(state, val)
                pooled[method]["truth"].extend(val.target.tolist())
                pooled[method]["pred"].extend(p.tolist())
                backtest_rows.append(
                    {
                        "horizon_days": horizon,
                        "validation_year": year,
                        "method": method,
                        "train_target_max": train.target_date.max().isoformat(),
                        "first_validation_origin": val.origin.min().isoformat(),
                        **metrics(val.target, p),
                    }
                )
        validation = {name: metrics(item["truth"], item["pred"]) for name, item in pooled.items()}
        chosen = min(validation, key=lambda n: validation[n]["rmse"])
        selected_errors = np.array(pooled[chosen]["truth"]) - np.array(pooled[chosen]["pred"])
        radius = residual_radius(selected_errors, config["interval_quantile"])
        train = table[table.target_date < config["test_start"]]
        test = table[
            (table.origin >= config["test_start"]) & (table.target_date <= config["test_end"])
        ]
        if train.target_date.max() >= test.origin.min():
            raise ValueError("Final horizon purge failed")
        test_results = {}
        predictions = test[["origin", "target_date", "target"]].copy()
        for method in METHODS:
            state = fit(method, train)
            p = predict(state, test)
            test_results[method] = metrics(test.target, p)
            predictions[method] = p
            if method == chosen:
                artifacts[str(horizon)] = {
                    **state,
                    "radius": radius,
                    "horizon_days": horizon,
                    "features": FEATURES,
                }
        predictions["selected_prediction"] = predictions[chosen]
        predictions["lower"] = np.maximum(0, predictions.selected_prediction - radius)
        predictions["upper"] = np.minimum(1, predictions.selected_prediction + radius)
        predictions["horizon_days"] = horizon
        coverage = float(
            (
                (predictions.target >= predictions.lower)
                & (predictions.target <= predictions.upper)
            ).mean()
        )
        all_results[str(horizon)] = {
            "validation": validation,
            "selected_on_validation": chosen,
            "test": test_results,
            "historical_error_radius": radius,
            "test_interval_coverage": coverage,
            "test_interval_mean_width": float((predictions.upper - predictions.lower).mean()),
            "train_rows": len(train),
            "test_rows": len(test),
        }
        prediction_frames.append(predictions)
    reports = root / "reports"
    (reports / "figures").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(backtest_rows).to_csv(reports / "backtest.csv", index=False)
    output = {
        "config": config,
        "data": evidence,
        "horizons": all_results,
        "interval_caveat": "Historical residual intervals; serial dependence and drift mean nominal coverage is not guaranteed",
    }
    (root / "models").mkdir(exist_ok=True)
    joblib.dump(artifacts, root / "models/forecasts.joblib")
    output["model_sha256"] = hashlib.sha256(
        (root / "models/forecasts.joblib").read_bytes()
    ).hexdigest()
    (reports / "metrics.json").write_text(json.dumps(output, indent=2))
    pd.concat(prediction_frames).to_csv(reports / "test-predictions.csv", index=False)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), layout="constrained")
    for ax, predictions, horizon in zip(
        axes, prediction_frames, config["horizons_days"], strict=True
    ):
        plotted = predictions.set_index("target_date").reindex(
            pd.date_range(config["test_start"], config["test_end"], freq="D")
        )
        ax.plot(
            plotted.index, plotted.target, label="Observed 10 cm moisture", color="#222222", lw=1
        )
        ax.plot(
            plotted.index,
            plotted.selected_prediction,
            label=all_results[str(horizon)]["selected_on_validation"],
            color="#227b62",
            lw=1,
        )
        ax.fill_between(
            plotted.index,
            plotted.lower,
            plotted.upper,
            alpha=0.18,
            color="#227b62",
            label="90% historical-error interval",
        )
        ax.set_title(
            f"Direct horizon {horizon} days · frozen model, new measurements at each origin"
        )
        ax.set_ylabel("m³/m³")
        ax.set_xlim(pd.Timestamp(config["test_start"]), pd.Timestamp(config["test_end"]))
        ax.legend(fontsize=8, loc="upper right")
    fig.suptitle("NOAA Missouri · future test 2023–2024 · gaps retain missing measurements")
    fig.savefig(reports / "figures/forecast-intervals.png", dpi=150)
    plt.close(fig)
    summary = []
    for h, v in all_results.items():
        for method, m in v["test"].items():
            summary.append({"horizon_days": int(h), "method": method, **m})
    pd.DataFrame(summary).to_csv(reports / "comparison.csv", index=False)
    return output


if __name__ == "__main__":
    result = run(Path.cwd())
    print(json.dumps(result["horizons"], indent=2))
