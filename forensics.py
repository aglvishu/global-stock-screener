import yfinance as yf
import pandas as pd
import numpy as np

def get_val(df, row_name, col_idx=0, default=0.0):
    """Safely extract a value from the financial dataframe."""
    if row_name in df.index:
        try:
            val = df.loc[row_name].iloc[col_idx]
            if pd.isna(val): return default
            return float(val)
        except:
            return default
    return default

def run_forensics(ticker_list, market="India"):
    """
    Fetches raw financial statements and calculates:
    - Piotroski F-Score (0-9)
    - Altman Z-Score
    - 3-Component DuPont ROE
    - Cash Conversion Cycle (CCC)
    """
    results = []
    
    for t in ticker_list:
        try:
            # Map ticker
            fetch_ticker = t
            if market == "India" and not t.endswith(".NS") and not t.endswith(".BO"):
                fetch_ticker = f"{t}.NS"
                
            stock = yf.Ticker(fetch_ticker)
            bs = stock.balance_sheet
            inc = stock.financials
            cf = stock.cashflow
            
            if bs.empty or inc.empty or cf.empty:
                results.append({"Ticker": t, "F-Score": None, "Z-Score": None, "DuPont ROE %": None, "CCC (Days)": None})
                continue
                
            # Need at least 2 years of data for trend-based F-score
            cols_bs = bs.columns
            cols_inc = inc.columns
            cols_cf = cf.columns
            
            if len(cols_bs) < 2 or len(cols_inc) < 2 or len(cols_cf) < 2:
                results.append({"Ticker": t, "F-Score": None, "Z-Score": None, "DuPont ROE %": None, "CCC (Days)": None})
                continue
            
            # --- EXTRACT COMPONENTS ---
            # Profitability
            net_income = get_val(inc, 'Net Income')
            net_income_prev = get_val(inc, 'Net Income', 1)
            
            total_assets = get_val(bs, 'Total Assets')
            total_assets_prev = get_val(bs, 'Total Assets', 1)
            if total_assets == 0: total_assets = 1
            if total_assets_prev == 0: total_assets_prev = 1
            
            roa = net_income / total_assets
            roa_prev = net_income_prev / total_assets_prev
            
            cfo = get_val(cf, 'Operating Cash Flow')
            if cfo == 0: cfo = get_val(cf, 'Total Cash From Operating Activities')
            
            # Leverage & Liquidity
            long_term_debt = get_val(bs, 'Long Term Debt')
            long_term_debt_prev = get_val(bs, 'Long Term Debt', 1)
            
            current_assets = get_val(bs, 'Current Assets')
            current_assets_prev = get_val(bs, 'Current Assets', 1)
            
            current_liabilities = get_val(bs, 'Current Liabilities')
            current_liabilities_prev = get_val(bs, 'Current Liabilities', 1)
            if current_liabilities == 0: current_liabilities = 1
            if current_liabilities_prev == 0: current_liabilities_prev = 1
            
            current_ratio = current_assets / current_liabilities
            current_ratio_prev = current_assets_prev / current_liabilities_prev
            
            # Shares (Dilution check)
            shares = get_val(bs, 'Ordinary Shares Number')
            if shares == 0: shares = get_val(bs, 'Share Issued')
            shares_prev = get_val(bs, 'Ordinary Shares Number', 1)
            if shares_prev == 0: shares_prev = get_val(bs, 'Share Issued', 1)
            
            # Operating Efficiency
            gross_profit = get_val(inc, 'Gross Profit')
            gross_profit_prev = get_val(inc, 'Gross Profit', 1)
            
            total_revenue = get_val(inc, 'Total Revenue')
            total_revenue_prev = get_val(inc, 'Total Revenue', 1)
            if total_revenue == 0: total_revenue = 1
            if total_revenue_prev == 0: total_revenue_prev = 1
            
            gross_margin = gross_profit / total_revenue
            gross_margin_prev = gross_profit_prev / total_revenue_prev
            
            asset_turnover = total_revenue / total_assets
            asset_turnover_prev = total_revenue_prev / total_assets_prev
            
            # --- 1. PIOTROSKI F-SCORE ---
            f_score = 0
            if roa > 0: f_score += 1
            if cfo > 0: f_score += 1
            if roa > roa_prev: f_score += 1
            if cfo > net_income: f_score += 1
            if long_term_debt < long_term_debt_prev: f_score += 1
            if current_ratio > current_ratio_prev: f_score += 1
            if shares <= shares_prev and shares != 0: f_score += 1
            if gross_margin > gross_margin_prev: f_score += 1
            if asset_turnover > asset_turnover_prev: f_score += 1
            
            # --- 2. ALTMAN Z-SCORE ---
            working_capital = current_assets - current_liabilities
            retained_earnings = get_val(bs, 'Retained Earnings')
            ebit = get_val(inc, 'EBIT')
            
            total_liabilities = get_val(bs, 'Total Liabilities Net Minority Interest')
            if total_liabilities == 0: total_liabilities = 1
            
            # Use market cap if available, otherwise estimate equity book value
            market_cap = stock.info.get('marketCap')
            if not market_cap:
                market_cap = get_val(bs, 'Total Equity Gross Minority Interest')
            
            z_score = (1.2 * (working_capital / total_assets) +
                       1.4 * (retained_earnings / total_assets) +
                       3.3 * (ebit / total_assets) +
                       0.6 * (market_cap / total_liabilities) +
                       1.0 * (total_revenue / total_assets))
                       
            # --- 3. DUPONT ROE (3-Component) ---
            net_profit_margin = net_income / total_revenue
            
            equity = get_val(bs, 'Stockholders Equity')
            if equity == 0: equity = get_val(bs, 'Total Equity Gross Minority Interest')
            if equity == 0: equity = 1
            equity_multiplier = total_assets / equity
            
            dupont_roe = net_profit_margin * asset_turnover * equity_multiplier
            
            # --- 4. CASH CONVERSION CYCLE (CCC) ---
            cogs = get_val(inc, 'Cost Of Revenue')
            # Fallback if Cost of Revenue missing
            if cogs == 0: cogs = total_revenue - gross_profit
            if cogs == 0: cogs = 1
            
            inventory = get_val(bs, 'Inventory')
            dio = (inventory / cogs) * 365
            
            receivables = get_val(bs, 'Accounts Receivable')
            dso = (receivables / total_revenue) * 365
            
            payables = get_val(bs, 'Accounts Payable')
            dpo = (payables / cogs) * 365
            
            ccc = dio + dso - dpo
            
            results.append({
                "Ticker": t,
                "F-Score": f_score,
                "Z-Score": round(z_score, 2),
                "DuPont ROE %": round(dupont_roe * 100, 2),
                "CCC (Days)": round(ccc, 1)
            })
            
        except Exception as e:
            print(f"Error calculating forensics for {t}: {e}")
            results.append({"Ticker": t, "F-Score": None, "Z-Score": None, "DuPont ROE %": None, "CCC (Days)": None})
            
    return pd.DataFrame(results)

if __name__ == "__main__":
    # Test script
    res = run_forensics(["TCS", "RELIANCE"], market="India")
    print(res)
