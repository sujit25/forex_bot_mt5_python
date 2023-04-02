import MetaTrader5 as mt5
import pandas as pd
import talib as ta
import logging
import sys
from utils import read_config
from mt5_interface import initialize_mt5, get_open_positions, cancel_orders
from time import sleep
from indicator_impl import compute_aroon_values, compute_rsi_value

logger = logging.getLogger(__name__)

def Aroon_strategy_custom_threshold_close_orders(symbol, timeframe, window_size=25, up_line_buy_exit_thresh=70, down_line_sell_exit_thresh=30):
    """
    Close existing orders opened by Aroon strategy 
    args:
        symbol: Symbol under consideration
        up_line_buy_exit_thresh: Threshold limit to be considered for performing exit when buy order is executed between up_line_buy_lower_thresh and up_line_buy_upper_thresh
        down_line_exit_thresh: Down line threshold to be considered for performing exit when sell order is executed between down_line_sell_upper_thresh and down_line_sell_lower_thresh
    return:
        None
    """
    open_positions = get_open_positions(symbol)
    if len(open_positions) > 0:
        logger.info(f"Got {len(open_positions)} open positions including buy and sell orders!!!")
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        rates_frame = pd.DataFrame(rates)
        ar_down_vals, ar_up_vals = compute_aroon_values(rates_frame, window_size)
        
        # Take last values 
        ar_up_val = ar_up_vals.values[-1]
        ar_down_val = ar_down_vals.values[-1]

        buy_open_positions = list(filter(lambda x: x[2] ==0, open_positions))
        logger.info(f"AR up value: {ar_up_val}, up line buy exit threshold: {up_line_buy_exit_thresh}, AR down value: {ar_down_val}, down_line_sell_exit_threshold: {down_line_sell_exit_thresh}")

        # Check if ar_up_val has crossed buy exit threshold
        if ar_up_val >= up_line_buy_exit_thresh:            
            logger.info(f"Buy open positions: {buy_open_positions}")
            # Close buy open positions
            positions_to_cancel = [(open_position[0], open_position[1]) for open_position in buy_open_positions]
            logger.info(f"AR up value: {ar_up_val} crossed up line buy exit threshold: {up_line_buy_exit_thresh}. Closing positions: {positions_to_cancel}")
            cancel_orders(positions_to_cancel)

        sell_open_positions = list(filter(lambda x: x[2] ==1, open_positions))
        # Check if ar_down_val has crossed sell exit threshold
        if ar_down_val <= down_line_sell_exit_thresh:
            # Close sell open positions
            positions_to_cancel = [(open_position[0], open_position[1]) for open_position in sell_open_positions]
            logger.info(f"AR down value: {ar_up_val} crossed down line sell exit threshold: {down_line_sell_exit_thresh}. Closing positions: {positions_to_cancel}")            
            cancel_orders(positions_to_cancel)

