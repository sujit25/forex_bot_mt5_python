import MetaTrader5 as mt5
from strategy import RSI_strategy
from utils import read_config
from mt5_interface import initialize_mt5, send_order
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


def send_order_loop_btc(symbol, lot_size):
    # Get the current market price
    signal = mt5.ORDER_TYPE_BUY
    tick = mt5.symbol_info_tick(symbol)
    print(tick)
    # price = tick.bid if signal == mt5.ORDER_TYPE_BUY else tick.ask
    price = tick.ask if signal == mt5.ORDER_TYPE_BUY else tick.bid
    ask_price = tick.ask
    bid_price = tick.bid

    # Set the stop loss and take profit levels
    # multiplication factor is 100 only for BTCUSDm or ETHUSD pairs
    stop_loss = bid_price - 100 * mt5.symbol_info(symbol).point * 20
    take_profit = ask_price + 100 * mt5.symbol_info(symbol).point * 50
    
    logger.info(f"Current price: {price}, Stop loss: {stop_loss}, take profit: {take_profit}")
    order_request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': lot_size,
        'type': signal,
        'price': price,    
        'sl': stop_loss,
        'tp': take_profit,
        'magic': 123456,
        'comment': f'Trading_Bot_{symbol}',
        "type_time": mt5.ORDER_TIME_GTC, 
        "type_filling": mt5.ORDER_FILLING_FOK, 
    }  
    response = mt5.order_send(order_request)
    logger.debug(f"Sending order request: {order_request}, response: {str(response)}")


if __name__ == "__main__":
    symbol = 'BTCUSDm'
    timeframe = mt5.TIMEFRAME_M1
    RSI_period = 14
    RSI_upper = 70
    RSI_lower = 30
    lot_size = 0.01
    config_data = read_config()
    init_status = initialize_mt5(config_data['credentials'])
    if not init_status:
        logger.error("Initialization failed!!!")
        sys.exit(0)
    else:
        logger.info("Initialization successful!!")

    # Send 10 orders for current pair BTCUSDm 
    limit = 50
    index = 0
    while True:
        if index > limit:
            break
        index += 1 
        send_order_loop_btc(symbol, lot_size)
        #sleep(5)