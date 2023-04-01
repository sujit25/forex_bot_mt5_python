
def compute_aroon_values(df, period=25):
    """ 
    Compute Aroon values for given dataframe with time period of 25 (by default) 
    args:
        df: Rates dataframe
        period: Time interval period of 25
    return:
        ar_down: Series representing Aroon down signal values as Numpy array
        ar_up: Series representing Arron up signal values as Numpy array
    """
    df['ar_up'] = df['high'].rolling(period).apply(lambda x: x.argmax()) / period * 100
    df['ar_down'] = df['low'].rolling(period).apply(lambda x: x.argmin()) / period * 100
    return df['ar_down'], df['ar_up']

