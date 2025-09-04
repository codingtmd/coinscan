import pandas as pd
import numpy as np

def calculate_momentum_factor(daily_data: pd.DataFrame, n_days: int = 7) -> float | None:
    """
    Calculates the momentum factor as the cumulative return over the past n_days.
    Uses 'close' price for calculation.
    """
    if daily_data is None or len(daily_data) < n_days:
        return None
    
    # Exclude the last day for factor calculation to avoid lookahead bias
    past_data = daily_data.iloc[-(n_days+1):-1]
    if len(past_data) < 2:
        return None

    returns = past_data['close'].pct_change().dropna()
    if returns.empty:
        return None
        
    momentum = (1 + returns).prod() - 1
    return momentum

def calculate_liquidity_factor(volume_24h: float, market_cap: float) -> float | None:
    """
    Calculates the liquidity factor as the turnover rate (24h volume / market cap).
    """
    if market_cap is None or market_cap == 0:
        return None
    return volume_24h / market_cap

def calculate_value_factor(market_cap: float, volume_24h: float) -> float | None:
    """
    Calculates the value factor as the market cap to 24h volume ratio.
    """
    if volume_24h is None or volume_24h == 0:
        return None
    return market_cap / volume_24h

def calculate_tokenomics_factor(circulating_supply: float, total_supply: float) -> float | None:
    """
    Calculates the tokenomics factor as the ratio of circulating supply to total supply.
    """
    if total_supply is None or total_supply == 0:
        return None
    return circulating_supply / total_supply

def calculate_volatility_factor(daily_data: pd.DataFrame, n_days: int = 7) -> float | None:
    """
    Calculates the volatility factor as the standard deviation of daily returns over n_days.
    """
    if daily_data is None or len(daily_data) < n_days:
        return None
        
    past_data = daily_data.iloc[-(n_days+1):-1]
    if len(past_data) < 2:
        return None

    returns = past_data['close'].pct_change().dropna()
    if len(returns) < 2:
        return None
        
    return returns.std()

def calculate_intraday_return(daily_data: pd.DataFrame) -> float | None:
    """
    Calculates the most recent intraday return.
    """
    if daily_data is None or daily_data.empty:
        return None
    latest_day = daily_data.iloc[-1]
    if latest_day['open'] == 0:
        return None
    return (latest_day['close'] - latest_day['open']) / latest_day['open']
