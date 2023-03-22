import logging
import MetaTrader5 as mt5
from mt5_interface import send_order, cancel_order, get_open_orders
logger = logging.getLogger(__name__)

def fetch_pending_orders():
    """ 
    Fetch pending orders 
    """
    orders = mt5.orders_get()
    return [order[0] for order in orders] 

def cancel_orders():
    """ Cancel all open orders"""
    # Fetch open orders
    orders = get_open_orders()
    if len(orders) > 0:
        logger.info(f"Cancelling orders since more than 1 orders pending: {len(orders)}")
        # Cancel orders         
        for order in orders:
            logger.info(f"Cancelling order: {order}")
            cancel_order(order)

def place_order(symbol, signal, lot_size, SL_MARGIN=50, TP_MARGIN=25):
    """ 
    Place order for given symbol with specific signal and lot size
    params:
        symbol: Symbol to be traded
        signal: Either its buy or sell signal
        lot_size: Lot size to be used for current order
    """
    if signal is not None:
        # Get the current market price
        tick = mt5.symbol_info_tick(symbol)            
        symbol_info = mt5.symbol_info(symbol)
        # Set the stop loss and take profit levels
        # stop_loss = price - 1000 * symbol_info.point
        # take_profit = price + 1000 * symbol_info.point
        price = tick.bid if signal == mt5.ORDER_TYPE_BUY else tick.ask        
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
    else:
        logger.debug("Not placing any order since signal is None!!!!")