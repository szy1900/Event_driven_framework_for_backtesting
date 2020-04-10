from pandas_datareader import data
import matplotlib.pyplot as plt
import pandas as pd

tickers = ['AAPL']

# We would like all available data from 01/01/2000 until 12/31/2016.
start_date = '2010-01-01'
end_date = '2020-3-1'

# User pandas_reader.data.DataReader to load the desired data. As simple as that.
panel_data = data.DataReader("AAPL", "yahoo", start_date, end_date)
panel_data.to_csv('AAPL.csv')
