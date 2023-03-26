import pandas as pd


def compute_aroon_values(df, period=25):    
    df['ar_up'] = df['high'].rolling(period).apply(lambda x: x.argmax()) / period * 100
    df['ar_down'] = df['low'].rolling(period).apply(lambda x: x.argmin()) / period * 100
    return df['ar_down'], df['ar_up']

