from datetime import datetime
import pandas as pd


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Load csv into a dataframe.
filename = 'AMD_15m_2022-06-07_2022-07-07.csv'
df = pd.read_csv(filename)
df.columns.values[0] = "Date"

# Convert time column string back to datetime object
df['Date'] = pd.to_datetime(df['Date'])

# Set index.
df.set_index("Date", inplace=True)

# print(df)
print(len(df.index), "rows before resample")

# Aggregation method for each column in the source dataframe.
KEY = {
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}

# See here for options stackoverflow.com/questions/17001389/pandas-resample-documentation.
target_resolution = "30min"

resampled_df = None

# resample() outputs a continous time series regardless of input so there will be
# NaN entries during market closures if using equities or other data sources that are not 24/7.
try:
    resampled_df = (df.resample(target_resolution).agg(KEY))
except Exception as exc:
    print("Resampling error", exc)

# Trim NaN rows.
if resampled_df is not None:
    resampled_df = resampled_df[resampled_df["Open"].notna()]
    print(len(resampled_df.index), "rows after resample")
    print(resampled_df)

    # Save the downsampled data.
    new_filename = "RESAMPLED_TO_" + target_resolution + "_" + filename
    resampled_df.to_csv(new_filename, index=True)
