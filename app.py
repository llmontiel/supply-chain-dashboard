"""
app.py
------
Interactive supply-chain KPI dashboard (Streamlit + Plotly).

Shows the metrics an inventory team watches daily — in-stock rate, demand vs.
units sold, inventory on-hand, and revenue — with sidebar filters for region,
store, category, and date range.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

The dashboard generates its synthetic dataset on first load if it isn't present,
so it runs out-of-the-box locally and when deployed (e.g. Streamlit Community
Cloud) with no manual data step.
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st

import generate_data

st.set_page_config(page_title="Supply Chain KPI Dashboard", layout="wide",
                   page_icon="📦")

DATA_PATH = "data/supply_chain.csv"


@st.cache_data
def load():
    # Auto-generate the synthetic data if it's not already present. This makes
    # the app self-contained — no separate "run generate_data.py" step needed,
    # which is what lets it deploy cleanly on Streamlit Community Cloud.
    if not os.path.exists(DATA_PATH):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        generate_data.generate().to_csv(DATA_PATH, index=False)
    return pd.read_csv(DATA_PATH, parse_dates=["date"])


df = load()

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")
regions = st.sidebar.multiselect("Region", sorted(df["region"].unique()),
                                 default=sorted(df["region"].unique()))
cats = st.sidebar.multiselect("Category", sorted(df["category"].unique()),
                              default=sorted(df["category"].unique()))

# Streamlit's date_input expects plain python date objects, not pandas
# Timestamps — convert explicitly so the widget renders reliably on first load.
dmin = df["date"].min().date()
dmax = df["date"].max().date()
date_range = st.sidebar.date_input("Date range", (dmin, dmax),
                                   min_value=dmin, max_value=dmax)

f = df[df["region"].isin(regions) & df["category"].isin(cats)]
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    f = f[(f["date"] >= start) & (f["date"] <= end)]

# ---------------- Header ----------------
st.title("📦 Supply Chain KPI Dashboard")
st.caption("In-stock, demand, inventory, and revenue — synthetic data, "
           "fully reproducible.")

if f.empty:
    st.warning("No data for the selected filters — widen your selection.")
    st.stop()

# ---------------- KPI row ----------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("In-Stock Rate", f"{f['in_stock_rate'].mean()*100:.1f}%")
c2.metric("Total Revenue", f"${f['revenue'].sum():,.0f}")
c3.metric("Units Sold", f"{f['units_sold'].sum():,.0f}")
demand_fill = f["units_sold"].sum() / f["demand"].sum() * 100 if f["demand"].sum() else 0
c4.metric("Demand Fill Rate", f"{demand_fill:.1f}%")

st.divider()

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:
    st.subheader("In-stock rate over time")
    ts = f.groupby("date")["in_stock_rate"].mean().reset_index()
    fig = px.line(ts, x="date", y="in_stock_rate",
                  labels={"in_stock_rate": "In-stock rate"})
    fig.update_yaxes(tickformat=".0%")
    fig.update_traces(line_color="#2f7a3f")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Revenue by category")
    bycat = f.groupby("category")["revenue"].sum().reset_index().sort_values("revenue")
    fig2 = px.bar(bycat, x="revenue", y="category", orientation="h",
                  labels={"revenue": "Revenue ($)"})
    fig2.update_traces(marker_color="#2f7a3f")
    st.plotly_chart(fig2, width="stretch")

st.subheader("Demand vs. units sold by region")
reg = f.groupby("region")[["demand", "units_sold"]].sum().reset_index()
fig3 = px.bar(reg, x="region", y=["demand", "units_sold"], barmode="group",
              labels={"value": "Units", "variable": "Metric"})
st.plotly_chart(fig3, width="stretch")

st.caption("Built with Streamlit + Plotly · data is synthetic")
