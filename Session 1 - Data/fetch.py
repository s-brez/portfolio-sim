from dateutil.relativedelta import relativedelta
from datetime import datetime
from time import sleep
import yfinance as yf
import pandas as pd
import numpy as np


# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# ###### Step 1: get raw data #################################################

symbol = "AMD"

# Adjust below params according to desired period and granularity.
# Data resolution options for yfinance : 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo 3mo
# These parameters will fetch the last 10 years worth of daily data.
resolution = "1d"
period = 10
end_date = datetime.now()
start_date = end_date - relativedelta(years=period)
end_date, start_date = end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

# These parameters would instead fetch the last 30 days worth of 15m resolution data.
# resolution = "15m"
# period = 30
# end_date = datetime.now().replace(microsecond=0, second=0, minute=0)
# start_date = end_date - relativedelta(days=period)
# end_date, start_date = end_date.strftime("%Y-%m-%d"), start_date.strftime("%Y-%m-%d")

# Fetch data and return a dataframe.
sleep(1)
df = yf.download(symbol,
                 start=start_date,
                 end=end_date,
                 interval=resolution)

# Drop unwanted columns, if any. Axis 0 is rows, axis 1 is columns.
df.drop("Adj Close", inplace=True, axis=1)

# Drop the final in-progress row for intra-daily timeframes.
if resolution != "1d" or resolution != "1wk" or resolution != "1mo" or resolution != "3mo":
    df = df.iloc[:-1, :]

# Set timestamp column as index.
df.index.names = ["Date"]

# Inspect data.
# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
# pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', None)
# print(df.dtypes)
# print(df)

# Save to csv.
filename = symbol + "_" + resolution + "_" + start_date + "_" + end_date + ".csv"
df.to_csv(filename, index=True)



# ###### Step 2 (optional): homogenise/clean data #################################

""" yfinance already provides fairly clean data, but for other data sources you
    will possibly want to do additional homogenizing and cleaning to avoid errors when
    working with the data.
"""

# 1. Reformat column/index values depending on application:
# E.g derive epoch timestamps from the Date column.
# modified_df = df.copy()
# new_column_data = list(df.index.values.astype(np.int64) // 10 ** 9)
# modified_df["Timestamp"] = new_column_data

# 2. Pad null or missing rows with their previous neighbour.
# modified_df.fillna(method="pad", inplace=True)

# Save to csv.
# filename = symbol + "_" + resolution + "_" + start_date + "_" + end_date + ".csv"
# modified_df.to_csv(filename, index=True)
# print(modified_df.dtypes)
# print(modified_df)



##### Option data  ############################################################

# Historical option data not available from Yahoo.
# We can fetch chains for current expirations only.
# ticker = yf.Ticker(symbol)
# options = ticker.options
# chain = ticker.option_chain(options[1])
# print("\nAll expirations:", options)
# print("\nPut data for expiry", str(options[1]) + ":")
# print(chain.puts)