
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis

def calculate_historical_volatility(df):
    """Calculates historical volatility (standard deviation of daily returns)."""
    if df.empty:
        return None
    returns = df['close'].pct_change().dropna()
    if returns.empty:
        return None
    return returns.std() * np.sqrt(252) # Annualized volatility (assuming 252 trading days)

def calculate_beta(group_df, binance_data, market_index_symbol='BTCUSDT'):
    """Calculates beta for each symbol in a group relative to a market index."""
    if market_index_symbol not in binance_data or binance_data[market_index_symbol].empty:
        print(f"Market index symbol {market_index_symbol} data not available for Beta calculation.")
        return {}

    market_returns = binance_data[market_index_symbol]['close'].pct_change().dropna()
    if market_returns.empty:
        return {}

    betas = {}
    for symbol in group_df['symbol'].tolist():
        if symbol in binance_data and not binance_data[symbol].empty:
            asset_returns = binance_data[symbol]['close'].pct_change().dropna()
            
            # Align returns by date
            aligned_returns = pd.DataFrame({'market': market_returns, 'asset': asset_returns}).dropna()
            
            if len(aligned_returns) > 1:
                covariance = aligned_returns['asset'].cov(aligned_returns['market'])
                market_variance = aligned_returns['market'].var()
                if market_variance != 0:
                    betas[symbol] = covariance / market_variance
    return betas

def calculate_tail_risk(df, confidence_level=0.95):
    """Calculates VaR and CVaR for a given DataFrame of returns."""
    if df.empty:
        return None, None
    returns = df['close'].pct_change().dropna()
    if returns.empty:
        return None, None

    sorted_returns = returns.sort_values(ascending=True)
    
    # VaR (Value-at-Risk)
    # VaR at 95% confidence level means 5% of losses are worse than VaR
    var_index = int(len(sorted_returns) * (1 - confidence_level))
    var = sorted_returns.iloc[var_index]

    # CVaR (Conditional VaR)
    # CVaR is the average of losses worse than VaR
    cvar = sorted_returns[sorted_returns <= var].mean()
    
    return var, cvar

def calculate_return_distribution_metrics(df):
    """Calculates skewness and kurtosis of daily returns."""
    if df.empty:
        return None, None
    returns = df['close'].pct_change().dropna()
    if returns.empty:
        return None, None
    
    return skew(returns), kurtosis(returns) # Fisher's definition of kurtosis (excess kurtosis)
