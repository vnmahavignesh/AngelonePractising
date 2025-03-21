import os
import json
import pyotp
from SmartApi.smartConnect import SmartConnect

# File to store credentials
CREDENTIAL_FILE = "angelone_login_credential.json"

# Function to load or create credentials
def load_or_create_credentials():
    try:
        # Try to load credentials from the file
        with open(CREDENTIAL_FILE, "r") as f:
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
            with open(CREDENTIAL_FILE, "w") as f:
                json.dump(credentials, f)
            print(f"'{CREDENTIAL_FILE}' saved successfully")
        else:
            print(f"'{CREDENTIAL_FILE}' Cancelled!!!!!")
    return credentials

# Load or create credentials
credentials = load_or_create_credentials()

# Extract credentials
apikey = credentials["api_key"]
username = credentials["username"]
pin = credentials["pin"]
totp_key = credentials["totp_key"]

# Initialize SmartConnect and generate session
try:
    obj = SmartConnect(api_key=apikey)
    data = obj.generateSession(username, pin, pyotp.TOTP(totp_key).now())

    if 'data' not in data:
        raise Exception("Failed to generate session. Response: " + str(data))

    refreshToken = data['data']['refreshToken']
    res = obj.getProfile(refreshToken)
    print(res)

except Exception as e:
    print(f"Error: {e}")