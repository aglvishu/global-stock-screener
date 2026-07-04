#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from technicals import fetch_and_calculate_technicals

# Threshold Constants for Stage 1 (Fundamentals Hard Gate)
ROCE_AVG_LIMIT = 15.0       
ROE_AVG_LIMIT = 15.0        
SALES_GROWTH_LIMIT = 10.0   
PROFIT_GROWTH_LIMIT = 12.0  
DEBT_EQUITY_LIMIT = 0.5     
ENFORCE_CONSISTENCY = True

# New Advanced Constants
MIN_DIVIDEND_YIELD = 0.0
REQUIRE_POSITIVE_FCF = False
REQUIRE_PE_LT_INDUSTRY = False
MIN_1YR_RETURN = -100.0


def clean_numeric(val):
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip().replace('%', '').replace(',', '')
    if val_str in ('-', '', 'None', 'NaN'):
        return 0.0
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def load_indian_fundamentals(file_path):
    """
    Loads and standardizes Indian fundamentals from CSV.
    """
    if not os.path.exists(file_path):
        # Return empty DataFrame with expected columns if file doesn't exist
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    
    # Simple mapping for Indian CSV
    mappings = {
        'ROCE %': ['ROCE %', 'Return on capital employed'],
        'Avg ROCE 3Yr %': ['Average return on capital employed 3Years'],
        'Avg ROCE 5Yr %': ['Avg ROCE 5Yr %', 'Average return on capital employed 5Years'],
        'ROE %': ['ROE %', 'Return on equity'],
        'Avg ROE 3Yr %': ['Average return on equity 3Years'],
        'Avg ROE 5Yr %': ['Avg ROE 5Yr %', 'Average return on equity 5Years'],
        'Sales growth 3Yr %': ['Sales growth 3Years'],
        'Sales growth 5Yr %': ['Sales growth 5Yr %', 'Sales growth 5Years %', 'Sales growth 5Years'],
        'Profit growth 3Yr %': ['Profit growth 3Years'],
        'Profit growth 5Yr %': ['Profit growth 5Yr %', 'Profit growth 5Years %', 'Profit growth 5Years'],
        'Debt to equity': ['Debt to equity', 'Debt to Equity'],
        'Promoter holding %': ['Promoter holding %', 'Promoter holding'],
        'Promoter holding 3Yr ago %': ['Promoter holding 3Yr ago %', 'Promoter holding 3years back'],
        'Pledged percentage %': ['Pledged percentage %', 'Pledged percentage'],
        'PEG Ratio': ['PEG Ratio'],
        'PE': ['PE', 'Price to Earning'],
        'Avg PE 5Yr': ['Avg PE 5Yr', 'Average PE 5Years'],
        'Industry PE': ['Industry PE'],
        'Sector': ['Sector', 'Industry', 'Industry Group'],
        'Price to book': ['Price to book', 'Price to book value'],
        'Free cash flow last year': ['Free cash flow last year'],
        'Dividend yield %': ['Dividend yield'],
        'Return 1Yr %': ['Return over 1year'],
        'Return 3Yr %': ['Return over 3years'],
        'Return 5Yr %': ['Return over 5years']
    }
    
    for standard, aliases in mappings.items():
        for col in df.columns:
            if col in aliases or col == standard:
                df.rename(columns={col: standard}, inplace=True)
                break
                
    # Fill average/min fields if they are missing in export
    if 'Avg ROCE 5Yr %' not in df.columns and 'ROCE %' in df.columns:
        df['Avg ROCE 5Yr %'] = df['ROCE %']
    if 'Avg ROE 5Yr %' not in df.columns and 'ROE %' in df.columns:
        df['Avg ROE 5Yr %'] = df['ROE %']
    if 'Min ROCE 5Yr %' not in df.columns:
        df['Min ROCE 5Yr %'] = df.get('Avg ROCE 5Yr %', 0.0) * 0.9
    if 'Min ROE 5Yr %' not in df.columns:
        df['Min ROE 5Yr %'] = df.get('Avg ROE 5Yr %', 0.0) * 0.9

    df['Market'] = 'India'
    
    # Create Ticker column for Yahoo Finance (NSE Code + .NS)
    if 'NSE Code' in df.columns:
        df['Ticker'] = df['NSE Code'].astype(str).str.strip() + '.NS'
    elif 'BSE Code' in df.columns:
        df['Ticker'] = df['BSE Code'].astype(str).str.strip() + '.BO'
    elif 'Ticker' not in df.columns:
        df['Ticker'] = 'UNKNOWN'
        
    return df

