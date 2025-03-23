import pandas as pd
import requests
from datetime import date, datetime
import logging
from Login import LoginManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
            logging.error("Login required. Please initialize the Symbols.")
            return None

        url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
        logging.info(f"Fetching master list from {url}")
        d = requests.get(url).json()
        token_df = pd.DataFrame.from_dict(d)
        token_df['expiry'] = pd.to_datetime(
            token_df['expiry'], format='mixed').apply(lambda x: x.date())
        token_df = token_df.astype({'strike': 'float64'})
        return token_df[(token_df['exch_seg'].isin(['NFO', 'NSE', 'MCX']))]

    def get_historic_data(self, exchange, symboltoken, interval, fromdate, todate):
        if self.smart_connect_obj is None:
            logging.error("Login required. Please initialize the Symbols.")
            return None, None

        historicParam = {
            "exchange": exchange,
            "symboltoken": symboltoken,
            "interval": interval,
            "fromdate": fromdate,
            "todate": todate
        }

        res = self.smart_connect_obj.getCandleData(historicParam)
        if res and 'data' in res:
            historic_data = pd.DataFrame(res['data'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return historicParam, historic_data
        else:
            logging.error("Failed to fetch historical data.")
            return historicParam, None

    @staticmethod
    def get_previous_day_close(historic_data):
        """Helper function to fetch the previous day's close price."""
        if historic_data is None or historic_data.empty:
            logging.warning("No historical data available.")
            return None

        try:
            previous_day_close = historic_data['close'].iloc[-1]  # Get the last close price
            logging.info(f"Previous day's close: {previous_day_close}")
            return previous_day_close
        except Exception as e:
            logging.error(f"Error fetching previous day's close: {e}")
            return None

    @staticmethod
    def round_to_nearest_100(value):
        """Helper function to round a value to the nearest 100."""
        if value is None:
            return None
        return round(value / 100) * 100
    
    @staticmethod
    def generate_levels(rounded_close, levels=2):
        """
        Generate levels above and below the rounded_close value.
        :param rounded_close: The base value (e.g., 23400).
        :param levels: Number of levels above and below to generate (default is 2).
        :return: List of levels (e.g., [23200, 23300, 23400, 23500, 23600]).
        """
        if rounded_close is None:
            return []

        base = rounded_close
        result = [base + (i * 100) for i in range(-levels, levels + 1)]
        return sorted([level * 100 for level in result])  # Multiply each level by 100
    
    def fetch_symbols_for_levels(self, master_list, levels,expiry_date):
        """
        Fetch symbols, tokens, and exch_seg for the generated levels.
        :param master_list: DataFrame containing the master list of symbols.
        :param levels: List of levels for which symbols need to be fetched.
        :return: DataFrame with symbols, tokens, and exch_seg for the levels.
        """
        if master_list is None or levels is None:
            logging.error("Master list or levels are not provided.")
            return None

        # Ensure the 'expiry' column is in datetime format
        master_list['expiry'] = pd.to_datetime(master_list['expiry'])

        # Filter for the specific expiry date (2025-03-27)
        specific_expiry_df = master_list[master_list['expiry'] == pd.Timestamp(expiry_date)]

        # Further filter the master list based on the levels
        filtered_df = specific_expiry_df[(specific_expiry_df['strike'].isin(levels)) & (specific_expiry_df['name'] == 'NIFTY')]
        return filtered_df[['symbol', 'token', 'exch_seg']]



# Execution starts here
if __name__ == "__main__":
    fetcher = Symbols()
    if fetcher.initialize():
        master_list = fetcher.fetch_master_list()
        logging.info("Master list fetched successfully.")

        # Example usage of get_historic_data
        exchange = "NSE"
        symboltoken = "99926000"
        interval = "ONE_DAY"
        fromdate = "2025-03-01 09:15"
        todate = datetime.now().strftime("%Y-%m-%d %H:%M")  # Current date and time

        historicParam, historic_data = fetcher.get_historic_data(exchange, symboltoken, interval, fromdate, todate)
        if historic_data is not None:
            logging.info("Historical data fetched successfully.")

            # Fetch the previous day's close price
            previous_day_close = fetcher.get_previous_day_close(historic_data)
            if previous_day_close is not None:
                rounded_close = fetcher.round_to_nearest_100(previous_day_close)
                logging.info(f"Rounded to nearest 100: {rounded_close}")

                # Generate levels above and below the rounded_close
                levels = fetcher.generate_levels(rounded_close)
                logging.info(f"Levels around {rounded_close}: {levels}")

                # Define the specific expiry date (e.g., March 27, 2025)
                expiry_date = date(2025, 3, 27)

                # Fetch symbols, tokens, and exch_seg for the generated levels with the specific expiry date
                symbols_for_levels = fetcher.fetch_symbols_for_levels(master_list, levels, expiry_date)
                if symbols_for_levels is not None:
                    logging.info(f"Symbols for levels: {symbols_for_levels}")
                    # Access the symbols, tokens, and exch_seg in the main method
                    for index, row in symbols_for_levels.iterrows():
                        symbol = row['symbol']
                        token = row['token']
                        exch_seg = row['exch_seg']
                        logging.info(f"Symbol: {symbol}, Token: {token}, Exchange Segment: {exch_seg}")
    else:
        logging.error("Failed to initialize Symbols. Please check your credentials.")