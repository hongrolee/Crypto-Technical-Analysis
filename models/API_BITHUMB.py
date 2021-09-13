import requests
import pandas as pd
from datetime import datetime


# 캔들스틱 불러오기
def call_data_from_bithumb(period, ticker='DOGE', start_date='2021-06-07', end_date='2021-06-30'):
    juso = "https://api.bithumb.com/public/candlestick/{coin}_KRW/{t}".format(coin=ticker, t=period)
    data = requests.get(juso)
    data = data.json()
    data = data.get("data")
    df = pd.DataFrame(data)
    df.rename(columns={0: "time", 1: "open", 2: "close", 3: "high", 4: "low", 5: "volume"}, inplace=True)
    df.sort_values("time", inplace=True)
    # df = df.tail(500)
    df = df[["time", "open", "close", "high", "low", "volume"]].astype("float")
    df.reset_index(drop=True, inplace=True)
    df['date'] = [datetime.fromtimestamp(x / 1000) for x in df['time']]

    df['date'] = pd.to_datetime(df['date'])
    d1 = pd.to_datetime(start_date)
    d2 = pd.to_datetime(end_date)
    df = df[df.date.between(d1, d2)]
    df.reset_index(drop=True, inplace=True)

    return df