def load_us_fundamentals(file_path):
    """
    Loads US stock fundamentals from cache CSV.
    """
    if not os.path.exists(file_path):
        return pd.DataFrame()
    df = pd.read_csv(file_path)
    df['Market'] = 'US'
    return df

def apply_fundamental_gate(row):
    """
    Applies Stage 1 fundamental hard filters.
    """
    reasons = []
    
    # ROCE Consistency Gate
    roce_5 = clean_numeric(row.get('Avg ROCE 5Yr %', 0.0))
    roce_3 = clean_numeric(row.get('Avg ROCE 3Yr %', 0.0))
    roce_1 = clean_numeric(row.get('ROCE %', 0.0))
    
    if ENFORCE_CONSISTENCY:
        if roce_5 < ROCE_AVG_LIMIT or roce_3 < ROCE_AVG_LIMIT or roce_1 < ROCE_AVG_LIMIT:
            reasons.append(f"ROCE Consistency Fail (1Y:{roce_1:.0f}%, 3Y:{roce_3:.0f}%, 5Y:{roce_5:.0f}% < {ROCE_AVG_LIMIT}%)")
    else:
        if roce_5 < ROCE_AVG_LIMIT:
            reasons.append(f"Avg ROCE 5Yr ({roce_5:.1f}%) < {ROCE_AVG_LIMIT}%")
            
    # ROE Consistency Gate
    roe_5 = clean_numeric(row.get('Avg ROE 5Yr %', 0.0))
    roe_3 = clean_numeric(row.get('Avg ROE 3Yr %', 0.0))
    roe_1 = clean_numeric(row.get('ROE %', 0.0))
    
    if ENFORCE_CONSISTENCY:
        if roe_5 < ROE_AVG_LIMIT or roe_3 < ROE_AVG_LIMIT or roe_1 < ROE_AVG_LIMIT:
            reasons.append(f"ROE Consistency Fail (1Y:{roe_1:.0f}%, 3Y:{roe_3:.0f}%, 5Y:{roe_5:.0f}% < {ROE_AVG_LIMIT}%)")
    else:
        if roe_5 < ROE_AVG_LIMIT:
            reasons.append(f"Avg ROE 5Yr ({roe_5:.1f}%) < {ROE_AVG_LIMIT}%")
        
    # Sales Growth > 10%
    sales = clean_numeric(row.get('Sales growth 5Yr %', 0.0))
    if sales < SALES_GROWTH_LIMIT:
        reasons.append(f"Sales growth 5Yr ({sales:.1f}%) < {SALES_GROWTH_LIMIT}%")
        
    # Profit Growth > 12%
    profit = clean_numeric(row.get('Profit growth 5Yr %', 0.0))
    if profit < PROFIT_GROWTH_LIMIT:
        reasons.append(f"Profit growth 5Yr ({profit:.1f}%) < {PROFIT_GROWTH_LIMIT}%")
        
    # Debt/Equity < 0.5 (Skipped for BFSI)
    is_bfsi = str(row.get('Sector', '')).strip().upper() == 'BFSI'
    de = clean_numeric(row.get('Debt to equity', 0.0))
    if not is_bfsi and de >= DEBT_EQUITY_LIMIT:
        reasons.append(f"Debt/Equity ({de:.2f}) >= {DEBT_EQUITY_LIMIT}")
        
    # Advanced: Dividend Yield
    div_yield = clean_numeric(row.get('Dividend yield %', 0.0))
    if div_yield < MIN_DIVIDEND_YIELD:
        reasons.append(f"Dividend Yield ({div_yield:.1f}%) < {MIN_DIVIDEND_YIELD}%")
        
    # Advanced: Free Cash Flow
    if REQUIRE_POSITIVE_FCF:
        fcf = clean_numeric(row.get('Free cash flow last year', 0.0))
        if fcf <= 0:
            reasons.append(f"Negative FCF Last Year ({fcf:.2f})")
            
    # Advanced: PE vs Industry PE
    if REQUIRE_PE_LT_INDUSTRY:
        pe = clean_numeric(row.get('PE', 0.0))
        ind_pe = clean_numeric(row.get('Industry PE', 0.0))
        if pe > 0 and ind_pe > 0 and pe >= ind_pe:
            reasons.append(f"PE ({pe:.1f}) >= Industry PE ({ind_pe:.1f})")
            
    # Advanced: 1Yr Return
    ret_1yr = clean_numeric(row.get('Return 1Yr %', 0.0))
    if ret_1yr < MIN_1YR_RETURN:
        reasons.append(f"1Yr Return ({ret_1yr:.1f}%) < {MIN_1YR_RETURN}%")
        
    if reasons:
        return False, "; ".join(reasons)
    return True, "Passed"

