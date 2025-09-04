import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from descriptive_statistics import calculate_basic_stats, calculate_return_and_risk, calculate_liquidity
from risk_return_analysis import calculate_historical_volatility, calculate_beta, calculate_tail_risk, calculate_return_distribution_metrics

def get_beta_interpretation(beta):
    if beta > 1: return "More volatile than BTC"
    if beta < 0: return "Moves opposite to BTC"
    return "Less volatile than BTC"

def get_skewness_interpretation(skewness):
    if skewness > 0.5: return "Significant upside potential"
    if skewness < -0.5: return "Significant downside risk"
    return "Relatively symmetrical"

def get_kurtosis_interpretation(kurtosis):
    if kurtosis > 3: return "Fat tails (more outliers)"
    return "Normal tails"

def generate_comparative_descriptive_statistics_table(groups, binance_data, market_cap_data):
    """Generates a comparative table of descriptive statistics for all groups."""
    
    stats_list = []
    for name, group_df in groups.items():
        if group_df.empty:
            continue
            
        basic_stats = calculate_basic_stats(group_df)
        return_risk_stats = calculate_return_and_risk(group_df, binance_data)
        liquidity_stats = calculate_liquidity(group_df)
        
        stats = {
            'Group': name.capitalize(),
            'Number of Tokens': basic_stats.get('num_tokens', 0),
            'Mean Market Cap (USD)': f"${basic_stats.get('mkt_cap_mean', 0):,.2f}",
            'Median Market Cap (USD)': f"${basic_stats.get('mkt_cap_median', 0):,.2f}",
            'Mean Circ. Supply Ratio': f"{basic_stats.get('circ_supply_ratio_mean', 0):.2%}",
            'Median Circ. Supply Ratio': f"{basic_stats.get('circ_supply_ratio_median', 0):.2%}",
            'Avg. Daily Return': f"{return_risk_stats.get('mean_return', 0):.4%}",
            'Volatility': f"{return_risk_stats.get('std_dev', 0):.4%}",
            'Sharpe Ratio (Annualized)': f"{return_risk_stats.get('sharpe_ratio', 0):.2f}",
            'Avg. 24h Volume': f"${liquidity_stats.get('avg_volume', 0):,.2f}",
            'Avg. Turnover Rate': f"{liquidity_stats.get('avg_turnover_rate', 0):.2%}",
        }
        stats_list.append(stats)
        
    if not stats_list:
        return ""
        
    df = pd.DataFrame(stats_list)
    df = df.set_index('Group').T
    
    report_parts = ["### Comparative Descriptive Statistics\n\n"]
    report_parts.append(df.to_markdown())
    report_parts.append("\n\n*Note: Token age and category proportions are not available with the current data sources.*\n")
    
    return "".join(report_parts)

def generate_risk_return_report(group_df, group_name, binance_data, output_dir):
    """Generates the risk-return analysis report for a single group."""
    report_parts = ["### Risk and Return Analysis\n\n"]


    # Volatility
    group_symbols = group_df['symbol'].tolist()
    all_volatilities = []
    for symbol in group_symbols:
        if symbol in binance_data and not binance_data[symbol].empty:
            vol = calculate_historical_volatility(binance_data[symbol])
            if vol is not None:
                all_volatilities.append(vol)
    
    if all_volatilities:
        report_parts.append(f"- **Average Historical Volatility:** {np.mean(all_volatilities):.4f} (Higher is riskier)\n")
    else:
        report_parts.append("- **Average Historical Volatility:** N/A\n")

    # Beta
    betas = calculate_beta(group_df, binance_data)
    if betas:
        avg_beta = np.mean(list(betas.values()))
        report_parts.append(f"- **Average Beta (vs. BTC):** {avg_beta:.2f} ({get_beta_interpretation(avg_beta)})\n")
    else:
        report_parts.append("- **Average Beta (vs. BTC):** N/A\n")

    # Tail Risk (VaR and CVaR)
    all_vars = []
    all_cvars = []
    for symbol in group_symbols:
        if symbol in binance_data and not binance_data[symbol].empty:
            var, cvar = calculate_tail_risk(binance_data[symbol])
            if var is not None:
                all_vars.append(var)
            if cvar is not None:
                all_cvars.append(cvar)
    
    if all_vars:
        report_parts.append(f"- **Average VaR (95%):** {np.mean(all_vars):.4f} (More negative is higher tail risk)\n")
    else:
        report_parts.append("- **Average VaR (95%):** N/A\n")
    
    if all_cvars:
        report_parts.append(f"- **Average CVaR (95%):** {np.mean(all_cvars):.4f} (More negative is higher tail risk)\n")
    else:
        report_parts.append("- **Average CVaR (95%):** N/A\n")

    # Return Distribution (Skewness and Kurtosis)
    all_skews = []
    all_kurtoses = []
    all_returns = [] # Collect all returns for plotting
    for symbol in group_symbols:
        if symbol in binance_data and not binance_data[symbol].empty:
            returns = binance_data[symbol]['close'].pct_change().dropna()
            if not returns.empty:
                all_returns.extend(returns.tolist())
                skewness, kurtosis_val = calculate_return_distribution_metrics(binance_data[symbol])
                if skewness is not None:
                    all_skews.append(skewness)
                if kurtosis_val is not None:
                    all_kurtoses.append(kurtosis_val)
    
    if all_skews:
        avg_skew = np.mean(all_skews)
        report_parts.append(f"- **Average Skewness:** {avg_skew:.2f} ({get_skewness_interpretation(avg_skew)})\n")
    else:
        report_parts.append("- **Average Skewness:** N/A\n")
    
    if all_kurtoses:
        avg_kurtosis = np.mean(all_kurtoses)
        report_parts.append(f"- **Average Kurtosis:** {avg_kurtosis:.2f} ({get_kurtosis_interpretation(avg_kurtosis)})\n")
    else:
        report_parts.append("- **Average Kurtosis:** N/A\n")

    # Plot Return Distribution
    if all_returns:
        plt.figure(figsize=(10, 6))
        plt.hist(all_returns, bins=50, density=True, alpha=0.7, color='skyblue')
        plt.title(f'{group_name.capitalize()} Group - Daily Return Distribution')
        plt.xlabel('Daily Return')
        plt.ylabel('Density')
        return_dist_path = os.path.join(output_dir, f'{group_name}_return_distribution.png')
        plt.savefig(return_dist_path)
        plt.close()
        report_parts.append(f"![Daily Return Distribution]({group_name}_return_distribution.png)\n\n")

    return "".join(report_parts)


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
        report_parts.append(f"![Normalized Price Trends]({group_name}_group_price_trends.png)\n\n")

    # --- Risk and Return Analysis ---
    report_parts.append(generate_risk_return_report(group_df, group_name, binance_data, output_dir))

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
        report_parts.append(latest_df[['open', 'high', 'low', 'close', 'volume', 'unlocked_mkt_cap', 'volume_24h', 'volume_market_cap_24h']].describe().to_markdown())
        report_parts.append("\n\n")
        
    return "".join(report_parts)
