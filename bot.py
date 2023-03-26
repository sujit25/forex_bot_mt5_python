import MetaTrader5 as mt5
from strategy import RSI_strategy_mean, ADX_RSI_strategy, DXI_strategy, Aroon_strategy, Aroon_custom_threshold_based_exit_strategy, Aroon_strategy_custom_threshold_close_orders
from utils import read_config, parse_config, parse_trade_timeframe
from mt5_interface import initialize_mt5
from order_manager import place_order
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


def rsi_strategy(trade_params, strategy_params, timeframe):
    """ 
    RSI trading strategy
    args:
        symbol: Currency to be traded
        timeframe: Timeframe under consideration
        strategy_params: Strategy params        
    return: None
    """ 
    # Trading params   
    symbol = trade_params['symbol']
    lot_size = trade_params['lot_size']
    sleep_interval = trade_params['sleep_interval']

    # Strategy params
    rsi_params = strategy_params['RSI']
    rsi_period = rsi_params['rsi_period']
    rsi_lower_threshold = rsi_params['rsi_lower_thresh']
    rsi_upper_threshold = rsi_params['rsi_upper_thresh']

    prev_rsi_val = None
    # Enter the main trading loop
    while True:
        # Check for a trading signal
        prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, rsi_period, rsi_upper_threshold, rsi_lower_threshold, prev_rsi_val)

        # use RSI mean strategy to generate trading signal
        #prev_rsi_val, signal = RSI_strategy_mean(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)        
        logger.info(f"RSI value: {prev_rsi_val}")
        # Execute the trade if there is a signal
        if signal is not None:        
            place_order(symbol, signal, lot_size)

        # Wait for 1 minute before checking for another trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking")
   
def adx_rsi_strategy(trade_params, strategy_params, timeframe):
    """
    ADX RSI strategy
    args:
        trade_params: Trading params
        strategy_params: Strategy params
        timeframe: mt5 timeframe
    """
    # Trading params   
    symbol = trade_params['symbol']
    lot_size = trade_params['lot_size']
    sleep_interval = trade_params['sleep_interval']

    # Strategy params
    rsi_params = strategy_params['ADX_RSI_DI']
    rsi_period = rsi_params['rsi_period']
    rsi_lower_threshold = rsi_params['rsi_lower_thresh']
    rsi_upper_threshold = rsi_params['rsi_upper_thresh']
    prev_rsi_val = None

    # Enter the main trading loop
    while True:
        # Check for a trading signal                                                
        prev_rsi_val, signal = ADX_RSI_strategy(symbol, timeframe, rsi_period, rsi_upper_threshold, rsi_lower_threshold, prev_rsi_val)
        # use RSI mean strategy to generate trading signal       
        logger.info(f"RSI value: {prev_rsi_val}")
        # Execute the trade if there is a signal
        if signal is not None:
            place_order(symbol, signal, lot_size)

        # Wait for 1 minute before checking for another trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking")

def dxi_strategy(trade_params, timeframe):
    """
    DXI Strategy
    args:
        trade_params: Trading params
        timeframe: Timeframe for trading
    """
    symbol = trade_params['symbol']
    lot_size = trade_params['lot_size']
    stop_loss_pips = trade_params['stop_loss_pips_margin']
    take_profit_pips = trade_params['take_profit_pips_margin']
    sleep_interval = trade_params['sleep_interval']
    prev_pos_di_val = None
    prev_neg_di_val = None

    while True:
        prev_pos_di_val, prev_neg_di_val, signal = DXI_strategy(symbol, timeframe, prev_pos_di_val, prev_neg_di_val)
        if signal is not None:            
            # cancel order
            # cancel_orders()
            logger.info(f"Found crossover for pos di val and neg di val!!. executing signal: {signal}")
            place_order(symbol, signal, lot_size, SL_MARGIN=stop_loss_pips, TP_MARGIN=take_profit_pips, comment='DXI trading bot')
        
        # Wait for sleep interval before checking again to generate trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking again!!")


