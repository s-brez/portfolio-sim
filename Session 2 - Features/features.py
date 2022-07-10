from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from datetime import datetime
from time import sleep
from os import listdir
import yfinance as yf
import pandas as pd
import numpy as np


# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
INTRADAILY_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

SYMBOLS = ["GOOGL", "AMZN", "XOM"]  # "WMT", "JPM", "NVDA", "BRK-A", "UNH", "JNJ", "TSLA"]


def load_local_data(symbols: list) -> dict:
    """
    Args:
        symbols: list of ticker codes to load.

    Returns:
        Nested dictionary of dataframes matching parameters.
            e.g. calling "df = data['MSFT']['1d']"" on the dict produced by this function will
            return the MSFT 1d resolution dataframe, assuming MSFT 1d was loaded.

    Raises:
        None.
    """

    # Load only files matching symbol list and ending in .csv.
    filenames = []
    for filename in listdir():
        if filename.split("_")[0] in symbols and filename[-4:].upper() == ".CSV":
            filenames.append(filename)

    # Load each dataset into a nested dictionary stored under ticker code and timeframe.
    data = {s: {} for s in symbols}
    if len(filenames) > 0:
        for filename in filenames:
            substrings = filename.split("_")
            symbol = substrings[0]
            timeframe = substrings[1]

            df = pd.read_csv(filename)
            df.columns.values[0] = "Date"
            df.set_index("Date", inplace=True)

            data[symbol][timeframe] = df

    return data


def fetch_historical_data(symbol: str, resolution: str, period: int, save=False) -> pd.DataFrame:
    """
    Args:
        symbol: Ticker code (string).
        resolution: Bar granularity (string). Must exist in TIMEFRAMES.
        period: Lookback period (int). Period per category:
            intradaily: days
            daily or higher: years
        save: if True, save data as CSV.

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
        start_date = end_date - relativedelta(years=period) if not intradaily else end_date - relativedelta(days=period)
        end_date, start_date = end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

        # Poll with yfinance.
        sleep(1)
        df = yf.download(symbol,
                         start=start_date,
                         end=end_date,
                         interval=resolution)

        # Drop adj close column and current in-progress row for intra-daily bars.
        if not df.empty:
            df.drop("Adj Close", inplace=True, axis=1)
            if intradaily:
                df = df.iloc[:-1, :]

            # Save data as csv.
            if save:
                filename = symbol + "_" + resolution + "_" + start_date + "_" + end_date + ".csv"
                df.to_csv(filename, index=True)
            result = df

        else:
            print("Unable to fetch data for:", symbol)

    return result


def sma(data: pd.DataFrame, period=10) -> pd.Series:
    """
    Using pandas built-in SMA.
    Returns pandas series containing SMA values for source data.
    """
    return data['Close'].rolling(period).mean()


def ema(data: pd.DataFrame, period=10) -> pd.Series:
    """
    Using pandas built-in EMA.
    Returns pandas series containing EMA values for source data.
    """

    return data['Close'].ewm(span=period, adjust=False).mean()


def atr(data: pd.DataFrame, period=14) -> pd.Series:
    """
    Using investopedia.com/terms/a/atr.asp definition.
    Returns pandas series containing ATR values for source data.
    """

    diff_high_low = data['High'] - data['Low']
    diff_high_close = np.abs(data['High'] - data['Close'].shift())
    diff_low_close = np.abs(data['Low'] - data['Close'].shift())

    ranges = pd.concat([diff_high_low, diff_high_close, diff_low_close], axis=1)
    true_range = np.max(ranges, axis=1)

    return true_range.rolling(period).sum() / period


def apply_features_all_datasets(root: dict) -> None:
    """
    Generates and applies features to all existing datasets.

    Args:
        root: nested dict of dataframes as formatted by load_local_data().

    Returns:
        None (modifies root dictionary contents in place).

    Raises:
        None.
    """

    for symbol in root.keys():
        for timeframe in root[symbol].keys():
            f1 = sma(root[symbol][timeframe], period=10)
            f2 = ema(root[symbol][timeframe], period=20)
            f3 = atr(root[symbol][timeframe], period=14)
            root[symbol][timeframe] = root[symbol][timeframe].assign(SMA10=f1, EMA20=f2, ATR=f3)


def correlation_matrix(symbols: list, timeframe: list) -> pd.DataFrame:
    """
    Generates and applies features to all existing datasets.

    Args:
        symbols: list of ticker codes to assess.
        timeframe: timeframe to assess.

    Returns:
        matrix: Dataframe containing correlation values.

    Raises:
        None.
    """

    pass


# # Fetch and store 3 datasets for each stock
# for symbol in SYMBOLS:

#     # 5 years, daily resolution
#     fetch_historical_data(symbol, "1d", 5, save=True)

#     # 45 days, hourly resolution
#     fetch_historical_data(symbol, "1h", 45, save=True)

#     # 45 days, 15m resolution
#     fetch_historical_data(symbol, "15m", 45, save=True)


# Load stored datasets
data = load_local_data(SYMBOLS)
# print("data[]:              ", list(data.keys()))
# print("data['AMZN']:        ", list(data["AMZN"].keys()))
# print("data['AMZN']['1d']:  ")
# print(data['AMZN']['1d'])

# Example: derive features from price data.
# df = data['AMZN']['1d'].loc['2021-07-08':'2022-07-08']
# sma = sma(df, period=10)
# ema = ema(df, period=20)
# atr = atr(df, period=14)
# df = df.assign(SMA10=sma, EMA20=ema, ATR=atr)
# print(df)

# Replicate for all datasets.
# apply_features_all_datasets(data)

# Example: check correlation of two instruments.


# Example: plot with matplotlib.
# fig, axes = plt.subplots()
# df['Close'].plot(ax=axes, secondary_y=True)
# atr.plot(ax=axes, subplots=True, color='red')
# plt.show()


# Example: plot with mplfinance.
