# Local verification — 5 October 2026

The initial Iowa source could not support the 2022 seven-day validation fold; it was replaced using observed train/validation coverage, before model test evaluation. Nine Missouri NOAA source files were hash verified. The complete two-horizon backtest, final refits, test predictions and historical-error intervals executed. Five meaningful tests passed, as did Ruff lint/format and the executed notebook. The full-window plot was inspected; unavailable second-half-2024 measurements remain blank.

A local Git clone was installed in the separate Python 3.12 tabular verification environment (also used for the screening project, with the same scoped dependency pins). It independently downloaded the nine public source files and reran the entire experiment. Backtest, comparison, coverage and per-origin test CSVs reproduce within atol=rtol=1e-10, with the same validation-selected methods. No source cache or model was copied into the clone. pip check and all five tests passed.

No independent-site forecasting validity, guaranteed interval coverage, operational deployment or public GitHub CI run is claimed. Raw sources and trusted local model artifacts are saved locally and ignored in Git. Verify actual CI on its scheduled daily publication day.
