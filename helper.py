import sys
import requests
import pytz

import numpy as np
import pandas as pd

from zipline.assets._assets import Equity  # Required for USEquityPricing
from zipline.pipeline.data import USEquityPricing
from zipline.pipeline.classifiers import Classifier
from zipline.pipeline.engine import SimplePipelineEngine
from zipline.pipeline.loaders import USEquityPricingLoader
from zipline.utils.numpy_utils import int64_dtype

from collections import OrderedDict
from time import sleep


EOD_BUNDLE_NAME = 'eod-quotemedia'


class PricingLoader(object):
    def __init__(self, bundle_data):
        self.loader = USEquityPricingLoader(
            bundle_data.equity_daily_bar_reader,
            bundle_data.adjustment_reader)

    def get_loader(self, column):
        if column not in USEquityPricing.columns:
            raise Exception('Column not in USEquityPricing')
        return self.loader

def beautify_tickers(tickers):
    '''Takes in a list of zipline generated tickers and makes them readable'''
    pretty_tickers = []
    for ticker in tickers:
        # Format is 'Equity(0, [TICK])' -- search for '[' and up to ']'
        ticker = str(ticker)
        start_idx = ticker.find('[') + 1
        end_idx = ticker.find(']')        
        pretty_tickers.append(ticker[start_idx:end_idx])
        
    return pretty_tickers

def beautify_ticker(ticker):
    ''' Takes individual Zipline formatted ticker and returns just the symbol'''
    # Format is 'Equity(0, [TICK])' -- search for '[' and up to ']'
    ticker = str(ticker)
    start_idx = ticker.find('[') + 1
    end_idx = ticker.find(']')        
    return ticker[start_idx:end_idx]
    
    

def build_pipeline_engine(bundle_data, trading_calendar):
    pricing_loader = PricingLoader(bundle_data)

    engine = SimplePipelineEngine(
        get_loader=pricing_loader.get_loader,
        calendar=trading_calendar.all_sessions,
        asset_finder=bundle_data.asset_finder)

    return engine



def get_sector_etf_panel():
    '''
        Get a panel containing data on the 9 main sector ETFs
        
        @returns (pd.Panel) a Panel containing historical data for all 9 of the major sector ETFs
    '''
    # Get API key from file
    api_file = 'api_key.txt'
    api_key = ''
    with open(api_file) as f:
        api_key = f.readline()

    sector_etfs = {
        'XLK': 'Technology',
        'XLB': 'Materials',
        'XLI': 'Industrials',
        'XLP': 'Staples',
        'XLY': 'Discretionary',
        'XLE': 'Energy',
        'XLU': 'Utilities',
        'XLF': 'Financials',
        'XLV': 'Healthcare',
        #'RSP': 'SP 500 EW',
        #'SPY': 'SP 500',
        #'XLRE': 'Real Estate',
        #'XLC': 'Communications'
    }
    # For each ETF, grab data from 1998-2019
    etf_data = OrderedDict()
    minor_axis = ['Open', 'High', 'Low', 'Close', 'Volume']
    symbols = list(sector_etfs.keys())
    for idx, symbol in enumerate(symbols):
        # Get daily data from API
        print('Obtaining Data for {0} -- {1}/{2}'.format(symbol, str((idx+1)), str(len(symbols))), end='\r', flush=True)
        api_path = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={0}&outputsize=full&apikey={1}'\
                    .format(symbol, api_key)
        r = requests.get(api_path)
        df = pd.DataFrame.from_dict(r.json()['Time Series (Daily)']).transpose()
        df.columns = minor_axis
        # Convert columns to numeric values
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        # Save ETF data to ordered dict
        etf_data[symbol] = df
        # Sleep to avoid API limit of 5 calls per minute -- don't have to sleep after last call
        if idx != len(sector_etfs.keys()):
            sleep(15)

    # From OrderedDict, create pd.Panel
    etf_panel = pd.Panel(etf_data)
    etf_panel.minor_axis = minor_axis
    etf_panel.major_axis = pd.to_datetime(etf_panel.major_axis).tz_localize(pytz.utc)
    
    return etf_panel

def create_monthly_date_ranges(start_year, end_year):
    '''
        Create two lists representing the start/end dates of each month between start/end year, inclusive.
        
        @param start_year: (int) the first year in range
        @param end_year: (int) the last yaer in range
        
        returns ([str]), ([str]): two lists -- the first is a list of start dates, the second is corresponding end
                                dates. The format is YYYY-MM-DD.
    '''
    monthly_date_ranges = [
        ('01-01', '01-31'),
        ('02-01', '02-28'),
        ('03-01', '03-31'),
        ('04-01', '04-30'),
        ('05-01', '05-31'),
        ('06-01', '06-30'),
        ('07-01', '07-31'),
        ('08-01', '08-31'),
        ('09-01', '09-30'),
        ('10-01', '10-31'),
        ('11-01', '11-30'),
        ('12-01', '12-31')
    ]

    years = [str(x) for x in range(start_year, (end_year + 1))]
    monthly_start_dates = []
    monthly_end_dates = []
    # Create start/end dates for each month
    for year in years:
        for date_range in monthly_date_ranges:
            monthly_start_dates.append(year + '-' + date_range[0])
            monthly_end_dates.append(year + '-' + date_range[1])
                                   
    return monthly_start_dates, monthly_end_dates