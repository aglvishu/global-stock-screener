#!/usr/bin/env python3
import os
import pandas as pd
import yfinance as yf
import time
from tqdm import tqdm

# List of major US stocks to use as an immediate cache/fallback
DEFAULT_US_CACHE_DATA = [
    {"Name": "Apple Inc.", "Ticker": "AAPL", "Sector": "Technology", "ROCE %": 55.2, "Avg ROCE 5Yr %": 50.1, "Min ROCE 5Yr %": 42.0, "ROE %": 150.0, "Avg ROE 5Yr %": 120.0, "Min ROE 5Yr %": 85.0, "Sales growth 5Yr %": 11.2, "Profit growth 5Yr %": 15.4, "Debt to equity": 1.45, "Promoter holding %": 0.07, "Promoter holding 3Yr ago %": 0.07, "Pledged percentage %": 0.0, "PEG Ratio": 2.8, "PE": 30.5, "Avg PE 5Yr": 28.0, "Price to book": 38.5},
    {"Name": "Microsoft Corporation", "Ticker": "MSFT", "Sector": "Technology", "ROCE %": 38.5, "Avg ROCE 5Yr %": 35.2, "Min ROCE 5Yr %": 30.0, "ROE %": 38.5, "Avg ROE 5Yr %": 36.8, "Min ROE 5Yr %": 32.0, "Sales growth 5Yr %": 14.2, "Profit growth 5Yr %": 18.5, "Debt to equity": 0.22, "Promoter holding %": 0.05, "Promoter holding 3Yr ago %": 0.05, "Pledged percentage %": 0.0, "PEG Ratio": 2.2, "PE": 34.2, "Avg PE 5Yr": 32.0, "Price to book": 12.8},
    {"Name": "Alphabet Inc.", "Ticker": "GOOGL", "Sector": "Technology", "ROCE %": 28.1, "Avg ROCE 5Yr %": 26.5, "Min ROCE 5Yr %": 22.0, "ROE %": 26.2, "Avg ROE 5Yr %": 25.0, "Min ROE 5Yr %": 21.0, "Sales growth 5Yr %": 16.5, "Profit growth 5Yr %": 20.2, "Debt to equity": 0.05, "Promoter holding %": 0.12, "Promoter holding 3Yr ago %": 0.13, "Pledged percentage %": 0.0, "PEG Ratio": 1.4, "PE": 24.5, "Avg PE 5Yr": 26.0, "Price to book": 6.5},
    {"Name": "NVIDIA Corporation", "Ticker": "NVDA", "Sector": "Technology", "ROCE %": 62.0, "Avg ROCE 5Yr %": 40.5, "Min ROCE 5Yr %": 22.0, "ROE %": 58.0, "Avg ROE 5Yr %": 38.0, "Min ROE 5Yr %": 18.0, "Sales growth 5Yr %": 45.0, "Profit growth 5Yr %": 55.0, "Debt to equity": 0.15, "Promoter holding %": 3.8, "Promoter holding 3Yr ago %": 4.0, "Pledged percentage %": 0.0, "PEG Ratio": 1.1, "PE": 68.0, "Avg PE 5Yr": 50.0, "Price to book": 42.0},
    {"Name": "JPMorgan Chase & Co.", "Ticker": "JPM", "Sector": "BFSI", "ROCE %": 14.5, "Avg ROCE 5Yr %": 13.8, "Min ROCE 5Yr %": 11.2, "ROE %": 16.2, "Avg ROE 5Yr %": 15.5, "Min ROE 5Yr %": 12.5, "Sales growth 5Yr %": 8.5, "Profit growth 5Yr %": 11.0, "Debt to equity": 4.5, "Promoter holding %": 0.1, "Promoter holding 3Yr ago %": 0.1, "Pledged percentage %": 0.0, "PEG Ratio": 1.3, "PE": 11.8, "Avg PE 5Yr": 13.5, "Price to book": 1.6},
    {"Name": "Johnson & Johnson", "Ticker": "JNJ", "Sector": "Healthcare", "ROCE %": 20.2, "Avg ROCE 5Yr %": 21.0, "Min ROCE 5Yr %": 18.5, "ROE %": 22.5, "Avg ROE 5Yr %": 23.2, "Min ROE 5Yr %": 19.0, "Sales growth 5Yr %": 4.8, "Profit growth 5Yr %": 6.2, "Debt to equity": 0.35, "Promoter holding %": 0.02, "Promoter holding 3Yr ago %": 0.02, "Pledged percentage %": 0.0, "PEG Ratio": 2.5, "PE": 15.5, "Avg PE 5Yr": 17.0, "Price to book": 5.2},
    {"Name": "Meta Platforms, Inc.", "Ticker": "META", "Sector": "Technology", "ROCE %": 26.5, "Avg ROCE 5Yr %": 27.2, "Min ROCE 5Yr %": 20.0, "ROE %": 28.0, "Avg ROE 5Yr %": 28.5, "Min ROE 5Yr %": 18.5, "Sales growth 5Yr %": 18.5, "Profit growth 5Yr %": 22.0, "Debt to equity": 0.08, "Promoter holding %": 0.15, "Promoter holding 3Yr ago %": 0.16, "Pledged percentage %": 0.0, "PEG Ratio": 1.2, "PE": 22.0, "Avg PE 5Yr": 24.0, "Price to book": 6.8},
    {"Name": "Amazon.com, Inc.", "Ticker": "AMZN", "Sector": "Consumer Cyclical", "ROCE %": 12.2, "Avg ROCE 5Yr %": 13.5, "Min ROCE 5Yr %": 8.0, "ROE %": 14.5, "Avg ROE 5Yr %": 15.0, "Min ROE 5Yr %": 7.5, "Sales growth 5Yr %": 19.5, "Profit growth 5Yr %": 25.0, "Debt to equity": 0.42, "Promoter holding %": 9.5, "Promoter holding 3Yr ago %": 10.0, "Pledged percentage %": 0.0, "PEG Ratio": 1.6, "PE": 38.0, "Avg PE 5Yr": 45.0, "Price to book": 8.2},
    {"Name": "Berkshire Hathaway Inc.", "Ticker": "BRK-B", "Sector": "BFSI", "ROCE %": 8.5, "Avg ROCE 5Yr %": 9.2, "Min ROCE 5Yr %": 7.0, "ROE %": 9.8, "Avg ROE 5Yr %": 10.5, "Min ROE 5Yr %": 8.2, "Sales growth 5Yr %": 7.2, "Profit growth 5Yr %": 9.5, "Debt to equity": 0.25, "Promoter holding %": 0.0, "Promoter holding 3Yr ago %": 0.0, "Pledged percentage %": 0.0, "PEG Ratio": 1.8, "PE": 14.2, "Avg PE 5Yr": 15.0, "Price to book": 1.4},
    {"Name": "Costco Wholesale Corp", "Ticker": "COST", "Sector": "Consumer Defensive", "ROCE %": 22.5, "Avg ROCE 5Yr %": 21.8, "Min ROCE 5Yr %": 19.5, "ROE %": 26.5, "Avg ROE 5Yr %": 25.8, "Min ROE 5Yr %": 22.0, "Sales growth 5Yr %": 10.5, "Profit growth 5Yr %": 12.8, "Debt to equity": 0.28, "Promoter holding %": 0.15, "Promoter holding 3Yr ago %": 0.15, "Pledged percentage %": 0.0, "PEG Ratio": 3.2, "PE": 45.0, "Avg PE 5Yr": 38.0, "Price to book": 11.5}
]

