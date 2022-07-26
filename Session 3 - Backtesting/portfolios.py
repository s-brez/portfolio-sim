from dateutil.relativedelta import relativedelta
from datetime import datetime
import pandas as pd
import json

from strategies import EMACross50200


class TestPortfolio():

    def __init__(self):
        self.name = "Test Portfolio"
        self.currency = "USD"
        self.start_equity = 1000000
        self.current_equity = 1000000

        self.positions = {}                         # positions[symbol][strategy] ..
        self.position_count = 0

        self.simulated_fee_flat = 2                 # dollar value added to each trade cost
        self.simulated_fee_percentage = 0.025       # percentage of trade size added to each trade cost
        self.max_simultaneous_positions = 10
        self.correlation_threshold = 1              # 1 for simplicity, allowing correlated trades
        self.drawdown_limit_percentage = 15         # percentage loss of starting capital trading will cease at
        self.max_risk_per_trade_percentage = 1      # max loss per trade, when not using kelly fraction.

        self.start_date = datetime.now() - relativedelta(years=5)

        # This implementation is limited to supporting one timeframe.
        self.timeframes = ["1d"]

        self.strategies = {
            "EMACross50200": EMACross50200
        }

        self.assets = {
            "EQUITIES": ["GOOGL", "AMZN", "TSLA", "F"],
            "CURRENCIES": ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"],
            "COMMODITIES": ["GC=F", "ZO=F", "ZS=F", "KC=F"],
            "INDICES": ["^VIX", "^AXJO", "^GSPC", "^KS11", "DX-Y.NYB"],
            "CRYPTO": ["BTC-USD"]
        }

        self.assets_flattened = [i for j in self.assets.values() for i in j]
        self.transaction_history = {i: [] for i in self.assets_flattened}  # tx_history[symbol] ..

        # Asset class allocations across all asset classes must total 100.
        # Likewise strategy allocations within each asset class must total 100.
        self.allocations = {
            "EQUITIES": {
                "allocation": 20,
                "in_use": 0,  # 0-100
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CURRENCIES": {
                "allocation": 20,
                "in_use": 0,  # 0-100
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "COMMODITIES": {
                "allocation": 20,
                "in_use": 0,  # 0-100
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "INDICES": {
                "allocation": 20,
                "in_use": 0,  # 0-100
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CRYPTO": {
                "allocation": 20,
                "in_use": 0,  # 0-100
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            }
        }

        # Validate settings.
        if sum([i["allocation"] for i in self.allocations.values()]) != 100:
            raise ValueError("Asset class allocation must total 100.")

        for asset_class in self.allocations.values():
            if sum([i['allocation'] for i in asset_class["strategy_allocations"].values()]) != 100:
                raise ValueError("Strategy allocation per asset class must total 100.")

        if self.correlation_threshold < -1 or self.correlation_threshold > 1:
            raise ValueError("Acceptable correlation value must be between -1 and 1.")

    def calculate_position_size(self, signal: dict) -> int:
        """
        If p_win and avg_r are set for the strategy, use kelly fraction.
        Otherwise use self.max_risk_per_trade_percentage to find the size.

        Fixed risk works such that the distance between stop and entry is used to calculate
        a position size that would lose no more than the pre-defined loss amount, in this case
        a percentage of the allocation for that asset class/strategy.
        """

        alloc_remaining_ac = 100 - self.allocations[signal["asset_class"]]["in_use"]
        alloc_remaining_s = 100 - self.allocations[signal["asset_class"]]["strategy_allocations"][signal["strategy"]]["in_use"]

        deployable_capital = (self.current_equity * alloc_remaining_ac / 100) * alloc_remaining_s / 100

        try:
            # Kelly fraction.
            avg_r = self.strategies[signal['strategy']].avg_r[signal['symbol']][signal['timeframe']]
            r_adjusted_target = signal['entry'] * avg_r if signal['direction'] == "BUY" else signal['entry'] * -avg_r

            p_win = self.strategies[signal['strategy']].p_win[signal['symbol']][signal['timeframe']]
            p_lose = 1 - p_win
            f_lost = abs((signal['stop'] - signal['entry']) / signal['entry'])  # % change from entry to stop.
            f_won = abs((r_adjusted_target - signal['entry']) / signal['entry'])  # % change from entry to R adjusted target.
            size = (p_win / f_lost) - (p_lose / f_won)

        except KeyError:
            # Fixed risk.
            risked_amt = (deployable_capital / 1000) * self.max_risk_per_trade_percentage
            size = abs(risked_amt // ((signal['stop'] - signal['entry']) / signal['entry']))

        return size

    def update_price(self, bar: pd.Series) -> dict:
        """
        If a resting limit or stop limit entry order is triggered, return a signal.
        If a stop loss order is triggered, dont return a a signal, just close the position.
        if a partial take-profit order is triggered, dont return a signal, just modify position.
        if a final take-profit order is triggered, dont return a signal, just clost the position.

        This implementation is limited to checking only for stops, as our example
        strategies rely on separate exit signals for take-profit/exit. Realistically you'd
        need to check against every order scenario in use by your basket of strategies.
        """
        return None

    def metrics(self) -> dict:
        """
        TODO:   Net profit, gross profit, gross loss, fees total, max DD, total trades, avg hold time,
                avg hold time win, avg hold time loss, sharpe & sortino portfolio and individual,
                win:loss, long:short, RR portfolio and individual, avg RR winner, avg RR loser, EXP,
                avg size, total winners, total losers, percent profitable, largest winner, largest loser
        """
        pass

    def summary(self) -> str:
        return (
            f"\n** {self.name} **"
            f"\nOpening balance: {self.start_equity} {self.currency}"
            f"\nStart date: {self.start_date}"
            f"\nTimeframes in use: {self.timeframes}"
            f"\nStrategies in use: {self.strategies}"
            f"\nMax open positions allowed: {self.max_simultaneous_positions}"
            f"\nMax allowable correlation between positions: {self.correlation_threshold}"
            f"\nSimulated flat transaction fee: {self.simulated_fee_flat}"
            f"\nSimulated percentage transaction fee: {self.simulated_fee_percentage}"
            f"\nMax allowable drawdown before trading ceases: {self.drawdown_limit_percentage}"
            f"\nMax exposure per trade when not using a kelly fraction: {self.max_risk_per_trade_percentage}"
            f"\nTarget instruments: {json.dumps(self.assets, indent=2)}"
            f"\nAllocations: {json.dumps(self.allocations, indent=2)}"
        )
