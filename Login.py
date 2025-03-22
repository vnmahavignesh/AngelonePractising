import os
import json
import pyotp
from SmartApi.smartConnect import SmartConnect

class LoginManager:
    CREDENTIAL_FILE = "angelone_login_credential.json"

    def __init__(self):
        self.credentials = self._load_or_create_credentials()
        self.smart_connect_obj = None
        self.refresh_token = None

    def _load_or_create_credentials(self):
        try:
            # Try to load credentials from the file
            with open(self.CREDENTIAL_FILE, "r") as f:
                credentials = json.load(f)
            # Ensure all required keys are present
            required_keys = ["api_key", "username", "pin", "totp_key"]
            for key in required_keys:
                if key not in credentials:
                    raise KeyError(f"Missing key in credentials: {key}")
        except (FileNotFoundError, KeyError):
            # If the file doesn't exist or keys are missing, prompt the user for credentials
            print("-----Enter your Login Credentials-----")
            credentials = {
                "api_key": str(input("Enter Your API Key: ")).strip(),
                "username": str(input("Enter Your Username: ")).strip(),
                "pin": str(input("Enter Your PIN: ")).strip(),
                "totp_key": str(input("Enter Your TOTP Key: ")).strip()
            }
            # Ask the user if they want to save the credentials
            if input("Press Y to save Login Credential and any key to bypass: ").upper() == 'Y':
                with open(self.CREDENTIAL_FILE, "w") as f:
                    json.dump(credentials, f)
                print(f"'{self.CREDENTIAL_FILE}' saved successfully")
            else:
                print(f"'{self.CREDENTIAL_FILE}' Cancelled!!!!!")
        return credentials

    def login(self):
        try:
            self.smart_connect_obj = SmartConnect(api_key=self.credentials["api_key"])
            data = self.smart_connect_obj.generateSession(
                self.credentials["username"],
                self.credentials["pin"],
                pyotp.TOTP(self.credentials["totp_key"]).now()            
            )

            if 'data' not in data:
                raise Exception("Failed to generate session. Response: " + str(data))

            self.refresh_token = data['data']['refreshToken']
            res = self.smart_connect_obj.getProfile(self.refresh_token)
            print('------------Login Successful------------')
            print(res)           
            return True  # Login successful
        except Exception as e:
            print(f"Error: {e}")
            return False  # Login failed

    def get_smart_connect_obj(self):
        return self.smart_connect_obj

    def get_refresh_token(self):
        return self.refresh_token