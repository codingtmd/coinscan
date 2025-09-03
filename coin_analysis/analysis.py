
import os
import pandas as pd
from binance.client import Client
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError
import matplotlib.pyplot as plt

# --- Configuration ---
# Replace with your actual API keys
BINANCE_API_KEY = ""
BINANCE_API_SECRET = ""
COINMARKETCAP_API_KEY = ""

# Number of past days to fetch data fors
N_DAYS = 1

# Output directory
OUTPUT_DIR = "analysis_output"

# --- Functions ---

def get_usdt_pairs(client):
    """Gets all USDT trading pairs from Binance."""
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
    return symbols

def get_daily_data(client, symbol, n_days=1):
    """Gets the last n days of k-line data for a symbol."""
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, f"{n_days} day ago UTC")
    if not klines:
        return None
    
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']:
        df[col] = pd.to_numeric(df[col])
    return df

def get_market_cap_data(cmc_client, symbols):
    """Gets market cap data from CoinMarketCap."""
    # CMC library expects symbols without USDT
    base_symbols = [s.replace('USDT', '') for s in symbols]
    
    try:
        # Fetching quotes for the symbols
        response = cmc_client.cryptocurrency_quotes_latest(symbol=','.join(base_symbols))
        
        market_caps = {}
        for symbol_base in base_symbols:
            if symbol_base in response.data:
                data = response.data[symbol_base]
                quote_usd = data['quote']['USD']
                market_caps[symbol_base + 'USDT'] = {
                    'unlocked_mkt_cap': quote_usd.get('market_cap'),
                    'circulating_supply': data.get('circulating_supply'),
                    'total_supply': data.get('total_supply'),
                    'volume_24h': quote_usd.get('volume_24h'),
                    'volume_market_cap_24h': quote_usd.get('volume_24h') / quote_usd.get('market_cap') if quote_usd.get('market_cap') else 0
                }
        return market_caps
    except CoinMarketCapAPIError as e:
        print(f"Could not fetch CoinMarketCap data: {e.error}")
        return {}


def analyze_and_report(binance_data, market_cap_data):
    """Analyzes the data and generates a report."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Combine data
    combined_data = []
    for symbol, df in binance_data.items():
        if symbol in market_cap_data:
            data_row = {
                'symbol': symbol,
                'open': df['open'].iloc[0],
                'high': df['high'].iloc[0],
                'low': df['low'].iloc[0],
                'close': df['close'].iloc[0],
                'volume': df['volume'].iloc[0],
                **market_cap_data[symbol]
            }
            combined_data.append(data_row)

    if not combined_data:
        print("No combined data to analyze.")
        return

    full_df = pd.DataFrame(combined_data)
    full_df.to_csv(os.path.join(OUTPUT_DIR, "combined_data.csv"), index=False)

    # Group by market cap
    full_df = full_df.sort_values(by='unlocked_mkt_cap', ascending=False).dropna(subset=['unlocked_mkt_cap'])
    
    if full_df.empty:
        print("No data with market cap to analyze.")
        return
        
    top_third_index = int(len(full_df) / 3)
    mid_third_index = int(2 * len(full_df) / 3)

    top_group = full_df.iloc[:top_third_index]
    mid_group = full_df.iloc[top_third_index:mid_third_index]
    low_group = full_df.iloc[mid_third_index:]

    groups = {'top': top_group, 'mid': mid_group, 'low': low_group}

    # --- Generate Report ---
    report_parts = ["# Cryptocurrency Analysis Report\n\n"]

    # Market Cap Distribution
    plt.figure(figsize=(10, 6))
    full_df['unlocked_mkt_cap'].log10().hist(bins=50)
    plt.title('Log of Unlocked Market Cap Distribution')
    plt.xlabel('Log(Unlocked Market Cap)')
    plt.ylabel('Frequency')
    dist_path = os.path.join(OUTPUT_DIR, 'market_cap_distribution.png')
    plt.savefig(dist_path)
    plt.close()
    report_parts.append("## Market Cap Distribution\n\n")
    report_parts.append(f"![Market Cap Distribution]({dist_path})\n\n")


    for name, group_df in groups.items():
        report_parts.append(f"## {name.capitalize()} Group Analysis\n\n")
        
        if group_df.empty:
            report_parts.append("No data in this group.\n\n")
            continue

        # Save group data
        group_df.to_csv(os.path.join(OUTPUT_DIR, f"{name}_group.csv"), index=False)
        
        # Statistical Summary
        report_parts.append("### Statistical Summary\n\n")
        report_parts.append(group_df[['open', 'high', 'low', 'close', 'volume', 'unlocked_mkt_cap', 'volume_24h']].describe().to_markdown())
        report_parts.append("\n\n")

        # Correlation Matrix
        corr = group_df[['close', 'volume', 'unlocked_mkt_cap', 'volume_24h']].corr()
        report_parts.append("### Correlation Matrix\n\n")
        report_parts.append(corr.to_markdown())
        report_parts.append("\n\n")

    report = "".join(report_parts)
    with open(os.path.join(OUTPUT_DIR, "report.md"), "w") as f:
        f.write(report)
    
    print(f"Analysis complete. Report and data saved in '{OUTPUT_DIR}' directory.")


# --- Main Execution ---

if __name__ == "__main__":
    # Initialize clients
    binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
    cmc_client = CoinMarketCapAPI(COINMARKETCAP_API_KEY)

    # 1. Get all USDT pairs from Binance
    print("Fetching USDT pairs from Binance...")
    usdt_pairs = get_usdt_pairs(binance_client)
    print(f"Found {len(usdt_pairs)} USDT pairs.")

    # 2. Get daily data for each pair
    print(f"Fetching last {N_DAYS} day(s) of data for each pair...")
    all_daily_data = {}
    for i, symbol in enumerate(usdt_pairs):
        print(f"Fetching {symbol} ({i+1}/{len(usdt_pairs)})...")
        daily_data = get_daily_data(binance_client, symbol, N_DAYS)
        if daily_data is not None:
            all_daily_data[symbol] = daily_data
    
    # 3. Get market cap data
    print("Fetching market cap data from CoinMarketCap...")
    market_caps = get_market_cap_data(cmc_client, list(all_daily_data.keys()))

    # 4. & 5. Analyze and generate report
    print("Analyzing data and generating report...")
    analyze_and_report(all_daily_data, market_caps)

