import logging
import time

import numpy as np
import pandas as pd
import yfinance as yf

logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)


def fetch_data(symbol: str, interval: str = '1d', period: str = '100d') -> pd.DataFrame:
    """Fetch historical price data from Yahoo Finance."""
    df = yf.download(symbol, period=period, interval=interval)
    if df.empty:
        return df
    df = df.rename(
        columns={
            'Close': 'close',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Volume': 'volume',
        }
    )
    return df


def strategy(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a simple moving average crossover signal."""
    if df.empty:
        return df

    df = df.copy()
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['signal'] = np.where(df['SMA_20'] > df['SMA_50'], 1, 0)
    df['position'] = df['signal'].diff().fillna(0).astype(int)
    return df


def execute_trade(action: str, symbol: str, amount: float) -> None:
    """Placeholder for trade execution logic."""
    logging.info('Executing %s order for %s of %s', action, amount, symbol)
    print(f'Executing {action} for {amount} of {symbol}')


def send_alert(message: str) -> None:
    """Send an alert about trading bot events."""
    logging.info('ALERT: %s', message)
    print(f'Alert: {message}')


def main() -> None:
    symbol = 'AAPL'
    amount = 1

    while True:
        try:
            df = fetch_data(symbol)
            if df.empty:
                send_alert(f'No data fetched for {symbol}')
                time.sleep(60)
                continue

            df = strategy(df)
            last_position = int(df['position'].iloc[-1])

            if last_position == 1:
                send_alert(f'Buy signal detected for {symbol}')
                execute_trade('buy', symbol, amount)
            elif last_position == -1:
                send_alert(f'Sell signal detected for {symbol}')
                execute_trade('sell', symbol, amount)
            else:
                logging.info('No trade signal for %s', symbol)

        except Exception as exc:
            send_alert(f'Error in trading bot: {exc}')

        time.sleep(60)


if __name__ == '__main__':
    main()
