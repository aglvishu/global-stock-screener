import streamlit as st
import pandas as pd
import numpy as np
import os
import yfinance as yf
import plotly.graph_objects as go
from unified_screener import load_indian_fundamentals, load_us_fundamentals, apply_fundamental_gate, calculate_validation_score
from technicals import fetch_and_calculate_technicals

# Set Page Config for Premium Theme
st.set_page_config(
    page_title="Global Quality Compounders Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Glassmorphism & Harmonious Colors)
st.markdown("""
<style>
    /* Main Layout Styling */
    .reportview-container {
        background: #0f172a;
        color: #f8fafc;
    }
    
    /* Sleek Cards */
    .card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Header/Hero Section */
    .hero-banner {
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 30px;
        color: white;
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.025em;
    }
    .hero-banner p {
        margin: 10px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Custom Badges */
    .badge-pass {
        background-color: #059669;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.85rem;
    }
    .badge-fail {
        background-color: #dc2626;
        color: white;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="hero-banner">
    <h1>📈 Quality Compounders Screener</h1>
    <p>Dual-Market Investment Engine — Identifying High-Quality, Structural Growth Stocks in the US & Indian Markets (1yr+ Hold)</p>
</div>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIGURATION -----------------
st.sidebar.markdown("### ⚙️ Screening Configuration")

# Market Selector
market_selection = st.sidebar.multiselect(
    "Select Markets",
    options=["US", "India"],
    default=["US", "India"]
)

# Fundamental Slider Limits
st.sidebar.markdown("---")
st.sidebar.markdown("#### 📊 Fundamental Gates")

roce_limit = st.sidebar.slider("Min ROCE % (Target)", 5.0, 30.0, 15.0, 1.0)
roe_limit = st.sidebar.slider("Min ROE % (Target)", 5.0, 30.0, 15.0, 1.0)
req_consistency = st.sidebar.checkbox("Enforce Consistency (1Yr, 3Yr, 5Yr all > Target)", value=True, help="Avoids 1-year spikes by checking all historical periods.")
sales_limit = st.sidebar.slider("Min 5Yr Sales CAGR %", 5.0, 25.0, 10.0, 1.0)
profit_limit = st.sidebar.slider("Min 5Yr Earnings CAGR %", 5.0, 25.0, 12.0, 1.0)
debt_limit = st.sidebar.slider("Max Debt to Equity (Non-BFSI)", 0.1, 2.0, 0.5, 0.05)

st.sidebar.markdown("---")
st.sidebar.markdown("#### 🚀 Advanced Fundamentals")
min_div_yield = st.sidebar.slider("Min Dividend Yield %", 0.0, 10.0, 0.0, 0.5)
min_1yr_ret = st.sidebar.slider("Min 1Yr Return %", -50.0, 100.0, -100.0, 5.0, help="Set to -100 to ignore")
req_fcf = st.sidebar.checkbox("Require Positive FCF (Last Year)")
req_pe_ind = st.sidebar.checkbox("Require PE < Industry PE")


# Technical Gate Options
st.sidebar.markdown("---")
st.sidebar.markdown("#### 📈 Technical Trend Gate")
enforce_technical_hard_gate = st.sidebar.checkbox(
    "Enforce Stan Weinstein Stage 2 Uptrend (Hard Filter)",
    value=False,
    help="If enabled, stocks not trading above their 150/200 DMAs in an uptrend are completely excluded. If disabled, they are scored but remain visible."
)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reload Raw Data / Clear Cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared!")

# ----------------- CORE LOGIC DEFINITIONS -----------------
@st.cache_data
def load_all_fundamentals():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Load India
    ind_path = os.path.join(BASE_DIR, 'data', 'nifty_200_screener_mock.csv')
    if os.path.exists(os.path.join(BASE_DIR, 'data', 'nifty_200_screener.csv')):
        ind_path = os.path.join(BASE_DIR, 'data', 'nifty_200_screener.csv')
    df_ind = load_indian_fundamentals(ind_path)
    
    # Load US
    us_path = os.path.join(BASE_DIR, 'data', 'us_fundamentals_cache.csv')
    df_us = load_us_fundamentals(us_path)
    
    if df_ind.empty and df_us.empty:
        return pd.DataFrame()
        
    df = pd.concat([df_ind, df_us], ignore_index=True)
    return df

# ----------------- SCREENING EXECUTION -----------------
raw_df = load_all_fundamentals()

if raw_df.empty:
    st.error("No fundamental data found. Please verify that your fundamental cache CSVs are present.")
else:
    # Filter based on market selection
    df_filtered = raw_df[raw_df['Market'].isin(market_selection)].copy()
    
    # Override global constraints from sliders
    import unified_screener
    unified_screener.ROCE_AVG_LIMIT = roce_limit
    unified_screener.ROE_AVG_LIMIT = roe_limit
    unified_screener.ENFORCE_CONSISTENCY = req_consistency
    unified_screener.SALES_GROWTH_LIMIT = sales_limit
    unified_screener.PROFIT_GROWTH_LIMIT = profit_limit
    unified_screener.DEBT_EQUITY_LIMIT = debt_limit
    unified_screener.MIN_DIVIDEND_YIELD = min_div_yield
    unified_screener.REQUIRE_POSITIVE_FCF = req_fcf
    unified_screener.REQUIRE_PE_LT_INDUSTRY = req_pe_ind
    unified_screener.MIN_1YR_RETURN = min_1yr_ret
    
    # Apply Fundamental Stage 1 Hard Gate
    gates = df_filtered.apply(apply_fundamental_gate, axis=1)
    df_filtered['Fund_Pass'] = [g[0] for g in gates]
    df_filtered['Fund_Reason'] = [g[1] for g in gates]
    
    passed_fund = df_filtered[df_filtered['Fund_Pass']].copy()
    failed_fund = df_filtered[~df_filtered['Fund_Pass']].copy()
    
    # Main Dashboard Columns
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Universe Analyzed", len(df_filtered))
    kpi2.metric("Passed Fundamentals", len(passed_fund))
    kpi3.metric("Filtered Out", len(failed_fund))
    
    if passed_fund.empty:
        st.warning("No stocks passed your fundamental sliders. Adjust the filters in the sidebar.")
    else:
        # Fetch Live Technicals for survivors
        with st.spinner("Fetching live pricing and technical indicators from Yahoo Finance..."):
            tech_results = []
            for idx, row in passed_fund.iterrows():
                tech = fetch_and_calculate_technicals(row['Ticker'])
                tech_results.append(tech)
            tech_df = pd.DataFrame(tech_results)
            
        # Drop Current Price from fundamental CSV to avoid _x/_y collision with Yahoo live price
        if 'Current Price' in passed_fund.columns:
            passed_fund = passed_fund.drop(columns=['Current Price'])
            
        merged_df = pd.merge(passed_fund, tech_df, on='Ticker', how='inner')
        merged_df['Stage 2 Pass'] = merged_df.get('Stage 2 Pass', True).fillna(False)
        
        # Calculate Validation Scores
        scores = merged_df.apply(calculate_validation_score, axis=1)
        merged_df['Validation_Score'] = [s[0] for s in scores]
        merged_df['Red_Flags'] = [s[1] for s in scores]
        
        # Filter based on Technical Gate
        if enforce_technical_hard_gate:
            final_shortlist = merged_df[merged_df['Stage 2 Pass']].copy()
            failed_tech = merged_df[~merged_df['Stage 2 Pass']].copy()
        else:
            final_shortlist = merged_df.copy()
            failed_tech = pd.DataFrame()
            
        final_shortlist.sort_values(by='Validation_Score', ascending=False, inplace=True)
        
        # ----------------- DISPLAY TABLES -----------------
        st.markdown("### 📊 Ranked Investment Shortlist")
        
        # Column selection for clean display
        display_cols = [
            'Name', 'Ticker', 'Market', 'Sector', 
            'ROCE %', 'Avg ROCE 3Yr %', 'Avg ROCE 5Yr %', 
            'ROE %', 'Avg ROE 3Yr %', 'Avg ROE 5Yr %', 
            'PE', 'Industry PE', 'Current Price', 'Analyst Rec', 'Dividend yield %', 'Free cash flow last year', 
            'Return 1Yr %', 'Return 3Yr %', 'Return 5Yr %',
            'Relative Strength (3m vs Index %)', 'Stage 2 Pass', 'Validation_Score', 'Red_Flags'
        ]
        
        # Make sure columns exist (US stocks might miss some)
        for col in display_cols:
            if col not in final_shortlist.columns:
                final_shortlist[col] = 0.0

        final_shortlist_display = final_shortlist.copy()
        
        def format_price(row):
            val = row.get('Current Price', 0.0)
            return f"${val:.2f}" if row['Market'] == 'US' else f"₹{val:.2f}"
            
        def format_fcf(row):
            val = row.get('Free cash flow last year', 0.0)
            if row['Market'] == 'US':
                return f"${val / 1e9:.2f}B" if val != 0 else "$0.00B"
            else:
                return f"₹{val:.0f}Cr" if val != 0 else "₹0Cr"
                
        final_shortlist_display['Current Price'] = final_shortlist_display.apply(format_price, axis=1)
        final_shortlist_display['Free cash flow last year'] = final_shortlist_display.apply(format_fcf, axis=1)

        st.dataframe(
            final_shortlist_display[display_cols].reset_index(drop=True),
            column_config={
                "Stage 2 Pass": st.column_config.CheckboxColumn("Stage 2 Pass"),
                "Validation_Score": st.column_config.NumberColumn("Score", format="%.1f"),
                "Current Price": st.column_config.TextColumn("Price"),
                "Analyst Rec": st.column_config.TextColumn("Analyst"),
                "ROCE %": st.column_config.NumberColumn("1Yr ROCE", format="%.1f%%"),
                "Avg ROCE 3Yr %": st.column_config.NumberColumn("3Yr ROCE", format="%.1f%%"),
                "Avg ROCE 5Yr %": st.column_config.NumberColumn("5Yr ROCE", format="%.1f%%"),
                "ROE %": st.column_config.NumberColumn("1Yr ROE", format="%.1f%%"),
                "Avg ROE 3Yr %": st.column_config.NumberColumn("3Yr ROE", format="%.1f%%"),
                "Avg ROE 5Yr %": st.column_config.NumberColumn("5Yr ROE", format="%.1f%%"),
                "Dividend yield %": st.column_config.NumberColumn("Div Yield", format="%.2f%%"),
                "Free cash flow last year": st.column_config.TextColumn("FCF"),
                "Return 1Yr %": st.column_config.NumberColumn("1Yr Ret", format="%.1f%%"),
                "Return 3Yr %": st.column_config.NumberColumn("3Yr Ret", format="%.1f%%"),
                "Return 5Yr %": st.column_config.NumberColumn("5Yr Ret", format="%.1f%%"),
                "Relative Strength (3m vs Index %)": st.column_config.NumberColumn("Rel Strength", format="%.1f%%")
            },
            use_container_width=True
        )
        
        # ----------------- FORENSIC ANALYSIS -----------------
        st.markdown("---")
        st.markdown("### 🕵️‍♂️ Advanced Forensic Analysis")
        st.write("Dynamically calculate Piotroski F-Score, Altman Z-Score, DuPont ROE, and Cash Conversion Cycle for the shortlisted stocks using live financial statements.")
        
        with st.expander("📖 Forensic Metrics Guide (Click to read)"):
            st.markdown("""
            *   **Piotroski F-Score (0-9)**: Measures the trend in financial health over the last year. **Higher is better.** (8-9 = Exceptional, 0-2 = High risk of distress).
            *   **Altman Z-Score**: Predicts bankruptcy risk by heavily penalizing debt and rewarding working capital. **Higher is better.** (> 3.0 = Safe, 1.8 to 3.0 = Grey Zone, < 1.8 = Distress/Bankruptcy zone).
            *   **DuPont ROE**: The true Return on Equity derived directly from the balance sheet (Net Margin × Asset Turnover × Leverage). **Higher is better**, unless the high number is driven purely by massive debt leverage.
            *   **CCC (Days)**: Cash Conversion Cycle. The number of days a company's cash is trapped in inventory and unpaid bills. **Lower is better.** (A negative CCC is incredible, meaning suppliers are effectively funding the business).
            """)
        
        if st.button("Run Forensic Analysis on Shortlist"):
            with st.spinner("Fetching live financial statements... This may take a minute..."):
                from forensics import run_forensics
                
                india_tickers = final_shortlist[final_shortlist['Market'] == 'India']['Ticker'].tolist()
                us_tickers = final_shortlist[final_shortlist['Market'] == 'US']['Ticker'].tolist()
                
                res_india = pd.DataFrame()
                res_us = pd.DataFrame()
                
                if india_tickers:
                    res_india = run_forensics(india_tickers, market="India")
                if us_tickers:
                    res_us = run_forensics(us_tickers, market="US")
                    
                forensic_results = pd.concat([res_india, res_us], ignore_index=True)
                
                if not forensic_results.empty:
                    # Join back to final_shortlist for display
                    enhanced_df = pd.merge(final_shortlist, forensic_results, on="Ticker", how="left")
                    
                    st.success("Forensic Analysis Complete!")
                    st.dataframe(
                        enhanced_df[["Ticker", "Name", "Market", "Validation_Score", "F-Score", "Z-Score", "DuPont ROE %", "CCC (Days)"]].sort_values(by="Validation_Score", ascending=False).reset_index(drop=True),
                        column_config={
                            "Validation_Score": st.column_config.NumberColumn("Score", format="%.1f"),
                            "F-Score": st.column_config.NumberColumn("F-Score (0-9)", help="Higher is better (8-9 is exceptional, <3 is dangerous)."),
                            "Z-Score": st.column_config.NumberColumn("Z-Score", help="Higher is better (>3 is safe, <1.8 is distress)."),
                            "DuPont ROE %": st.column_config.NumberColumn("DuPont ROE", format="%.1f%%", help="True ROE. Higher is better."),
                            "CCC (Days)": st.column_config.NumberColumn("CCC (Days)", format="%.1f", help="Days cash is tied up. Lower is better.")
                        },
                        use_container_width=True
                    )
        
        # ----------------- DEEP DIVE & CHARTING -----------------
        st.markdown("---")
        st.markdown("### 🔍 Stock Deep-Dive & Charts")
        
        selected_ticker = st.selectbox(
            "Select a stock to view details and price chart",
            options=final_shortlist['Ticker'].tolist()
        )
        
        if selected_ticker:
            stock_row = final_shortlist[final_shortlist['Ticker'] == selected_ticker].iloc[0]
            
            # Layout detail columns
            d_col1, d_col2 = st.columns([1, 2])
            
            with d_col1:
                st.markdown(f"#### {stock_row['Name']} ({stock_row['Ticker']})")
                
                # Check status
                status_badge = '<span class="badge-pass">Stage 2 Pass</span>' if stock_row['Stage 2 Pass'] else '<span class="badge-fail">Stage 2 Fail</span>'
                st.markdown(f"**Status**: {status_badge}", unsafe_allow_html=True)
                
                st.markdown(f"""
                *   **Sector**: {stock_row['Sector']} | **Market**: {stock_row['Market']}
                *   **ROCE Trend (1Yr/3Yr/5Yr)**: {stock_row.get('ROCE %', 0.0):.1f}% / {stock_row.get('Avg ROCE 3Yr %', 0.0):.1f}% / {stock_row['Avg ROCE 5Yr %']:.1f}%
                *   **ROE Trend (1Yr/3Yr/5Yr)**: {stock_row.get('ROE %', 0.0):.1f}% / {stock_row.get('Avg ROE 3Yr %', 0.0):.1f}% / {stock_row['Avg ROE 5Yr %']:.1f}%
                *   **Free Cash Flow (Last Yr)**: {stock_row.get('Free cash flow last year', 0.0)}
                *   **Dividend Yield**: {stock_row.get('Dividend yield %', 0.0):.2f}%
                *   **Returns (1Yr/3Yr/5Yr)**: {stock_row.get('Return 1Yr %', 0.0):.1f}% / {stock_row.get('Return 3Yr %', 0.0):.1f}% / {stock_row.get('Return 5Yr %', 0.0):.1f}%
                *   **Debt to Equity**: {stock_row['Debt to equity']:.2f}
                *   **Current PE**: {stock_row['PE']:.1f} (Ind PE: {stock_row.get('Industry PE', 0.0):.1f} | 5Yr Avg: {stock_row['Avg PE 5Yr']:.1f})
                *   **Red Flags**: {stock_row['Red_Flags']}
                """)
                
            with d_col2:
                # Plot Interactive Price Chart with plotly
                with st.spinner("Downloading price chart data..."):
                    ticker_data = yf.download(selected_ticker, period="1y", interval="1d", progress=False)
                    
                    if not ticker_data.empty:
                        # Compute moving averages on-the-fly
                        close_prices = ticker_data['Close']
                        # Handle MultiIndex column structures if returned
                        if isinstance(close_prices, pd.DataFrame):
                            close_prices = close_prices[selected_ticker]
                            
                        sma_50 = close_prices.rolling(window=50).mean()
                        sma_150 = close_prices.rolling(window=150).mean()
                        sma_200 = close_prices.rolling(window=200).mean()
                        
                        fig = go.Figure()
                        
                        # Add Close Price
                        fig.add_trace(go.Scatter(
                            x=close_prices.index, y=close_prices.values,
                            name="Price", line=dict(color='#38bdf8', width=2)
                        ))
                        
                        # Add MAs
                        fig.add_trace(go.Scatter(
                            x=sma_50.index, y=sma_50.values,
                            name="50 DMA", line=dict(color='#fbbf24', width=1.5, dash='dash')
                        ))
                        fig.add_trace(go.Scatter(
                            x=sma_150.index, y=sma_150.values,
                            name="150 DMA", line=dict(color='#a855f7', width=1.5)
                        ))
                        fig.add_trace(go.Scatter(
                            x=sma_200.index, y=sma_200.values,
                            name="200 DMA", line=dict(color='#ef4444', width=2)
                        ))
                        
                        fig.update_layout(
                            title=f"{selected_ticker} Price & Moving Averages (1 Year)",
                            template="plotly_dark",
                            xaxis_title="Date",
                            yaxis_title="Price",
                            height=400,
                            margin=dict(l=20, r=20, t=40, b=20),
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No price data available for chart.")
                        
        # ----------------- SHOW FILTERED OUT STOCKS -----------------
        st.markdown("---")
        with st.expander("🚫 Inspect Filtered Out Stocks (Reasons for Failure)"):
            f_col1, f_col2 = st.columns(2)
            
            with f_col1:
                st.markdown("#### Failed Fundamental Gates")
                for idx, row in failed_fund.iterrows():
                    st.markdown(f"**{row['Name']}** ({row['Ticker']}): {row['Fund_Reason']}")
                    
            with f_col2:
                st.markdown("#### Failed Technical Trend Gates (Weinstein Stage 2)")
                if not failed_tech.empty:
                    for idx, row in failed_tech.iterrows():
                        st.markdown(f"**{row['Name']}** ({row['Ticker']}): {row['Technical Failure Reason']}")
                else:
                    st.write("No stocks were filtered strictly by technical gates (or hard technical filter is disabled).")
