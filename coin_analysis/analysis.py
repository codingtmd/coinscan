import os
import numpy as np 
import pandas as pd
from binance.client import Client
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from config import BINANCE_API_KEY, BINANCE_API_SECRET, COINMARKETCAP_API_KEY
from data_fetcher import get_usdt_pairs, get_daily_data, get_market_cap_data
from statistics import generate_group_statistics_report, generate_comparative_descriptive_statistics_table

# --- Grouping Method ---
# Choose the grouping method: 'terciles', 'thresholds', or 'kmeans'
GROUPING_METHOD = 'thresholds'

# Thresholds for 'thresholds' method
LOW_CAP_THRESHOLD = 100_000_000  # 100 Million
MID_CAP_THRESHOLD = 1_000_000_000  # 1 Billion

# Number of past days to fetch data fors
N_DAYS = 5

# Output directory
OUTPUT_DIR_PREFIX = "analysis_output"

# --- Functions ---

def analyze_and_report(binance_data, market_cap_data):
    from datetime import datetime

    # 获取当前UTC时间
    utc_time = datetime.utcnow()

    # 格式化为YYYYMMDD_HHMM
    timestamp_str = utc_time.strftime("%Y%m%d_%H%M")

    OUTPUT_DIR = OUTPUT_DIR_PREFIX + timestamp_str
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
        
    groups = {}
    if GROUPING_METHOD == 'terciles':
        top_third_index = int(len(full_df) / 3)
        mid_third_index = int(2 * len(full_df) / 3)
        groups['top'] = full_df.iloc[:top_third_index]
        groups['mid'] = full_df.iloc[top_third_index:mid_third_index]
        groups['low'] = full_df.iloc[mid_third_index:]
    elif GROUPING_METHOD == 'thresholds':
        groups['low'] = full_df[full_df['unlocked_mkt_cap'] < LOW_CAP_THRESHOLD]
        groups['mid'] = full_df[(full_df['unlocked_mkt_cap'] >= LOW_CAP_THRESHOLD) & (full_df['unlocked_mkt_cap'] < MID_CAP_THRESHOLD)]
        groups['top'] = full_df[full_df['unlocked_mkt_cap'] >= MID_CAP_THRESHOLD]
    elif GROUPING_METHOD == 'kmeans':
        kmeans = KMeans(n_clusters=3, random_state=0, n_init=10)
        full_df['cluster'] = kmeans.fit_predict(full_df[['unlocked_mkt_cap']])
        
        # Identify clusters as low, mid, top based on the mean market cap
        cluster_means = full_df.groupby('cluster')['unlocked_mkt_cap'].mean().sort_values()
        low_cluster, mid_cluster, top_cluster = cluster_means.index
        
        groups['low'] = full_df[full_df['cluster'] == low_cluster]
        groups['mid'] = full_df[full_df['cluster'] == mid_cluster]
        groups['top'] = full_df[full_df['cluster'] == top_cluster]

    # --- Generate Report ---
    report_parts = ["# Cryptocurrency Analysis Report\n\n"]

    # Market Cap Distribution
    plt.figure(figsize=(10, 6))
    np.log10(full_df[full_df['unlocked_mkt_cap'] > 0]['unlocked_mkt_cap']).hist(bins=50)  
    plt.title('Log of Unlocked Market Cap Distribution')
    plt.xlabel('Log(Unlocked Market Cap)')
    plt.ylabel('Frequency')
    dist_path = os.path.join(OUTPUT_DIR, 'market_cap_distribution.png')
    plt.savefig(dist_path)
    plt.close()
    report_parts.append("## Market Cap Distribution\n\n")
    report_parts.append(f"![Market Cap Distribution]({dist_path})\n\n")

    # --- Comparative Descriptive Statistics ---
    report_parts.append(generate_comparative_descriptive_statistics_table(groups, binance_data, market_cap_data))

    for name, group_df in groups.items():
        report_parts.append(f"## {name.capitalize()} Group Analysis\n\n")
        
        if group_df.empty:
            report_parts.append("No data in this group.\n\n")
            continue

        report_parts.append(generate_group_statistics_report(group_df, name, binance_data, market_cap_data, OUTPUT_DIR))

        # Save group data
        group_df.to_csv(os.path.join(OUTPUT_DIR, f"{name}_group.csv"), index=False)

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
    #usdt_pairs = usdt_pairs[:100]
    print(f"Found {len(usdt_pairs)} USDT pairs.")
    

    # 2. Get daily data for each pair
    print(f"Fetching last {N_DAYS} day(s) of data for each pair...")
    all_daily_data = {}
    for i, symbol in enumerate(usdt_pairs):
        print(f"Fetching {symbol} ({i+1}/{len(usdt_pairs)})...")
        daily_data = get_daily_data(binance_client, symbol, N_DAYS)
        if daily_data is not None:
            all_daily_data[symbol] = daily_data
    
    print(f"{len(all_daily_data)} symbols have trade data...")
    # 3. Get market cap data
    print("Fetching market cap data from CoinMarketCap...")
    market_caps = get_market_cap_data(cmc_client, list(all_daily_data.keys()))

    # 4. & 5. Analyze and generate report
    print("Analyzing data and generating report...")
    analyze_and_report(all_daily_data, market_cap_data)