def aroon_strategy(trade_params, timeframe):
    """
    Aroon Strategy
    args:
        trade_params: Trade parameters
        timeframe: Timeframe
    return:
        None
    """
    prev_ar_up_val = None
    prev_ar_down_val = None
    symbol = trade_params['strategy']
    lot_size = trade_params['lot_size']
    sleep_interval = trade_params['sleep_interval']
    stop_loss_pips = trade_params['stop_loss_pips_margin']
    take_profit_pips = trade_params['take_profit_pips_margin']

    while True:
        prev_ar_up_val, prev_ar_down_val, signal = Aroon_strategy(symbol, timeframe, prev_ar_up_val, prev_ar_down_val)
        if signal is not None:            
            logger.info(f"Found crossover for AR up val and AR down val!!. executing signal: {signal}")
            place_order(symbol, signal, lot_size, SL_MARGIN=stop_loss_pips, TP_MARGIN=take_profit_pips, comment='AR trading bot')
        
        # Wait for sleep interval before checking again to generate trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking again!!")

def aroon_strategy_with_custom_threshold(trade_params, timeframe):
    """
    Aroon strategy with custom threshold
    args:
        symbol: Symbol under consideration
        timeframe: Timeframe for candlesticks
        lot_size: Lot size for order
        sleep_interval: No. of seconds to wait before re-checking for any possible signal possibility
    """
    prev_ar_up_val = None
    prev_ar_down_val = None
    symbol = trade_params['symbol']
    lot_size = trade_params['lot_size']
    sleep_interval = trade_params['sleep_interval']
    sl_margin = trade_params['stop_loss_pips_margin']
    tp_margin = trade_params['take_profit_pips_margin']

    while True:
        # Check thresholds and close orders
        Aroon_strategy_custom_threshold_close_orders(symbol, timeframe)

        # Place orders using Aroon strategy
        prev_ar_up_val, prev_ar_down_val, signal = Aroon_custom_threshold_based_exit_strategy(symbol, timeframe, prev_ar_up_val, prev_ar_down_val)
        if signal is not None:            
            logger.info(f"Found crossover for AR up val and AR down val!!. executing signal: {signal}")
            place_order(symbol, signal, lot_size, SL_MARGIN=sl_margin, TP_MARGIN=tp_margin, comment='AR custom trading bot')
        
        # Wait for sleep interval before checking again to generate trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking again!!")

def main(strategy_name, timeframe, trade_params, strategy_params):
    """ 
    Main function
    args:
        strategy_name: Strategy name
        timeframe: Timeframe
        trade_params: Trade params
        strategy_params: Strategy params
    return: None
    """
    strategy_name = trade_params['strategy']
    symbol = trade_params['symbol']

    try:    
        if strategy_name == 'RSI':
            logger.info(f"Running RSI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            rsi_strategy(trade_params, timeframe)
        elif strategy_name == 'ADX_RSI_DI':
            logger.info(f"Running ADX_RSI_DI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            adx_rsi_strategy(trade_params, timeframe)
        elif strategy_name == 'DXI':
            logger.info(f"Running DXI trading strategy for symbol: {symbol}, timeframe: {timeframe}")
            dxi_strategy(trade_params, timeframe)
        elif strategy_name == "AROON":
            logger.info(f"Running Aroon strategy for symbol: {symbol}, timeframe: {timeframe}")
            aroon_strategy(trade_params, timeframe)
        elif strategy_name == "AROON_CUSTOM_ENTRY_EXIT":
            logger.info(f"Running Arooon strategy for symbol: {symbol}, timeframe: {timeframe} with custom entry and exit thresholds")
            aroon_strategy_with_custom_threshold(trade_params, timeframe)
    except Exception as ex:
        logger.error(f"Got Error while runnning bot: {ex}")
        logger.error(ex, exc_info=True)
        logger.error("Terminating bot!!!")

if __name__ == "__main__":    
    config_data = read_config()
    credentials, trade_params, strategy_params = parse_config(config_data)
    trade_timeframe = parse_trade_timeframe(trade_params['timeframe'])
    init_status = initialize_mt5(config_data['credentials'])
    if not init_status:
        logger.error("Initialization failed!!!")
        sys.exit(0)
    else:
        logger.info("Initialization successful!!")
    strategy_name = trade_params['strategy']
    main(strategy_name, trade_timeframe, trade_params, strategy_params)