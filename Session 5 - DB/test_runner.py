from portfolios import TestPortfolio
from backtest import Backtester
from copy import deepcopy
import json
import sys


def menu():
    print("1: Portfolio parameter summary")
    print("2: Portfolio performance")
    print("3: Per-strategy, per-asset, per-timeframe performance")
    print("4: Portfolio equity curve")
    print("5: Target assets")
    print("6: Asset class and strategy allocations")
    print("7: Transaction record")
    print("8: Trade record")
    print("9: Exit")


bt = Backtester(TestPortfolio())
bt.start()

while(True):

    menu()

    try:
        option = int(input("> "))
    except ValueError:
        print("Invalid input")

    if option == 1:
        print(bt.portfolio.parameter_summary())

    elif option == 2:

        # Extend this by returning a list, which can then be sorted by return, sharpe etc
        print(bt.portfolio.metrics())

    elif option == 3:

        # Extend this by returning a list, which can then be sorted by return, sharpe etc
        print(bt.portfolio.strategy_metrics())

    elif option == 4:
        bt.portfolio.equity_curve()

    elif option == 5:
        print(json.dumps(bt.portfolio.assets, indent=2))

    elif option == 6:
        print(json.dumps(bt.portfolio.allocations, indent=2))

    elif option == 7:
        print(json.dumps(bt.portfolio.transaction_history, indent=2))

    elif option == 8:

        # json.dumps wont accept timedelta objects, reformat them to strings.
        str_trade_history = []
        for index, trade in enumerate(bt.portfolio.trade_history):
            str_trade_history.append(deepcopy(trade))
            str_trade_history[index]['hold_time'] = str(str_trade_history[index]['hold_time'])

        print(json.dumps(str_trade_history, indent=2))

    elif option == 9:
        sys.exit(0)
    else:
        pass