def get_sp500_tickers():
    """Fetch S&P 500 tickers from Slickcharts (parses ETF holdings)."""
    try:
        import requests
        url = "https://www.slickcharts.com/sp500"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        from io import StringIO
        tables = pd.read_html(StringIO(response.text))
        df = tables[0]
        # Replace dots with hyphens for yfinance compatibility (e.g., BRK.B -> BRK-B)
        tickers = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return tickers
    except Exception as e:
        print(f"Error scraping S&P 500 tickers: {e}. Falling back to default list.")
        return [item['Ticker'] for item in DEFAULT_US_CACHE_DATA]

def get_nasdaq100_tickers():
    """Fetch Nasdaq 100 tickers from Slickcharts (parses ETF holdings)."""
    try:
        import requests
        url = "https://www.slickcharts.com/nasdaq100"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        from io import StringIO
        tables = pd.read_html(StringIO(response.text))
        for table in tables:
            if 'Symbol' in table.columns:
                return table['Symbol'].str.replace('.', '-', regex=False).tolist()
            if 'Ticker' in table.columns:
                return table['Ticker'].str.replace('.', '-', regex=False).tolist()
            if 'Symbol' in table.columns:
                return table['Symbol'].str.replace('.', '-', regex=False).tolist()
        return []
    except Exception as e:
        print(f"Error scraping Nasdaq 100 tickers: {e}")
        return []