def Aroon_custom_threshold_based_exit_strategy(symbol, timeframe, ar_up_prev=None, ar_down_prev=None, window_size=25, \
                                                up_line_buy_lower_thresh=0, up_line_buy_upper_thresh=100, 
                                                down_line_sell_upper_thresh=100, down_line_sell_lower_thresh=0):
    """ 
    Compute buy/sell signal using Aaroon indicator
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        ar_up_prev: AR up value (previously computed)
        ar_down_prev: AR down value (previously computed)
        up_line_buy_lower_thresh: Up line buy lower threshold to be considered for cross over during buy operation
        up_line_buy_upper_thresh: Up line buy upper threshold to be considered for cross over during buy operation        
        down_line_sell_upper_thresh: Down line sell upper threshold to be considered for cross over during sell operation
        down_line_sell_lower_thresh: Down line sell lower threshold to be considered for cross over during sell operation        
    return:
        ar_up_val: Newly computed ar up val
        ar_down_val: Newly computed ar down val
        signal: Buy/sell or None if not crossover found
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    rates_frame = pd.DataFrame(rates)
    ar_down_vals, ar_up_vals = compute_aroon_values(rates_frame, window_size+1)
    
    ar_up_val = int(ar_up_vals.values[-1])
    ar_down_val = int(ar_down_vals.values[-1])
    if ar_up_prev is None or ar_down_val is None:
        ar_up_prev = ar_up_val
        ar_down_prev = ar_down_val
        return ar_up_prev, ar_down_prev, None
    print(f"symbol: {symbol}, AR up val: {ar_up_val}, AR down val: {ar_down_val}")
    signal = None
    # if AR UP is betwen 30 and 50
    if ar_up_prev >= up_line_buy_lower_thresh and ar_up_prev <= up_line_buy_upper_thresh:
        logger.info(f"symbol: {symbol}, ar up prev: {ar_up_prev}, ar down prev: {ar_down_prev}, ar_up_val: {ar_up_val}, ar_down_val: {ar_down_val}")
        # Check for cross over between prev ar values and current ar values
        # Bullish crossover
        if ar_up_prev < ar_down_prev and ar_up_val > ar_down_val:
            signal = mt5.ORDER_TYPE_BUY
            logger.info(f"for symbol: {symbol} Found bullish cross over!!!!")

    # if AR DOWN is between 50 and 70
    if ar_down_prev >= down_line_sell_lower_thresh and ar_down_prev <= down_line_sell_upper_thresh:
        # Bearish crossover
        if ar_up_prev > ar_down_prev and ar_up_val < ar_down_val:
            signal = mt5.ORDER_TYPE_SELL
            logger.info(f"for symbol: {symbol} Found bearish cross over!!!!")
    
    # Copy back current values to prev values
    ar_up_prev = ar_up_val
    ar_down_prev = ar_down_val
    return ar_up_prev, ar_down_prev, signal


def Aroon_strategy_custom_threshold_close_orders2(symbol, timeframe, window_size, ar_up_prev, ar_down_prev, \
                                                up_line_buy_exit_thresh, down_line_sell_exit_thresh):
    """
    Close existing orders opened by Aroon strategy 
    args:
        symbol: Symbol under consideration
        ar_up_prev: Up line previous value. This value be None if its not initialized already.
        ar_down_prev: Down line previous value. This value be None if its not initialized already.
        up_line_buy_exit_thresh: Threshold limit to be considered for performing exit when buy order is executed between up_line_buy_lower_thresh and up_line_buy_upper_thresh
        down_line_exit_thresh: Down line threshold to be considered for performing exit when sell order is executed between down_line_sell_upper_thresh and down_line_sell_lower_thresh
    return:
        ar_up_prev_val: Ar up prev value
        ar_down_prev_val: Ar down prev value
    """
    open_positions = get_open_positions(symbol)
    if len(open_positions) > 0:
        logger.info(f"Got {len(open_positions)} open positions including buy and sell orders!!!")
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        rates_frame = pd.DataFrame(rates)
        ar_down_vals, ar_up_vals = compute_aroon_values(rates_frame, window_size)
        
        # Take last values 
        ar_up_val = ar_up_vals.values[-1]
        ar_down_val = ar_down_vals.values[-1]

        if ar_up_prev is None or ar_down_prev is None:
            ar_up_prev = ar_up_val        
            ar_down_prev = ar_down_val
            return ar_up_prev, ar_down_prev
        
        buy_open_positions = list(filter(lambda x: x[2] ==0, open_positions))        
        
        if len(buy_open_positions) > 0:
            logger.info(f"Buy open positions: {buy_open_positions}.")
            # Check if ar_down_val has crossed buy exit threshold
            # i.e it has touched 0 line
            if ar_down_prev > up_line_buy_exit_thresh and ar_down_val <= up_line_buy_exit_thresh:            
                # Close buy open positions
                positions_to_cancel = [(open_position[0], open_position[1]) for open_position in buy_open_positions]
                logger.info(f"Buy Threshold crossed!!! AR up prev value: {ar_up_prev} > up buy threshold: {up_line_buy_exit_thresh} & AR down value: {ar_up_val} < up buy threshold: {up_line_buy_exit_thresh}. hence closing positions: {positions_to_cancel}")
                cancel_orders(positions_to_cancel)
                ar_up_prev = None
        else:
            ar_up_prev = None

        # Close existing sell orders
        sell_open_positions = list(filter(lambda x: x[2] ==1, open_positions))
        if len(sell_open_positions) > 0:
            logger.info(f"Sell open positions: {sell_open_positions}")
            # Check if ar_up_val has crossed sell exit threshold 
            # i.e it has touched 0 line
            if ar_up_prev > down_line_sell_exit_thresh and ar_up_val <= down_line_sell_exit_thresh:
                # Close sell open positions
                positions_to_cancel = [(open_position[0], open_position[1]) for open_position in sell_open_positions]
                logger.info(f"Sell Threshold crossed!!! AR down prev. value: {ar_down_prev} > down sell threshold {down_line_sell_exit_thresh} & Ar down value: {ar_down_val} < down sell threshold: {down_line_sell_exit_thresh}. Closing positions: {positions_to_cancel}")
                cancel_orders(positions_to_cancel)
                ar_down_prev = None
        else:
            ar_down_prev = None        
    return ar_up_prev, ar_down_prev

def Aroon_custom_threshold_based_exit_strategy2(symbol, timeframe, ar_up_prev=None, \
                                                ar_down_prev=None, window_size=25, \
                                                up_line_buy_thresh=60, down_line_buy_thresh=40, \
                                                up_line_sell_thresh=40, down_line_sell_thresh=60):
    """ 
    Compute buy/sell signal using Aaroon indicator
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        ar_up_prev: AR up value (previously computed)
        ar_down_prev: AR down value (previously computed)
        window_size: Window size to be considered for Aroon calculations
        up_line_buy_thresh: Up line buy lower threshold to be considered before cross over during buy operation
        down_line_buy_thresh: Up line buy upper threshold to be considered before cross over during buy operation        
        up_line_sell_thresh: Down line sell upper threshold to be considered before during sell operation
        down_line_sell_thresh: Down line sell lower threshold to be considered before cross during sell operation        
    return:
        ar_up_val: Newly computed ar up val
        ar_down_val: Newly computed ar down val
        signal: Buy/sell or None if not crossover found
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    rates_frame = pd.DataFrame(rates)
    if rates_frame is None or rates_frame.shape[0] == 0:
        return 0, 0, None
    ar_down_vals, ar_up_vals = compute_aroon_values(rates_frame, window_size+1)
    
    ar_up_val = int(ar_up_vals.values[-1])
    ar_down_val = int(ar_down_vals.values[-1])
    if ar_up_prev is None or ar_down_val is None:
        ar_up_prev = ar_up_val
        ar_down_prev = ar_down_val
        return ar_up_prev, ar_down_prev, None
    print(f"symbol: {symbol}, AR up val: {ar_up_val}, AR down val: {ar_down_val}")
    signal = None

    # Check for cross over between prev ar values and current ar values
    # Bullish crossover
    if ar_up_prev < ar_down_prev and ar_up_val > ar_down_val:
        # if AR up is above 60 an down value is below 40
        if ar_up_val >= up_line_buy_thresh and ar_down_val <= down_line_buy_thresh:
            logger.info(f"symbol: {symbol}, ar up val: {ar_up_val}, ar down val: {ar_down_val}")        
            signal = mt5.ORDER_TYPE_BUY
            logger.info(f"for symbol: {symbol} Found bullish cross over!!!!")
    
    # Bearish crossover
    if ar_up_prev > ar_down_prev and ar_up_val < ar_down_val:        
        # If AR up is below 40 and AR down is above 60
        if ar_up_val <= up_line_sell_thresh and ar_down_val >= down_line_sell_thresh:
            logger.info(f"symbol: {symbol}, ar up val: {ar_up_val}, ar down val: {ar_down_val}")
            signal = mt5.ORDER_TYPE_SELL
            logger.info(f"for symbol: {symbol} Found bearish cross over!!!!")
    
    # Copy back current values to prev values
    ar_up_prev = ar_up_val
    ar_down_prev = ar_down_val
    return ar_up_prev, ar_down_prev, signal

