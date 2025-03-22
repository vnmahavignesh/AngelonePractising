import pandas as pd
import requests
from datetime import date, datetime
import time
from Login import LoginManager
import matplotlib.pyplot as plt

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
        token_df['expiry'] = pd.to_datetime(token_df['expiry'], format='mixed').apply(lambda x: x.date())
        token_df = token_df.astype({'strike': 'float64'})
        token_df = token_df[(token_df['exch_seg'].isin(['NFO'])) & (token_df.name == 'NIFTY') & (token_df.expiry == date(2025, 3, 27))]
        historicParam = self.get_historic_param()
        res = self.smart_connect_obj.getCandleData(historicParam)
        histDf = pd.DataFrame(res['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return histDf

    def get_historic_param(self):
        return {
            "exchange": "NFO",
            "symboltoken": "51120",
            "interval": "ONE_MINUTE",
            "fromdate": "2025-03-21 09:15",
            "todate": "2025-03-21 15:30"
        }

    def plot_ohlc_data(self, histDf):
        if histDf is None or histDf.empty:
            print("No data to plot.")
            return
        print(master_list)
        plt.figure(figsize=(14, 7))
        plt.plot(histDf['timestamp'], histDf['close'], label='Close Price', color='blue')
        plt.title('1min Historical OHLC Data')
        plt.xlabel('Timestamp')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()

# Example usage
if __name__ == "__main__":
    fetcher = Symbols()
    if fetcher.initialize():
        master_list = fetcher.fetch_master_list()
        if master_list is not None:
            fetcher.plot_ohlc_data(master_list)
    else:
        print("Failed to initialize Symbols. Please check your credentials.")