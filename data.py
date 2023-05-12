#!/usr/bin/env python3
import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
from pandas_datareader import data as pdr
# override yfinance with pandas – seems to be a common step
yf.pdr_override()

def data():
    today = date.today()
    decadeAgo = today - timedelta(days=1095)

    data = pdr.get_data_yahoo('BP.L', start=decadeAgo, end=today)

    data['Buy'] = 0
    data['Sell'] = 0

    for i in range(2, len(data)):
        body = 0.01

        # Three Soldiers
        if (
            (data.Close[i] - data.Open[i]) >= body and
            data.Close[i] > data.Close[i-1] and
            (data.Close[i-1] - data.Open[i-1]) >= body and
            data.Close[i-1] > data.Close[i-2] and
            (data.Close[i-2] - data.Open[i-2]) >= body
        ):
            data.at[data.index[i], 'Buy'] = 1

        # Three Crows
        if (
            (data.Open[i] - data.Close[i]) >= body and
            data.Close[i] < data.Close[i-1] and
            (data.Open[i-1] - data.Close[i-1]) >= body and
            data.Close[i-1] < data.Close[i-2] and
            (data.Open[i-2] - data.Close[i-2]) >= body
        ):
            data.at[data.index[i], 'Sell'] = 1
            
    data.reset_index(drop=False, inplace=True)
    data = data.to_dict(orient='records')
            
    return data