def Aroon_strategy(symbol, timeframe, ar_up_prev=None, ar_down_prev=None, window_size=25):
    """ 
    Compute buy/sell signal using Aaroon indicator
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        ar_up_prev: AR up value (previously computed)
        ar_down_prev: AR down value (previously computed)
    return:
        ar_up_val: Newly computed ar up val
        ar_down_val: Newly computed ar down val
        signal: Buy/sell or None if not crossover found
    """
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    rates_frame = pd.DataFrame(rates)
    if rates_frame.shape[0] == 0:
        logger.info(f"Got empty rates dataframe for symbol: {symbol}, timeframe: {timeframe}")
        return ar_up_prev, ar_down_prev, None
    ar_down_vals, ar_up_vals = compute_aroon_values(rates_frame, window_size)
    
    ar_up_val = int(ar_up_vals.values[-1])
    ar_down_val = int(ar_down_vals.values[-1])   
    if ar_up_prev is None or ar_down_val is None:
        ar_up_prev = ar_up_val
        ar_down_prev = ar_down_val
        return ar_up_prev, ar_down_prev, None
    
    signal = None
    logger.info(f"ar up prev: {ar_up_prev}, ar down prev: {ar_down_prev}, ar_up_val: {ar_up_val}, ar_down_val: {ar_down_val}")
    # Check for cross over between prev ar values and current ar values
    # Bullish crossover
    if ar_up_prev < ar_down_prev and ar_up_val > ar_down_val:
        signal = mt5.ORDER_TYPE_BUY
        logger.info(f"for symbol: {symbol}, Found bullish cross over!!!!")

    # Bearish crossover
    elif ar_up_prev > ar_down_prev and ar_up_val < ar_down_val:
        signal = mt5.ORDER_TYPE_SELL
        logger.info(f"for symbol: {symbol} Found bearish cross over!!!!")
    
    ar_up_prev = ar_up_val
    ar_down_prev = ar_down_val
    return ar_up_prev, ar_down_prev, signal


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

