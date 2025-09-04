import pandas as pd
from scipy.stats import pearsonr, spearmanr
from coin_analysis.factors import (
    calculate_momentum_factor,
    calculate_liquidity_factor,
    calculate_value_factor,
    calculate_tokenomics_factor,
    calculate_volatility_factor,
    calculate_intraday_return
)

def get_ic_strength(ic_value):
    abs_ic = abs(ic_value)
    if abs_ic > 0.05:
        return "Strong"
    elif abs_ic > 0.02:
        return "Normal"
    elif abs_ic > 0:
        return "Weak"
    else:
        return "None"

def is_significant(p_value, threshold=0.05):
    return "Yes" if p_value < threshold else "No"

def validate_factors_for_group(group_df: pd.DataFrame, binance_data: dict, market_cap_data: dict, n_days_momentum: int = 7):
    """
    Calculates and validates factors for a given group of coins.
    """
    factor_data = []
    for symbol in group_df['symbol']:
        if symbol not in binance_data or symbol not in market_cap_data:
            continue

        daily_data = binance_data[symbol]
        market_data = market_cap_data[symbol]
        
        future_return = calculate_intraday_return(daily_data)
        
        if future_return is None:
            continue

        factors = {
            'symbol': symbol,
            'future_return': future_return,
            'size': market_data.get('unlocked_mkt_cap'),
            'momentum': calculate_momentum_factor(daily_data, n_days=n_days_momentum),
            'liquidity': calculate_liquidity_factor(market_data.get('volume_24h'), market_data.get('unlocked_mkt_cap')),
            'value': calculate_value_factor(market_data.get('unlocked_mkt_cap'), market_data.get('volume_24h')),
            'tokenomics': calculate_tokenomics_factor(market_data.get('circulating_supply'), market_data.get('total_supply')),
            'volatility': calculate_volatility_factor(daily_data, n_days=n_days_momentum)
        }
        factor_data.append(factors)

    if not factor_data:
        return "No data for factor validation in this group.\n"

    factor_df = pd.DataFrame(factor_data).dropna()

    if len(factor_df) < 2:
        return "Not enough data for meaningful correlation analysis in this group.\n"

    report_parts = ["### Factor Effectiveness Testing\n\n"]
    report_parts.append("#### Information Coefficient (IC) Analysis\n\n")
    report_parts.append("*IC (Information Coefficient) measures the correlation between a factor and subsequent returns. A higher absolute IC value indicates a stronger predictive power. *\n*   **> 0.05:** Strong signal\n*   **0.02 - 0.05:** Normal signal\n*   **0 - 0.02:** Weak signal\n\n")
    report_parts.append("**P-value:** The P-value indicates the statistical significance of the IC. A low P-value (typically < 0.05) suggests that the observed correlation is unlikely to be due to random chance.\n\n")
    report_parts.append("**Pearson vs. Spearman Correlation:**\n*   **Pearson IC:** Measures the linear relationship between the factor and returns. It's sensitive to outliers.\n*   **Spearman IC:** Measures the monotonic relationship (whether the factor and returns move in the same direction, but not necessarily at a constant rate). It is less sensitive to outliers.\n\n")


    ic_results = []
    for factor_name in ['size', 'momentum', 'liquidity', 'value', 'tokenomics', 'volatility']:
        if factor_name not in factor_df.columns or factor_df[factor_name].isnull().all():
            continue
        
        # Ensure there's variance in the factor data
        if factor_df[factor_name].var() == 0:
            continue

        pearson_corr, p_value_pearson = pearsonr(factor_df[factor_name], factor_df['future_return'])
        spearman_corr, p_value_spearman = spearmanr(factor_df[factor_name], factor_df['future_return'])
        
        ic_results.append({
            'Factor': factor_name.capitalize(),
            'Pearson IC': f"{pearson_corr:.4f}",
            'Pearson Signal': get_ic_strength(pearson_corr),
            'Pearson Significant (p < 0.05)': is_significant(p_value_pearson),
            'Spearman IC': f"{spearman_corr:.4f}",
            'Spearman Signal': get_ic_strength(spearman_corr),
            'Spearman Significant (p < 0.05)': is_significant(p_value_spearman)
        })

    if not ic_results:
        return "Could not calculate IC for any factor.\n"

    ic_df = pd.DataFrame(ic_results)
    report_parts.append(ic_df.to_markdown(index=False))
    report_parts.append("\n\n")
    
    return "".join(report_parts)

def generate_factor_validation_report(groups: dict, binance_data: dict, market_cap_data: dict, n_days_momentum: int = 7):
    """
    Generates a full factor validation report for all groups.
    """
    report_parts = ["\n## Factor Validation Report\n"]
    for name, group_df in groups.items():
        if group_df.empty:
            continue
        report_parts.append(f"### {name.capitalize()} Group\n")
        report_parts.append(validate_factors_for_group(group_df, binance_data, market_cap_data, n_days_momentum))
        
    return "".join(report_parts)