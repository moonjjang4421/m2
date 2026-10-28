from __future__ import annotations

import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
IMAGE_DIR = ROOT / "images"
DATA_PATH = DATA_DIR / "wti_crude_oil_daily.csv"

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"
START_DATE = "2020-01-01"
END_DATE = "2024-12-31"


def load_data() -> pd.DataFrame:
    """Download the public FRED series once, then reuse the local copy."""
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_PATH.exists():
        with urllib.request.urlopen(FRED_URL, timeout=30) as response:
            DATA_PATH.write_bytes(response.read())

    raw = pd.read_csv(DATA_PATH, parse_dates=["observation_date"])
    raw = raw.rename(columns={"observation_date": "date", "DCOILWTICO": "price_usd"})
    raw["price_usd"] = pd.to_numeric(raw["price_usd"], errors="coerce")
    data = (
        raw.dropna(subset=["price_usd"])
        .set_index("date")
        .sort_index()
        .loc[START_DATE:END_DATE]
    )
    data["daily_return_pct"] = data["price_usd"].pct_change() * 100
    data["rolling_30d_mean"] = data["price_usd"].rolling(30, min_periods=1).mean()
    data["rolling_30d_volatility"] = (
        data["daily_return_pct"].rolling(30, min_periods=10).std()
    )
    return data


def save_figures(data: pd.DataFrame) -> None:
    IMAGE_DIR.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(data.index, data["price_usd"], color="#1565c0", linewidth=1, label="WTI price")
    ax.plot(
        data.index,
        data["rolling_30d_mean"],
        color="#ef6c00",
        linewidth=2,
        label="30-day moving average",
    )
    ax.set(title="WTI crude oil price and 30-day moving average", ylabel="USD per barrel")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "01_price_and_moving_average.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(data.index, data["daily_return_pct"], color="#546e7a", width=1)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(title="Daily percentage change in WTI price", ylabel="Daily return (%)")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "02_daily_returns.png", dpi=160)
    plt.close(fig)

    monthly = data["price_usd"].resample("ME").last().pct_change().mul(100)
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#c62828" if value < 0 else "#2e7d32" for value in monthly]
    ax.bar(monthly.index, monthly, color=colors, width=20)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(title="Month-end WTI returns", ylabel="Monthly return (%)")
    fig.tight_layout()
    fig.savefig(IMAGE_DIR / "03_monthly_returns.png", dpi=160)
    plt.close(fig)


def main() -> None:
    data = load_data()
    save_figures(data)
    monthly = data["price_usd"].resample("ME").last().pct_change().mul(100)
    largest_gain = data["daily_return_pct"].idxmax()
    largest_loss = data["daily_return_pct"].idxmin()
    print(f"rows={len(data)}")
    print(f"period={data.index.min().date()} to {data.index.max().date()}")
    print(f"missing_price_values={int(data['price_usd'].isna().sum())}")
    print(f"price_start={data['price_usd'].iloc[0]:.2f}")
    print(f"price_end={data['price_usd'].iloc[-1]:.2f}")
    print(f"price_min={data['price_usd'].min():.2f}")
    print(f"price_max={data['price_usd'].max():.2f}")
    print(f"largest_gain={largest_gain.date()} ({data.loc[largest_gain, 'daily_return_pct']:.2f}%)")
    print(f"largest_loss={largest_loss.date()} ({data.loc[largest_loss, 'daily_return_pct']:.2f}%)")
    print(f"monthly_mean={monthly.mean():.2f}%")
    print(f"monthly_std={monthly.std():.2f}%")
    print(f"high_volatility_days={(data['rolling_30d_volatility'] > data['rolling_30d_volatility'].quantile(.9)).sum()}")


if __name__ == "__main__":
    main()
