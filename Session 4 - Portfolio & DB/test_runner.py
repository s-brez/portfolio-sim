from portfolios import TestPortfolio
from backtest import Backtester
import json
import sys


def menu():
    print("1: Parameter summary")
    print("2: Portfolio performance")
    print("3: Per-strategy performance")
    print("4: Display equity curve")
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
        print(bt.portfolio.metrics())
    elif option == 3:
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
        print(json.dumps(bt.portfolio.trade_history, indent=2))
    elif option == 9:
        sys.exit(0)
    else:
        pass
