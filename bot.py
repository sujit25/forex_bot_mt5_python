import MetaTrader5 as mt5
from strategy import RSI_strategy
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


def main(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, lot_size):
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
        prev_rsi_val, signal = RSI_strategy(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, prev_rsi_val)

        # Execute the trade if there is a signal
        if signal is not None:

            # Fetch open orders
            orders = get_open_orders()
            if len(orders) > 0:
                logger.info(f"Cancelling orders since more than 1 orders pending: {len(orders)}")
                # Cancel orders         
                for order in orders:
                    logger.info(f"Cancelling order: {order}")
                    cancel_order(order)

            # Get the current market price
            tick = mt5.symbol_info_tick(symbol)
            price = tick.bid if signal == mt5.ORDER_TYPE_BUY else tick.ask
            logger.info(f"tick point: {tick.point}, tick ask price: {tick.ask}, tick bid price: {tick.bid}")
            # Set the stop loss and take profit levels
            #stop_loss = price - 1000 * tick.point
            #take_profit = price + 1000 * tick.point
            stop_loss = tick.ask - 500 * tick.point
            take_profit = tick.bid + 500 * tick.point
            # stop_loss = price - 50
            # take_profit = price + 100

            order_request = {
                'action': mt5.TRADE_ACTION_DEAL,
                'symbol': symbol,
                'volume': lot_size,
                'type': signal,
                'price': price,
                'sl': stop_loss,
                'tp': take_profit,
                'magic': 123456,
                'comment': 'RSI Trading Bot'
            }
            send_order(order_request)
            logger.info(f"Sending order request: {order_request}")        

        # Wait for 1 minute before checking for another trading signal        
        sleep(5)
        logger.debug("Waiting for 5s prior to checking")

def fetch_pending_orders():
    # fetch pending orders
    orders = mt5.orders_get()
    return [order[0] for order in orders]    

if __name__ == "__main__":
    symbol = 'BTCUSDm'
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
    else:
        logger.info("Initialization successful!!")
    main(symbol, timeframe, RSI_period, RSI_upper, RSI_lower, lot_size)

