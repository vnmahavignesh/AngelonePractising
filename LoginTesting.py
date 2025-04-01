import os
import pyotp
import pandas as pd
import requests
from dotenv import load_dotenv
from SmartApi.smartConnect import SmartConnect
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class CredentialsManager:
    """Handles loading and managing credentials from environment variables"""

    def __init__(self):
        load_dotenv()  # Load environment variables from .env file

    def get_api_key(self) -> str:
        return os.getenv('API_KEY')

    def get_username(self) -> str:
        return os.getenv('USERNAME')

    def get_pin(self) -> str:
        return os.getenv('PIN')

    def get_totp_token(self) -> str:
        return os.getenv('TOTP_TOKEN')


class Authenticator(ABC):
    """Abstract base class for authentication"""

    @abstractmethod
    def authenticate(self) -> Dict[str, Any]:
        pass


class SmartApiAuthenticator(Authenticator):
    """Concrete implementation for Smart API authentication"""

    def __init__(self, credentials_manager: CredentialsManager):
        self.credentials = credentials_manager
        self.smart_connect = None

    def generate_totp(self) -> str:
        """Generate Time-based One-Time Password"""
        return pyotp.TOTP(self.credentials.get_totp_token()).now()

    def authenticate(self) -> Dict[str, Any]:
        """Authenticate with Smart API"""
        try:
            api_key = self.credentials.get_api_key()
            username = self.credentials.get_username()
            pin = self.credentials.get_pin()
            totp = self.generate_totp()

            self.smart_connect = SmartConnect(api_key)
            session_data = self.smart_connect.generateSession(
                username, pin, totp)

            return {
                'status': 'success',
                'data': session_data,
                'message': 'Authentication successful',
                'connection': self.smart_connect  # Return the connection object
            }
        except Exception as e:
            return {
                'status': 'error',
                'data': None,
                'message': str(e),
                'connection': None
            }