def calculate_validation_score(row):
    """
    Computes fundamentals validation score + technical momentum adjustments.
    """
    # 1. PE vs Avg PE 5Yr (Max 40 points)
    pe = clean_numeric(row.get('PE', 0.0))
    avg_pe = clean_numeric(row.get('Avg PE 5Yr', 0.0))
    pe_score = 0.0
    if pe > 0:
        if pe <= avg_pe:
            pe_score = 40.0
        else:
            pe_score = max(0.0, 40.0 * (avg_pe / pe))
    else:
        pe_score = 20.0
        
    # 2. PEG Ratio (Max 30 points)
    peg = clean_numeric(row.get('PEG Ratio', 0.0))
    peg_score = 0.0
    if peg > 0:
        if peg <= 1.5:
            peg_score = 30.0
        elif peg <= 2.5:
            peg_score = max(0.0, 30.0 * (1.5 / peg))
        else:
            peg_score = 0.0
    else:
        peg_score = 15.0
        
    # 3. Promoter Pledge / Insider Selling (Max 15 points)
    # Deduct points for pledged percentage
    pledge = clean_numeric(row.get('Pledged percentage %', 0.0))
    pledge_score = max(0.0, 15.0 - pledge)
    
    # 4. Promoter Holding / Institutional Ownership Trend (Max 15 points)
    curr_hold = clean_numeric(row.get('Promoter holding %', 0.0))
    old_hold = clean_numeric(row.get('Promoter holding 3Yr ago %', 0.0))
    holding_score = 15.0
    if old_hold > 0:
        decline = old_hold - curr_hold
        if decline > 0:
            holding_score = max(0.0, 15.0 - (decline * 2.0))
            
    # 5. Trend Improvement Bonus (Max 10 points)
    # Check if ROCE or ROE is improving (Current > 3Yr > 5Yr)
    trend_bonus = 0.0
    roce_1 = clean_numeric(row.get('ROCE %', 0.0))
    roce_3 = clean_numeric(row.get('Avg ROCE 3Yr %', 0.0))
    roce_5 = clean_numeric(row.get('Avg ROCE 5Yr %', 0.0))
    if roce_1 > roce_3 and roce_3 > roce_5 and roce_5 > 0:
        trend_bonus += 5.0
        
    roe_1 = clean_numeric(row.get('ROE %', 0.0))
    roe_3 = clean_numeric(row.get('Avg ROE 3Yr %', 0.0))
    roe_5 = clean_numeric(row.get('Avg ROE 5Yr %', 0.0))
    if roe_1 > roe_3 and roe_3 > roe_5 and roe_5 > 0:
        trend_bonus += 5.0
            
    # Combine scores
    f_score = pe_score + peg_score + pledge_score + holding_score + trend_bonus
    
    # 5. Technical Relative Strength Adjustment (Max +/- 10 points)
    # Add bonus for high relative strength, penalize negative relative strength
    rs = clean_numeric(row.get('Relative Strength (3m vs Index %)', 0.0))
    rs_adjustment = 0.0
    if rs > 15.0:
        rs_adjustment = 10.0
    elif rs > 5.0:
        rs_adjustment = 5.0
    elif rs < -10.0:
        rs_adjustment = -10.0
    elif rs < -5.0:
        rs_adjustment = -5.0
        
    total_score = f_score + rs_adjustment
    total_score = min(100.0, max(0.0, total_score))
    
    # Gather warnings
    red_flags = []
    if pledge > 10.0:
        red_flags.append(f"High pledge ({pledge:.1f}%)")
    if old_hold > 0 and (old_hold - curr_hold) > 5.0:
        red_flags.append(f"Declining ownership (-{(old_hold - curr_hold):.1f}%)")
    if peg > 2.5:
        red_flags.append(f"High PEG ({peg:.2f})")
    if not row.get('Stage 2 Pass', True):
        red_flags.append("Not in Stage 2 Uptrend")
        
    red_flags_str = ", ".join(red_flags) if red_flags else "None"
    
    return round(total_score, 1), red_flags_str

