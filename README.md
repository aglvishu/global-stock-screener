# Global Quality Compounders & Stage 2 Stock Screener (US & India)

An interactive multi-market stock screener that screens for **1+ year (mid/long-term) high-quality growth investments** by blending fundamental indicators with technical trend validation.

## Strategy Layers

### 1. Fundamentals Hard Gate (Stage 1)
Identifies businesses with durable profitability and growth while avoiding leverage risk:
*   **Average ROCE (5 years)** > 15.0%
*   **Average ROE (5 years)** > 15.0%
*   **Sales Growth (5 years CAGR)** > 10.0%
*   **Profit Growth (5 years CAGR)** > 12.0%
*   **Debt to Equity** < 0.5 (automatically bypassed for BFSI/financial stocks)

### 2. Technical Trend Gate (Stage 2 - Stan Weinstein)
Validates that stocks are in a mature uptrend and not "falling knives" before buying:
*   **Trend Template**: Price must be above its 150-day and 200-day Simple Moving Averages (SMAs).
*   **Sloping MA**: The 200-day SMA must be actively sloping upwards.
*   **Momentum**: The 50-day SMA is above the 150-day SMA.
*   **Strength & Highs**: Price is within 25% of its 52-week High and at least 30% above its 52-week Low.
*   **Relative Strength**: Compares the stock's 3-month price return relative to its index benchmark (S&P 500 for US, Nifty 50 for India).

### 3. Valuation Validation & Score (Stage 3)
Ranks passing stocks on a scale of 0 to 100 based on current valuation ratios (PE vs 5Yr Avg PE, PEG ratio) and warning signs (promoter/insider share pledging and selling trends).

---

## File Structure

*   `screener.py`: Original India-only screening script.
*   `us_fundamentals.py`: Script to download and cache S&P 500 fundamentals from Yahoo Finance.
*   `technicals.py`: Engine to fetch historical daily prices and compute MA trends & Relative Strength.
*   `unified_screener.py`: Dual-market backend that aggregates datasets, filters, and saves shortlist results.
*   `app.py`: Streamlit interactive dashboard UI.
*   `data/`: Directory storing fundamentals mock files and the US fundamentals cache.

---

## Installation & Running

This project uses the `uv` tool to run commands instantly and automatically resolve libraries (`streamlit`, `pandas`, `yfinance`, `plotly`, `tqdm`, `lxml`) without polluting your system Python environment.

### 1. Update the US Fundamentals Cache
Run this script once to populate/refresh the cached fundamental metrics for US stocks:
```bash
uv run --with pandas --with yfinance --with tqdm --with lxml python3 us_fundamentals.py
```

### 2. Run the Command Line Screener
To run a quick screening output directly on your terminal:
```bash
uv run --with pandas --with yfinance --with tqdm --with lxml python3 unified_screener.py
```

### 3. Start the Interactive Web Dashboard
To open the premium UI in your browser:
```bash
uv run --with streamlit --with pandas --with yfinance --with plotly --with lxml streamlit run app.py
```
This command starts a local server and opens a tab in your default browser at `http://localhost:8501`.

---

## Real Data Configuration

### India Market (Screener.in)
Export Nifty 200 screen columns to Excel/CSV and save it as `nifty_200_screener.csv` under `data/`. Ensure the following columns are included:
*   `Name`, `Sector`, `ROCE %`, `Average return on capital employed 5Years`
*   `ROE %`, `Average return on equity 5Years`, `Sales growth 5Years %`, `Profit growth 5Years %`
*   `Debt to equity`, `Promoter holding %`, `Promoter holding 3years back`, `Pledged percentage %`
*   `PEG Ratio`, `Price to Earning`, `Average PE 5Years`, `Price to book value`

### US Market (Yahoo Finance)
The US pipeline runs dynamically. By default, `us_fundamentals.py` fetches the top S&P 500 stocks. You can adjust the limit parameter in the script main block to fetch more tickers.
