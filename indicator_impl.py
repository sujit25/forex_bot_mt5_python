import pandas as pd
import talib as ta
import MetaTrader5 as mt5
import numpy as np

def compute_aroon_values(df, period=25):
    """ 
    Compute Aroon values for given dataframe with time period of 25 (by default) 
    args:
        df: Rates dataframe
        period: Time interval period of 25
    return:
        ar_down: Series representing Aroon down signal values as Numpy array
        ar_up: Series representing Arron up signal values as Numpy array
    """
    df['ar_up'] = df['high'].rolling(period).apply(lambda x: x.argmax()) / period * 100
    df['ar_down'] = df['low'].rolling(period).apply(lambda x: x.argmin()) / period * 100
    return df['ar_down'], df['ar_up']

def compute_rsi_value(symbol, timeframe, rsi_period, compute_rsi_mean=False):
    """
    Compute RSI values for particular symbol with time period of rsi period (14)
    args:
        symbol: Symbol to be value
        rsi_period: Rsi period to be considered
        timeframe: Timeframe 
    return:
        rsi_value: Computed RSI value
    """
    # Get the historical data for the symbol and timeframe
    time_period = rsi_period + 1
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, time_period)
    if rates is None:
        print("rates series is None")
        return 0
        
    # Calculate the RSI indicator
    #RSI = ta.RSI(rates_frame['close'], timeperiod=rsi_period)
    #rsi_val = RSI.values[-1]
    #return rsi_val

    # Custom implementation of RSI values
    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    delta = rates_frame['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    average_gain = gain.rolling(window=time_period).mean()
    average_loss = loss.rolling(window=time_period).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    rsi_values = rsi.values
    if compute_rsi_mean:
        return rsi_values[~np.isnan(rsi_values)].mean()
    else:
        return rsi_values[-1]
