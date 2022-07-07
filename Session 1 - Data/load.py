import pandas as pd


# pd.set_option('display.max_rows', None)
# pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

df = pd.read_csv('AMD_1d_2012-07-07_2022-07-07.csv')
# df = pd.read_csv('AMD_15m_2022-06-07_2022-07-07.csv')

df.columns.values[0] = "Date"
df.set_index("Date", inplace=True)

print(df)
