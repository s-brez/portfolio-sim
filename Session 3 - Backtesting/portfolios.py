from dateutil.relativedelta import relativedelta
from datetime import datetime
import json

from strategies import EMACross50200


class TestPortfolio():

    def __init__(self):
        self.name = "Test Portfolio"
        self.currency = "USD"
        self.start_balance = 100000
        self.current_balance = 100000
        self.positions = None
        self.max_simultaneous_positions = 0
        self.acceptable_correlation_threshold = 1

        self.start_date = datetime.now() - relativedelta(years=5)

        self.strategies = [EMACross50200]

        # This implementation is limited to one timeframe.
        self.timeframes = ["1d"]

        self.assets = {
            "EQUITIES": ["GOOGL", "AMZN", "TSLA", "F"],
            "CURRENCIES": ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"],
            "COMMODITIES": ["GC=F", "ZO=F", "ZS=F", "KC=F"],
            "INDICES": ["^VIX", "^AXJO", "^GSPC", "^KS11", "DX-Y.NYB"],
            "CRYPTO": ["BTC-USD"]
        }

        self.assets_flattened = [i for j in self.assets.values() for i in j]

        # Percentage of portfolio starting balance.
        self.equities_allocation = 20
        self.currencies_allocation = 20
        self.commodities_allocation = 20
        self.indices_allocation = 20
        self.crypto_allocation = 20

        # Percentage of asset class allocation to use for each strategy.
        self.strategy_allocations = {
            "EQUITIES": {
                EMACross50200.name: 100,
            },
            "CURRENCIES": {
                EMACross50200.name: 100,
            },
            "COMMODITIES": {
                EMACross50200.name: 100,
            },
            "INDICES": {
                EMACross50200.name: 100,
            },
            "CRYPTO": {
                EMACross50200.name: 100,
            },
        }

        if self.equities_allocation + self.currencies_allocation + self.commodities_allocation + self.indices_allocation + self.crypto_allocation != 100:
            raise ValueError("Asset class allocations must total 100.")

        if self.acceptable_correlation_threshold < -1 or self.acceptable_correlation_threshold > 1:
            raise ValueError("Acceptable correlation value must be between -1 and 1.")

    def summary(self) -> str:
        return (
            f"\n** {self.name} **"
            f"\nOpening balance: {self.start_balance} {self.currency}"
            f"\nStart date: {self.start_date}]"
            f"\nMax open positions allowed: {self.max_simultaneous_positions}"
            f"\nMax allowable correlation between positions: {self.acceptable_correlation_threshold}"
            f"\nTarget instruments: {json.dumps(self.assets, indent=2)}"
            f"\n\nAllocations per asset class (% of portfolio balance):"
            f"\nEquities: {self.equities_allocation}"
            f"\nCurrencies: {self.currencies_allocation}"
            f"\nCommodities: {self.commodities_allocation}"
            f"\nIndicies: {self.indices_allocation}"
            f"\nCrypto: {self.crypto_allocation}"
            f"\n\nStrategy allocations per asset class: (% of asset class allocation) {json.dumps(self.strategy_allocations, indent=2)}"
        )
