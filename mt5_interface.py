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


# Function to cancel an order
def cancel_order(order_number):
    # Create the request
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order_number,
        "comment": "Order Removed"
    }
    # Send order to MT5
    order_result = mt5.order_send(request)
    return order_result

def get_open_orders():
    """ Fetch open orders"""
    orders = mt5.orders_get()
    order_array = []
    for order in orders:
        order_array.append(order[0])
    return order_array