def run_unified_screener(enforce_technical_hard_gate=False):
    """
    Executes the full dual-market screening pipeline.
    """
    print("=== Launching Dual-Market Stock Screener ===")
    
    # 1. Load Data
    ind_path = 'data/nifty_200_screener_mock.csv'
    # Try real CSV first, fallback to mock
    if os.path.exists('data/nifty_200_screener.csv'):
        ind_path = 'data/nifty_200_screener.csv'
        
    us_path = 'data/us_fundamentals_cache.csv'
    
    df_ind = load_indian_fundamentals(ind_path)
    df_us = load_us_fundamentals(us_path)
    
    if df_ind.empty and df_us.empty:
        print("Error: No data available for screening. Run us_fundamentals.py first.")
        return pd.DataFrame()
        
    # Combine markets
    df = pd.concat([df_ind, df_us], ignore_index=True)
    
    # Clean numerical values
    numeric_cols = [
        'ROCE %', 'Avg ROCE 3Yr %', 'Avg ROCE 5Yr %', 
        'ROE %', 'Avg ROE 3Yr %', 'Avg ROE 5Yr %', 
        'Sales growth 3Yr %', 'Sales growth 5Yr %', 
        'Profit growth 3Yr %', 'Profit growth 5Yr %', 
        'Debt to equity', 'Promoter holding %', 
        'Promoter holding 3Yr ago %', 'Pledged percentage %', 
        'PEG Ratio', 'PE', 'Avg PE 5Yr', 'Industry PE', 'Price to book',
        'Free cash flow last year', 'Dividend yield %',
        'Return 1Yr %', 'Return 3Yr %', 'Return 5Yr %'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)
        else:
            df[col] = 0.0
            
    # 2. Stage 1 Hard Gate
    gates = df.apply(apply_fundamental_gate, axis=1)
    df['Fund_Pass'] = [g[0] for g in gates]
    df['Fund_Reason'] = [g[1] for g in gates]
    
    passed_fund = df[df['Fund_Pass']].copy()
    failed_fund = df[~df['Fund_Pass']].copy()
    
    print(f"Fundamentals gate: {len(passed_fund)} passed, {len(failed_fund)} filtered out.")
    
    # 3. Fetch Technicals for Fundamental Survivors
    if passed_fund.empty:
        print("No stocks passed the fundamental hard gates.")
        return pd.DataFrame()
        
    print("\nFetching live technicals for fundamental survivors...")
    tech_results = []
    for idx, row in passed_fund.iterrows():
        ticker = row['Ticker']
        print(f"  Processing {ticker}...")
        tech = fetch_and_calculate_technicals(ticker)
        tech_results.append(tech)
        
    tech_df = pd.DataFrame(tech_results)
    
    # Merge fundamental survivors with technical metrics
    merged_df = pd.merge(passed_fund, tech_df, on='Ticker', how='inner')
    
    # Apply Technical filter rules (Weinstein Stage 2)
    # Handle technical errors by assuming they fail/pass neutral
    merged_df['Stage 2 Pass'] = merged_df.get('Stage 2 Pass', True).fillna(False)
    
    # 4. Calculate Scores and Red Flags
    scores = merged_df.apply(calculate_validation_score, axis=1)
    merged_df['Validation_Score'] = [s[0] for s in scores]
    merged_df['Red_Flags'] = [s[1] for s in scores]
    
    # Apply technical hard filter if enforced
    if enforce_technical_hard_gate:
        final_shortlist = merged_df[merged_df['Stage 2 Pass']].copy()
        filtered_tech = merged_df[~merged_df['Stage 2 Pass']].copy()
    else:
        final_shortlist = merged_df.copy()
        filtered_tech = pd.DataFrame()
        
    final_shortlist.sort_values(by='Validation_Score', ascending=False, inplace=True)
    
    print(f"\n--- PASSED STOCKS (Ranked by Validation Score) ---")
    cols_to_print = [
        'Name', 'Ticker', 'Market', 'Avg ROCE 5Yr %', 'Avg ROE 5Yr %', 
        'Debt to equity', 'PE', 'PEG Ratio', 'Current Price', 
        'Relative Strength (3m vs Index %)', 'Stage 2 Pass', 'Validation_Score', 'Red_Flags'
    ]
    print(final_shortlist[cols_to_print].to_string(index=False))
    
    if not filtered_tech.empty:
        print("\n--- STOCKS FILTERED BY TECHNICAL GATES ---")
        for idx, row in filtered_tech.iterrows():
            print(f"- {row['Name']} ({row['Ticker']}): {row['Technical Failure Reason']}")
            
    # Save outputs
    os.makedirs('data', exist_ok=True)
    final_shortlist.to_csv('data/screener_passed_shortlist.csv', index=False)
    print(f"\nSaved combined ranked shortlist to: data/screener_passed_shortlist.csv")
    
    return final_shortlist

if __name__ == '__main__':
    run_unified_screener(enforce_technical_hard_gate=False)
