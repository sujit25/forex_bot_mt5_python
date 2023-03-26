import MetaTrader5 as mt5
import pandas as pd
import talib as ta
import logging
import sys
from utils import read_config
from mt5_interface import initialize_mt5
from time import sleep

logger = logging.getLogger(__name__)

def DXI_strategy(symbol, timeframe, prev_pos_di_val, prev_neg_di_val, RSI_period=5, ADX_THRESHOLD=25):
    """
    Compute DI indicator value and decide buy or sell on crossover
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        prev_pos_di_val: Prev pos di value
        prev_neg_di_val: Prev neg di value
    return:
        signal: Buy/Sell signal if its generated or None
        curr_pos_di_val: Current positive di value
        curr_neg_di_val: Current negative di value
    """
    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    adx_value = ta.ADX(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1]    
    # Calculate the RSI indicator 
    minus_di_val = int(ta.MINUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1])
    plus_di_val = int(ta.PLUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1])
    # minus_di_val = ta.MINUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-5:].mean()
    # plus_di_val = ta.PLUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-5:].mean()
   
    # If prev values are not set
    if prev_pos_di_val is None or prev_neg_di_val is None:
        prev_pos_di_val = plus_di_val
        prev_neg_di_val = minus_di_val
        return prev_pos_di_val, prev_neg_di_val, None

    # if adx threshold is not met, dont do anything
    if adx_value < ADX_THRESHOLD:
        prev_pos_di_val = plus_di_val
        prev_neg_di_val = minus_di_val
        logger.info(f"adx value: {adx_value} is less than threshold: {ADX_THRESHOLD}..plus di val: {plus_di_val}, neg di val: {minus_di_val}")
        return prev_pos_di_val, prev_neg_di_val, None

    logger.debug(f"Adx value: {adx_value}, prev pos di val: {prev_pos_di_val}, prev neg di val: {prev_neg_di_val}, minus di val: {minus_di_val}, plus di val: {plus_di_val}")
    # Check for crossover between positive di value and negative di value -- buy case.
    order = None
    if (prev_pos_di_val < prev_neg_di_val) and (plus_di_val > minus_di_val):
        logger.info(f"---->Found crossover: prev pos di val: {prev_pos_di_val} < prev neg di val: {prev_neg_di_val}...plus di val: {plus_di_val} > minus di val: {minus_di_val}")
        logger.info("Executing BUY order!!!")
        order = mt5.ORDER_TYPE_BUY
    else:
        logger.debug(f"Didnt found crossover: prev pos di val: {prev_pos_di_val}  prev neg di val: {prev_neg_di_val}...plus di val: {plus_di_val} > minus di val: {minus_di_val}")
    # Check for crossover between pos di val > neg di value -- sell case.
    if (prev_pos_di_val > prev_neg_di_val) and (plus_di_val < minus_di_val):
        logger.info(f"----->Found crossover: prev pos di val: {prev_pos_di_val} > prev neg di val: {prev_neg_di_val}...plus di val: {plus_di_val} < minus di val: {minus_di_val}")
        logger.info("Executing SELL order!!!")
        order = mt5.ORDER_TYPE_SELL
    else:
        logger.debug(f"Didnt found crossover: prev pos di val: {prev_pos_di_val} < prev neg di val: {prev_neg_di_val}...plus di val: {plus_di_val} > minus di val: {minus_di_val}")        

    # Update values for pos di val and minus di val.
    prev_pos_di_val = plus_di_val
    prev_neg_di_val = minus_di_val
    return prev_pos_di_val, prev_neg_di_val, order
    
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
    # Get the historical data for the symbol and timeframe    
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)

    # Convert the rates to a pandas DataFrame
    rates_frame = pd.DataFrame(rates)
    #rates_frame.to_csv("usdjpy_rates_dataframe.csv", index=False)
    # Calculate the RSI indicator            
    index = -1 * RSI_period
    # adx_value = ta.ADX(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-5:].mean()
    # minus_di_val = ta.MINUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-5:].mean()
    # plus_di_val = ta.PLUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-5:].mean()
    adx_value = ta.ADX(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1]
    minus_di_val = ta.MINUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1]
    plus_di_val = ta.PLUS_DI(rates_frame['high'], rates_frame['low'], rates_frame['close'], timeperiod=RSI_period).values[-1]
    RSI = ta.RSI(rates_frame['close'][-1 *(RSI_period*2):], timeperiod=RSI_period+1)
    #rsi_val = RSI.values[-5:].mean()
    rsi_val = RSI.values[-1]
    #rsi_val = RSI.ewm(span=5, adjust=False).mean()
    logger.info(f"RSI value computed for adx strategy- rsi period: {RSI_period}, adx value: {adx_value}, minus di val: {minus_di_val}, plus di val: {plus_di_val}")
    
    # Initialize prev rsi value first time if its not initialized already
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
    
    #ADX > 35 AND RSI < 50 AND +DI < -DI ==> BUY SIGNAL
    #ADX > 35 AND RSI > 50 AND +DI > -DI ==> SELL SIGNAL
    if adx_value > ADX_THRESHOLD:
        # buy case 
        # check RSI 
        if prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
            prev_rsi_val = rsi_val
            logger.info(f"prev rsi val: {prev_rsi_val} < {RSI_lower} and current rsi val: {rsi_val} > {RSI_lower}..Checking for adx values")
            # Check for di indicator values
            if plus_di_val < minus_di_val:                
                logger.info(f"Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} < minus_di_val: {minus_di_val}")
                logger.info("Sending buy order!!!")
                return prev_rsi_val, mt5.ORDER_TYPE_BUY
            else:
                logger.info(f"plus_di_val: {plus_di_val} > minus_di_val: {minus_di_val}...Hence skipping order submission for buy case!!!")

        # Sell case
        # check RSI
        elif prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
            prev_rsi_val = rsi_val
            logger.info(f"Prev rsi value: {prev_rsi_val} > {RSI_upper} and current rsi val: {rsi_val} < {RSI_upper}...Checking for adx values")
            # Check for di indicator values
            if plus_di_val > minus_di_val:                
                logger.info(f"Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} > minus_di_val: {minus_di_val}")
                logger.info("Sending sell order!!!")
                return prev_rsi_val, mt5.ORDER_TYPE_SELL
            else:
                logger.info(f"plus_di_val : {plus_di_val} < minus_di_val: {minus_di_val}...Hence skipping order submission for sell case!!!!")

    prev_rsi_val = rsi_val        
    return prev_rsi_val, None

    # if adx_value > ADX_THRESHOLD and plus_di_val < minus_di_val:
    #     logger.info(f"Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} < minus_di_val: {minus_di_val}")
    #     # Check for buy condition using RSI
    #     if prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
    #         logger.info(f"Sending buy order since prev rsi val: {prev_rsi_val} < {RSI_lower} and current rsi val: {rsi_val} > {RSI_lower}")
    #         prev_rsi_val = rsi_val
    #         return prev_rsi_val, mt5.ORDER_TYPE_BUY
    #     else:            
    #         logger.info(f"NOT Sending buy order since prev rsi val: {prev_rsi_val} !< {RSI_lower} OR current rsi val: {rsi_val} !> {RSI_lower}")
    #         prev_rsi_val = rsi_val
    #         return prev_rsi_val, None
    # elif adx_value > ADX_THRESHOLD and plus_di_val > minus_di_val:
    #     logger.info(f"Adx value: {adx_value} > Adx threshold: {ADX_THRESHOLD} & plus_di_val: {plus_di_val} > minus_di_val: {minus_di_val}")
    #     # Check for sell condition using RSI
    #     if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
    #         logger.info(f"Sending sell order since {prev_rsi_val} > {RSI_upper} and current rsi val: {rsi_val} < {RSI_upper}")            
    #         prev_rsi_val = rsi_val
    #         return prev_rsi_val, mt5.ORDER_TYPE_SELL
    #     else:
    #         logger.info(f"NOT Sending sell order since {prev_rsi_val} !> {RSI_upper} OR current rsi val: {rsi_val} !< {RSI_upper}") 
    #         prev_rsi_val = rsi_val
    #         return prev_rsi_val, None
    # prev_rsi_val = rsi_val
    # return prev_rsi_val, None


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
    symbol = 'USDJPYm'
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
        prev_rsi_val, signal = ADX_RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None)
        print(f"Prev rsi val: {prev_rsi_val}")
        sleep(5)