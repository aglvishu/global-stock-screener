#!/usr/bin/env python3
import pandas as pd
import yfinance as yf
import numpy as np

def fetch_and_calculate_technicals(ticker_symbol):
    """
    Downloads historical daily prices and computes technical indicators for a ticker.
    Supports Weinstein Stage 2 and Minervini Trend Template conditions.
    """
    try:
        # Determine the benchmark based on the market suffix
        is_india = ticker_symbol.endswith('.NS') or ticker_symbol.endswith('.BO')
        benchmark_symbol = "^NSEI" if is_india else "^GSPC"
        
        # Download 2 years of daily data for the stock and benchmark to calculate moving averages and RS
        # We fetch 2 years to ensure the 200 DMA is fully warmed up and has historical slope data
        data = yf.download([ticker_symbol, benchmark_symbol], period="2y", interval="1d", progress=False)
        
        # Handle multi-index columns returned by yf.download when querying multiple symbols
        if isinstance(data.columns, pd.MultiIndex):
            stock_close = data['Close'][ticker_symbol].dropna()
            bench_close = data['Close'][benchmark_symbol].dropna()
        else:
            # Fallback if only one ticker is processed (though we query two)
            stock_close = data['Close'].dropna()
            bench_close = pd.Series()
            
        if stock_close.empty:
            return {"Ticker": ticker_symbol, "Error": "No price data found"}
            
        current_price = float(stock_close.iloc[-1])
        
        # 1. Moving Averages
        sma_50 = stock_close.rolling(window=50).mean()
        sma_150 = stock_close.rolling(window=150).mean()
        sma_200 = stock_close.rolling(window=200).mean()
        
        curr_sma_50 = float(sma_50.iloc[-1])
        curr_sma_150 = float(sma_150.iloc[-1])
        curr_sma_200 = float(sma_200.iloc[-1])
        
        # 2. 200 DMA Slope (Is 200 DMA trending up?)
        # We check if today's 200 DMA is higher than it was 20 trading days (approx. 1 month) ago
        sma_200_20d_ago = float(sma_200.iloc[-20]) if len(sma_200) > 20 else curr_sma_200
        is_sma_200_sloping_up = curr_sma_200 > sma_200_20d_ago
        
        # 3. 52-Week High & Low (approx. 252 trading days)
        last_year_data = stock_close.iloc[-252:] if len(stock_close) >= 252 else stock_close
        high_52w = float(last_year_data.max())
        low_52w = float(last_year_data.min())
        
        # 4. Proximity Checks
        # Price within 25% of 52w High -> Price >= 0.75 * 52w High
        is_near_52w_high = current_price >= (0.75 * high_52w)
        # Price at least 30% above 52w Low -> Price >= 1.30 * 52w Low
        is_above_30pct_52w_low = current_price >= (1.30 * low_52w)
        
        # 5. Relative Strength (RS) score calculation vs benchmark
        # We calculate the relative outperformance of the stock vs the benchmark index over 3 months (approx 63 trading days)
        rs_score = 0.0
        if not bench_close.empty and len(stock_close) >= 63 and len(bench_close) >= 63:
            stock_perf = (stock_close.iloc[-1] / stock_close.iloc[-63]) - 1.0
            bench_perf = (bench_close.iloc[-1] / bench_close.iloc[-63]) - 1.0
            # Relative strength is the difference in returns
            rs_score = round((stock_perf - bench_perf) * 100.0, 2)
            
        # 6. Stan Weinstein Stage 2 Template Verification
        # - Price > 150 DMA and Price > 200 DMA
        # - 150 DMA > 200 DMA
        # - 200 DMA sloping up
        # - 50 DMA > 150 DMA and 50 DMA > 200 DMA
        stage_2_pass = (
            current_price > curr_sma_150 and
            current_price > curr_sma_200 and
            curr_sma_150 > curr_sma_200 and
            is_sma_200_sloping_up and
            curr_sma_50 > curr_sma_150 and
            is_near_52w_high and
            is_above_30pct_52w_low
        )
        
        # Collect failure reasons if it doesn't pass the technical gate
        failed_reasons = []
        if current_price <= curr_sma_150: failed_reasons.append("Price <= 150 DMA")
        if current_price <= curr_sma_200: failed_reasons.append("Price <= 200 DMA")
        if curr_sma_150 <= curr_sma_200: failed_reasons.append("150 DMA <= 200 DMA")
        if not is_sma_200_sloping_up: failed_reasons.append("200 DMA not sloping up")
        if curr_sma_50 <= curr_sma_150: failed_reasons.append("50 DMA <= 150 DMA")
        if not is_near_52w_high: failed_reasons.append("Price not within 25% of 52W High")
        if not is_above_30pct_52w_low: failed_reasons.append("Price not 30% above 52W Low")
        
        tech_reason = "Passed Stage 2 Template" if stage_2_pass else "; ".join(failed_reasons)
        
        # Get Analyst Recommendation
        recommendation = 'N/A'
        try:
            ticker_obj = yf.Ticker(ticker_symbol)
            info = ticker_obj.info
            rec = info.get('recommendationKey', 'N/A')
            if rec and rec.lower() not in ['n/a', 'none']:
                recommendation = rec.replace('_', ' ').title()
        except Exception:
            pass

        return {
            "Ticker": ticker_symbol,
            "Current Price": round(current_price, 2),
            "50 DMA": round(curr_sma_50, 2),
            "150 DMA": round(curr_sma_150, 2),
            "200 DMA": round(curr_sma_200, 2),
            "200 DMA Sloping Up": is_sma_200_sloping_up,
            "52W High": round(high_52w, 2),
            "52W Low": round(low_52w, 2),
            "Relative Strength (3m vs Index %)": rs_score,
            "Analyst Rec": recommendation,
            "Stage 2 Pass": stage_2_pass,
            "Technical Failure Reason": tech_reason
        }
    except Exception as e:
        return {"Ticker": ticker_symbol, "Error": f"Technical calculation failed: {e}"}

if __name__ == '__main__':
    # Test calculations
    test_tickers = ['AAPL', 'MSFT', 'TCS.NS']
    print("Testing technical calculations...")
    for t in test_tickers:
        res = fetch_and_calculate_technicals(t)
        print(f"\nResults for {t}:")
        for k, v in res.items():
            print(f"  {k}: {v}")
