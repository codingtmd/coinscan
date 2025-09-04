import os
import pickle
import pandas as pd
from binance.client import Client
from coinmarketcapapi import CoinMarketCapAPI, CoinMarketCapAPIError
import concurrent.futures

CACHE_DIR = "coin_analysis/fetched_data"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_usdt_pairs(client):
    """Gets all USDT trading pairs from Binance, with caching."""
    cache_file = os.path.join(CACHE_DIR, "usdt_pairs.pkl")
    if os.path.exists(cache_file):
        print("Loading USDT pairs from cache...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print("Fetching USDT pairs from Binance...")
    exchange_info = client.get_exchange_info()
    symbols = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
    
    with open(cache_file, 'wb') as f:
        pickle.dump(symbols, f)
    return symbols

def get_daily_data(client, symbol, n_days=1):
    """Gets the last n days of k-line data for a symbol, with caching."""
    cache_file = os.path.join(CACHE_DIR, f"daily_{symbol}_{n_days}d.pkl")
    if os.path.exists(cache_file):
        print(f"Loading daily data for {symbol} from cache...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    print(f"{symbol} not exist in {cache_file}. Fetching daily data for {symbol} from Binance...")
    klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, f"{n_days} day ago UTC")
    if not klines:
        print(f"{symbol} Not have trade data")
        return None
    
    df = pd.DataFrame(klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
        'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    for col in ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']:
        df[col] = pd.to_numeric(df[col])
        
    with open(cache_file, 'wb') as f:
        pickle.dump(df, f)
    return df

def get_all_daily_data_multithreaded(client, symbols, n_days=1):
    """
    Gets the last n days of k-line data for multiple symbols in parallel, with caching.
    """
    all_daily_data = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_symbol = {executor.submit(get_daily_data, client, symbol, n_days): symbol for symbol in symbols}
        for future in concurrent.futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                data = future.result()
                if data is not None:
                    all_daily_data[symbol] = data
            except Exception as exc:
                print(f'{symbol} generated an exception: {exc}')
    return all_daily_data

def get_market_cap_data(cmc_client, symbols):
    """Gets market cap data from CoinMarketCap, with caching."""
    cache_file = os.path.join(CACHE_DIR, "market_cap_data.pkl")
    if os.path.exists(cache_file):
        print("Loading market cap data from cache...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    print("Fetching market cap data from CoinMarketCap...")
    base_symbols = [s.replace('USDT', '') for s in symbols]
    
    try:
        response = cmc_client.cryptocurrency_quotes_latest(symbol=','.join(base_symbols))
        
        market_caps = {}
        for symbol_base in base_symbols:
            if symbol_base in response.data:
                print(f"Fetch {symbol_base} from CoinMarketCap data")
                data = response.data[symbol_base]

                if len(data) == 0:
                    print(f"!!!{symbol_base} has no data")
                    print(data)
                    continue

                data = data[0]
                quote_usd = data['quote']['USD']
                unlocked_mkt_cap = quote_usd.get('market_cap')
                if unlocked_mkt_cap is None or unlocked_mkt_cap == 0:
                    print(f"!!! {symbol_base} has 0 or None unlocked_mkt_cap. Skipping.")
                    continue

                market_caps[symbol_base + 'USDT'] = {
                    'unlocked_mkt_cap': unlocked_mkt_cap,
                    'circulating_supply': data.get('circulating_supply'),
                    'total_supply': data.get('total_supply'),
                    'volume_24h': quote_usd.get('volume_24h'),
                    'volume_market_cap_24h': quote_usd.get('volume_24h') / unlocked_mkt_cap
                }
            else:
                print(f"Could not find {symbol_base} in CoinMarketCap data")
        
        with open(cache_file, 'wb') as f:
            pickle.dump(market_caps, f)
        return market_caps
    except CoinMarketCapAPIError as e:
        print(f"Could not fetch CoinMarketCap data: {e.error}")
        return {}