import json
import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

def read_config(config_fpath):
    """ 
    Parse json configuration file 
    args:
        config_fpath: Configuration file path
    returns:
        Configuration data loaded from JSON file
    """
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
        logger.info("Selecting timeframe as 1 min")
        return mt5.TIMEFRAME_M1
    elif trade_timeframe == "5min":
        logger.info("Selecting timeframe as 5 min")
        return mt5.TIMEFRAME_M5
    elif trade_timeframe == "15min":
        logger.info("Selecting timeframe as 15 min")
        return mt5.TIMEFRAME_M15
    elif trade_timeframe == "30min":
        logger.info("Selecting timeframe as 30 min")
        return mt5.TIMEFRAME_M30
    elif trade_timeframe == "1hr":
        logger.info("Selecting timeframe as 1 hr")
        return mt5.TIMEFRAME_H1
    elif trade_timeframe == "4hr":
        logger.info("Selecting timeframe as 4 hr")
        return mt5.TIMEFRAME_H4
    elif trade_timeframe == "1day":
        logger.info("Selecting timeframe as 1 day")
        return mt5.TIMEFRAME_D1
    elif trade_timeframe == "1week":
        logger.info("Selecting timeframe as 1 week")
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