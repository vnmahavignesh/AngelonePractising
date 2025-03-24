import logging
import pandas as pd
import requests
import time
from datetime import date,datetime
import matplotlib.pyplot as plt
from collections import namedtuple
from Login import LoginManager

class Symbols:
    def __init__(self):
        self.login_manager = LoginManager()
        self.smart_connect_obj = None
        self.refresh_token = None

    def initialize(self):
        if self.login_manager.login():
            self.smart_connect_obj = self.login_manager.get_smart_connect_obj()
            self.refresh_token = self.login_manager.get_refresh_token()
            return True
        return False

    def fetch_master_list(self):
        if self.smart_connect_obj is None:
            print("Login required. Please initialize the Symbols.")
            return None

        url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
        print(f"Fetching master list from {url}")
        d = requests.get(url).json()
        token_df = pd.DataFrame.from_dict(d)
        token_df['expiry'] = pd.to_datetime(
            token_df['expiry'], format='mixed').apply(lambda x: x.date())
        token_df = token_df.astype({'strike': 'float64'})
        return token_df[(token_df['exch_seg'].isin(['NFO', 'NSE', 'MCX']))]

    def get_live_data(self, token):
        if self.smart_connect_obj is None:
            logging.error("Login required. Please initialize the Symbols.")
            return None

        exchangeTokens = {
            "NSE": [str(token)],
            "NFO": []
        }

        res = self.smart_connect_obj.getMarketData("FULL", exchangeTokens)
        if res and 'data' in res:
            live_data = res['data']
            logging.info(f"Live data fetched successfully for token {token}: {live_data}")
            return live_data
        else:
            logging.error(f"Failed to fetch live data for token {token}")
            return None

# Execution starts here
if __name__ == "__main__":
    fetcher = Symbols()
    if fetcher.initialize():
        master_list = fetcher.fetch_master_list()
        print(master_list)
        
        # Example usage of get_live_data
        manual_token = 99926000  # Example token
        interval = 60  # Interval in seconds (1 minute)
        live_data = fetcher.get_live_data(manual_token)
        try:
            while True:
                live_data = fetcher.get_live_data(manual_token)
                if live_data is not None:
                     print(f"Live Data for Token {manual_token} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:")
                     print(live_data)
                else:
                    logging.error(f"Failed to fetch live data for token {manual_token}.")

                time.sleep(interval)  # Wait for the specified interval
        except KeyboardInterrupt:
            logging.info("Polling stopped by user.")
    else:
        print("Failed to initialize Symbols. Please check your credentials.")