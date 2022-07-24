import pandas as pd


class EMACross50200:

    name = "EMACross50200"
    timeframe = "1d"

    def feature_data(data: pd.DataFrame, slow=200, fast=50) -> [pd.Series]:
        return [
            ("50EMA", data['Close'].ewm(span=fast, adjust=False).mean()),
            ("200EMA", data['Close'].ewm(span=slow, adjust=False).mean())]

    def check_for_signal(data: pd.Series) -> dict:
        """
        Given a single row, return a signal if one presents or None.
        """
        print("yeet")


class EMACross1020:

    name = "EMACross1020"
    timeframe = "1d"

    def feature_data(data: pd.DataFrame, slow=20, fast=10) -> [pd.Series]:
        return [
            ("10EMA", data['Close'].ewm(span=fast, adjust=False).mean()),
            ("20EMA", data['Close'].ewm(span=slow, adjust=False).mean())]

    def check_for_signal(data: pd.Series) -> dict:
        pass


class BBSimple:

    name = "BBSimple"
    timeframe = "1d"

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal():
        pass


class MeanReversion:

    name = "MeanReversion"
    timeframe = "1d"

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal():
        pass