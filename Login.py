import os
import pyotp
import pandas as pd
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
            session_data = self.smart_connect.generateSession(username, pin, totp)

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
            full_response = self.smart_connect.placeOrderFullResponse(order_params)
            
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


class LoginManager:
    """Main class to coordinate the login process"""

    def __init__(self):
        self.credentials_manager = CredentialsManager()
        self.authenticator = SmartApiAuthenticator(self.credentials_manager)
        self.order_manager = None

    def login(self) -> Dict[str, Any]:
        """Execute the login process and return session data"""
        session_data = self.authenticator.authenticate()
        
        if session_data['status'] == 'success' and session_data['connection']:
            self.order_manager = OrderManager(session_data['connection'])
        
        return session_data
    
    def get_order_manager(self) -> Optional[OrderManager]:
        """Get the order manager instance if authenticated"""
        return self.order_manager