class SessionDataHandler:
    """Handles processing and formatting of session data"""

    @staticmethod
    def to_dataframe(session_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert session data to pandas DataFrame"""
        return pd.DataFrame([session_data['data']]) if session_data['status'] == 'success' else pd.DataFrame()

    @staticmethod
    def get_token(session_data: Dict[str, Any], token_name: str) -> Optional[str]:
        """Extract specified token from session data"""
        if session_data['status'] == 'success':
            return session_data['data'].get(token_name)
        return None

    @staticmethod
    def display(session_data: Dict[str, Any]) -> None:
        """Display session data in a user-friendly format"""
        if session_data['status'] == 'success':
            df = SessionDataHandler.to_dataframe(session_data)
            print("Authentication Successful!")
            print(df)
        else:
            print(f"Authentication Failed: {session_data['message']}")


class OrderManager:
    """Handles order placement and management"""

    def __init__(self, smart_connect: SmartConnect):
        self.smart_connect = smart_connect

    def place_order(self, order_params: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order and return both order ID and full response"""
        try:
            # SmartConnect.placeOrder
            # order_id = self.smart_connect.placeOrder(order_params)
            full_response = self.smart_connect.placeOrderFullResponse(
                order_params)

            return {
                'status': 'success',
                # 'order_id': order_id,
                'full_response': full_response,
                'message': 'Order placed successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'order_id': None,
                'full_response': None,
                'message': str(e)
            }


class DataManager:
    """Handles market data fetching operations"""

    def __init__(self, smart_connect: SmartConnect):
        self.smart_connect = smart_connect

    def get_historical_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """Fetch historical candle data and return as DataFrame

        Args:
            params: Dictionary containing historical data parameters:
                - exchange: Exchange name (NSE, NFO, etc.)
                - symboltoken: Token of the instrument
                - interval: Time interval (ONE_MINUTE, FIVE_MINUTE, etc.)
                - fromdate: Start datetime (YYYY-MM-DD HH:MM)
                - todate: End datetime (YYYY-MM-DD HH:MM)

        Returns:
            pd.DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        try:
            res = self.smart_connect.getCandleData(params)

            if not res or 'data' not in res:
                return pd.DataFrame()

            hist_df = pd.DataFrame(
                res['data'],
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )

            # Convert timestamp to datetime (uncomment if needed)
            hist_df['timestamp'] = pd.to_datetime(
                hist_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')

            return hist_df

        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()


class MasterList:
    """Handles fetching and processing of instrument master list"""

    def __init__(self):
        pass  # No URL stored in initialization

    def fetch_master_list(self, url: str) -> pd.DataFrame:
        """Fetch and process the master list of instruments from given URL"""
        try:
            print(f"\nFetching master list from {url}")
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for bad status codes

            data = response.json()
            token_df = pd.DataFrame.from_dict(data)

            # Process the data
            token_df['expiry'] = pd.to_datetime(
                token_df['expiry'], format='mixed').apply(lambda x: x.date())
            token_df = token_df.astype({'strike': 'float64'})

            # Convert strike to float and then to int if it's a whole number
            token_df['strike'] = pd.to_numeric(
                token_df['strike'], errors='coerce')
            token_df['strike'] = token_df['strike'].apply(
                lambda x: int(x) if not pd.isna(x) and x.is_integer() else x
            )

            # Instead of converting to datetime, keep as string
            token_df['expiry'] = token_df['expiry'].astype(str)

            return token_df

        except Exception as e:
            print(f"Error fetching master list: {str(e)}")

            return None


class OptionGreeksManager:
    """Handles fetching and processing of option Greeks data"""
    
    def __init__(self, smart_connect: SmartConnect):
        self.smart_connect = smart_connect
        
    def get_option_greeks(self, params: Dict[str, Any]) -> pd.DataFrame:
        """Fetch option Greeks data and return as DataFrame"""
        try:
            response = self.smart_connect.optionGreek(params)
            
            if not response or 'data' not in response:
                return pd.DataFrame()
                
            response_df = pd.DataFrame(response['data'])
            
            # Conversion dictionary: column -> (type, is_percentage)
            column_conversions = {
                'strikePrice': ('int', False),
                'delta': ('float', False),
                'gamma': ('float', False),
                'theta': ('float', False),
                'vega': ('float', False),
                'impliedVolatility': ('float', False),
                'tradeVolume': ('int', False),
                # 'expiry': ('date', '%d%b%Y')
            }
            
            for column, (conv_type, *args) in column_conversions.items():
                if column in response_df.columns:
                    try:
                        if conv_type == 'int':
                            # Convert to numeric first, then multiply by 100 for strikePrice
                            if column == 'strikePrice':
                                response_df[column] = (pd.to_numeric(response_df[column], errors='coerce')
                                                     .fillna(0)
                                                     .astype(float)  # Convert to float first to handle large numbers
                                                     .mul(100)
                                                     .astype(int))
                            else:
                                response_df[column] = pd.to_numeric(response_df[column], errors='coerce').fillna(0).astype(int)
                        elif conv_type == 'float':
                            response_df[column] = pd.to_numeric(response_df[column], errors='coerce').fillna(0.0).astype(float)
                        # elif conv_type == 'date' and args:
                        #     response_df[column] = pd.to_datetime(
                        #         response_df[column], 
                        #         format=args[0]
                        #     ).dt.strftime('%d-%m-%Y')
                    except Exception as e:
                        print(f"Error converting column {column}: {str(e)}")
                        continue
            
            return response_df
            
        except Exception as e:
            print(f"Error processing option Greeks: {str(e)}")
            return pd.DataFrame()


class LoginManager:
    """Main class to coordinate the login process"""

    def __init__(self):
        self.credentials_manager = CredentialsManager()
        self.authenticator = SmartApiAuthenticator(self.credentials_manager)
        self.order_manager = None
        self.data_manager = None
        self.master_list_manager = None
        self.option_greeks_manager = None

    def login(self) -> Dict[str, Any]:
        """Execute the login process and return session data"""
        session_data = self.authenticator.authenticate()

        if session_data['status'] == 'success' and session_data['connection']:
            self.order_manager = OrderManager(session_data['connection'])
            self.data_manager = DataManager(session_data['connection'])
            self.master_list_manager = MasterList()  # Initialize without URL
            self.option_greeks_manager = OptionGreeksManager(
                session_data['connection'])  # Add this line

        return session_data

    def get_order_manager(self) -> Optional[OrderManager]:
        """Get the order manager instance if authenticated"""
        return self.order_manager

    def get_data_manager(self) -> Optional[DataManager]:
        """Get the data manager instance if authenticated"""
        return self.data_manager

    def get_master_list_manager(self) -> Optional[MasterList]:
        """Get the master list manager instance if authenticated"""
        return self.master_list_manager

    # Add this new method
    def get_option_greeks_manager(self) -> Optional[OptionGreeksManager]:
        """Get the option Greeks manager instance if authenticated"""
        return self.option_greeks_manager
