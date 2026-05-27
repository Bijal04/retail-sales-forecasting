"""
forecasting.py
~~~~~~~~~~~~~~
Standalone script version of notebooks/03_forecasting_models.ipynb.
Run:  python src/forecasting.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
import os
warnings.filterwarnings("ignore")

from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.stattools import adfuller

try:
    from pmdarima import auto_arima
    HAS_PMDARIMA = True
except ImportError:
    HAS_PMDARIMA = False

PROCESSED_DIR = "data/processed"
REPORTS_DIR   = "reports"
N_FORECAST    = 6    # months ahead to forecast
TRAIN_RATIO   = 0.80


# ── Metrics ───────────────────────────────────────────────────

def mape(actual, predicted):
    a, p = np.array(actual), np.array(predicted)
    mask = a != 0
    return float(np.mean(np.abs((a[mask] - p[mask]) / a[mask])) * 100)

def mae(actual, predicted):
    return float(np.mean(np.abs(np.array(actual) - np.array(predicted))))

def rmse(actual, predicted):
    return float(np.sqrt(np.mean((np.array(actual) - np.array(predicted))**2)))


# ── Stationarity ──────────────────────────────────────────────

def check_stationarity(series: pd.Series, label: str = "") -> bool:
    result = adfuller(series.dropna())
    stationary = result[1] < 0.05
    print(f"ADF [{label}]: stat={result[0]:.4f}  p={result[1]:.4f}  "
          f"{'→ STATIONARY' if stationary else '→ needs differencing'}")
    return stationary


# ── SARIMA ────────────────────────────────────────────────────

def fit_sarima(train: pd.Series) -> tuple:
    if HAS_PMDARIMA:
        print("  Running auto_arima ...")
        am = auto_arima(
            train,
            start_p=0, max_p=3, start_q=0, max_q=3,
            d=None, seasonal=True, m=12,
            start_P=0, max_P=2, start_Q=0, max_Q=2, D=1,
            information_criterion="aic", stepwise=True,
            suppress_warnings=True, error_action="ignore"
        )
        p, d, q = am.order
        P, D, Q, m = am.seasonal_order
        print(f"  Best order: SARIMA({p},{d},{q})({P},{D},{Q},{m})")
    else:
        p, d, q = 1, 1, 1
        P, D, Q, m = 1, 1, 1, 12
        print(f"  Using default SARIMA({p},{d},{q})({P},{D},{Q},{m})")

    model = SARIMAX(train, order=(p, d, q), seasonal_order=(P, D, Q, m),
                    enforce_stationarity=False, enforce_invertibility=False)
    fit   = model.fit(disp=False)
    return fit, (p, d, q, P, D, Q, m)


# ── Exponential Smoothing ─────────────────────────────────────

def fit_ets(train: pd.Series) -> tuple:
    best_seasonal, best_fit, best_mape_val, best_pred = None, None, np.inf, None

    for seasonal in ["add", "mul"]:
        try:
            model = ExponentialSmoothing(
                train, trend="add", seasonal=seasonal,
                seasonal_periods=12, initialization_method="estimated"
            )
            fit  = model.fit(optimized=True, use_brute=True)
            pred = fit.forecast(1)   # dummy; real eval done in main
            best_fit      = fit
            best_seasonal = seasonal
            break
        except Exception as e:
            print(f"  ETS ({seasonal}) failed: {e}")

    return best_fit, best_seasonal


# ── Forecast export ───────────────────────────────────────────

def save_results(
    test, sarima_pred, ets_pred, forecast, lower, upper,
    best_model_name, model_summary, out_dir
):
    os.makedirs(out_dir, exist_ok=True)

    # Model evaluation
    eval_df = pd.DataFrame({
        "YearMonth"   : test.index.strftime("%Y-%m"),
        "Actual"      : test.values,
        "SARIMA_Pred" : sarima_pred.values,
        "ETS_Pred"    : ets_pred.values,
        "SARIMA_APE"  : np.abs(test.values - sarima_pred.values) / test.values * 100,
        "ETS_APE"     : np.abs(test.values - ets_pred.values)    / test.values * 100,
    })
    eval_df.to_csv(f"{out_dir}/model_evaluation.csv", index=False)

    # Forecast
    forecast_df = pd.DataFrame({
        "YearMonth"      : forecast.index.strftime("%Y-%m"),
        "ForecastRevenue": forecast.values.round(2),
        "Lower_80CI"     : lower.values.round(2),
        "Upper_80CI"     : upper.values.round(2),
        "ModelUsed"      : best_model_name,
    })
    forecast_df.to_csv(f"{out_dir}/revenue_forecast.csv", index=False)

    # Summary
    pd.DataFrame(model_summary).to_csv(f"{out_dir}/model_summary.csv", index=False)

    print(f"\nSaved to {out_dir}/:")
    print("  model_evaluation.csv")
    print("  revenue_forecast.csv")
    print("  model_summary.csv")


def plot_comparison(train, test, sarima_pred, ets_pred, mape_s, mape_e, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(train.index, train / 1e6, label="Train", color="steelblue", lw=2)
    ax.plot(test.index,  test  / 1e6, label="Test (actual)", color="black", lw=2, ls="--")
    ax.plot(test.index, sarima_pred.values / 1e6,
            label=f"SARIMA (MAPE {mape_s:.1f}%)", color="darkorange", lw=2, marker="o", ms=5)
    ax.plot(test.index, ets_pred.values / 1e6,
            label=f"Holt-Winters (MAPE {mape_e:.1f}%)", color="green", lw=2, marker="s", ms=5)
    ax.axvline(test.index[0], color="gray", ls=":", lw=1.5, label="Split")
    ax.set_title("SARIMA vs Holt-Winters — Model Comparison")
    ax.set_ylabel("Revenue (£M)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{out_dir}/model_comparison.png", bbox_inches="tight")
    plt.close()
    print(f"  → {out_dir}/model_comparison.png")


def plot_forecast(full_ts, forecast, lower, upper, best_model_name, out_dir):
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(full_ts.index, full_ts / 1e6, label="Historical", color="steelblue", lw=2)
    ax.plot(forecast.index, forecast / 1e6,
            label=f"Forecast ({best_model_name})", color="darkorange", lw=2.5,
            marker="o", ms=6, ls="--")
    ax.fill_between(forecast.index, lower / 1e6, upper / 1e6,
                    alpha=0.2, color="darkorange", label="80% CI")
    ax.axvline(full_ts.index[-1], color="gray", ls=":", lw=1.5)
    ax.set_title(f"6-Month Revenue Forecast — {best_model_name}")
    ax.set_ylabel("Revenue (£M)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(f"{out_dir}/forecast_6months.png", bbox_inches="tight")
    plt.close()
    print(f"  → {out_dir}/forecast_6months.png")


# ── Main ──────────────────────────────────────────────────────

def main():
    print("=== FORECASTING PIPELINE ===\n")

    monthly = pd.read_csv(f"{PROCESSED_DIR}/monthly_sales.csv")
    monthly["InvoiceDate"] = pd.to_datetime(monthly["YearMonth"])
    monthly = monthly.sort_values("InvoiceDate").reset_index(drop=True)
    print(f"Loaded {len(monthly)} monthly periods")

    ts = monthly.set_index("InvoiceDate")["TotalRevenue"]

    # Stationarity
    print("\n[Stationarity]")
    check_stationarity(ts, "original")
    check_stationarity(ts.diff().dropna(), "1st diff")

    # Split
    split = int(len(monthly) * TRAIN_RATIO)
    train = monthly.iloc[:split].set_index("InvoiceDate")["TotalRevenue"]
    test  = monthly.iloc[split:].set_index("InvoiceDate")["TotalRevenue"]
    print(f"\nTrain: {len(train)} periods  |  Test: {len(test)} periods")

    # SARIMA
    print("\n[SARIMA]")
    sarima_fit, sarima_order = fit_sarima(train)
    sarima_pred = sarima_fit.predict(start=test.index[0], end=test.index[-1])
    sarima_pred.index = test.index
    mape_s = mape(test.values, sarima_pred.values)
    print(f"  MAPE: {mape_s:.2f}%  (Accuracy: {100-mape_s:.1f}%)")

    # ETS
    print("\n[Exponential Smoothing]")
    ets_fit, best_seasonal = fit_ets(train)
    ets_pred = ets_fit.forecast(len(test))
    ets_pred.index = test.index
    mape_e = mape(test.values, ets_pred.values)
    print(f"  Best seasonal: {best_seasonal}")
    print(f"  MAPE: {mape_e:.2f}%  (Accuracy: {100-mape_e:.1f}%)")

    # Winner
    best_model_name = "SARIMA" if mape_s < mape_e else f"Holt-Winters ({best_seasonal})"
    print(f"\n✓ Best model: {best_model_name}")

    # Refit on full series → forecast
    p, d, q, P, D, Q, m = sarima_order
    full_ts = monthly.set_index("InvoiceDate")["TotalRevenue"]

    if best_model_name == "SARIMA":
        final = SARIMAX(full_ts, order=(p,d,q), seasonal_order=(P,D,Q,m),
                        enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
        forecast = final.forecast(N_FORECAST)
        ci       = final.get_forecast(N_FORECAST).conf_int(alpha=0.2)
        lower, upper = ci.iloc[:,0], ci.iloc[:,1]
    else:
        final    = ExponentialSmoothing(full_ts, trend="add", seasonal=best_seasonal,
                                        seasonal_periods=12, initialization_method="estimated").fit(optimized=True)
        forecast = final.forecast(N_FORECAST)
        std      = np.std(final.resid)
        lower    = forecast - 1.28 * std
        upper    = forecast + 1.28 * std

    forecast_idx   = pd.date_range(
        start=full_ts.index[-1] + pd.offsets.MonthBegin(1),
        periods=N_FORECAST, freq="MS"
    )
    forecast.index = lower.index = upper.index = forecast_idx

    print(f"\n6-Month Forecast:")
    for dt, v, lo, hi in zip(forecast_idx, forecast, lower, upper):
        print(f"  {dt.strftime('%Y-%m')}: £{v:>10,.0f}  (£{lo:,.0f} – £{hi:,.0f})")

    # Plots
    print("\n[Plots]")
    plot_comparison(train, test, sarima_pred, ets_pred, mape_s, mape_e, REPORTS_DIR)
    plot_forecast(full_ts, forecast, lower, upper, best_model_name, REPORTS_DIR)

    # Save
    model_summary = [
        {"Model": "SARIMA",                    "MAPE": round(mape_s, 2), "Accuracy": round(100-mape_s, 1),
         "MAE": round(mae(test.values, sarima_pred.values), 0), "RMSE": round(rmse(test.values, sarima_pred.values), 0)},
        {"Model": f"Holt-Winters ({best_seasonal})", "MAPE": round(mape_e, 2), "Accuracy": round(100-mape_e, 1),
         "MAE": round(mae(test.values, ets_pred.values), 0),    "RMSE": round(rmse(test.values, ets_pred.values), 0)},
    ]
    save_results(test, sarima_pred, ets_pred, forecast, lower, upper,
                 best_model_name, model_summary, PROCESSED_DIR)

    print("\n✓ Done. Load CSVs from data/processed/ into Power BI.")


if __name__ == "__main__":
    main()
