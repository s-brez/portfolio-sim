from dateutil.relativedelta import relativedelta
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
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

ASSET_CLASSES = ["EQUITIES", "CURRENCIES", "COMMODITIES", "INDICES"]
EQUITIES = ["GOOGL", "AMZN", "XOM", "WMT", "JPM", "NVDA", "AMD", "AAL", "F", "BRK-A", "UNH", "JNJ", "TSLA", "LKO"]
CURRENCIES = ["EURUSD=X", "EURAUD=X", "USDJPY=X", "GBPUSD=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X"]
COMMODITIES = ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "PL=F", "PL=F", "ZO=F", "ZS=F", "KC=F", "KE=F", "ZC=F", "CT=F"]
INDICES = ["^IXIC", "^AORD", "^DJI", "^AXJO", "^GSPC", "^KS11", "IMOEX.ME", "^N225", "^VIX", "399001.SZ"]
SYMBOLS = EQUITIES + CURRENCIES + COMMODITIES + INDICES


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

    # Create nested dict structure to house dataframes i.e: data[asset_class][symbol][timeframe]
    data = {asc: {} for asc in ASSET_CLASSES}
    [data["EQUITIES"].update({eqt: {}}) for eqt in EQUITIES]
    [data["CURRENCIES"].update({cur: {}}) for cur in CURRENCIES]
    [data["COMMODITIES"].update({com: {}}) for com in COMMODITIES]
    [data["INDICES"].update({idx: {}}) for idx in INDICES]

    # Load each dataset.
    if len(filenames) > 0:
        for filename in filenames:
            substrings = filename.split("_")
            symbol = substrings[0]
            timeframe = substrings[1]

            df = pd.read_csv(filename)
            df.columns.values[0] = "Date"
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)

            asset_class = None
            if symbol in EQUITIES:
                asset_class = "EQUITIES"
            elif symbol in CURRENCIES:
                asset_class = "CURRENCIES"
            elif symbol in COMMODITIES:
                asset_class = "COMMODITIES"
            elif symbol in INDICES:
                asset_class = "INDICES"
            else:
                raise Exception(str("Symbol " + symbol + " not known."))

            data[asset_class][symbol][timeframe] = df

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
        sleep(3)
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


def correlation_matrix(root: dict, symbols: list, timeframe: str) -> pd.DataFrame:
    """
    Create correlation matrix for the given symbols.

    Args:
        root: nested dict of dataframes as formatted by load_local_data().
        symbols: list of ticker codes to assess.
        timeframe: timeframe to assess.

    Returns:
        matrix: Dataframe containing correlation values.

    Raises:
        None.
    """

    # Add ticker code column to existing data.
    for symbol in symbols:
        root[symbol][timeframe]['Ticker'] = symbol
        # print(root[symbol][timeframe])

    # Aggregate close prices from all datasets into one.
    # 'Date' series needs to be changed from index to column for the next step.
    agg_data = pd.concat([root[s][timeframe] for s in symbols]).reset_index()
    agg_data = agg_data[['Date', 'Ticker', 'Close']]
    # print(agg_data)

    # Use df.pivot to re-organise the data by column value.
    # This turns our individual stocks into columns and flattens out the duplicated Date values.
    # This is also why we needed to change 'Date' Series from index to column.
    reorg_data = agg_data.pivot('Date', 'Ticker', 'Close').reset_index()
    # print(reorg_data.head())

    # Finally run pandas bultin correlation on the prepared data.
    matrix = reorg_data.corr(method="pearson")
    matrix.index.name = None
    # print(matrix.head())

    return matrix


# Note: Run this once to fetch data initially. Use local data thereon.
# for symbol in SYMBOLS:

    # # 10 years, daily resolution
    # fetch_historical_data(symbol, "1d", 10, save=True)

    # # 45 days, hourly resolution
    # fetch_historical_data(symbol, "1h", 45, save=True)

    # # 45 days, 15m resolution
    # fetch_historical_data(symbol, "15m", 45, save=True)


# Load stored datasets
data = load_local_data(SYMBOLS)
print("data[]:                          ", list(data.keys()))
print("data[EQUITIES]:                  ", list(data["EQUITIES"].keys()))
print("data[CURRENCIES]:                ", list(data["CURRENCIES"].keys()))
print("data[COMMODITIES]:               ", list(data["COMMODITIES"].keys()))
print("data[INDICES]:                   ", list(data["INDICES"].keys()))
print("data['EQUITIES']['AMZN']:        ", list(data["EQUITIES"]["AMZN"].keys()))
print("data['EQUITIES']['AMZN']['1d']:  ")
print(data["EQUITIES"]['AMZN']['1d'].head())


# print(data)


# Example: derive features from close prices and add to existing dataframe.
# df = data['AMZN']['1d']  # whole dataset
# df = data['AMZN']['1d'].loc['2021-07-14':'2022-07-14']  # 1 year slice
# df = data['AMZN']['1d'][-100:]  # last 100 bars slice
# sma = sma(df, period=10)
# ema = ema(df, period=20)
# atr = atr(df, period=14)
# df = df.assign(SMA10=sma, EMA20=ema, ATR=atr)
# print(df)

# Example: replicate features across all datasets.
# apply_features_all_datasets(data)

# Example: Caclculate correlation matrix for all data.
# correlations = correlation_matrix(data, SYMBOLS, '1d')
# print(correlations)

# Example: Access correlation of 2 particular symbols.
# print(correlations.loc['AMZN', 'GOOGL'])

# Example: plot Close and ATR with matplotlib.
# 2 subplots are needed because Close and ATR share only 1 common axis ('Date')
# fig = plt.figure(figsize=(14, 10))
# fig.subplots_adjust(hspace=0.1)
# gs = gridspec.GridSpec(nrows=2, ncols=1, figure=fig, height_ratios=[2, 1])

# price_subplot = plt.subplot(gs[0, 0])
# price_subplot.plot(df.index, df['Close'], label="Daily close price", color='purple')
# price_subplot.plot(sma, color="lightblue", label="10 period SMA")
# price_subplot.legend(loc="upper right")
# price_subplot.set_ylabel("USD ($)")
# price_subplot.set_title("AMZN 1d Close with ATR and 10 period SMA")
# price_subplot.grid(b=True, linestyle='--', alpha=0.5)
# # price_subplot.get_xaxis().set_visible(False)
# price_subplot.margins(0.05, 0.2)

# atr_subplot = plt.subplot(gs[1, 0], sharex=price_subplot)  # 2 rows, 1 col, 2nd.
# atr_subplot.plot(atr, label="ATR", color='orange')
# atr_subplot.legend(loc="upper right")
# atr_subplot.set_ylabel("ATR")
# atr_subplot.grid(b=True, linestyle='--', alpha=0.5)
# atr_subplot.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%b'))
# atr_subplot.margins(0.05, 0.2)

# plt.show()
