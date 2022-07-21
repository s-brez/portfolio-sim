from portfolios import TestPortfolio
from backtest import Backtester

bt = Backtester(TestPortfolio())
bt.start()