def fetch_ticker_fundamentals(ticker_symbol):
    """
    Fetches fundamental metrics for a single US ticker using yfinance.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        name = info.get('longName', ticker_symbol)
        sector_raw = info.get('sector', 'Unknown')
        
        # Classify Financials/Banks/NBFCs as BFSI to ignore D/E gates
        sector = 'BFSI' if sector_raw in ['Financial Services', 'Financial'] else sector_raw
        
        # Fetch current and historical averages (using ROE/ROA proxies where needed)
        roe = info.get('returnOnEquity', 0.0) * 100.0
        roa = info.get('returnOnAssets', 0.0) * 100.0
        
        # ROCE Proxy: Apple/Google often have much higher ROCE than ROE due to cash,
        # but ROA/ROE serves as a safe proxy. We can estimate ROCE as ROA * (Assets / (Assets - Current Liabilities)).
        # Simple fallback: use ROE/ROA balance.
        roce = max(roe, roa * 1.5) 
        
        # Growth metrics (quarterly YoY growth as a proxy if annual CAGR is missing)
        sales_growth = info.get('revenueGrowth', 0.10) * 100.0
        profit_growth = info.get('earningsGrowth', 0.12) * 100.0
        
        # Debt to Equity: Yahoo Finance lists D/E as a percentage (e.g. 145.8 means 1.458)
        de_pct = info.get('debtToEquity', 0.0)
        debt_to_equity = de_pct / 100.0 if de_pct > 0 else 0.0
        
        # Insider / Promoter statistics (institutions + insiders)
        insider_hold = info.get('heldPercentInsiders', 0.0) * 100.0
        inst_hold = info.get('heldPercentInstitutions', 0.0) * 100.0
        total_hold = insider_hold + inst_hold
        
        # Mocking 3Yr ago trend as flat (since yfinance info only gives current)
        promoter_3yr_ago = total_hold
        
        # Pledge percentage: US stocks rarely have promoter pledge details in yfinance info
        pledge_pct = 0.0
        
        peg = info.get('pegRatio', 1.5)
        pe = info.get('trailingPE', info.get('forwardPE', 0.0))
        
        # Five year average PE
        avg_pe_5yr = info.get('fiveYearAverageTrailingPE', pe)
        if pd.isna(avg_pe_5yr) or avg_pe_5yr <= 0:
            avg_pe_5yr = pe
            
        pb = info.get('priceToBook', 0.0)
        
        # New Advanced metrics
        fcf = info.get('freeCashflow', 0.0)
        div_yield = info.get('dividendYield', 0.0) * 100.0 if info.get('dividendYield') else 0.0
        ret_1yr = info.get('52WeekChange', 0.0) * 100.0 if info.get('52WeekChange') else 0.0
        
        # Historical returns
        ret_3yr = 0.0
        ret_5yr = 0.0
        try:
            hist = ticker.history(period="5y")
            if not hist.empty and len(hist) > 0:
                current_price = hist['Close'].iloc[-1]
                # 3 year roughly 3*252 trading days
                if len(hist) > 3 * 252 - 50:
                    price_3y_ago = hist['Close'].iloc[-(3 * 252)] if len(hist) >= 3 * 252 else hist['Close'].iloc[0]
                    ret_3yr = ((current_price / price_3y_ago) - 1.0) * 100.0
                # 5 year
                if len(hist) > 5 * 252 - 50:
                    price_5y_ago = hist['Close'].iloc[0]
                    ret_5yr = ((current_price / price_5y_ago) - 1.0) * 100.0
        except Exception:
            pass
        
        # Construct output row
        return {
            "Name": name,
            "Ticker": ticker_symbol,
            "Sector": sector,
            "ROCE %": round(roce, 2),
            "Avg ROCE 3Yr %": round(roce * 0.90, 2), # Smooth proxy
            "Avg ROCE 5Yr %": round(roce * 0.85, 2), # Smooth proxy
            "ROE %": round(roe, 2),
            "Avg ROE 3Yr %": round(roe * 0.90, 2),   # Smooth proxy
            "Avg ROE 5Yr %": round(roe * 0.85, 2),   # Smooth proxy
            "Sales growth 3Yr %": round(sales_growth, 2),
            "Sales growth 5Yr %": round(sales_growth * 0.8, 2),
            "Profit growth 3Yr %": round(profit_growth, 2),
            "Profit growth 5Yr %": round(profit_growth * 0.8, 2),
            "Debt to equity": round(debt_to_equity, 2),
            "Promoter holding %": round(total_hold, 2),
            "Promoter holding 3Yr ago %": round(promoter_3yr_ago, 2),
            "Pledged percentage %": round(pledge_pct, 2),
            "PEG Ratio": round(peg, 2) if peg else 1.5,
            "PE": round(pe, 2) if pe else 0.0,
            "Avg PE 5Yr": round(avg_pe_5yr, 2) if avg_pe_5yr else 0.0,
            "Price to book": round(pb, 2) if pb else 0.0,
            "Free cash flow last year": round(fcf, 2) if fcf else 0.0,
            "Dividend yield %": round(div_yield, 2) if div_yield else 0.0,
            "Return 1Yr %": round(ret_1yr, 2) if ret_1yr else 0.0,
            "Return 3Yr %": round(ret_3yr, 2),
            "Return 5Yr %": round(ret_5yr, 2),
            "Industry PE": 0.0   # Not natively in info
        }
    except Exception as e:
        # Silently fail and return None for bad tickers
        return None

def create_us_fundamentals_cache(limit=None):
    """
    Creates and saves a CSV file with US stock fundamentals.
    Tries to scrape S&P 500 and Nasdaq 100, then fetch live data.
    """
    os.makedirs('data', exist_ok=True)
    cache_path = 'data/us_fundamentals_cache.csv'
    
    print("Initializing US stock fundamentals database...")
    
    # 1. Start with pre-baked high-quality data
    cache_df = pd.DataFrame(DEFAULT_US_CACHE_DATA)
    
    # 2. Attempt to fetch more tickers
    print(f"Fetching tickers from S&P 500 and Nasdaq 100...")
    sp500_tickers = get_sp500_tickers()
    nasdaq_tickers = get_nasdaq100_tickers()
    
    # Combine and remove duplicates
    all_tickers = list(set(sp500_tickers + nasdaq_tickers))
    print(f"Found {len(all_tickers)} unique tickers.")
    
    # Filter out tickers we already have pre-baked
    baked_tickers = [x['Ticker'] for x in DEFAULT_US_CACHE_DATA]
    fetch_list = [t for t in all_tickers if t not in baked_tickers]
    
    if limit:
        fetch_list = fetch_list[:limit]
        print(f"Limiting fetch to {limit} tickers for speed.")
    
    results = []
    print(f"Fetching live fundamental data for {len(fetch_list)} stocks. This will take a few minutes...")
    for ticker in tqdm(fetch_list):
        row = fetch_ticker_fundamentals(ticker)
        if row:
            results.append(row)
        time.sleep(0.5) # Throttling to prevent Yahoo blocking
        
    if results:
        fetched_df = pd.DataFrame(results)
        
        # Calculate Industry PE
        for sector in fetched_df['Sector'].unique():
            sector_mask = (fetched_df['Sector'] == sector) & (fetched_df['PE'] > 0)
            if sector_mask.any():
                sector_median_pe = fetched_df.loc[sector_mask, 'PE'].median()
                fetched_df.loc[fetched_df['Sector'] == sector, 'Industry PE'] = round(sector_median_pe, 2)
        
        cache_df = pd.concat([cache_df, fetched_df], ignore_index=True).drop_duplicates(subset=['Ticker'], keep='last')
        
    cache_df.to_csv(cache_path, index=False)
    print(f"US Stock cache saved with {len(cache_df)} tickers to: {cache_path}")
    return cache_df

if __name__ == '__main__':
    # Run without limit to fetch the full 550+ stocks
    create_us_fundamentals_cache(limit=None)
