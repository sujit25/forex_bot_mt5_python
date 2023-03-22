import MetaTrader5 as mt5
from strategy import RSI_strategy, RSI_strategy_mean
from utils import read_config
from mt5_interface import initialize_mt5, send_order, get_open_orders, cancel_order
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


def main(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, lot_size, sleep_interval=60):
    """ 
    Trading bot entry point
    args:
        symbol: Currency to be traded
        timeframe: Timeframe under consideration
        RSI_period: Num of data points to be considered for computing RSI signal
        RSI_upper: Upper threshold value
        RSI_lower: Lower threshold value
        lot_size: Lot size to be considered for order
    return:

    """
    # Define the trading parameters    
    price = None
    stop_loss = None
    take_profit = None
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

            # # Fetch open orders
            # orders = get_open_orders()
            # if len(orders) > 0:
            #     logger.info(f"Cancelling orders since more than 1 orders pending: {len(orders)}")
            #     # Cancel orders         
            #     for order in orders:
            #         logger.info(f"Cancelling order: {order}")
            #         cancel_order(order)

            # Get the current market price
            tick = mt5.symbol_info_tick(symbol)            
            symbol_info = mt5.symbol_info(symbol)
            # Set the stop loss and take profit levels
            # stop_loss = price - 1000 * symbol_info.point
            # take_profit = price + 1000 * symbol_info.point
            price = tick.bid if signal == mt5.ORDER_TYPE_BUY else tick.ask            
            SL_MARGIN = 50
            TP_MARGIN = 25
            if signal == mt5.ORDER_TYPE_BUY:
                price = tick.bid
                # Set stop loss to 25 points only
                stop_loss = price - (SL_MARGIN * symbol_info.point)
                # Set TP to 50 points 
                take_profit = price + (TP_MARGIN * symbol_info.point)
            else:
                price = tick.ask 
                # Set stop loss to 25 points only
                stop_loss = price + (SL_MARGIN * symbol_info.point)
                # Set TP to 50 points
                take_profit = price - (TP_MARGIN * symbol_info.point)

            logger.info(f"symbol point: {symbol_info.point}, price: {price}, take profit: {take_profit},stop loss: {stop_loss}")            
            order_request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': lot_size,
                'type': signal,
                'price': price,
                'sl': stop_loss,
                'tp': take_profit,
                'magic': 123456,
                'comment': 'RSI Trading Bot',
                "type_time": mt5.ORDER_TIME_GTC, 
                "type_filling": mt5.ORDER_FILLING_FOK, 
            }
            send_order(order_request)
            logger.info(f"Sending order request: {order_request}")        

        # Wait for 1 minute before checking for another trading signal
        sleep(sleep_interval)
        logger.debug(f"Waiting for {sleep_interval}s prior to checking")

def fetch_pending_orders():
    # fetch pending orders
    orders = mt5.orders_get()
    return [order[0] for order in orders]    

if __name__ == "__main__":
    symbol = 'USDJPYm'
    timeframe = mt5.TIMEFRAME_M1
    RSI_period = 14    
    RSI_upper = 70
    RSI_lower = 30
    lot_size = 0.5
    sleep_interval = 5
    config_data = read_config()
    init_status = initialize_mt5(config_data)
    if not init_status:
        logger.error("Initialization failed!!!")
        sys.exit(0)
    else:
        logger.info("Initialization successful!!")
    try:
        main(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, lot_size, sleep_interval)
    except Exception as ex:
        logger.error(f"Got Error while runnning bot: {ex}")
        logger.error("Terminating bot!!!")

