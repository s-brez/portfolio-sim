import psycopg2


tables = ["exchange", "asset_class", "asset", "price", "allocation_asset_class", "allocation_strategy", "strategy", "portfolio"]
connection, cursor = None, None

try:
    connection = psycopg2.connect(host="localhost", database="portfolio_sim", user="", password="")

    # Create tables if they dont already exist. Database "portfolio_sim" must already exist.
    cursor = connection.cursor()
    cursor.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""")
    result = cursor.fetchall()

    for table in tables:
        if table not in result:

            if table == "exchanges":
                cursor.execute("""
                    CREATE TABLE exchanges
                    (
                        name varchar PRIMARY KEY
                    );
                """)

            elif table == "asset_classes":
                cursor.execute("""
                    CREATE TABLE asset_classes
                    (
                      name varchar PRIMARY KEY
                    );
                """)

            elif table == "assets":
                cursor.execute("""
                    CREATE TABLE assets
                    (
                        asset_ID serial PRIMARY KEY,
                        FOREIGN KEY exchange REFERENCES exchanges (exchange),
                        FOREIGN KEY asset_class REFERENCES asset_classes (name),
                        symbol varchar NOT NULL
                    );
                """)

            elif table == "price":
                cursor.execute("""
                    CREATE TABLE price
                    (
                        FOREIGN KEY symbol REFERENCES assets (symbol),
                        FOREIGN KEY exchange REFERENCES exchanges (exchange),
                        timeframe varchar NOT NULL,
                        timestamp timestamp NOT NULL,
                        open real NOT NULL,
                        high real NOT NULL,
                        low real NOT NULL,
                        close real NOT NULL,
                        adj_close real,
                        volume real NOT NULL,
                    );
                """)

            elif table == "allocation_asset_class":
                cursor.execute("""
                    CREATE TABLE allocation_asset_class
                    (
                        FOREIGN KEY asset_class REFERENCES asset_classes (name),
                        allocation int NOT NULL
                    );
                """)

            elif table == "allocation_strategy":
                cursor.execute("""
                    CREATE TABLE allocation_strategy
                    (
                        FOREIGN KEY asset_class REFERENCES asset_classes (name),
                        strategy varchar NOT NULL,
                        allocation int NOT NULL
                    );
                """)
                pass

            elif table == "strategy_results":
                cursor.execute("""
                    CREATE TABLE strategies
                    (
                        name varchar NOT NULL,
                        FOREIGN KEY symbol REFERENCES assets (symbol),
                        FOREIGN KEY exchange REFERENCES exchanges (exchange),
                        timeframe varchar NOT NULL,
                        currency varchar NOT NULL,
                        start timestamp NOT NULL,
                        finish timestamp NOT NULL,
                        avg_return
                        net_pnl
                        winners
                        losers
                        win_loss
                        p_win
                        avg_size
                        avg_size_winner
                        avg_size_loser
                        avg_r
                        avg_r_winner
                        avg_r_loser
                        expectancy
                        exp_return
                        std_dev_returns
                        std_dev_downside_returns
                        sharpe
                        sortino

                    );
                """)
                pass

            elif table == "portfolio_results":
                cursor.execute("""
                    CREATE TABLE portfolios
                    (
                        name
                        start
                        finish
                        timeframes
                        strategies
                        assets
                        max_correlated_positions
                        max_open_positions
                        flat_fee
                        percent_fee
                        kelly
                        flat_risk_non_kelly
                        drawdown_limit
                        allocation_asset_class
                        allocation_strategy
                        start_equity
                        realised_equity
                        open_equity
                        final_equity
                        return
                        avg_return
                        high_watermark
                        drawdown_watermark
                        fees_paid
                        gross_profit
                        gross_loss
                        net_profit
                        avg_hold_time
                        avg_hold_time_winner
                        avg_hold_time_loser
                        open_trades
                        closed_trades
                        winners
                        losers
                        win_loss
                        p_win
                        expectancy
                        expected_return
                        largest_winner
                        largest_loser
                        avg_size_winner
                        avg_size_loser
                        avg_size
                        avg_r
                        avg_r_winner
                        avg_r_loser
                        std_dev_returns
                        std_dev_downside_returns
                        sharpe
                        sortino
                    );
                """)
                pass

except (psycopg2.DatabaseError) as exc:
    print(exc)

if connection is not None:
    connection.commit()
    connection.close()
    cursor.close()
