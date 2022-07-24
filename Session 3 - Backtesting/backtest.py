from os import listdir
import pandas as pd
import sys

# pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
INTRADAILY_TIMEFRAMES = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]

ASSET_CLASSES = ["EQUITIES", "CURRENCIES", "COMMODITIES", "INDICES", "CRYPTO"]
EQUITIES = ["GOOGL", "AMZN", "XOM", "WMT", "JPM", "NVDA", "AMD", "AAL", "F", "BRK-A", "UNH", "JNJ", "TSLA", "LKO"]
CURRENCIES = ["EURUSD=X", "EURAUD=X", "USDJPY=X", "GBPUSD=X", "USDCHF=X", "USDCAD=X", "AUDUSD=X", "NZDUSD=X"]
COMMODITIES = ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "PL=F", "PL=F", "ZO=F", "ZS=F", "KC=F", "KE=F", "ZC=F", "CT=F"]
INDICES = ["DX-Y.NYB", "^IXIC", "^AORD", "^DJI", "^AXJO", "^GSPC", "^KS11", "IMOEX.ME", "^N225", "^VIX", "399001.SZ"]
CRYPTO = ["BTC-USD"]
SYMBOLS = EQUITIES + CURRENCIES + COMMODITIES + INDICES + CRYPTO


# Backtester implementation.
class Backtester:

    def __init__(self, portfolio):
        self.data = self.load_local_data(SYMBOLS)
        self.portfolio = portfolio
        self.c_matrix = None

    def load_local_data(self, symbols: list) -> dict:
        """
        Expects data to be stored at ./data/ with filename "ticker_timeframe_startdate_enddate.csv"

        Args:
            symbols: list of ticker codes to load.

        Returns:
            Nested dictionary of dataframes matching parameters.
            i.e data[asset_class][symbol][timeframe]

        Raises:
            ValueError if symbol not recognised.
        """

        # Load only files matching symbol list and ending in .csv.
        filenames = []
        for filename in listdir("./data/"):
            if filename.split("_")[0] in symbols and filename[-4:].upper() == ".CSV":
                filenames.append(filename)

        # Create nested dict structure to house dataframes: data[asset_class][symbol][timeframe]
        data = {asc: {} for asc in ASSET_CLASSES}
        [data["EQUITIES"].update({i: {}}) for i in EQUITIES]
        [data["CURRENCIES"].update({i: {}}) for i in CURRENCIES]
        [data["COMMODITIES"].update({i: {}}) for i in COMMODITIES]
        [data["INDICES"].update({i: {}}) for i in INDICES]
        [data["CRYPTO"].update({i: {}}) for i in CRYPTO]

        # Load each dataset.
        if len(filenames) > 0:
            for filename in filenames:
                substrings = filename.split("_")
                symbol = substrings[0]
                timeframe = substrings[1]

                df = pd.read_csv("./data/" + filename)
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
                elif symbol in CRYPTO:
                    asset_class = "CRYPTO"
                else:
                    raise ValueError(str("Symbol " + symbol + " asset class not known."))

                data[asset_class][symbol][timeframe] = df

        return data

    def apply_features_all_datasets(self, root: dict, strategies: list, symbols: list) -> None:
        """
        Generates and applies features to existing datasets.

        Args:
            root: nested dict of dataframes as formatted by load_local_data().
            i.e data[asset_class][symbol][timeframe]
            strategies: list of strategy objects from target portfolio.
            symbols: flattened list of symbols from target portfolio.

        Returns:
            None (modifies root dictionary contents in place).

        Raises:
            None.
        """

        print("Applying feature data...")

        # Iterate all stored data.
        for asset_class in root.keys():
            for symbol in root[asset_class].keys():
                for timeframe in root[asset_class][symbol].keys():

                    # Only apply features to datasets we need.
                    if symbol in symbols:

                        # Iterate strategies used by the portfolio.
                        for strategy in strategies:

                            # Iterate individual features needed by each strategy.
                            for feature in strategy.feature_data(root[asset_class][symbol][timeframe]):
                                col_count = root[asset_class][symbol][timeframe].shape[1]
                                root[asset_class][symbol][timeframe].insert(col_count, feature[0], feature[1])

                            # Re-index date column such that non-24/7 markets have continuous time series.
                            start = root[asset_class][symbol][timeframe].iloc[0].name
                            finish = root[asset_class][symbol][timeframe].iloc[-1].name
                            index = pd.date_range(start, finish)
                            root[asset_class][symbol][timeframe] = root[asset_class][symbol][timeframe].reindex(index, fill_value=0)

                            # Add ticker column value, used later for correlation.
                            root[asset_class][symbol][timeframe]['Ticker'] = symbol

                        # print(symbol, timeframe)
                        # print(root[asset_class][symbol][timeframe])

        print("Feature data complete.")

    def correlation_matrix(self, root: dict, timeframes: list, symbols: list) -> None:
        """
        Create correlation matrix from source datasets.

        Args:
            root: nested dict of dataframes as formatted by load_local_data().
                e.g data[asset_class][symbol][timeframe]
            timeframes: list of timeframes used by target portfolio.
            timeframes: list of symbols used by target portfolio.

        Returns:
            c_matrix: dict of correlation matrices for each timeframe
                e.g c_matrix[1d]

        Raises:
            None.
        """

        c_matrix = {}

        # Aggregate close prices for each timeframe.
        for timeframe in timeframes:

            data_to_agg = []

            for asset_class in root.keys():
                for symbol in root[asset_class].keys():

                    # Only run correlation for datasets we need.
                    if symbol in symbols:

                        data_to_agg.append(root[asset_class][symbol][timeframe])

            agg_data = pd.concat(data_to_agg).reset_index()
            agg_data.columns.values[0] = "Date"
            agg_data = agg_data[['Date', 'Ticker', 'Close']]
            # print(agg_data)

            reorg_data = agg_data.pivot('Date', 'Ticker', 'Close').reset_index()
            matrix = reorg_data.corr(method="pearson")
            matrix.index.name = None

            c_matrix[timeframe] = matrix

        return c_matrix

    def action_signal(self, signal: dict):
        # print(signal)
        pass

    def start(self, start_timestamp=None, finish_timestamp=None):
        """
        IMPORTANT: all dataframes must be synchronised on date index, i.e have a continuous date index,
        no missing timestamps, start and finish on same timestamps.

        Limitations:
            - Simulation supports only a single timeframe across all strategies.
            - Features requiring analysis of > 1 bar time periods must be condensed into a single bar.
                see EmaCross50200 for example using Cross column.
        """

        # Data pre-processing.
        self.apply_features_all_datasets(self.data, self.portfolio.strategies, self.portfolio.assets_flattened)
        self.c_matrix = self.correlation_matrix(self.data, self.portfolio.timeframes, self.portfolio.assets_flattened)

        # print(self.c_matrix["1d"])
        # print(self.c_matrix["1d"]['GOOGL']['AMZN'])
        # print(self.c_matrix["1d"]['F']['TSLA'])

        # Use first asset's data for start/finish indexing.
        asset_class = list(self.portfolio.assets.keys())[0]
        symbol = self.portfolio.assets[asset_class][0]
        timeframe = self.portfolio.strategies[0].timeframe
        df = self.data[asset_class][symbol][timeframe]
        rows = df.shape[0]

        start_index = df.iloc[start_timestamp].name if start_timestamp is not None else 0
        finish_index = df.iloc[start_timestamp].name if finish_timestamp is not None else rows

        # print(self.portfolio.summary())
        print(f"Running simulation for {self.portfolio.name}...")

        # Iterate dataframes timestamp by timestamp.
        for index in range(start_index, finish_index - 1):
            for asset_class in self.portfolio.assets:
                for symbol in self.portfolio.assets[asset_class]:

                    for strategy in self.portfolio.strategies:
                        signal = strategy.check_for_signal(
                            self.data[asset_class][symbol][strategy.timeframe].iloc[index])
                        if signal:
                            signal['asset_class'] = asset_class
                            signal['symbol'] = symbol
                            signal['timeframe'] = strategy.timeframe
                            signal['strategy'] = strategy.name
                            self.action_signal(signal)