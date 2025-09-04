import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def generate_group_statistics_report(group_df, group_name, binance_data, market_cap_data, output_dir):
    """Generates the statistical analysis report for a single group."""
    
    report_parts = []

    # --- Price Trend Consistency Analysis ---
    report_parts.append("### Price Trend Consistency\n\n")
    
    group_symbols = group_df['symbol'].tolist()
    group_daily_data = {sym: binance_data[sym] for sym in group_symbols if sym in binance_data}

    if not group_daily_data:
        report_parts.append("No historical data for this group.\n\n")
    else:
        # Normalize prices
        normalized_prices = pd.DataFrame()
        for symbol, df in group_daily_data.items():
            if not df.empty:
                normalized_prices[symbol] = df['close'] / df['close'].iloc[0]

        # Plot normalized prices
        plt.figure(figsize=(12, 7))
        normalized_prices.plot(ax=plt.gca(), legend=False)
        plt.title(f'{group_name.capitalize()} Group - Normalized Price Trends (7 days)')
        plt.xlabel('Days')
        plt.ylabel('Normalized Price')
        trend_plot_path = os.path.join(output_dir, f'{group_name}_group_price_trends.png')
        plt.savefig(trend_plot_path)
        plt.close()
        report_parts.append(f"![Normalized Price Trends]({trend_plot_path})\n\n")

        # Calculate and display correlation of daily returns
        daily_returns = pd.DataFrame()
        for symbol, df in group_daily_data.items():
            if not df.empty:
                daily_returns[symbol] = df['close'].pct_change()
        
        if not daily_returns.empty:
            returns_corr = daily_returns.corr()
            report_parts.append("#### Daily Returns Correlation Matrix\n\n")
            report_parts.append(returns_corr.to_markdown())
            report_parts.append("\n\n")

    # --- Statistical Summary (of the latest day) ---
    latest_data = []
    group_symbols = group_df['symbol'].tolist()
    for symbol in group_symbols:
        if symbol in binance_data and not binance_data[symbol].empty:
            latest_day = binance_data[symbol].iloc[-1]
            market_cap_info = market_cap_data.get(symbol, {})
            row = {
                'symbol': symbol,
                'open': latest_day['open'],
                'high': latest_day['high'],
                'low': latest_day['low'],
                'close': latest_day['close'],
                'volume': latest_day['volume'],
                **market_cap_info
            }
            latest_data.append(row)
    
    if latest_data:
        latest_df = pd.DataFrame(latest_data)
        report_parts.append("### Statistical Summary (Latest Day)\n\n")
        report_parts.append(latest_df[['open', 'high', 'low', 'close', 'volume', 'unlocked_mkt_cap', 'volume_24h']].describe().to_markdown())
        report_parts.append("\n\n")
        
    return "".join(report_parts)
