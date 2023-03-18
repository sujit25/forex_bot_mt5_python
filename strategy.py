import MetaTrader5 as mt5
import pandas as pd
import talib as ta
import logging
import sys
from utils import read_config
from mt5_interface import initialize_mt5
from time import sleep

logger = logging.getLogger(__name__)

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

    logger.info(f"RSI value: {rsi_val}")

    # Determine the trading signal based on the RSI value
    if prev_rsi_val > RSI_upper and rsi_val < RSI_upper:
        logger.info(f"Sending sell order since {rsi_val} > {RSI_upper}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_SELL
    elif prev_rsi_val < RSI_lower and rsi_val > RSI_lower:
        logger.info(f"Sending buy order since {rsi_val} > {RSI_lower}")
        prev_rsi_val = rsi_val
        return prev_rsi_val, mt5.ORDER_TYPE_BUY
    else:
        prev_rsi_val = rsi_val
        return prev_rsi_val, None
    

# if __name__ == "__main__":    
#     symbol = 'USDJPY'
#     timeframe = mt5.TIMEFRAME_M1
#     RSI_period = 14
#     RSI_upper = 70
#     RSI_lower = 30
#     lot_size = 0.11
#     config_data = read_config()
#     init_status = initialize_mt5(config_data)
#     if not init_status:
#         logger.error("Initialization failed!!!")
#         sys.exit(0)
    
#     # Continuously pull rates using mt5
#     while True:
#         rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, RSI_period +1)
#         rates_df = pd.DataFrame(rates)
#         RSI = ta.RSI(rates_df['close'], timeperiod=RSI_period)
#         #print("rsi dataframe:", RSI)
#         rsi_val = RSI.values[-1]
#         print(f"RSI value: {rsi_val}")
#         sleep(5)