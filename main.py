import yfinance as yf
import pandas as pd
import datetime

# Read ASX tickers
with open("asx_tickers.txt", "r") as f:
    asx_tickers = [line.strip() for line in f.readlines() if line.strip()]

tickers = asx_tickers

def chunks(lst, n):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

results = []

for batch in chunks(tickers, 10):
    for ticker in batch:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            current_price = info.get('currentPrice')
            shares_outstanding = info.get('sharesOutstanding')
            market_cap = info.get('marketCap')

            pe = info.get('trailingPE')
            roe = info.get('returnOnEquity')
            de = info.get('debtToEquity')
            div_yield = info.get('dividendYield')
            profit_margin = info.get('profitMargins')
            current_ratio = info.get('currentRatio')
            quick_ratio = info.get('quickRatio')
            book_value = info.get('bookValue')
            earnings_growth = info.get('earningsGrowth')
            operating_cf = info.get('operatingCashflow')
            free_cf = info.get('freeCashflow')
            ebitda = info.get('ebitda')

            total_assets = None
            total_liabilities = None
            total_revenue = None

            bs = stock.balance_sheet
            fs = stock.financials

            if not bs.empty:
                try:
                    total_assets = bs.loc["Total Assets"].iloc[0]
                    total_liabilities = bs.loc["Total Liab"].iloc[0]
                except:
                    pass

            if not fs.empty:
                try:
                    total_revenue = fs.loc["Total Revenue"].iloc[0]
                except:
                    pass

            score = 0
            if pe is not None and pe < 20:
                score += 1
            if roe is not None and roe > 0.15:
                score += 1
            if de is not None and de < 100:
                score += 1
            if profit_margin is not None and profit_margin > 0.10:
                score += 1
            if current_ratio is not None and current_ratio > 1.5:
                score += 1

            fair_value = None
            if book_value is not None:
                fair_value = book_value * (1 + (score / 10))

            cash_flow_per_share = None
            if operating_cf is not None and shares_outstanding:
                cash_flow_per_share = operating_cf / shares_outstanding

            fcf_yield = None
            if free_cf is not None and market_cap and market_cap != 0:
                fcf_yield = free_cf / market_cap

            ebit_margin = None
            if ebitda is not None and total_revenue and total_revenue != 0:
                ebit_margin = ebitda / total_revenue

            peg_ratio = None
            if pe is not None and earnings_growth and earnings_growth != 0:
                peg_ratio = pe / earnings_growth

            if pe is not None and roe is not None:
                if pe < 20 and roe > 0.15:
                    flag = "FLAGGED"
                else:
                    flag = "Not flagged"
            else:
                flag = "Missing data"

            # Earnings date
            earnings_date = None
            try:
                cal = stock.calendar
                if not cal.empty and "Earnings Date" in cal.index:
                    earnings_date = cal.loc["Earnings Date"].iloc[0]
            except:
                pass

            # Headlines
            news_list = []
            try:
                news_items = stock.news
                for item in news_items[:3]:
                    title = item.get("title")
                    if title is not None:
                        news_list.append(title)
            except:
                pass

            news_str = "; ".join(news_list) if news_list else None

            results.append({
                "Ticker": ticker,
                "SharePrice": current_price,
                "FairValueEstimate": fair_value,
                "PE": pe,
                "ROE": roe,
                "DebtToEquity": de,
                "DividendYield": div_yield,
                "ProfitMargin": profit_margin,
                "CurrentRatio": current_ratio,
                "QuickRatio": quick_ratio,
                "CashFlowPerShare": cash_flow_per_share,
                "FCFYield": fcf_yield,
                "EBITMargin": ebit_margin,
                "PEGRatio": peg_ratio,
                "TotalAssets": total_assets,
                "TotalLiabilities": total_liabilities,
                "TotalRevenue": total_revenue,
                "Score": score,
                "Flag": flag,
                "EarningsDate": earnings_date,
                "News": news_str
            })

        except Exception as e:
            print(f"Error with {ticker}: {e}")
            results.append({
                "Ticker": ticker,
                "SharePrice": None,
                "FairValueEstimate": None,
                "PE": None,
                "ROE": None,
                "DebtToEquity": None,
                "DividendYield": None,
                "ProfitMargin": None,
                "CurrentRatio": None,
                "QuickRatio": None,
                "CashFlowPerShare": None,
                "FCFYield": None,
                "EBITMargin": None,
                "PEGRatio": None,
                "TotalAssets": None,
                "TotalLiabilities": None,
                "TotalRevenue": None,
                "Score": 0,
                "Flag": "Error",
                "EarningsDate": None,
                "News": None
            })

df = pd.DataFrame(results)

# Save files
df.to_csv("analysis_results.csv", index=False)

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
history_filename = f"analysis_results_{today_str}.csv"
df.to_csv(history_filename, index=False)

flagged_count = df[df["Flag"] == "FLAGGED"].shape[0]

print("Results saved to analysis_results.csv and", history_filename)
print(f"Total stocks analyzed: {df.shape[0]}")
print(f"Stocks flagged as potential buys: {flagged_count}")
