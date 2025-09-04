
import numpy as np

def calculate_basic_stats(group_df):
    """Calculates basic statistics for a group."""
    stats = {}
    num_tokens = len(group_df)
    stats['num_tokens'] = num_tokens
    
    if num_tokens > 0:
        mkt_cap_stats = group_df['unlocked_mkt_cap'].describe()
        stats['mkt_cap_mean'] = mkt_cap_stats['mean']
        stats['mkt_cap_median'] = mkt_cap_stats['50%']
        stats['mkt_cap_min'] = mkt_cap_stats['min']
        stats['mkt_cap_max'] = mkt_cap_stats['max']

        circ_supply_ratio = group_df['circulating_supply'] / group_df['total_supply']
        circ_supply_ratio_stats = circ_supply_ratio.describe()
        stats['circ_supply_ratio_mean'] = circ_supply_ratio_stats['mean']
        stats['circ_supply_ratio_median'] = circ_supply_ratio_stats['50%']
        
    return stats

def calculate_return_and_risk(group_df, binance_data):
    """Calculates return and risk metrics for a group."""
    stats = {}
    group_symbols = group_df['symbol'].tolist()
    
    intraday_returns = []
    for symbol in group_symbols:
        if symbol in binance_data and not binance_data[symbol].empty:
            df = binance_data[symbol]
            returns = (df['close'] - df['open']) / df['open']
            intraday_returns.extend(returns)
            
    if intraday_returns:
        stats['mean_return'] = np.mean(intraday_returns)
        stats['std_dev'] = np.std(intraday_returns)
        stats['sharpe_ratio'] = (stats['mean_return'] / stats['std_dev']) * np.sqrt(365) if stats['std_dev'] > 0 else 0
        
    return stats

def calculate_liquidity(group_df):
    """Calculates liquidity metrics for a group."""
    stats = {}
    num_tokens = len(group_df)
    
    if num_tokens > 0:
        stats['avg_volume'] = group_df['volume_24h'].mean()
        #turnover_rate = group_df['volume_24h'] / group_df['unlocked_mkt_cap']
        stats['avg_turnover_rate'] = group_df['volume_market_cap_24h'].mean()
        
    return stats
