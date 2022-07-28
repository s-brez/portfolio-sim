from portfolios import TestPortfolio
from backtest import Backtester
import json
import sys


def menu():
    print("\n1: Portfolio performance")
    # print("2: Strategy performance")
    # print("3: Equity curve")
    print("4: Parameters")
    print("5: Assets")
    print("6: Allocations")
    print("7: Transaction records")
    print("8: Trade records")
    print("9: Exit")


bt = Backtester(TestPortfolio())
bt.start()

print(bt.portfolio.parameter_summary())

while(True):

    menu()

    try:
        option = int(input("> "))
    except ValueError:
        print("Invalid input")

    if option == 1:
        print(bt.portfolio.metrics())
    elif option == 2:
        # print(bt.portfolio.strategy_metrics())
        pass
    elif option == 3:
        # bt.portfolio.equity_curve()
        pass
    elif option == 4:
        print(bt.portfolio.parameter_summary())
    elif option == 5:
        print(json.dumps(bt.portfolio.assets, indent=2))
    elif option == 6:
        print(json.dumps(bt.portfolio.allocations, indent=2))
    elif option == 7:
        print(json.dumps(bt.portfolio.transaction_history, indent=2))
    elif option == 8:
        print(json.dumps(bt.portfolio.trade_history, indent=2))
    elif option == 9:
        sys.exit(0)
    else:
        pass
