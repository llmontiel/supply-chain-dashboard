"""
generate_data.py
----------------
Generate synthetic supply-chain KPI data for the dashboard.

Simulates daily store x category metrics: demand, units sold, on-hand
inventory, and in-stock rate — the metrics an inventory team watches.

No real or confidential data is used.
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(21)

REGIONS = {"Central": ["STORE_ATX", "STORE_HOU"], "West": ["STORE_LAX"],
           "South": ["STORE_MIA"], "East": ["STORE_NYC"]}
CATEGORIES = ["Beverage", "Breakfast", "Candy", "Snacks", "Grocery Bulk"]
START, END = "2025-01-01", "2025-06-30"


def generate() -> pd.DataFrame:
    dates = pd.date_range(START, END, freq="D")
    rows = []
    for region, stores in REGIONS.items():
        for store in stores:
            for cat in CATEGORIES:
                base = {"Beverage": 180, "Breakfast": 120, "Candy": 70,
                        "Snacks": 95, "Grocery Bulk": 240}[cat]
                for d in dates:
                    season = 1 + 0.12 * np.sin(2 * np.pi * d.dayofyear / 365.25)
                    weekend = 1.25 if d.dayofweek >= 5 else 1.0
                    demand = max(0, RNG.normal(base * season * weekend, base * 0.2))
                    # in-stock rate: usually high, occasional dips
                    instock = min(1.0, max(0.6, RNG.normal(0.96, 0.05)))
                    units_sold = demand * instock
                    on_hand = max(0, RNG.normal(base * 3, base * 0.5))
                    rows.append({
                        "date": d, "region": region, "store_id": store,
                        "category": cat,
                        "demand": round(demand, 1),
                        "units_sold": round(units_sold, 1),
                        "on_hand": round(on_hand, 1),
                        "in_stock_rate": round(instock, 4),
                    })
    df = pd.DataFrame(rows)
    df["revenue"] = (df["units_sold"] * 4.5).round(2)
    return df


if __name__ == "__main__":
    df = generate()
    df.to_csv("data/supply_chain.csv", index=False)
    print(f"Generated {len(df):,} rows "
          f"({df['date'].nunique()} days x {df['store_id'].nunique()} stores "
          f"x {df['category'].nunique()} categories).")
