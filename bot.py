import MetaTrader5 as mt5
from strategy import RSI_strategy_mean, ADX_RSI_strategy, DXI_strategy
from utils import read_config
from mt5_interface import initialize_mt5
from order_manager import place_order, cancel_orders, place_order_without_sltp
from time import sleep
import sys
import logging
from datetime import datetime
import os

os.makedirs("logs", exist_ok=True)
curr_dt = datetime.now().strftime(f"%Y_%m_%d")
logging.basicConfig(
     filename=f'logs/rsi_trading_bot_{curr_dt}.log',
     level=logging.INFO, 
     format= '[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
     datefmt='%H:%M:%S'
 )

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)

# add the handler to the root logger
logging.getLogger(__name__).addHandler(console)
logger = logging.getLogger(__name__)


def rsi_strategy(symbol, timeframe, RSI_period=14, RSI_upper=70, RSI_lower=30, lot_size=0.5, sleep_interval=5):
    """ 
    RSI trading strategy
    args:
        symbol: Currency to be traded
        timeframe: Timeframe under consideration
        RSI_period: Num of data points to be considered for computing RSI signal
        RSI_upper: Upper threshold value
        RSI_lower: Lower threshold value
        lot_size: Lot size to be considered for order
        sleep interval: No. of seconds to wait before re-checking for any possible signal generation possibility
    return: None
    """    
    prev_rsi_val = None
    # Enter the main trading loop
    while True:
        # Check for a trading signal
        prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)

        # use RSI mean strategy to generate trading signal
        #prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)        
        logger.info(f"RSI value: {prev_rsi_val}")
        # Execute the trade if there is a signal
        if signal is not None:        
            place_order(symbol, signal, lot_size)

        # Wait for 1 minute before checking for another trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking")
   
def adx_rsi_strategy(symbol, timeframe, RSI_period=14, RSI_upper=70, RSI_lower=30, lot_size=0.5, sleep_interval=5):
    """
    ADX RSI strategy
    args:
        symbol: Symbol under consideration
        timeframe: Timeframe under consideration
        RSI_period: Num of data points to be considered for computing RSI signal
        RSI_upper: Upper threshold value
        RSI_lower: Lower threshold value
        lot_size: Lot size to be considered for order
        sleep interval: No. of seconds to wait before re-checking for any possible signal generation possibility
    """
    prev_rsi_val = None
    # Enter the main trading loop
    while True:
        # Check for a trading signal                                                
        prev_rsi_val, signal = ADX_RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)
        #prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)

        # use RSI mean strategy to generate trading signal       
        logger.info(f"RSI value: {prev_rsi_val}")
        # Execute the trade if there is a signal
        if signal is not None:
            place_order(symbol, signal, lot_size)

        # Wait for 1 minute before checking for another trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking")

def dxi_strategy(symbol, timeframe, lot_size=0.5, sleep_interval=5):
    """
    DXI Strategy
    args:
        symbol: Symbol under consideration
        timeframe: Timeframe for candlesticks
        lot_size: Lot size for order
        sleep_interval: No. of seconds to wait before re-checking for any possible signal possibility
    """
    prev_pos_di_val = None
    prev_neg_di_val = None

    while True:
        prev_pos_di_val, prev_neg_di_val, signal = DXI_strategy(symbol, timeframe, prev_pos_di_val, prev_neg_di_val)
        if signal is not None:            
            # cancel order
            cancel_orders()
            logger.info(f"Found crossover for pos di val and neg di val!!. executing signal: {signal}")
            place_order(symbol, signal, lot_size, SL_MARGIN=30, TP_MARGIN=60, comment='DXI trading bot')
        
        # Wait for sleep interval before checking again to generate trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking again!!")


def main(strategy_name):
    try:    
        if strategy_name == 'RSI':
            logger.info(f"Running RSI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            rsi_strategy(symbol, timeframe)
        elif strategy_name == 'ADX_RSI_DI':
            logger.info(f"Running ADX_RSI_DI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            adx_rsi_strategy(symbol, timeframe)
        elif strategy_name == 'DXI':
            logger.info(f"Running DXI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            dxi_strategy(symbol, timeframe)
    except Exception as ex:
        logger.error(f"Got Error while runnning bot: {ex}")
        logger.error(ex, exc_info=True)
        logger.error("Terminating bot!!!")

if __name__ == "__main__":
    symbol = 'USDJPYm'
    #strategy_name = "ADX_RSI_DI"
    strategy_name = "DXI"
    timeframe = mt5.TIMEFRAME_M1
    config_data = read_config()
    init_status = initialize_mt5(config_data)
    if not init_status:
        logger.error("Initialization failed!!!")
        sys.exit(0)
    else:
        logger.info("Initialization successful!!")
    main(strategy_name)