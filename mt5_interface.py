import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

def initialize_mt5(config):
    """
    Initialize mt5 with credentials
    params:
        config: Configuration params
    returns:
        init_status: Initialization status
    """    
    # connect to MetaTrader5 as mt5
    init_status = mt5.initialize(path=config['mt5_exe_path'], 
                                login=config['login'],
                                password=config['password'],
                                server=config['server'])
    return init_status


def send_order(request):
    """ 
    Send order request 
    params: 
        request: Request payload
    return:
        result: Order request return value
    """          
    result = mt5.order_send(request)    
    # Print the result of the trade
    logger.info(f"Send order result: {str(result)}")

def cancel_orders(orders):
    """ 
    Cancel orders in bulk
    args:
        orders: Orders to be cancelled
    return: None
    """
    if orders is None or len(orders) == 0:
        return
    for order in orders:
        order_ticket_id, symbol = order
        cancel_order(symbol, order_ticket_id)

def cancel_order(symbol, order_number):
    """ 
    Cancel order
    args: 
        symbol: Symbol for which order needs to be closed
        order_number: Order number for which order needs to be closed
    returns: None
    """
    try:
        logger.info(f"Cancelling order with ticket id: {order_number} for symbol: {symbol}")
        mt5.Close(symbol, ticket=order_number)
    except Exception as ex:
        logger.error(f"Failed to cancel order: {order_number} for symbol: {symbol}")
        logger.error(ex)

def get_open_positions(symbol):
    """ 
    Fetch open orders for current symbol under consideration 
    args:
        symbol: Current symbol currently being traded
    returns:
        list: List of tuples including pair in format of symbol, order ticket id
    """
    orders = mt5.positions_get(symbol=symbol)
    return [] if orders is None else [(order.symbol, order.ticket, order.type) for order in orders]    