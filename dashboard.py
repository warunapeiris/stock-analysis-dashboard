import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

st.image("logo.png", width=200)

# --- Historical snapshots ---
historical_files = glob.glob("analysis_results_*.csv")
historical_files = sorted(historical_files, reverse=True)

if historical_files:
    selected_file = st.selectbox("Select snapshot to view", options=historical_files, index=0)
    df = pd.read_csv(selected_file)
else:
    st.warning("No historical data files found. Please run main.py first.")
    st.stop()

st.title("📊 Stock Analysis Dashboard (ASX Top 50)")

# --- Summary metrics ---
total_stocks = df.shape[0]
average_score = df["Score"].mean()
num_undervalued = df[
    (df["FairValueEstimate"].notnull()) &
    (df["SharePrice"].notnull()) &
    (df["SharePrice"] < df["FairValueEstimate"])
].shape[0]
num_flagged = df[df["Flag"] == "FLAGGED"].shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Stocks", total_stocks)
col2.metric("Average Score", f"{average_score:.2f}")
col3.metric("Undervalued", num_undervalued)
col4.metric("Flagged", num_flagged)

st.write("---")

# --- Filters ---
min_score = st.slider("Minimum Score", 0, 5, 0)
only_undervalued = st.checkbox("Show only undervalued stocks (Share Price < Fair Value)")
only_flagged = st.checkbox("Show only FLAGGED stocks")

filtered_df = df[df["Score"] >= min_score]

if only_undervalued:
    filtered_df = filtered_df[
        (filtered_df["FairValueEstimate"].notnull()) &
        (filtered_df["SharePrice"].notnull()) &
        (filtered_df["SharePrice"] < filtered_df["FairValueEstimate"])
    ]

if only_flagged:
    filtered_df = filtered_df[filtered_df["Flag"] == "FLAGGED"]

# --- Highlighting function ---
def highlight_rows(row):
    if row["Flag"] == "FLAGGED" and row["FairValueEstimate"] is not None and row["SharePrice"] < row["FairValueEstimate"]:
        return ['background-color: lightgreen'] * len(row)
    elif row["Flag"] == "FLAGGED":
        return ['background-color: lightyellow'] * len(row)
    elif row["FairValueEstimate"] is not None and row["SharePrice"] < row["FairValueEstimate"]:
        return ['background-color: lightblue'] * len(row)
    else:
        return [''] * len(row)

st.write("### Filtered Stocks")
styled_df = filtered_df.style.apply(highlight_rows, axis=1)
st.dataframe(styled_df, use_container_width=True)

st.write(f"Total stocks shown: {filtered_df.shape[0]}")

# Download button
if st.button("Download filtered data as CSV"):
    filtered_df.to_csv("filtered_results.csv", index=False)
    st.success("✅ File saved as filtered_results.csv")

st.write("---")
st.header("📈 Charts & Visualizations")

# Score distribution
st.subheader("Score Distribution")
score_counts = df["Score"].value_counts().sort_index()
st.bar_chart(score_counts)

# Debt-to-equity vs Score
st.subheader("Debt-to-Equity vs Score")
scatter_df = df[(df["DebtToEquity"].notnull()) & (df["Score"].notnull())]
fig1, ax1 = plt.subplots()
ax1.scatter(scatter_df["DebtToEquity"], scatter_df["Score"], alpha=0.7)
ax1.set_xlabel("Debt to Equity")
ax1.set_ylabel("Score")
ax1.set_title("Debt-to-Equity vs Score")
st.pyplot(fig1)

# Share price vs Fair Value
st.subheader("Share Price vs Fair Value Estimate")
fair_df = df[(df["SharePrice"].notnull()) & (df["FairValueEstimate"].notnull())]
fig2, ax2 = plt.subplots()
ax2.scatter(fair_df["SharePrice"], fair_df["FairValueEstimate"], alpha=0.7)
ax2.plot([fair_df["SharePrice"].min(), fair_df["SharePrice"].max()],
         [fair_df["SharePrice"].min(), fair_df["SharePrice"].max()],
         color='red', linestyle='--', label="1:1 Line")
ax2.set_xlabel("Share Price")
ax2.set_ylabel("Fair Value Estimate")
ax2.set_title("Share Price vs Fair Value Estimate")
ax2.legend()
st.pyplot(fig2)

st.write("---")
st.header("🏅 Top Picks")

show_only_strict = st.checkbox("Top picks: Only show undervalued & flagged", value=True)

if show_only_strict:
    top_df = df[
        (df["FairValueEstimate"].notnull()) &
        (df["SharePrice"].notnull()) &
        (df["SharePrice"] < df["FairValueEstimate"]) &
        (df["Flag"] == "FLAGGED")
    ]
else:
    top_df = df

top_df = top_df.sort_values(by="Score", ascending=False).head(5)
st.dataframe(top_df, use_container_width=True)

st.write("---")
st.header("⭐ Watchlist")

tickers = df["Ticker"].tolist()
watchlist_selection = st.multiselect("Select stocks to add to watchlist", options=tickers)

if st.button("Save Watchlist"):
    watchlist_df = df[df["Ticker"].isin(watchlist_selection)]
    watchlist_df.to_csv("watchlist.csv", index=False)
    st.success("✅ Watchlist saved to watchlist.csv")

if os.path.exists("watchlist.csv"):
    st.subheader("Your Watchlist")
    wl_df = pd.read_csv("watchlist.csv")
    st.dataframe(wl_df, use_container_width=True)
else:
    st.info("ℹ️ No watchlist saved yet.")
st.write("---")
st.header("🗓️ Earnings Dates & News")

st.write("Below table shows next earnings dates and latest headlines for each stock.")

earnings_df = df[["Ticker", "EarningsDate", "News"]]
st.dataframe(earnings_df, use_container_width=True)
