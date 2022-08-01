import pandas as pd


class EMACross50200:

    name = "EMACross50200"
    timeframe = "1d"

    # flip_on_signalled_exit = True

    p_win = {}    # p_win[symbol][timeframe] ..
    avg_r = {}    # avg_r[symbol][timeframe] ..

    def feature_data(data: pd.DataFrame, slow=200, fast=50) -> [pd.Series]:
        """
        Use a third "cross" column for if-or-not a cross occurred on that row.
        """
        slow_ema = data['Close'].ewm(span=slow, adjust=False).mean().rename('EMA200')
        fast_ema = data['Close'].ewm(span=fast, adjust=False).mean().rename('EMA50')
        cross = pd.Series(None, index=data.index).rename("Cross")

        # Populate cross column.
        # If using timeframes more granular than 1d you'll want to optimise this to cut processing time.
        # (or if using more than 1-2k bars per dataset)
        temp_df = pd.concat([fast_ema, slow_ema], axis=1)
        for index in range(0, temp_df.shape[0]):
            if index > 0:
                prev_slow = temp_df.iloc[index - 1]["EMA200"]
                prev_fast = temp_df.iloc[index - 1]["EMA50"]
                curr_slow = temp_df.iloc[index]["EMA200"]
                curr_fast = temp_df.iloc[index]["EMA50"]

                # Buy side check (fast crosses above slow)
                if (prev_slow > prev_fast) and (curr_fast > curr_slow):
                    cross.iloc[index] = "BUY"

                # Sell side check (slow crosses above fast)
                elif (prev_slow < prev_fast) and (curr_fast < curr_slow):
                    cross.iloc[index] = "SELL"

        return [("50EMA", fast_ema), ("200EMA", slow_ema), ("Cross", cross)]

    def check_for_signal(data: pd.Series) -> dict:
        """
        Return a signal if one presents, or None.

        Stop: 150% of bar range.
        Take profit: not set, uses separate exit signal.
        """
        signal = None

        if data['Cross'] == "BUY" or data['Cross'] == "SELL":

            stop_dist = abs(data['High'] - data['Low']) * 1.5
            stop = data['Close'] - stop_dist if data['Cross'] == "BUY" else data['Close'] + stop_dist

            signal = {
                'timestamp': data.name,  # .name is the index in a Series
                'direction': data['Cross'],
                'entry': data['Close'],
                'stop': stop,
                'targets': []   # No defined targets for this strategy, uses an exit signal.
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
