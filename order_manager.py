import logging
import MetaTrader5 as mt5
from mt5_interface import send_order
logger = logging.getLogger(__name__)

def fetch_pending_orders():
    """ 
    Fetch pending orders 
    """
    orders = mt5.orders_get()
    return [order[0] for order in orders] 


def place_order_without_sltp(symbol, signal, lot_size, comment='RSI Trading bot'):
    """
    Place order for given symbol without setting SL or TP
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

        logger.info(f"symbol point: {symbol_info.point}, price: {price}")            
        order_request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': lot_size,
            'type': signal,
            'price': price,
            'magic': 123456,
            'comment': comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        send_order(order_request)
        logger.info(f"Sending order request: {order_request} without setting sl or tp")
    else:
        logger.debug("Not placing any order since signal is None!!!!")

def place_order(symbol, signal, lot_size, SL_MARGIN=50, TP_MARGIN=25, comment='RSI Trading bot'):
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
        price = tick.bid if signal == mt5.ORDER_TYPE_BUY else tick.ask
        multiplier = 10 ** 2

        if signal == mt5.ORDER_TYPE_BUY:
            price = tick.bid
            # Set stop loss to SL points from current price
            stop_loss = price - (SL_MARGIN * symbol_info.point) * multiplier
            # Set take profit to TP points from current price
            take_profit = price + (TP_MARGIN * symbol_info.point) * multiplier
        else:
            price = tick.ask 
            # Set stop loss to SL points from current price
            stop_loss = price + (SL_MARGIN * symbol_info.point) * multiplier
            # Set take profit to TP points from current price
            take_profit = price - (TP_MARGIN * symbol_info.point) * multiplier

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
            'comment': comment,
            "type_time": mt5.ORDER_TIME_GTC, 
            "type_filling": mt5.ORDER_FILLING_FOK, 
        }
        send_order(order_request)
        logger.info(f"Sending order request: {order_request}")
    else:
        logger.debug("Not placing any order since signal is None!!!!")