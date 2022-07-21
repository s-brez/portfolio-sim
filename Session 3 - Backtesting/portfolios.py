from dateutil.relativedelta import relativedelta
from datetime import datetime

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

        self.assets = {
            "EQUITIES": ["GOOGL", "AMZN", "TSLA", "F"],
            "CURRENCIES": ["EURUSD=X", "GBPUSD=X", "AUDUSD=X"],
            "COMMODITIES": ["GC=F", "ZO=F", "ZS=F", "KC=F"],
            "INDICES": ["^VIX", "^AXJO", "^GSPC", "^KS11"],
            "CRPYTO": []
        }

        self.assets_flattened = [i for j in self.assets.values() for i in j]

        # Percentage of portfolio starting balance.
        self.equities_allocation = 25
        self.currencies_allocation = 25
        self.commodities_allocation = 25
        self.indices_allocation = 25
        self.crypto_allocation = 0

        # Percentage of asset class allocation.
        self.strategy_allocations = {
            "EQUITIES": {
                EMACross50200: 100,
            },
            "CURRENCIES": {
                EMACross50200: 100,
            },
            "COMMODITIES": {
                EMACross50200: 100,
            },
            "INDICES": {
                EMACross50200: 100,
            },
            "CRPYTO": {
                EMACross50200: 100,
            },
        }

        if self.equities_allocation + self.currencies_allocation + self.commodities_allocation + self.indices_allocation + self.crypto_allocation != 100:
            raise ValueError("Asset class allocations must total 100")

        if self.acceptable_correlation_threshold < -1 or self.acceptable_correlation_threshold > 1:
            raise ValueError("Acceptable correlation value must be between -1 and 1.")
