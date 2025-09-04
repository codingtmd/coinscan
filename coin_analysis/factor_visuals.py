import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from coin_analysis.factors import (
    calculate_momentum_factor,
    calculate_liquidity_factor,
    calculate_value_factor,
    calculate_tokenomics_factor,
    calculate_volatility_factor,
    calculate_intraday_return
)

def generate_factor_visuals_report(groups: dict, binance_data: dict, market_cap_data: dict, output_dir: str, n_days: int):
    report_parts = ["\n## Factor Visualization and Comparative Analysis\n"]

    all_factor_data = []
    for name, group_df in groups.items():
        if group_df.empty:
            continue

        group_factor_data = []
        for symbol in group_df['symbol']:
            if symbol in binance_data and symbol in market_cap_data:
                daily_data = binance_data[symbol]
                market_data = market_cap_data[symbol]
                
                future_return = calculate_intraday_return(daily_data)
                if future_return is None:
                    continue

                group_factor_data.append({
                    'symbol': symbol,
                    'group': name,
                    'future_return': future_return,
                    'size': market_data.get('unlocked_mkt_cap'),
                    'momentum': calculate_momentum_factor(daily_data, n_days=n_days),
                    'liquidity': calculate_liquidity_factor(market_data.get('volume_24h'), market_data.get('unlocked_mkt_cap')),
                    'value': calculate_value_factor(market_data.get('unlocked_mkt_cap'), market_data.get('volume_24h')),
                    'tokenomics': calculate_tokenomics_factor(market_data.get('circulating_supply'), market_data.get('total_supply')),
                    'volatility': calculate_volatility_factor(daily_data, n_days=n_days)
                })
        
        if not group_factor_data:
            continue

        group_factor_df = pd.DataFrame(group_factor_data).dropna()
        all_factor_data.extend(group_factor_data)

        # --- Factor Correlation Heatmap ---
        plt.figure(figsize=(10, 8))
        sns.heatmap(group_factor_df[['future_return', 'size', 'momentum', 'liquidity', 'value', 'tokenomics', 'volatility']].corr(), annot=True, cmap='vlag')
        plt.title(f'{name.capitalize()} Group - Factor Correlation Heatmap')
        heatmap_path = os.path.join(output_dir, f'{name}_factor_heatmap.png')
        plt.savefig(heatmap_path)
        plt.close()
        
        report_parts.append(f"### {name.capitalize()} Group Factor Analysis\n")
        report_parts.append("#### Factor Correlation Heatmap\n")
        report_parts.append(f"![Factor Correlation Heatmap]({name}_factor_heatmap.png)\n\n")

        # --- Factor vs. Return Scatter Plots ---
        report_parts.append("#### Factor vs. Return Scatter Plots\n")
        for factor in ['size', 'momentum', 'liquidity', 'value', 'tokenomics', 'volatility']:
            plt.figure(figsize=(8, 5))
            sns.regplot(x=factor, y='future_return', data=group_factor_df, scatter_kws={'alpha':0.5})
            plt.title(f'{name.capitalize()} Group - {factor.capitalize()} vs. Return')
            scatter_path = os.path.join(output_dir, f'{name}_{factor}_scatter.png')
            plt.savefig(scatter_path)
            plt.close()
            report_parts.append(f"![{factor.capitalize()} vs. Return]({name}_{factor}_scatter.png)\n")
        report_parts.append("\n")


    if not all_factor_data:
        return "".join(report_parts)

    all_factor_df = pd.DataFrame(all_factor_data).dropna()

    # --- Comparative Analysis ---
    report_parts.append("### Comparative Analysis Across Groups\n")

    # --- Average Factor Values Bar Chart ---
    avg_factor_df = all_factor_df.groupby('group')[['size', 'momentum', 'liquidity', 'value', 'tokenomics', 'volatility']].mean()
    avg_factor_df.plot(kind='bar', subplots=True, layout=(3, 2), figsize=(15, 15), legend=False)
    plt.suptitle('Average Factor Values Across Groups')
    avg_factor_plot_path = os.path.join(output_dir, 'avg_factor_values.png')
    plt.savefig(avg_factor_plot_path)
    plt.close()
    report_parts.append("#### Average Factor Values\n")
    report_parts.append("![Average Factor Values](avg_factor_values.png)\n\n")

    return "".join(report_parts)
