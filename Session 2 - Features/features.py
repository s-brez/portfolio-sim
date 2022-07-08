from dateutil.relativedelta import relativedelta
from datetime import datetime
from time import sleep
import yfinance as yf
import pandas as pd
import numpy as np


TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
INTRADAILY_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

SYMBOLS = ["GOOGL", "AMZN", "XOM"]  # "WMT", "JPM", "NVDA", "BRK-A", "UNH", "JNJ", "TSLA"]


def fetch_historical_data(symbol: str, resolution: str, period: int) -> pd.DataFrame:
    """
    Args:
        symbol: Ticker code (string).
        resolution: Bar granularity (string). Must exist in TIMEFRAMES.
        period: Lookback period (int). Period per category:
            intradaily: days
            daily or higher: years

    Returns:
        Dataframe containing requisite data, or None in error case.

    Raises:
        None.
    """

    result = None
    intradaily = True if resolution in INTRADAILY_TIMEFRAMES else False

    if resolution not in TIMEFRAMES:
        print("Invalid resolution:", resolution)

    else:

        # Set start and end dates depending on period and resolution.
        end_date = datetime.now()
        if not intradaily:
            start_date = end_date - relativedelta(years=period)
        else:
            start_date = end_date - relativedelta(days=period)
        end_date, start_date = end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

        # Attempt to poll with yfinance.
        sleep(1)
        df = yf.download(symbol,
                         start=start_date,
                         end=end_date,
                         interval=resolution)

        # Drop adj close, and current in-progress row for intra-daily bars.
        if not df.empty:
            df.drop("Adj Close", inplace=True, axis=1)
            if intradaily:
                df = df.iloc[:-1, :]
            result = df

        else:
            print("Unable to fetch data for:", symbol)

    return result


# Fetch 3 years of daily data for each stock.
data = {s: fetch_historical_data(s, "1d", 5) for s in SYMBOLS}

# Dict comprehension above is equivalent to:
# data = {}
# for symbol in SYMBOLS:
#     data[symbol] = fetch_historical_data(symbol, "1d", 3)

print(data)

