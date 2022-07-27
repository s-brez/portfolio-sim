from dateutil.relativedelta import relativedelta
from datetime import datetime
import pandas as pd
import json

from strategies import EMACross50200


class TestPortfolio():

    def __init__(self):
        self.name = "Test Portfolio"
        self.currency = "USD"
        self.start_date = datetime.now() - relativedelta(years=5)
        self.finish_date = None
        self.start_equity = 1000000
        self.current_equity = 1000000
        self.trade_history = []                     # [{tx pnl data}, ..]

        self.positions = {}                         # positions[symbol][strategy] ..
        self.position_count = 0
        self.total_trades = 0

        self.simulated_fee_flat = 2                 # dollar value added to each trade cost
        self.simulated_fee_percentage = 0.025       # percentage of trade size added to each trade cost
        self.max_simultaneous_positions = 10
        self.correlation_threshold = 1              # 1 for simplicity, allowing correlated trades
        self.drawdown_limit_percentage = 15         # percentage loss of starting capital trading will cease at
        self.drawdown_watermark_percentage = 0
        self.close_positions_at_finish = False

        self.max_risk_per_trade_percentage = 2.5    # max loss per trade, when not using kelly fraction.

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
        self.transaction_history = {a: {s: [] for s in self.strategies.keys()} for a in self.assets_flattened}   # tx_history[symbol][strategy] ..

        # Asset class allocations across all asset classes must total 100.
        # Likewise strategy allocations within each asset class must total 100.
        self.allocations = {
            "EQUITIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CURRENCIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "COMMODITIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "INDICES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross50200.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CRYPTO": {
                "allocation": 20,
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

    def calculate_fees(self, size: float) -> float:
        """
        Return simulated fee cost for the given position size.
        """
        return self.simulated_fee_flat + (self.simulated_fee_percentage / 100) * size

    def calculate_position_size(self, signal: dict) -> int:
        """
        If p_win and avg_r are set for the strategy, use kelly fraction.
        Otherwise use self.max_risk_per_trade_percentage to find the size.

        Fixed risk works such that the distance between stop and entry is used to calculate
        a position size that would lose no more than the pre-defined loss amount, in this case
        a percentage of the allocation for that asset class/strategy.
        """

        alloc_ac = 100 - self.allocations[signal["asset_class"]]["allocation"]
        alloc_remaining_s = 100 - self.allocations[signal["asset_class"]]["strategy_allocations"][signal["strategy"]]["in_use"]

        deployable_capital = (self.current_equity / (100 / alloc_ac)) / (100 / alloc_remaining_s)

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

    def within_limits(self, signal: dict) -> bool:
        """
        Return True if signal would be allowable according to portfolio rules.
        """
        should_trade = False

        alloc_remaining_strategy = 100 - self.allocations[signal["asset_class"]]["strategy_allocations"][signal["strategy"]]["in_use"]

        if alloc_remaining_strategy > 0:
            should_trade = True

        if self.position_count + 1 >= self.max_simultaneous_positions:
            should_trade = False

        if self.drawdown_watermark_percentage >= self.drawdown_limit_percentage:
            should_trade = False
            self.active = False

        # TODO: correlation threshold check

        return should_trade

    def open_position(self, signal: dict) -> None:
        """
        This method assumes we have already checked that a position exists or not, so naively assigns
        a new positon directly to portfolio.positions['symbol']['strategy'], updates portfolio metrics,
        and adds a record to transaction history. Portfolio balance is not altered until position is closed.
        """

        # Dont action signals where entry and stop are the same. Very low volatility assets may produce
        # undesirable signals for certain strategies.
        if signal['entry'] != signal['stop']:

            size = self.calculate_position_size(signal)
            entry_fees = self.calculate_fees(size)

            position = {
                'entry': signal['entry'],
                'stop': signal['stop'],
                'targets': signal['targets'],
                'size': size,
                'fees': entry_fees,
                'direction': signal['direction'],
                'strategy': signal['strategy'],
                'timeframe': signal['timeframe']
            }

            # Update position and transaction records.
            try:
                self.positions[signal['symbol']][signal['strategy']] = position
            except KeyError:
                self.positions[signal['symbol']] = {}
                self.positions[signal['symbol']][signal['strategy']] = position

            self.position_count += 1

            self.transaction_history[signal['symbol']][signal['strategy']].append({
                'qty': position['size'],
                'price': signal['entry'],
                'direction': signal['direction'],
                'fees': entry_fees,
                'timestamp': str(signal['timestamp'])
            })

            # Update allocation records.
            asset_class, strategy = signal['asset_class'], signal['strategy']
            allocation = self.allocations[asset_class]['strategy_allocations'][strategy]['allocation']
            self.allocations[asset_class]['strategy_allocations'][strategy]['in_use'] = allocation

    def close_position(self, signal: dict) -> None:

        # Update transaction records.
        self.transaction_history[signal['symbol']][signal['strategy']].append({
            'qty': self.positions[signal['symbol']][signal['strategy']]['size'],
            'price': signal['entry'],
            'direction': signal['direction'],
            'fees': self.calculate_fees(self.positions[signal['symbol']][signal['strategy']]['size']),
            'timestamp': str(signal['timestamp'])
        })

        # Update allocation records.
        asset_class, strategy = signal['asset_class'], signal['strategy']
        allocation = self.allocations[asset_class]['strategy_allocations'][strategy]['allocation']
        self.allocations[asset_class]['strategy_allocations'][strategy]['in_use'] -= allocation

        # Update portfolio stats.
        self.calculate_pnl(signal)

        # Remove position from portfolio.
        self.positions[signal['symbol']][signal['strategy']] = None
        self.position_count -= 1
        self.total_trades += 1

    def modify_position(self, signal: dict) -> None:
        self.close_position(signal)

    def update_price(self, bar: pd.Series, strategy: str) -> dict:
        """
        If a resting limit or stop limit entry order is triggered, return a signal.
        If a stop loss order is triggered, dont return a a signal, just close the position.
        if a partial take-profit order is triggered, dont return a signal, just modify position.
        if a final take-profit order is triggered, dont return a signal, just clost the position.

        Note this implementation is limited to checking only for stops, as our example
        strategies rely on separate exit signals for take-profit/exit. Realistically you'd
        need to check against every order scenario in use by your basket of strategies.
        """

        signal = None

        try:
            position = self.positions[bar['ticker']][strategy]

            # Check if stops were triggered.
            if position:
                stop_exit_signal = {
                    'timestamp': bar.name,
                    "symbol": position['symbol'],
                    "entry": position['stop'],
                    "stop": None,
                    "targets": None,
                    "timeframe": "1d",
                    'asset_class': position['asset_class'],
                    'symbol': position['symbol'],
                    'timeframe': position['timeframe'],
                    'strategy': strategy,
                }

                if position['direction'] == "BUY":
                    if bar['Low'] <= position['stop']:
                        stop_exit_signal['direction'] = "SELL"
                        self.close_position(stop_exit_signal)
                else:
                    if bar['High'] >= position['stop']:
                        stop_exit_signal['direction'] = "BUY"
                        self.close_position(stop_exit_signal)

            # Check other resting order scenarios here in future.

        except KeyError:
            # No position exists, do nothing.
            pass

        return signal

    def calculate_pnl(self, signal: dict, stop=None) -> None:
        """
        Update equity with pnl for closed trade corresponding to parameter signal.
        """

        position = self.positions[signal['symbol']][signal['strategy']]
        entry = position['entry']
        exit = signal['entry'] if not stop else stop['price']
        fees = position['fees'] * 2

        delta = abs((entry - exit) / entry) * 100
        pnl = abs((position['size'] / 100) * delta) - fees

        if position['direction'] == "BUY":
            net_pnl = pnl if exit > entry + fees else -pnl
        else:
            net_pnl = pnl if exit < entry - fees else pnl

        self.current_equity += net_pnl

        self.trade_history.append({
            "net_pnl": net_pnl,
            "side": position['direction'],
            "size": position["size"],
            "entry": entry,
            "exit": exit,
            "delta": delta,
            "fees": fees,
            "strategy": signal['strategy'],
            "symbol": signal['symbol'],
            "asset_class": signal['asset_class'],
            "timestamp": str(signal['timestamp']),
        })

    def calculate_metrics(self) -> dict:
        """
        Net profit, gross profit, gross loss, fees total, max DD, total trades, avg hold time,
        avg hold time win, avg hold time loss, sharpe & sortino portfolio and individual,
        win:loss, long:short, RR portfolio and individual, avg RR winner, avg RR loser, EXP,
        avg size, total winners, total losers, percent profitable, largest winner, largest loser
        """
        pass

    def summary(self) -> str:
        return (
            f"\n** {self.name} **"
            f"\nOpening balance: {self.start_equity} {self.currency}"
            f"\nCurrent balance: {round(self.current_equity, 2)} {self.currency}"
            f"\nStart date: {self.start_date}"
            f"\nFinish date: {self.finish_date}"
            f"\nDuration: {pd.Timedelta(self.finish_date - self.start_date)}"
            f"\nTimeframes in use: {self.timeframes}"
            f"\nStrategies in use: {[s for s in self.strategies]}"
            f"\nMax open positions allowed: {self.max_simultaneous_positions}"
            f"\nMax allowable correlation between positions: {self.correlation_threshold}"
            f"\nSimulated flat transaction fee: {self.simulated_fee_flat} {self.currency}"
            f"\nSimulated percentage transaction fee: {self.simulated_fee_percentage}%"
            f"\nMax allowable drawdown before trading ceases: {self.drawdown_limit_percentage}%"
            f"\nMax exposure per trade when not using a kelly fraction: {self.max_risk_per_trade_percentage}%"
            # f"\nTarget instruments: {json.dumps(self.assets, indent=2)}"
            # f"\nAllocations: {json.dumps(self.allocations, indent=2)}"
            # f"\nPositions: {json.dumps(self.positions, indent=2)}"
        )
