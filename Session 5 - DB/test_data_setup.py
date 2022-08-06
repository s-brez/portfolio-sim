"""
    Tables:
     - "price" - time series price data
     - "portfolio" - portfolio results
     - "strategy" - strategy results
"""

"""
    Startup workflow:
     - Connect to postgres server.
     - Check tables and indexing are set up. Set up if not.
     - Check what data is stored locally. If required data not present, fetch and store it.
     - If newer data available, fetch and store the new data.
"""