import json
import MetaTrader5 as mt5

def read_config(config_fpath):
    """ Parse json configuration file """
    with open(config_fpath, 'r') as f:
        config_data = json.load(f)
        return config_data

def parse_trade_timeframe(trade_timeframe):
    """ 
    Parse trade timeframe from configuration parameter to metatrader specific format
        args: trade_timeframe
        return: Corresponding timeframe in meta trader format
    """
    if trade_timeframe == "1min":
        return mt5.TIMEFRAME_M1
    elif trade_timeframe == "5min":
        return mt5.TIMEFRAME_M5
    elif trade_timeframe == "15min":
        return mt5.TIMEFRAME_M15
    elif trade_timeframe == "30min":
        return mt5.TIMEFRAME_M30
    elif trade_timeframe == "1hr":
        return mt5.TIMEFRAME_H1
    elif trade_timeframe == "4hr":
        return mt5.TIMEFRAME_H4
    elif trade_timeframe == "1day":
        return mt5.TIMEFRAME_D1
    elif trade_timeframe == "1week":
        return mt5.TIMEFRAME_W1
    
def parse_config(config_data):
    """ 
    Parse configuration data 
    args:
        config_data: Configuration data dictionary
    returns:
        credentials: Account credentials
        trade_params: Trading parameters
        strategy_params: Strategy params for various trading strategies
    """
    credentials = config_data['credentials']
    trade_params = config_data['trade_params']
    strategy_params = config_data['strategy_params']
    return credentials, trade_params, strategy_params