import pandas as pd


class EMACross50200:

    name = "EMACross50200"
    timeframe = "1d"
    p_win = {}  # p_win[symbol][timeframe] ..

    def feature_data(data: pd.DataFrame, slow=200, fast=50) -> [pd.Series]:
        """
        Use a third "cross" column if-or-not a cross occurred on that row.
        """
        slow_ema = data['Close'].ewm(span=slow, adjust=False).mean().rename('EMA200')
        fast_ema = data['Close'].ewm(span=fast, adjust=False).mean().rename('EMA50')
        cross = pd.Series(None, index=data.index).rename("Cross")

        # Populate cross column.
        # Not the fastest way, use a vectorised method if dataframe sizes get much larger.
        temp_df = pd.concat([fast_ema, slow_ema], axis=1)
        for index in range(0, temp_df.shape[0]):
            if index > 0:
                prev_slow = temp_df.iloc[index - 1]["EMA200"]
                prev_fast = temp_df.iloc[index - 1]["EMA50"]
                curr_slow = temp_df.iloc[index]["EMA200"]
                curr_fast = temp_df.iloc[index]["EMA50"]

                # Buy side check (fast > slow)
                if (prev_slow > prev_fast) and (curr_fast > curr_slow):
                    cross.iloc[index] = "BUY"

                # Sell side check (slow > fast)
                if (prev_slow < prev_fast) and (curr_fast < curr_slow):
                    cross.iloc[index] = "SELL"

        return [("50EMA", fast_ema), ("200EMA", slow_ema), ("Cross", cross)]

    def check_for_signal(data: pd.Series) -> dict:
        """
        Return a signal if one presents, or None.
        """
        signal = None

        if data['Cross'] == "BUY" or data['Cross'] == "SELL":
            signal = {
                'direction': data['Cross']
            }

        return signal


class MeanReversion:

    name = "MeanReversion"
    timeframe = "1d"
    p_win = {}  # p_win[symbol][timeframe]

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal():
        pass


class EMACross1020:

    name = "EMACross1020"
    timeframe = "1d"
    p_win = {}  # p_win[symbol][timeframe]

    def feature_data(data: pd.DataFrame, slow=20, fast=10) -> [pd.Series]:
        return [
            ("10EMA", data['Close'].ewm(span=fast, adjust=False).mean()),
            ("20EMA", data['Close'].ewm(span=slow, adjust=False).mean())]

    def check_for_signal(data: pd.Series) -> dict:
        pass


class BBSimple:

    name = "BBSimple"
    timeframe = "1d"
    p_win = {}  # p_win[symbol][timeframe]

    def feature_data(data: pd.DataFrame, ) -> [pd.Series]:
        pass

    def check_for_signal():
        pass
