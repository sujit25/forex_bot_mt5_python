import MetaTrader5 as mt5
import pandas as pd
import talib as ta
import logging
import sys
from utils import read_config
from mt5_interface import initialize_mt5
from time import sleep

logger = logging.getLogger(__name__)
                                        
def ADX_RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val, ADX_THRESHOLD=35):
    """
    Compute ADX, RSI and DI indicator value and decide whether to buy/sell
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        RSI_Period: RSI time frame
        RSI_Upper: RSI upper value
        RSI_Lower: RSI lower value
        prev_rsi_val: Previous RSI value
    return:
        prev_rsi_val: Updated rsi value
        signal: Buy/Sell signal if its generated or None
    """
    print(f"symbol: {symbol}, timeframe: {timeframe}, RSI period: {RSI_period}")
    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, RSI_period)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    print(f"Rates dataframe: {rates_frame}")
    print(f"high values: {rates_frame['high']}, low values: {rates_frame['low']}, close: {rates_frame['close']}")
    # Calculate the RSI indicator    
    rsi_time_period = RSI_period + 1
    adx_value = ta.ADX(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=rsi_time_period)
    minus_di_val = ta.MINUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=rsi_time_period)
    plus_di_val = ta.PLUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=rsi_time_period)
    RSI = ta.RSI(rates_frame['close'], timeperiod=rsi_time_period)
    print(f"adx value: {adx_value}, minus_di_val: {minus_di_val}, plus_di_val: {plus_di_val}")
    rsi_val = RSI.values.mean()
    print(f"RSI value computed for adx strategy: {rsi_val}, rsi period: {RSI_period}, adx value: {adx_value}, minus di val: {minus_di_val}, plus di val: {plus_di_val}")
    logger.info(f"RSI value computed for adx strategy: {rsi_val}")

    # Initialize prev rsi value first time if its not initialized already
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
    
    if adx_value > ADX_THRESHOLD and plus_di_val < minus_di_val:
        logger.info("Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} < minus_di_val: {minus_di_val}")
        # Check for buy condition using RSI
        if prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
            logger.info(f"Sending buy order since prev rsi val: {prev_rsi_val} < {RSI_lower} and current rsi val: {rsi_val} > {RSI_lower}")
            prev_rsi_val = rsi_val
            return prev_rsi_val, mt5.ORDER_TYPE_BUY
        else:
            return prev_rsi_val, None
    elif adx_value > ADX_THRESHOLD and plus_di_val > minus_di_val:
        logger.info("Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} > minus_di_val: {minus_di_val}")
        # Check for sell condition using RSI
        if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
            logger.info(f"Sending sell order since {prev_rsi_val} > {RSI_upper} and current rsi val: {rsi_val} < {RSI_upper}")
            prev_rsi_val = rsi_val
            return prev_rsi_val, mt5.ORDER_TYPE_SELL
        else:
            return prev_rsi_val, None
    return prev_rsi_val, None


def RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None):
    """ 
    Compute RSI value and decide whether to buy/sell 
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        RSI_Period: RSI time frame
        RSI_Upper: Rsi upper value
        RSI_Lower: Rsi lower value
        prev_rsi_val: Previous rsi value
    """    
    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, RSI_period+1)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    
    # Calculate the RSI indicator
    RSI = ta.RSI(rates_frame['close'], timeperiod=RSI_period)        
    rsi_val = RSI.values[-1]
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None    
    # Determine the trading signal based on the RSI value
    if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
        logger.info(f"Sending sell order since {prev_rsi_val} > {RSI_upper} and current rsi val: {rsi_val} < {RSI_upper}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_SELL
    elif prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
        logger.info(f"Sending buy order since {rsi_val} > {RSI_lower} and prev rsi val: {prev_rsi_val} < {RSI_lower}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_BUY
    else:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
    
def RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None):
    """ 
    Compute mean RSI value and decide whether to buy/sell 
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        RSI_Period: RSI time frame
        RSI_Upper: Rsi upper value
        RSI_Lower: Rsi lower value
        prev_rsi_val: Previous rsi value
    """

    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, RSI_period+1)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    
    if rates_frame.shape[0] == 0:
        print(f"Rates frame shape: {rates_frame.shape}")
        return None, None
    # Calculate the RSI indicator
    RSI = ta.RSI(rates_frame['close'], timeperiod=RSI_period)        
    # Compute mean RSI value
    rsi_val = RSI.mean()
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None    
    # Determine the trading signal based on the RSI value
    if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
        logger.info(f"Sending sell order since prev rsi val: {prev_rsi_val} > {RSI_upper} and {rsi_val} < {RSI_upper}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_SELL
    elif prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
        logger.info(f"Sending buy order since prev rsi val: {prev_rsi_val} < {RSI_lower} and {rsi_val} > {RSI_lower}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_BUY
    else:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None

def RSI_strategy_ema(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None, smoothing_period=5):
    """ 
    Compute ema RSI value and decide whether to buy/sell 
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        RSI_Period: RSI time frame
        RSI_Upper: Rsi upper value
        RSI_Lower: Rsi lower value
        prev_rsi_val: Previous rsi value
    """

    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, RSI_period+1)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    
    # Calculate the RSI indicator
    RSI = ta.RSI(rates_frame['close'], timeperiod=RSI_period).ewm(span=smoothing_period, adjust=False)

    # Compute mean RSI value
    rsi_val = RSI.mean()
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None    
    # Determine the trading signal based on the RSI value
    if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
        logger.info(f"Sending sell order since current rsi val: {rsi_val} > {RSI_upper} and prev_rsi_val: {prev_rsi_val} < {RSI_upper}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_SELL
    elif prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
        logger.info(f"Sending buy order since current rsi val: {rsi_val} > {RSI_lower} and prev_rsi_val: {prev_rsi_val} < {RSI_lower}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_BUY
    else:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
        
if __name__ == "__main__":    
    symbol = 'USDJPY'
    timeframe = mt5.TIMEFRAME_M1
    RSI_period = 14
    RSI_upper = 70
    RSI_lower = 30
    lot_size = 0.5
    config_data = read_config()
    init_status = initialize_mt5(config_data)
    if not init_status:
        logger.error("Initialization failed!!!")
        sys.exit(0)
    print(f"symbol: {symbol}, timeframe: {timeframe}, RSI period: {RSI_period}")
    # Continuously pull rates using mt5
    prev_rsi_val = None
    while True:        
        prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None)
        print(f"Prev rsi val: {prev_rsi_val}")
        sleep(5)