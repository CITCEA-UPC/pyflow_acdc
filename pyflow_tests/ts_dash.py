import pyflow_acdc as pyf
import pandas as pd
from pyflow_acdc.Graph_Dash import create_dash_app

def ts_dash():
    [grid,results] = pyf.NS_MTDC()

    start = 5990
    end = 6000
    obj = {'Energy_cost': 1}

    market_prices_url = "https://raw.githubusercontent.com/BernardoCV/pyflow_acdc/main/examples/NS_MTDC_TS/NS_TS_marketPrices_data_sd2024.csv"
    TS_MK = pd.read_csv(market_prices_url)
    pyf.add_TimeSeries(grid,TS_MK)

    wind_load_url = "https://raw.githubusercontent.com/BernardoCV/pyflow_acdc/main/examples/NS_MTDC_TS/NS_TS_WL_data2024.csv"
    TS_wl = pd.read_csv(wind_load_url)
    pyf.add_TimeSeries(grid,TS_wl)

    pyf.TS_ACDC_OPF(grid,start,end,ObjRule=obj)

    app = create_dash_app(grid)
    assert app.layout is not None
    assert app.callback_map

    print('Time series OPF completed and Dash app created')

def run_test():
    """Test time series dash functionality."""
    try:
        import dash
        
    except:
        print("dash is not installed...")
        return
    
    try:
        import pyomo
    except ImportError:
        print("pyomo is not installed...")
        return  
    
    ts_dash()

if __name__ == "__main__":
    run_test()