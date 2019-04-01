import pandas as pd
import numpy as np
from pypf.instrument import DataframeInstrument
from pypf.chart import PFChart

def generate_pf_chart(ticker, historical_panel, duration=1.0):
    ''' 
        This function will create a p&f chart for the given ticker using historical data
        
        @param ticker: (str) ticker of asset to create P&F chart for
        @param historical_dfs: (pd.Panel) Panel holding historical ticker data
        
        return: PFChart object from which P&F chart/data can be extracted
    
    '''
    # Set up dataframe instrument
    try:
        df = historical_panel[ticker]
    except:
        raise ValueError('Ticker passed does not exist in historical dataset')

    # Format date and volume values
    df['Date'] = df.index.astype(str)
    df['Date'] = df['Date'].str.slice(0,10)
    df['Volume'] = df['Volume'].astype(int)

    # Tes
    dfi = DataframeInstrument(ticker, dataframe=df)

    # Create pf chart
    chart = PFChart(dfi, duration=duration)
    chart.create_chart()
    return chart


# This function will generate an rs chart for two given securities
def generate_rs_chart(numerator, denominator, historical_panel):
    ''' 
        This function will generate an RS chart of Numerator/Denominator usingn data from
        historical dfs
        
        @param numerator: (str) Numerator ticker symbol
        @param denominator: (str) Denominator ticker symbol
        @param historical_panel: (pd.Panel) Panel where each col is a ticker, and entry is OHLC data 
                                for that ticker.
    '''
    # Create joint dataframe to hold RS data
    rs_df = pd.DataFrame(columns = ['Open', 'High', 'Low', 'Close', 'Volume'])
    
    # Set 'Close' equal to ratio between two close prices on a daily basis
    rs_df['Close'] = historical_panel[numerator]['Close'] / historical_panel[denominator]['Close']
    
    # Set other columns equal to same ratio (close/close), since this is the only value that matters
    rs_df['High'] = rs_df['Close']
    rs_df['Low'] = rs_df['Close']
    rs_df['Open'] = rs_df['Close']
    rs_df['Volume'] = rs_df['Close']
    
    # Format date for use with DataframeInstrument
    rs_df['Date'] = rs_df.index.astype(str)
    rs_df['Date'] = rs_df['Date'].str.slice(0,10)
    try:
        rs_df['Volume'] = rs_df['Volume'].astype(int)
    except:
        print('ERROR: Numerator={0}, Denominator={1}'.format(numerator, denominator))
    
    
    # Create a new DataframeInstrument using this new dataframe
    rs_instrument = DataframeInstrument(numerator + '_' + denominator, dataframe=rs_df)
    
    # Chart the RS data
    chart = PFChart(rs_instrument)
    chart.create_chart()
    return chart

def sum_x(row):
    on_x = list(filter(lambda x: x == 'x', row))
    return len(on_x)

def sum_buy_signals(row):
    on_buy_signal = list(filter(lambda x: x == 'buy', row))
    return len(on_buy_signal)
    
def run_rs_matrix(historical_panel):
    '''
        This function will run a relative strength matrix for the symbols passed. 
        
        @param symbols: (list) list of symbols (tickers) to generate chart
        @param historical_panel: (pd.Panel) Panel holding historical ticker data
        
        return (pd.DataFrame) DataFrame representing an RS matrix
    '''
    if len(historical_panel.items) >= 2:
        # Create a blank matrix to hold the charts
        col_matrix = pd.DataFrame(index=historical_panel.items, columns=historical_panel.items)
        signal_matrix = pd.DataFrame(index=historical_panel.items, columns=historical_panel.items)
        for numerator in historical_panel.items:
            for denominator in historical_panel.items:
                # Create RS chart with every other chart
                chart = generate_rs_chart(numerator, denominator, historical_panel)  
                
                # Check to see if chart in column of Xs or Os, as well as Buy or Sell signal
                key = list(chart._chart_meta_data.keys())[-1]
                column_type = chart._chart_meta_data[key]['direction']
                signal = chart._chart_meta_data[key]['signal']
                
                # Save appropriate data to col/signal dataframes
                col_matrix.at[numerator, denominator] = column_type
                signal_matrix.at[numerator, denominator] = signal
                
        # Null out the diagonal of matrices, as this is RS versus itself
        for symbol in historical_panel.items:
            col_matrix.at[symbol, symbol] = None
            signal_matrix.at[symbol, symbol] = None
            
        # Get Counts for X columns/Buy Signals
        col_matrix['x_count'] = col_matrix.apply(sum_x, axis=1)
        signal_matrix['buy_count'] = signal_matrix.apply(sum_buy_signals, axis=1)
        
        # Combine matrices together
        columns = ['x_count', 'buy_count', 'total'] + list(historical_panel.items)
        rs_matrix = pd.DataFrame(index = historical_panel.items, columns=columns)
        for symbol in historical_panel.items:
            rs_matrix[symbol] = col_matrix[symbol] + '_' + signal_matrix[symbol]
        rs_matrix['x_count'] = col_matrix['x_count']
        rs_matrix['buy_count'] = signal_matrix['buy_count']
        rs_matrix['total'] = rs_matrix['buy_count'] + rs_matrix['x_count']
        
        return rs_matrix