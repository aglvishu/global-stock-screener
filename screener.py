#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np

# Threshold Constants for Stage 1 (Hard Gate)
ROCE_AVG_LIMIT = 15.0       # > 15-18% (5yr avg)
ROE_AVG_LIMIT = 15.0        # > 15% (5yr avg)
MIN_ROCE_LIMIT = 15.0       # Consistency check (min in any of last 5 yrs)
MIN_ROE_LIMIT = 15.0        # Consistency check (min in any of last 5 yrs)
SALES_GROWTH_LIMIT = 10.0   # > 10-12% (5yr revenue CAGR)
PROFIT_GROWTH_LIMIT = 12.0  # > 12-15% (5yr EPS/Profit CAGR)
DEBT_EQUITY_LIMIT = 0.5     # < 0.5 (skipped for BFSI)

def clean_numeric(val):
    """
    Cleans a string/numeric value from Screener.in CSV into a clean float.
    Handles percentages, commas, nulls, and hyphens.
    """
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

def load_and_clean_data(file_path):
    """
    Loads Screener.in CSV export and standardizes columns and numeric values.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at: {file_path}")
        
    df = pd.read_csv(file_path)
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Map possible Screener.in column aliases to standardized names
    column_mappings = {
        'ROCE %': ['ROCE %', 'ROCE', 'Return on capital employed', 'Return on capital employed %'],
        'Avg ROCE 5Yr %': ['Avg ROCE 5Yr %', 'Average return on capital employed 5Years', '5Yr Avg ROCE', 'Average ROCE 5Yr %'],
        'Min ROCE 5Yr %': ['Min ROCE 5Yr %', 'Minimum return on capital employed 5Years', 'Min ROCE 5Yr'],
        'ROE %': ['ROE %', 'ROE', 'Return on equity', 'Return on equity %'],
        'Avg ROE 5Yr %': ['Avg ROE 5Yr %', 'Average return on equity 5Years', '5Yr Avg ROE', 'Average ROE 5Yr %'],
        'Min ROE 5Yr %': ['Min ROE 5Yr %', 'Minimum return on equity 5Years', 'Min ROE 5Yr'],
        'Sales growth 5Yr %': ['Sales growth 5Yr %', 'Sales growth 5Years %', 'Sales growth 5Years', 'Revenue CAGR 5Yr', 'Sales growth 5Yr'],
        'Profit growth 5Yr %': ['Profit growth 5Yr %', 'Profit growth 5Years %', 'Profit growth 5Years', 'EPS CAGR 5Yr', 'Profit growth 5Yr'],
        'Debt to equity': ['Debt to equity', 'Debt to Equity', 'D/E', 'Debt to equity ratio'],
        'Promoter holding %': ['Promoter holding %', 'Promoter holding', 'Promoter Holding %'],
        'Promoter holding 3Yr ago %': ['Promoter holding 3Yr ago %', 'Promoter holding 3years back', 'Promoter holding 3Yr ago'],
        'Pledged percentage %': ['Pledged percentage %', 'Pledged percentage', 'Pledge %'],
        'PEG Ratio': ['PEG Ratio', 'PEG', 'PEG ratio'],
        'PE': ['PE', 'P/E', 'Price to Earning', 'Price to Earning ratio'],
        'Avg PE 5Yr': ['Avg PE 5Yr', '5Yr Avg PE', 'Average PE 5Yr', 'Average PE 5Years'],
        'Price to book': ['Price to book', 'Price to book value', 'P/B', 'P/B Ratio']
    }
    
    # Standardize columns by matching known aliases
    for standard_name, aliases in column_mappings.items():
        matched_col = None
        for col in df.columns:
            if col in aliases or col.lower() == standard_name.lower():
                matched_col = col
                break
        if matched_col and matched_col != standard_name:
            df.rename(columns={matched_col: standard_name}, inplace=True)
            
    # List of expected numeric columns to clean
    numeric_cols = [
        'ROCE %', 'Avg ROCE 5Yr %', 'Min ROCE 5Yr %', 
        'ROE %', 'Avg ROE 5Yr %', 'Min ROE 5Yr %', 
        'Sales growth 5Yr %', 'Profit growth 5Yr %', 
        'Debt to equity', 'Promoter holding %', 
        'Promoter holding 3Yr ago %', 'Pledged percentage %', 
        'PEG Ratio', 'PE', 'Avg PE 5Yr', 'Price to book'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_numeric)
        else:
            # Create default zero column if missing
            df[col] = 0.0
            
    return df

def apply_stage1_hard_gate(row):
    """
    Applies Stage 1 filters (Hard Gates) to a row.
    Returns (passed: bool, reason: str)
    """
    reasons = []
    
    # 1. ROCE (5yr avg) > 15-18%
    if row['Avg ROCE 5Yr %'] < ROCE_AVG_LIMIT:
        reasons.append(f"Avg ROCE 5Yr ({row['Avg ROCE 5Yr %']:.1f}%) < {ROCE_AVG_LIMIT}%")
        
    # 2. ROE (5yr avg) > 15%
    if row['Avg ROE 5Yr %'] < ROE_AVG_LIMIT:
        reasons.append(f"Avg ROE 5Yr ({row['Avg ROE 5Yr %']:.1f}%) < {ROE_AVG_LIMIT}%")
        
    # 3. Revenue CAGR (5yr) > 10%
    if row['Sales growth 5Yr %'] < SALES_GROWTH_LIMIT:
        reasons.append(f"Sales growth 5Yr ({row['Sales growth 5Yr %']:.1f}%) < {SALES_GROWTH_LIMIT}%")
        
    # 4. Profit growth (5yr) > 12%
    if row['Profit growth 5Yr %'] < PROFIT_GROWTH_LIMIT:
        reasons.append(f"Profit growth 5Yr ({row['Profit growth 5Yr %']:.1f}%) < {PROFIT_GROWTH_LIMIT}%")
        
    # 5. Debt to Equity < 0.5 (Skipped for BFSI)
    is_bfsi = str(row.get('Sector', '')).strip().upper() == 'BFSI'
    if not is_bfsi:
        if row['Debt to equity'] >= DEBT_EQUITY_LIMIT:
            reasons.append(f"Debt/Equity ({row['Debt to equity']:.2f}) >= {DEBT_EQUITY_LIMIT}")
            
    # 6. Consistency: Min ROE/ROCE never drops below threshold
    # Note: If Min ROCE/ROE is 0.0 (possibly because it was not exported), we log a warning but don't fail the hard gate.
    if row['Min ROCE 5Yr %'] > 0.0 and row['Min ROCE 5Yr %'] < MIN_ROCE_LIMIT:
        reasons.append(f"Min ROCE 5Yr consistency ({row['Min ROCE 5Yr %']:.1f}%) < {MIN_ROCE_LIMIT}%")
    if row['Min ROE 5Yr %'] > 0.0 and row['Min ROE 5Yr %'] < MIN_ROE_LIMIT:
        reasons.append(f"Min ROE 5Yr consistency ({row['Min ROE 5Yr %']:.1f}%) < {MIN_ROE_LIMIT}%")
        
    if reasons:
        return False, "; ".join(reasons)
    return True, "Passed"

def calculate_stage2_score(row):
    """
    Computes a score from 0 to 100 based on Stage 2 validation rules.
    - PE vs 5Yr Avg PE (Max 40 points)
    - PEG Ratio (Max 30 points)
    - Promoter Pledge Penalty (Max 15 points)
    - Promoter Holding Trend Penalty (Max 15 points)
    """
    # 1. Valuation PE vs Avg PE 5Yr (Max 40 points)
    pe_score = 0.0
    pe = row['PE']
    avg_pe = row['Avg PE 5Yr']
    if pe > 0:
        if pe <= avg_pe:
            pe_score = 40.0
        else:
            # Scale down if current PE is higher than historical average PE
            pe_score = max(0.0, 40.0 * (avg_pe / pe))
    else:
        # Default to neutral if no PE data
        pe_score = 20.0
        
    # 2. PEG Ratio (Max 30 points)
    peg_score = 0.0
    peg = row['PEG Ratio']
    if peg > 0:
        if peg <= 1.5:
            peg_score = 30.0
        elif peg <= 2.5:
            # Scale down for PEG between 1.5 and 2.5
            peg_score = max(0.0, 30.0 * (1.5 / peg))
        else:
            peg_score = 0.0
    else:
        peg_score = 15.0 # Neutral default
        
    # 3. Promoter Pledge Penalty (Max 15 points)
    # Full points if 0 pledge, deduct proportionally to pledge percentage
    pledge_pct = row['Pledged percentage %']
    pledge_score = max(0.0, 15.0 - pledge_pct)
    
    # 4. Promoter Holding Trend (Max 15 points)
    # Penalize if current holding is lower than 3 years ago
    curr_hold = row['Promoter holding %']
    old_hold = row['Promoter holding 3Yr ago %']
    
    holding_score = 15.0
    if old_hold > 0:
        decline = old_hold - curr_hold
        if decline > 0:
            # Deduct double the decline percentage as a penalty
            holding_score = max(0.0, 15.0 - (decline * 2.0))
            
    # Combine scores
    total_score = pe_score + peg_score + pledge_score + holding_score
    
    # Determine Red Flags
    red_flags = []
    if pledge_pct > 10.0:
        red_flags.append(f"High promoter pledge ({pledge_pct:.1f}%)")
    if old_hold > 0 and (old_hold - curr_hold) > 5.0:
        red_flags.append(f"Declining promoter holding (-{(old_hold - curr_hold):.1f}%)")
    if peg > 2.5:
        red_flags.append(f"High PEG ratio ({peg:.2f})")
        
    red_flags_str = ", ".join(red_flags) if red_flags else "None"
    
    return round(total_score, 1), red_flags_str

def run_screener(file_path):
    """
    Runs the screening process and outputs summaries of passing and failed stocks.
    """
    print(f"=== India Stock Screener ===")
    print(f"Loading data from: {file_path}\n")
    
    df = load_and_clean_data(file_path)
    
    # Apply Stage 1 Gate
    stage1_results = df.apply(apply_stage1_hard_gate, axis=1)
    df['Stage1_Passed'] = [r[0] for r in stage1_results]
    df['Stage1_Reason'] = [r[1] for r in stage1_results]
    
    # Calculate Stage 2 Scores and Red Flags
    scores_and_flags = df.apply(calculate_stage2_score, axis=1)
    df['Validation_Score'] = [sf[0] for sf in scores_and_flags]
    df['Red_Flags'] = [sf[1] for sf in scores_and_flags]
    
    # Separate passing and failed stocks
    passed_df = df[df['Stage1_Passed']].copy()
    failed_df = df[~df['Stage1_Passed']].copy()
    
    # Sort passed stocks by score descending
    passed_df.sort_values(by='Validation_Score', ascending=False, inplace=True)
    
    print(f"--- PASSED STOCKS (Ranked by Validation Score) ---")
    if not passed_df.empty:
        cols_to_print = [
            'Name', 'Ticker', 'Sector', 'Avg ROCE 5Yr %', 'Avg ROE 5Yr %', 
            'Sales growth 5Yr %', 'Debt to equity', 'PE', 'PEG Ratio', 
            'Validation_Score', 'Red_Flags'
        ]
        # Reorder and format columns
        print_df = passed_df[cols_to_print].reset_index(drop=True)
        print_df.index += 1
        print(print_df.to_string(index=True))
    else:
        print("No stocks passed the Stage 1 hard gates.")
        
    print("\n--- FILTERED OUT STOCKS ---")
    if not failed_df.empty:
        for idx, row in failed_df.iterrows():
            print(f"- {row['Name']} ({row['Ticker']}): {row['Stage1_Reason']}")
    else:
        print("No stocks were filtered out.")
        
    # Save results
    output_dir = os.path.dirname(file_path)
    passed_output = os.path.join(output_dir, 'screener_passed_shortlist.csv')
    passed_df.to_csv(passed_output, index=False)
    print(f"\nSaved ranked shortlist to: {passed_output}")
    
    return passed_df

if __name__ == '__main__':
    default_csv = os.path.join(os.path.dirname(__file__), 'data', 'nifty_200_screener_mock.csv')
    run_screener(default_csv)
