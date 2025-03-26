from Login import LoginManager, SessionDataHandler

def main():
    # Initialize and login
    login_manager = LoginManager()
    session_data = login_manager.login()
    SessionDataHandler.display(session_data)    

    # Token extraction and display
    if session_data['status'] == 'success':
        jwt_token = SessionDataHandler.get_token(session_data, 'data').get('jwtToken')
        feed_token = SessionDataHandler.get_token(session_data, 'data').get('feedToken')
        refresh_token = SessionDataHandler.get_token(session_data, 'data').get('refreshToken')
        
        # print(f"\njwtToken: {jwt_token}")
        # print(f"refreshToken: {refresh_token}")
        # print(f"feedToken: {feed_token}")

        # Order placement (kept within main as requested)
        if session_data['connection']:
            try:
                order_params = {
                    "variety": "NORMAL",
                    "tradingsymbol": "SBIN-EQ",
                    "symboltoken": "3045",
                    "transactiontype": "SELL",
                    "exchange": "NSE",
                    "ordertype": "LIMIT",
                    "producttype": "INTRADAY",
                    "duration": "DAY",
                    "price": "19500",
                    "squareoff": "0",
                    "stoploss": "35",
                    "quantity": "15"
                }
                
                # Place the order directly using the connection
                # order_id = session_data['connection'].placeOrder(order_params)
                full_response = session_data['connection'].placeOrderFullResponse(order_params)
                
                print("\nOrder Placement Successful!")
                # print(f"Order ID: {order_id}")
                print("Full Response:")
                print(full_response)
                
            except Exception as e:
                print(f"\nOrder Placement Failed: {str(e)}")
        else:
            print("\nNo active connection - cannot place orders")
    else:
        print("\nCannot place orders - authentication failed")

if __name__ == "__main__":
    main()