def Inverse_rsi_close_orders(symbol, timeframe, rsi_period, rsi_upper, rsi_lower, prev_rsi):
    """
    Close existing orders opened by Aroon strategy 
    args:
        symbol: Symbol under consideration
        timeframe: timeframe for
        rsi_period: RSI period
        rsi_upper: Rsi upper threshold 
        rsi_lower: Rsi lower threshold
        prev_rsi: Previous rsi    
    """
    rsi_val = compute_rsi_value(symbol, timeframe, rsi_period)

    if prev_rsi is None:
        prev_rsi = rsi_val
        return prev_rsi
    
    open_positions = get_open_positions(symbol)
    if len(open_positions) > 0:
        logger.info(f"Got {len(open_positions)} open positions including buy and sell orders!!!")        
        buy_open_positions = list(filter(lambda x: x[2] ==0, open_positions))        
        logger.info(f"Buy open positions: {buy_open_positions}")

        # Check if ar_up_val has crossed buy exit threshold
        if prev_rsi > rsi_upper and rsi_val < rsi_upper:
            # Close buy open positions
            positions_to_cancel = [(open_position[0], open_position[1]) for open_position in buy_open_positions]
            logger.info(f"Cancelling BUY positions using inverse rsi strategy!!! : {positions_to_cancel}")
            cancel_orders(positions_to_cancel)

        sell_open_positions = list(filter(lambda x: x[2] ==1, open_positions))
        # Check if ar_down_val has crossed sell exit threshold
        if prev_rsi > rsi_upper and rsi_val > rsi_lower:
            # Close sell open positions
            positions_to_cancel = [(open_position[0], open_position[1]) for open_position in sell_open_positions]
            logger.info(f"Cancelling SELL positions using inverse rsi strategy!!! : {positions_to_cancel}")
            cancel_orders(positions_to_cancel)

def Inverse_RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val=None):
    """
    Compute RSI value and decide whether to buy/sell
    In inverse RSI- we'll buy if upper threshold is crossed i.e prev. price < RSI_upper and current price > RSI_upper then we'll buy
    Similarly if prev. price > RSI_lower and current price < RSI_lower, then we'll sell.
    Continue to hold order till TP or SL is hit. To improve accuracy we'll use moving average of RSI values
    args:
        symbol: Symbol to trade
        timeframe: Timeframe under consideration
        RSI_period: RSI period
        RSI_upper: RSI upper threshold
        RSI_lower: RSI lower threshold
        prev_rsi_val: Previously computed RSI value
    return:
        prev_rsi_val: Previously computed RSI value
        signal
    """
    rsi_val = compute_rsi_value(symbol, timeframe, RSI_period)
    if prev_rsi_val is None:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
    
    logger.info(f"prev. rsi val: {prev_rsi_val}, current rsi val: {rsi_val}, RSI upper: {RSI_upper}, RSI lower: {RSI_lower}")

    # Determine the trading signal based on the RSI value
    if prev_rsi_val < RSI_upper and rsi_val > RSI_upper:
        logger.info(f"Sending buy order since prev rsi val: {prev_rsi_val} < rsi upper: {RSI_upper} and current rsi val: {rsi_val} > rsi upper: {RSI_upper}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_BUY
    elif prev_rsi_val > RSI_lower and rsi_val < RSI_lower:
        logger.info(f"Sending sell order since prev rsi val: {prev_rsi_val} > rsi lower: {RSI_lower} and prev rsi val: {rsi_val} < rsi lower: {RSI_lower}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_SELL
    else:
        prev_rsi_val = rsi_val
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
    rsi_val = compute_rsi_value(symbol, timeframe, RSI_period)
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