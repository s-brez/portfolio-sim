from os import listdir
import pandas as pd


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

        Returns:
            None (modifies root dictionary contents in place).

        Raises:
            None.
        """

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

                            # print(symbol, timeframe)
                            # print(root[asset_class][symbol][timeframe])

    def start(self):
        self.apply_features_all_datasets(self.data, self.portfolio.strategies, self.portfolio.assets_flattened)

