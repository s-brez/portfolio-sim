import psycopg2


connection = psycopg2.connect(host="localhost", database="portfolio_sim", user="postgres", password="niglet")

# Database "portfolio_sim" must already exist.
cursor = connection.cursor()
# cursor.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'""")
# result = cursor.fetchall()

cursor.execute("DROP TABLE IF EXISTS exchanges CASCADE")
cursor.execute("DROP TABLE IF EXISTS asset_classes CASCADE")
cursor.execute("DROP TABLE IF EXISTS assets CASCADE")
cursor.execute("DROP TABLE IF EXISTS prices CASCADE")
cursor.execute("DROP TABLE IF EXISTS strategy_results CASCADE")
cursor.execute("DROP TYPE IF EXISTS allocation_asset_class CASCADE")
cursor.execute("DROP TYPE IF EXISTS allocation_strategy CASCADE")
cursor.execute("DROP TABLE IF EXISTS portfolio_results CASCADE")


cursor.execute("""
    CREATE TABLE exchanges
        (
            name varchar NOT NULL,
            PRIMARY KEY (name)
        )
""")

cursor.execute("""
    CREATE TABLE asset_classes
        (
            name varchar NOT NULL,
            PRIMARY KEY (name)
        )
""")

cursor.execute("""
    CREATE TABLE assets
    (
        asset_ID serial NOT NULL,
        symbol int NOT NULL,
        exchange varchar NOT NULL,
        asset_class varchar NOT NULL,
        CONSTRAINT fk_exchange FOREIGN KEY(exchange) REFERENCES exchanges(name),
        CONSTRAINT fk_asset_class FOREIGN KEY(asset_class) REFERENCES asset_classes(name),
        PRIMARY KEY(asset_ID)
    )
""")

cursor.execute("""
    CREATE TABLE prices
    (
        asset_ID int NOT NULL,
        symbol varchar NOT NULL,
        exchange varchar NOT NULL,
        timeframe varchar NOT NULL,
        timestamp timestamp NOT NULL,
        open real NOT NULL,
        high real NOT NULL,
        low real NOT NULL,
        close real NOT NULL,
        adj_close real,
        volume real NOT NULL,
        CONSTRAINT fk_asset_ID FOREIGN KEY(asset_ID) REFERENCES assets(asset_ID),
        CONSTRAINT fk_exchange FOREIGN KEY(exchange) REFERENCES exchanges(name),
        PRIMARY KEY (symbol, exchange)
    );
""")

cursor.execute("""
    CREATE TABLE strategy_results
    (
        name varchar NOT NULL,
        asset_ID int NOT NULL,
        exchange varchar NOT NULL,
        timeframe varchar NOT NULL,
        currency varchar NOT NULL,
        start timestamp NOT NULL,
        finish timestamp NOT NULL,
        avg_return real NOT NULL,
        net_pnl real NOT NULL,
        winners int NOT NULL,
        losers int NOT NULL,
        win_loss real NOT NULL,
        p_win real NOT NULL,
        avg_size real NOT NULL,
        avg_size_winner real NOT NULL,
        avg_size_loser real NOT NULL,
        avg_r real NOT NULL,
        avg_r_winner real NOT NULL,
        avg_r_loser real NOT NULL,
        expectancy real NOT NULL,
        exp_return real NOT NULL,
        std_dev_returns real NOT NULL,
        std_dev_downside_returns real NOT NULL,
        sharpe real NOT NULL,
        sortino real NOT NULL,
        CONSTRAINT fk_asset_ID FOREIGN KEY(asset_ID) REFERENCES assets(asset_ID),
        CONSTRAINT fk_exchange FOREIGN KEY(exchange) REFERENCES exchanges(name),
        PRIMARY KEY (name)
    )
""")

cursor.execute("""
    CREATE TYPE allocation_asset_class AS
    (
        asset_class varchar,
        allocation int
    )
""")


cursor.execute("""
    CREATE TYPE allocation_strategy AS
    (
        asset_class varchar,
        strategy varchar,
        allocation int
    )
""")

cursor.execute("""
    CREATE TABLE portfolio_results
    (
        name varchar NOT NULL,
        start timestamp NOT NULL,
        finish timestamp NOT NULL,
        timeframes varchar[] NOT NULL,
        strategies varchar[] NOT NULL,
        assets int[] NOT NULL,
        max_correlated_positions int NOT NULL,
        max_open_positions int NOT NULL,
        flat_fee real NOT NULL,
        percent_fee real NOT NULL,
        kelly bool NOT NULL,
        flat_risk_non_kelly real NOT NULL,
        drawdown_limit real NOT NULL,
        allocation_asset_class allocation_asset_class[] NOT NULL,
        allocation_strategy allocation_strategy[] NOT NULL,
        start_equity real NOT NULL,
        realised_equity real NOT NULL,
        open_equity real NOT NULL,
        final_equity real NOT NULL,
        return real NOT NULL,
        avg_return real NOT NULL,
        high_watermark real NOT NULL,
        drawdown_watermark real NOT NULL,
        fees_paid real NOT NULL,
        gross_profit real NOT NULL,
        gross_loss real NOT NULL,
        net_profit real NOT NULL,
        avg_hold_time interval NOT NULL,
        avg_hold_time_winner interval NOT NULL,
        avg_hold_time_loser interval NOT NULL,
        open_trades int NOT NULL,
        closed_trades int NOT NULL,
        winners int NOT NULL,
        losers int NOT NULL,
        win_loss real NOT NULL,
        p_win real NOT NULL,
        expectancy real NOT NULL,
        expected_return real NOT NULL,
        largest_winner real NOT NULL,
        largest_loser real NOT NULL,
        avg_size_winner real NOT NULL,
        avg_size_loser real NOT NULL,
        avg_size real NOT NULL,
        avg_r real NOT NULL,
        avg_r_winner real NOT NULL,
        avg_r_loser real NOT NULL,
        std_dev_returns real NOT NULL,
        std_dev_downside_returns real NOT NULL,
        sharpe real NOT NULL,
        sortino real NOT NULL,
        PRIMARY KEY (name)
    );
""")




connection.commit()
connection.close()
