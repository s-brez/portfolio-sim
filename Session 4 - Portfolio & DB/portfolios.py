from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from statistics import pstdev, stdev, mean
import pandas as pd
import json

from strategies import EMACross1020


class TestPortfolio():

    def __init__(self):
        self.name = "Test Portfolio"
        self.currency = "USD"
        self.start_date = datetime.now() - relativedelta(years=5)
        self.finish_date = None
        self.start_equity = 1000000
        self.current_equity = self.start_equity
        self.open_equity = 0
        self.trade_history = []                     # [{tx pnl data}, ..]

        self.positions = {}                         # positions[symbol][strategy] ..
        self.position_count = 0
        self.total_trades = 0

        self.simulated_fee_flat = 5                 # dollar value added to each transaction cost
        self.simulated_fee_percentage = 0.025       # percentage of size added to each transaction cost

        self.max_simultaneous_positions = 10
        self.correlation_threshold = 1              # 1 for simplicity, allowing correlated trades

        self.drawdown_limit_percentage = 15         # percentage loss of starting capital trading will cease at
        self.drawdown_watermark = self.current_equity
        self.high_watermark = self.current_equity

        self.use_kelly = True
        self.max_risk_per_trade_percentage = 2.5    # max loss per trade, when not using kelly fraction.
        self.risk_free_rate = 3.04                  # US treasury bill 12 month yeild as at 03/08/22.

        # R multiple used to calculate target delta for trades without specified targets.
        # E.g. Value of 3 means 3x the distance from entry to stop is used as target distance.
        self.default_target_distance_r = 3

        self.total_fees = 0
        self.gross_profit = 0
        self.gross_loss = 0
        self.total_winners = 0
        self.total_losers = 0

        # This implementation is limited to supporting one timeframe.
        self.timeframes = ["1d"]

        self.assets = {
            "EQUITIES": ["GOOGL", "AMZN", "TSLA", "F"],
            "CURRENCIES": ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"],
            "COMMODITIES": ["GC=F", "ZO=F", "ZS=F", "KC=F"],
            "INDICES": ["^VIX", "^AXJO", "^GSPC", "^KS11", "DX-Y.NYB"],
            "CRYPTO": ["BTC-USD"]
        }

        self.assets_flattened = [i for j in self.assets.values() for i in j]

        # Invert asset dict for ease of mapping symbol : asset class
        self.assets_inverted = {}
        for key, value in self.assets.items():
            for string in value:
                self.assets_inverted.setdefault(string, key)

        self.strategies = {
            "EMACross1020": {
                "object": EMACross1020,
                "trades": {symbol: {} for symbol in self.assets_flattened},             # trades[symbol][timeframe] = [{trade, ..}]
                "metrics_per_asset": {symbol: {} for symbol in self.assets_flattened},  # metrics[symbol][timeframe] = {stats}
                "metrics_strategy": {
                    "exp_return": 0,
                    "std_dev": 0
                }
            }
        }

        self.transaction_history = {a: {s: [] for s in self.strategies.keys()} for a in self.assets_flattened}   # tx_history[symbol][strategy] ..

        # Asset class allocations across all asset classes must total 100.
        # Likewise strategy allocations within each asset class must total 100.
        self.allocations = {
            "EQUITIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross1020.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CURRENCIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross1020.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "COMMODITIES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross1020.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "INDICES": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross1020.name: {
                        "allocation": 100,
                        "in_use": 0
                    }
                }
            },
            "CRYPTO": {
                "allocation": 20,
                "strategy_allocations": {
                    EMACross1020.name: {
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
            avg_r = self.strategies[signal['strategy']]['object'].avg_r[signal['symbol']][signal['timeframe']]
            r_adjusted_target = signal['entry'] * avg_r if signal['direction'] == "BUY" else signal['entry'] * -avg_r
            p_win = self.strategies[signal['strategy']]['object'].p_win[signal['symbol']][signal['timeframe']]
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

        if self.drawdown_watermark != self.start_equity:
            if ((self.drawdown_watermark - self.current_equity) / self.current_equity) * 1000 >= self.drawdown_limit_percentage:
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
                'timeframe': signal['timeframe'],
                'timestamp': signal['timestamp'],
                'upnl': 0,
                'r': 0
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

    def close_position(self, signal: dict, mode=None) -> None:
        """
        Mode: "SIGNAL" or "STOP" or None
        """

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
        self.calculate_pnl_for_trade(signal)

        # Remove position from portfolio.
        self.positions[signal['symbol']][signal['strategy']] = None
        self.position_count -= 1
        self.total_trades += 1

    def modify_position(self, signal: dict) -> None:
        self.close_position(signal, "SIGNAL")

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

        # TODO: update open equity.

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
                    'mode': "STOP"
                }

                if position['direction'] == "BUY":
                    if bar['Low'] <= position['stop']:
                        stop_exit_signal['direction'] = "SELL"
                        self.close_position(stop_exit_signal, "STOP")
                else:
                    if bar['High'] >= position['stop']:
                        stop_exit_signal['direction'] = "BUY"
                        self.close_position(stop_exit_signal, "STOP")

            # Check other resting order scenarios here in future.

        except KeyError:
            # No position exists, do nothing.
            pass

        return signal

    def calculate_pnl_for_trade(self, signal: dict, stop=None) -> None:
        """
        Update equity with pnl for closed trade corresponding to parameter signal.
        """

        position = self.positions[signal['symbol']][signal['strategy']]
        stop_price = position['stop']
        entry = position['entry']
        exit = signal['entry'] if not stop else stop['price']
        fees = position['fees'] * 2  # entry and exit

        delta = abs((entry - exit) / entry) * 100
        stop_delta = abs((entry - stop_price) / entry) * 100
        pnl = abs((position['size'] / 100) * delta) - fees

        if position['direction'] == "BUY":
            net_pnl = pnl if exit > entry else -pnl
        else:
            net_pnl = pnl if exit < entry else -pnl

        # If trade profitable, target_delta = delta
        if net_pnl > 0:
            target_delta = delta
        else:
            # If not profitable, target_delta = default R distance multiple from entry, if no specified targets.
            if len(position['targets']) > 0:
                target = position['targets'][-1][0]  # Final take profit target (see strategies.py)
                target_delta = abs((entry - target) / entry) * 100
            else:
                if position['direction'] == "BUY":
                    target = (entry / 100) * (100 + (self.default_target_distance_r * stop_delta))
                else:
                    target = (entry / 100) * (100 - (self.default_target_distance_r * stop_delta))
                target_delta = abs((entry - target) / entry) * 100

        if net_pnl > 0:
            self.total_winners += 1
            self.gross_profit += abs((position['size'] / 100) * delta)
        else:
            self.total_losers += 1
            self.gross_loss += abs((position['size'] / 100) * delta)

        self.total_fees += fees

        self.current_equity += net_pnl

        if self.current_equity < self.drawdown_watermark:
            self.drawdown_watermark = self.current_equity

        if self.current_equity > self.high_watermark:
            self.high_watermark = self.current_equity

        self.trade_history.append({
            "net_pnl": net_pnl,
            "side": position['direction'],
            "entry": entry,
            "exit": exit,
            "delta": delta,
            "stop_delta": stop_delta,
            "target_delta": target_delta,
            "stop": position['stop'],
            "size": position["size"],
            "fees": fees,
            "strategy": signal['strategy'],
            "timeframe": signal['timeframe'],
            "symbol": signal['symbol'],
            "exit_mode": signal['mode'],
            "asset_class": signal['asset_class'],
            "open_timestamp": str(position['timestamp']),
            "close_timestamp": str(signal['timestamp']),
        })

    def calculate_open_equity_for_position(self, asset_class: str, symbol: str, strategy: object, price: float, timestamp: datetime) -> None:
        """
        Finds unrealised pnl for a given position and adds it to self.open_equity.
        """

        position = self.positions[symbol][strategy.name]
        if position:

            entry = position['entry']
            stop = position['stop']
            exit = price
            fees = position['fees']  # entry fee only as posiition is still open

            delta = abs((entry - exit) / entry) * 100
            stop_delta = abs((entry - stop) / entry) * 100
            pnl = abs((position['size'] / 100) * delta) - fees

            if position['direction'] == "BUY":
                net_pnl = pnl if exit > entry else -pnl
            else:
                net_pnl = pnl if exit < entry else -pnl

            # If trade profitable, target_delta = delta
            if net_pnl > 0:
                target_delta = delta
            else:
                # If not profitable, target_delta = default R distance multiple from entry, if no specified targets.
                if len(position['targets']) > 0:
                    target = position['targets'][-1][0]  # Final take profit target (see strategies.py)
                    target_delta = abs((entry - target) / entry) * 100
                else:
                    if position['direction'] == "BUY":
                        target = (entry / 100) * (100 + (self.default_target_distance_r * stop_delta))
                    else:
                        target = (entry / 100) * (100 - (self.default_target_distance_r * stop_delta))
                    target_delta = abs((entry - target) / entry) * 100

            if net_pnl > 0:
                self.total_winners += 1
                self.gross_profit += abs((position['size'] / 100) * delta)
            else:
                self.total_losers += 1
                self.gross_loss += abs((position['size'] / 100) * delta)

            self.total_fees += fees

            self.open_equity += net_pnl
            self.positions[symbol][strategy.name]['upnl'] = net_pnl

            self.true_equity = self.open_equity + self.current_equity

            if self.true_equity < self.drawdown_watermark:
                self.drawdown_watermark = self.true_equity

            if self.true_equity > self.high_watermark:
                self.high_watermark = self.true_equity

            # Add open positions to trade log - they arent realised yet but we will
            # consider them as closed trade for sake of pnl/metric calcs.
            self.trade_history.append({
                "net_pnl": net_pnl,
                "side": position['direction'],
                "entry": entry,
                "exit": exit,
                "delta": delta,
                "stop_delta": stop_delta,
                "target_delta": target_delta,
                "stop": position['stop'],
                "size": position["size"],
                "fees": fees,
                "strategy": strategy.name,
                "timeframe": position['timeframe'],
                "symbol": symbol,
                "exit_mode": "SIGNAL",
                "asset_class": asset_class,
                "open_timestamp": str(position['timestamp']),
                "close_timestamp": str(timestamp),
            })

    def metrics(self, display=True) -> str:

        final_equity = self.open_equity + self.current_equity
        largest_winner, largest_loser = 0, 0
        avg_size_winner, avg_size_loser, avg_size = 0, 0, 0
        avg_r_winner, avg_r_loser, r_portfolio = 0, 0, 0
        exp_return, std_dev_returns, sharpe, sortino = 0, 0, 0, 0
        avg_hold_time, avg_hold_time_loser, avg_hold_time_winner = timedelta(), timedelta(), timedelta()
        returns, downside_returns = [], []

        # Iterate trade records once, tally everything required, then run final calculations.
        for index, trade in enumerate(self.trade_history):

            capital_allocation = self.start_equity * (self.allocations[self.assets_inverted[trade['symbol']]]["allocation"] / 100)

            abs_r = abs(trade['entry'] - trade['exit']) / abs(trade['entry'] - trade['stop'])
            r = abs_r if trade['net_pnl'] > 0 else -abs_r
            self.trade_history[index]['r'] = r

            fs = "%Y-%m-%d %H:%M:%S"
            hold_time = datetime.strptime(trade['close_timestamp'], fs) - datetime.strptime(trade['open_timestamp'], fs)
            self.trade_history[index]['hold_time'] = hold_time
            avg_size += trade['size']
            avg_hold_time += hold_time

            # Group trades by symbol and timeframe under each strategy.
            try:
                self.strategies[trade['strategy']]['trades'][trade['symbol']][trade['timeframe']].append(trade)
            except KeyError:
                self.strategies[trade['strategy']]['trades'][trade['symbol']][trade['timeframe']] = []
                self.strategies[trade['strategy']]['trades'][trade['symbol']][trade['timeframe']].append(trade)

            if trade['net_pnl'] > 0:
                avg_size_winner += trade['size']
                avg_r_winner += r
                avg_hold_time_winner += hold_time
                returns.append(round((trade['net_pnl'] / capital_allocation) * 100, 2))
                if trade['size'] > largest_winner:
                    largest_winner = trade['size']

            else:
                avg_r_loser += r
                avg_size_loser += trade['size']
                avg_hold_time_loser += hold_time
                downside_returns.append(round((trade['net_pnl'] / capital_allocation) * 100, 2))
                if trade['size'] > largest_loser:
                    largest_loser = trade['size']

        avg_size_winner = round(avg_size_winner / self.total_winners, 2)
        avg_size_loser = round(avg_size_loser / self.total_losers, 2)
        avg_size = round(avg_size / self.total_trades, 2)
        avg_r_winner = round(avg_r_winner / self.total_winners, 2)
        avg_r_loser = round(avg_r_loser / self.total_losers, 2)
        r_portfolio = round(avg_size_winner / avg_size_loser, 2)
        p_win = round(self.total_winners / (self.position_count + self.total_trades), 5)
        win_loss = self.total_winners / self.total_losers
        expectancy = round((p_win * avg_size_winner) - ((1 - p_win) * avg_size_loser), 2)
        avg_hold_time = avg_hold_time / self.total_trades
        avg_hold_time_winner = avg_hold_time_winner / self.total_winners
        avg_hold_time_loser = avg_hold_time_loser / self.total_losers

        if p_win > 0:
            for trade in self.trade_history:
                # (% gained for win * p_win) + (% lost for loss * p_loss) + ..
                exp_return += ((trade['target_delta'] * p_win) + (trade['stop_delta'] * (1 - p_win)))

        exp_return = round(exp_return / self.total_trades, 2)

        avg_return = round(mean(returns), 2)
        std_dev_returns = round(pstdev(returns), 2)
        std_dev_downside_returns = round(pstdev(downside_returns), 2)
        sharpe = round((avg_return - self.risk_free_rate) / std_dev_returns, 3)
        sortino = round((avg_return - self.risk_free_rate) / std_dev_downside_returns, 3)

        if display:
            output = (
                f"{self.parameter_summary()}"
                f"\n--------------------------------------------------------------------------------"
                f"\nStart equity: {self.start_equity} {self.currency}"
                f"\nRealised equity: {round(self.current_equity, 2)} {self.currency}"
                f"\nOpen equity: {round(self.open_equity, 2)} {self.currency}"
                f"\nFinal equity: {round(final_equity, 2)} {self.currency}"
                f"\nReturn: {round(abs((self.start_equity - final_equity) / self.start_equity) * 100, 2)}%"
                f"\n--------------------------------------------------------------------------------"
                f"\nHigh-water mark: {round(self.high_watermark, 2)} {self.currency}"
                f"\nDrawdown-water mark: {round(self.drawdown_watermark, 2)} {self.currency}"
                f"\nFees paid: {round(self.total_fees, 2)} {self.currency}"
                f"\nGross profit: {round(self.gross_profit, 2)} {self.currency}"
                f"\nGross loss: {round(self.gross_loss, 2)} {self.currency}"
                f"\nNet profit: {round(self.gross_profit - self.gross_loss - self.total_fees, 2)} {self.currency}"
                f"\n--------------------------------------------------------------------------------"
                f"\nAvg hold time: {avg_hold_time}"
                f"\nAvg hold time winners: {avg_hold_time_winner}"
                f"\nAvg hold time losers: {avg_hold_time_loser}"
                f"\n--------------------------------------------------------------------------------"
                f"\nOpen trades: {self.position_count}"
                f"\nClosed trades: {self.total_trades}"
                f"\nWinning trades: {self.total_winners}"
                f"\nLosing trades: {self.total_losers}"
                f"\nWin/loss: {round(win_loss, 2)}"
                f"\nP_win: {p_win}"
                f"\nExpectancy ($): {expectancy} {self.currency}"
                f"\nPortfolio expected return: {exp_return}%"
                f"\n--------------------------------------------------------------------------------"
                f"\nLargest winning position: {round(largest_winner, 2)} {self.currency}"
                f"\nLargest losing position: {round(largest_loser, 2)} {self.currency}"
                f"\nAvg size winning position: {avg_size_winner} {self.currency}"
                f"\nAvg size losing position: {avg_size_loser} {self.currency}"
                f"\nAvg position size: {avg_size} {self.currency}"
                f"\nAvg R winner: {avg_r_winner}"
                f"\nAvg R loser: {avg_r_loser}"
                f"\nAvg R portfolio: {r_portfolio}"
                f"\n--------------------------------------------------------------------------------"
                f"\nStd dev. returns: {std_dev_returns}%"
                f"\nSharpe: {sharpe}"
                f"\nSortino: {sortino}"
                f"\n--------------------------------------------------------------------------------"
            )
        else:
            output = ""

        return output

    def strategy_metrics(self, display=True) -> str:

        output = ""
        for strategy in self.strategies.values():
            for symbol in strategy['trades'].keys():
                for timeframe in self.strategies[strategy['object'].name]['trades'][symbol].keys():

                    capital_allocation = self.start_equity * (self.allocations[self.assets_inverted[symbol]]["allocation"] / 100)

                    pnl, total_trades, winners, losers, win_loss, p_win = 0, 0, 0, 0, 0, 0
                    avg_size, avg_size_winner, avg_size_loser = 0, 0, 0
                    avg_r_winner, avg_r_loser, avg_r_strategy = 0, 0, 0
                    expectancy, std_dev_returns, std_dev_downside_returns = 0, 0, 0
                    exp_return, sharpe, sortino = 0, 0, 0
                    avg_hold_time = timedelta()
                    returns, downside_returns = [], []

                    for index, trade in enumerate(self.strategies[strategy['object'].name]['trades'][symbol][timeframe]):

                        avg_size += trade['size']
                        avg_hold_time += trade['hold_time']
                        avg_r_strategy += trade['r']
                        total_trades += 1
                        pnl += trade['net_pnl']

                        returns.append(round((pnl / capital_allocation) * 100, 2))

                        if trade['net_pnl'] > 0:
                            winners += 1
                            avg_size_winner += trade['size']
                            avg_r_winner += trade['r']

                        else:
                            losers += 1
                            avg_size_loser += trade['size']
                            avg_r_loser += trade['r']
                            downside_returns.append(round((pnl / capital_allocation) * 100, 2))

                    # Handle zero division where no wins/loses for a particular strategy/asset/timeframe.
                    if losers == 0 and winners > 0:
                        win_loss = 1.0
                    elif losers > 0 and winners > 0:
                        win_loss = winners / losers

                    if total_trades > 0:
                        pnl = round(pnl / total_trades, 2)
                        avg_size = round(avg_size / total_trades, 2)
                        avg_r_strategy = round(avg_r_strategy / total_trades, 2)
                        avg_hold_time = avg_hold_time / total_trades

                    if winners > 0:
                        avg_size_winner = round(avg_size_winner / winners, 2)
                        avg_r_winner = round(avg_r_winner / winners, 2)
                        p_win = round(winners / total_trades, 5)

                    if losers > 0:
                        avg_size_loser = round(avg_size_loser / losers, 2)
                        avg_r_loser = round(avg_r_loser / losers, 2)

                    if winners > 0 and losers > 0:
                        expectancy = round((p_win * avg_size_winner) - ((1 - p_win) * avg_size_loser), 2)

                    if p_win > 0:
                        for trade in self.strategies[strategy['object'].name]['trades'][symbol][timeframe]:
                            # (% gained for win * p_win) + (% lost for loss * p_loss) + ..
                            exp_return += ((trade['target_delta'] * p_win) + (trade['stop_delta'] * (1 - p_win)))
                        exp_return = round(exp_return / total_trades, 2)

                    avg_return = round(mean(returns), 2)
                    std_dev_returns = round(pstdev(returns), 2)
                    std_dev_downside_returns = round(pstdev(downside_returns), 2)
                    sharpe = round((avg_return - self.risk_free_rate) / std_dev_returns, 3)
                    sortino = round((avg_return - self.risk_free_rate) / std_dev_downside_returns, 3)

                    # Save.

                    if display:
                        output += (
                            f"\n{strategy['object'].name} {symbol} {timeframe}: "
                            f"\nReturn: {avg_return}%"
                            f"\nNet profit: {pnl} {self.currency}"
                            f"\nWinners: {winners} | Losers: {losers}"
                            f"\nWin/loss: {round(win_loss, 2)}"
                            f"\nP_win: {p_win}"
                            f"\nAvg size winning position: {avg_size_winner} {self.currency}"
                            f"\nAvg size losing position: {avg_size_loser} {self.currency}"
                            f"\nAvg position size: {avg_size} {self.currency}"
                            f"\nAvg R winner: {avg_r_winner}"
                            f"\nAvg R loser: {avg_r_loser}"
                            f"\nAvg R for strategy: {avg_r_strategy}"
                            f"\nAvg expected return: {exp_return}%  <-- (?)"
                            f"\nExpectancy ($): {expectancy} {self.currency}"
                            f"\nStd dev. returns: {std_dev_returns}%"
                            f"\nSharpe: {sharpe}"
                            f"\nSortino: {sortino}"
                            f"\n--------------------------------------------------------------------------------"
                        )

        return output

    def equity_curve(self) -> None:
        pass

    def post_simulation_analysis(self) -> None:
        self.metrics(display=False)             # 1. get baseline per-trade stats
        self.strategy_metrics(display=False)    # 2. derive indidivudal metrics from base stats
        self.metrics(display=False)             # 3. do portfolio calcs requiring indidividual stats

    def parameter_summary(self) -> str:
        return (
            f"\n** {self.name} **"
            f"\nPeriod: {self.start_date} - {self.finish_date}"
            f"\nDuration: {pd.Timedelta(self.finish_date - self.start_date)}"
            f"\nTimeframes in use: {self.timeframes}"
            f"\nStrategies in use: {[s for s in self.strategies]}"
            f"\nMax open positions at a time: {self.max_simultaneous_positions}"
            f"\nMax correlation between positions: {self.correlation_threshold}"
            f"\nSimulated flat transaction fee: {self.simulated_fee_flat} {self.currency}"
            f"\nSimulated percentage transaction fee: {self.simulated_fee_percentage}%"
            f"\nMax drawdown before trading ceases: {self.drawdown_limit_percentage}%"
            f"\nUse kelly criterion for sizing when available: {self.use_kelly}"
            f"\nMax risk per trade when not using a kelly fraction: {self.max_risk_per_trade_percentage}%"
            f"\nTarget instruments: {self.assets}"
        )
