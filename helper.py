import numpy as np
import sys

from zipline.assets._assets import Equity  # Required for USEquityPricing
from zipline.pipeline.data import USEquityPricing
from zipline.pipeline.classifiers import Classifier
from zipline.pipeline.engine import SimplePipelineEngine
from zipline.pipeline.loaders import USEquityPricingLoader
from zipline.utils.numpy_utils import int64_dtype


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
