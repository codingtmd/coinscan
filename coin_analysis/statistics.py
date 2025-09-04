import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from descriptive_statistics import calculate_basic_stats, calculate_return_and_risk, calculate_liquidity

def generate_descriptive_statistics_report(group_df, group_name, binance_data, market_cap_data):
    """Generates the descriptive statistics report for a single group."""
    
    report_parts = ["### Descriptive Statistics\n\n"]
    
    # --- Basic Statistics ---
    report_parts.append("#### Basic Statistics\n\n")
    basic_stats = calculate_basic_stats(group_df)
    report_parts.append(f"- **Number of Tokens:** {basic_stats.get('num_tokens', 0)}\n")
    if basic_stats:
        report_parts.append("- **Unlocked Market Cap (USD):**\n")
        report_parts.append(f"  - Mean: ${basic_stats.get('mkt_cap_mean', 0):,.2f}\n")
        report_parts.append(f"  - Median: ${basic_stats.get('mkt_cap_median', 0):,.2f}\n")
        report_parts.append(f"  - Min: ${basic_stats.get('mkt_cap_min', 0):,.2f}\n")
        report_parts.append(f"  - Max: ${basic_stats.get('mkt_cap_max', 0):,.2f}\n")
        report_parts.append("- **Circulating Supply Ratio:**\n")
        report_parts.append(f"  - Mean: {basic_stats.get('circ_supply_ratio_mean', 0):.2%}\n")
        report_parts.append(f"  - Median: {basic_stats.get('circ_supply_ratio_median', 0):.2%}\n")

    # --- Return and Risk ---
    report_parts.append("\n#### Return and Risk (7-day)\n\n")
    return_risk_stats = calculate_return_and_risk(group_df, binance_data)
    if return_risk_stats:
        report_parts.append(f"- **Average Daily Return:** {return_risk_stats.get('mean_return', 0):.4%}\n")
        report_parts.append(f"- **Volatility (Std. Dev. of Daily Return):** {return_risk_stats.get('std_dev', 0):.4%}\n")
        report_parts.append(f"- **Annualized Sharpe Ratio:** {return_risk_stats.get('sharpe_ratio', 0):.2f}\n")

    # --- Liquidity ---
    report_parts.append("\n#### Liquidity\n\n")
    liquidity_stats = calculate_liquidity(group_df)
    if liquidity_stats:
        report_parts.append(f"- **Average 24h Trading Volume:** ${liquidity_stats.get('avg_volume', 0):,.2f}\n")
        report_parts.append(f"- **Average Turnover Rate:** {liquidity_stats.get('avg_turnover_rate', 0):.2%}\n")
        
    report_parts.append("\n*Note: Token age and category proportions are not available with the current data sources.*\n")

    return "".join(report_parts)

def generate_group_statistics_report(group_df, group_name, binance_data, market_cap_data, output_dir):
    """Generates the statistical analysis report for a single group."""
    
    report_parts = []

    # --- Descriptive Statistics ---
    report_parts.append(generate_descriptive_statistics_report(group_df, group_name, binance_data, market_cap_data))

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
