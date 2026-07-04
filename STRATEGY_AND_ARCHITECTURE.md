# Global Quality Compounders Screener
**Project Documentation & Strategy Reference**

This document serves as a complete reference for the dual-market stock screening engine we built. It outlines the data sources, the underlying investment strategy, the exact thresholds used to filter stocks, and the technical architecture of the application.

---

## 1. Investment Strategy & Thresholds

The screener is built around a "Quality Compounders" strategy. The goal is to identify structurally robust businesses that generate high returns on capital with minimal debt, and ensure we only buy them when they are in a confirmed technical uptrend.

### Stage 1: Fundamental Hard Gates (The "Quality" Filter)
Before a stock is even considered, it must pass these strict fundamental gates. These are designed to weed out cyclical traps, highly leveraged businesses, and inconsistent performers.

*   **ROCE & ROE Consistency (Target: >15%)**
    *   **Rule:** The Return on Capital Employed (ROCE) and Return on Equity (ROE) must be consistently high.
    *   **Why:** A high ROCE indicates the business has a competitive moat. 
    *   **Consistency Check:** Instead of just looking at the current year (which could be a one-off spike), the screener checks the 1-Year, 3-Year, and 5-Year averages. All three must be above the target threshold.
*   **Sales & Profit Growth (Target: >10% Sales, >12% Profit over 5 Yrs)**
    *   **Rule:** The 5-year CAGR for both top-line revenue and bottom-line earnings must be strong.
    *   **Why:** Ensures the business is structurally growing, not just cutting costs to inflate margins.
*   **Debt to Equity (Target: <0.5)**
    *   **Rule:** Excludes highly leveraged companies. 
    *   **Exception:** This rule is automatically bypassed for BFSI (Banking, Financial Services, and Insurance) stocks, where high leverage is structural to the business model.

### Stage 1.5: Advanced Fundamental Filters
Optional strict filters that can be toggled in the dashboard:
*   **Positive Free Cash Flow (FCF):** Ensures the company is actually generating hard cash, not just accounting profits.
*   **Dividend Yield:** Filters for companies returning cash to shareholders.
*   **Relative Valuation (PE < Industry PE):** Ensures you aren't severely overpaying compared to sector peers.

### Stage 2: Technical Momentum (Stan Weinstein's Stage 2)
Fundamental analysis tells us *what* to buy; technical analysis tells us *when* to buy.

*   **Rule:** A stock must be in a confirmed "Stage 2 Uptrend". 
*   **Criteria:**
    1.  Current Price > 150-Day Moving Average
    2.  150-Day MA > 200-Day MA
    3.  The 200-Day MA must be trending upwards (Current 200 DMA > 200 DMA 1 month ago).
*   **Why:** Buying a fundamentally great company while it is in a Stage 4 downtrend leads to "dead money". The hard technical gate ensures capital is only deployed into stocks currently favored by the broader market.

### Stage 3: Validation Scoring & Red Flags
Stocks that survive the gates are ranked out of 100 based on a proprietary validation score:
*   **Valuation (PE vs 5Yr Avg PE & PEG Ratio):** Rewards stocks trading below their historical averages.
*   **Promoter Confidence:** Deducts massive points if promoters are pledging shares or actively selling down their stake over a 3-year period.
*   **Relative Strength Bonus:** Adds bonus points if the stock is significantly outperforming the broader market index over the last 3 months.

### Stage 4: Advanced Forensic Analysis (Shortlist Only)
For stocks that make it to the final shortlist, the screener can dynamically fetch raw balance sheet and income statement data to run advanced forensic checks to prevent falling for "cooked books":
*   **Piotroski F-Score (0-9 Scale):** A 9-point test comparing current vs prior year metrics (like ROA, Cash Flow, Leverage, and Asset Turnover). **Higher is better.** (8-9 = Exceptional, 0-2 = High risk of distress).
*   **Altman Z-Score:** A mathematical bankruptcy prediction model heavily penalizing debt while rewarding working capital. **Higher is better.** (> 3.0 = Safe, < 1.8 = Distress zone).
*   **DuPont ROE:** Breaks down the headline Return on Equity into *Net Margin × Asset Turnover × Leverage*. **Higher is better,** but this ensures the ROE isn't being artificially inflated by massive debt.
*   **Cash Conversion Cycle (CCC):** The number of days cash is trapped in inventory and unpaid bills. **Lower is better.** (Negative CCC means suppliers are funding the business).

---

## 2. Data Sources

The screener is built to handle both the Indian and US markets using distinct, reliable data pipelines.

### India Market
*   **Source:** `screener.in` (CSV Export)
*   **Methodology:** We rely on a manual CSV export (e.g., Nifty 200) from screener.in. This provides incredibly deep historical data (5-yr averages, promoter holdings history, etc.) that is difficult to get elsewhere for Indian markets without expensive API subscriptions.

### US Market (S&P 500 & Nasdaq 100)
*   **Ticker Sourcing:** We scrape `slickcharts.com` to get the exact, real-time holdings of the **SPY** (S&P 500) and **QQQ** (Nasdaq 100) ETFs. This avoids the fragility of Wikipedia scraping and licensing restrictions of official index APIs.
*   **Fundamental & Technical Data:** We use the `yfinance` Python library to dynamically download live market data, Advanced Fundamentals (FCF, Dividend Yield), and 5-year historical daily price charts.
*   **Data Processing:** The script automatically groups US stocks by sector to calculate a median **Industry PE**, and manually calculates 3-Year and 5-Year compound returns using the historical price charts.

---

## 3. System Architecture & Tech Stack

*   **Language:** Python
*   **Frontend:** `Streamlit` — Provides a sleek, glassmorphic UI with dynamic filtering sliders and real-time interactive Plotly charts.
*   **Backend Processing:** `Pandas` & `NumPy` for lightning-fast dataframe manipulation and cross-sectional scoring.
*   **Modularity:**
    *   `app.py`: The main Streamlit dashboard and UI rendering logic.
    *   `unified_screener.py`: The core mathematical engine that applies the gates and calculates validation scores.
    *   `us_fundamentals.py`: The background automated web scraper and Yahoo Finance API hook that builds the US database cache.
    *   `technicals.py`: The real-time technical analysis engine (Moving Averages, Relative Strength).

---

## 4. How to Run & Maintain

### Running the Dashboard
Open your terminal in the project directory and run:
```bash
uv run --with streamlit --with pandas --with yfinance --with plotly --with lxml streamlit run app.py
```

### Updating the Data
*   **For India:** Export a fresh CSV from `screener.in` and replace `data/nifty_200_screener.csv`.
*   **For the US:** Run the background fetching script to pull fresh data from Yahoo Finance. This will overwrite `data/us_fundamentals_cache.csv`.
    ```bash
    uv run --with pandas --with yfinance --with tqdm --with lxml --with requests python us_fundamentals.py
    ```

*Note: The US fetcher downloads 5 years of history for over 500 stocks. It takes roughly 5–8 minutes to run and uses throttling to prevent API bans.*
