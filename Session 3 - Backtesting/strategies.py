import pandas as pd


class EMACross50200:
    def __init__(self):
        self.name = "EMACross50200"

    def feature_data(data: pd.DataFrame, slow=200, fast=50) -> [pd.Series]:
        return [
            ("50EMA", data['Close'].ewm(span=fast, adjust=False).mean()),
            ("200EMA", data['Close'].ewm(span=slow, adjust=False).mean())]

    def check_for_signal(self):
        pass


class EMACross1020:
    def __init__(self):
        self.name = "EMACross1020"

    def feature_data(data: pd.DataFrame, slow=20, fast=10) -> [pd.Series]:
        return [
            ("10EMA", data['Close'].ewm(span=fast, adjust=False).mean()),
            ("20EMA", data['Close'].ewm(span=slow, adjust=False).mean())]

    def check_for_signal(self):
        pass


class BBSimple:
    def __init__(self):
        self.name = "BBSimple"

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal(self):
        pass


class MeanReversion:
    def __init__(self):
        self.name = "MeanReversion"

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal(self):
        pass
