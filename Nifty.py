import pandas as pd
import requests
from datetime import date
import matplotlib.pyplot as plt
from collections import namedtuple
from Login import LoginManager

# Define a namedtuple for the return type
HistoricData = namedtuple(
    "HistoricData", ["historicParam", "symbol_value", "historic_data"])


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

    def get_historic_param(self, token_df):
        """
        This method takes token_df as an argument and returns a namedtuple containing:
        - historicParam: The original parameters used for the API call.
        - symbol_value: The symbol name extracted from token_df.
        - historic_data: The DataFrame containing OHLC data.
        """
        historicParam = {
            "exchange": "NFO",
            "symboltoken": "51120",
            "interval": "ONE_MINUTE",
            "fromdate": "2025-03-21 09:15",
            "todate": "2025-03-21 15:30"
        }

        # Print the symboltoken value
        print(f"Symbol Token: {historicParam['symboltoken']}")

        # Extract the symboltoken from historicParam
        symboltoken_value = historicParam["symboltoken"]
        print(f"Symbol Token from historicParam: {symboltoken_value}")

        # Search for the symboltoken in token_df's 'token' column
        matching_row = token_df[token_df['token'] == symboltoken_value]

        if not matching_row.empty:
            # Extract the 'symbol' value from the matching row
            symbol_value = matching_row.iloc[0]['symbol']
            print(f"Matching Symbol in token_df: {symbol_value}")
        else:
            print(f"No matching symbol found for token: {symboltoken_value}")
            symbol_value = None

        # Fetch OHLC data
        res = self.smart_connect_obj.getCandleData(historicParam)
        historic_data = pd.DataFrame(
            res['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        # Return all values as a namedtuple
        return HistoricData(historicParam, symbol_value, historic_data)

    def plot_ohlc_data(self, historicParam, symbol_value, historic_data):
        """
        This method plots the OHLC data.
        """
        if historic_data is None or historic_data.empty:
            print("No data to plot.")
            return

        fromDate = historicParam['fromdate']
        toDate = historicParam['todate']
        interval = historicParam['interval']
        symboltoken = historicParam['symboltoken']

        # Map interval to its corresponding value
        interval_map = {
            "ONE_MINUTE": "1min",
            "THREE_MINUTE": "3min",
            "FIVE_MINUTE": "5min",
            "TEN_MINUTE": "10min",
            "FIFTEEN_MINUTE": "15min",
            "THIRTY_MINUTE": "30min",
            "ONE_HOUR": "1H",
            "ONE_DAY": "1D"
        }

        # Default to the original interval if not found
        interval_value = interval_map.get(interval, interval)

        plt.figure(figsize=(14, 7))
        plt.plot(historic_data['timestamp'], historic_data['close'],
                 label='Close Price', color='blue')
        plt.title(
            f'{interval_value} OHLC - {symbol_value}:{symboltoken} - {fromDate} to {toDate}')
        plt.xlabel('Timestamp')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.show()


# Execution starts here
if __name__ == "__main__":
    fetcher = Symbols()
    if fetcher.initialize():
        master_list = fetcher.fetch_master_list()
        print(master_list)

        # Example of using the get_historic_param method
        if master_list is not None:
            result = fetcher.get_historic_param(master_list)
            print("Historic Parameters:", result.historicParam)
            print("Symbol Value:", result.symbol_value)
            print("Historic Data:", result.historic_data)

            # Pass the required values to plot_ohlc_data
            fetcher.plot_ohlc_data(result.historicParam,
                                   result.symbol_value, result.historic_data)
    else:
        print("Failed to initialize Symbols. Please check your credentials.")
