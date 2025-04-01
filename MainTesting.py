from LoginTesting import LoginManager, SessionDataHandler

# Global variables to store the data
global_session_data = None
global_hist_data = None
global_master_list = None
global_order_response = None
global_option_greeks = None 


def main():
    global global_session_data, global_hist_data, global_master_list,global_order_response, global_option_greeks

    # Define the master list URL
    master_list_url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'

    # Initialize and login
    login_manager = LoginManager()
    global_session_data = login_manager.login()
    SessionDataHandler.display(global_session_data)

    # Token extraction and display
    if global_session_data['status'] == 'success':
        jwt_token = SessionDataHandler.get_token(
            global_session_data, 'data').get('jwtToken')
        feed_token = SessionDataHandler.get_token(
            global_session_data, 'data').get('feedToken')
        refresh_token = SessionDataHandler.get_token(
            global_session_data, 'data').get('refreshToken')

        print(f"\nJwtToken: {jwt_token}")
        print(f"\nRefreshToken: {refresh_token}")
        print(f"\nFeedToken: {feed_token}")

    # Fetch and display master list with URL passed directly
    master_list_manager = login_manager.get_master_list_manager()
    if master_list_manager:
        global_master_list = master_list_manager.fetch_master_list(
            master_list_url)  # Assign to global variable
        if global_master_list is not None:
            print("\nMaster List:")
            print(global_master_list)
        else:
            print("\nFailed to fetch master list")
    else:
        print("\nMaster list manager not available")

    # Example: Fetch historical data
    if global_session_data['status'] == 'success':
        data_manager = login_manager.get_data_manager()
        if data_manager:
            historic_param = {
                "exchange": "NFO",
                "symboltoken": "54683",
                "interval": "ONE_MINUTE",
                "fromdate": "2025-03-28 09:15",
                "todate": "2025-04-01 15:30"
            }
            global_hist_data = data_manager.get_historical_data(historic_param)
            print("\nHistorical Data:")
            print(global_hist_data)
        else:
            print("\nFailed to fetch historic data")

    else:
        print("\nHistoric Data is not available")

    # Add option Greeks example For daily data
    if global_session_data['status'] == 'success':
        option_greeks_manager = login_manager.get_option_greeks_manager()
        if option_greeks_manager:
            option_greeks_params = {
                "name": "NIFTY",
                "expirydate": "03APR2025"
            }
            global_option_greeks = option_greeks_manager.get_option_greeks(option_greeks_params)
            print("\nOption Greeks Data:")
            print(global_option_greeks)
        else:
            print("\nOption Greeks manager not available")
    else:
        print("\nOption Greeks data is not available")
    
    # # Order placement (kept within main as requested)
    # if global_session_data['status'] == 'success' and global_session_data['connection']:
    #     try:
    #         order_params = {
    #             "variety": "NORMAL",
    #             "tradingsymbol": "SBIN-EQ",
    #             "symboltoken": "3045",
    #             "transactiontype": "SELL",
    #             "exchange": "NSE",
    #             "ordertype": "LIMIT",
    #             "producttype": "INTRADAY",
    #             "duration": "DAY",
    #             "price": "19500",
    #             "squareoff": "0",
    #             "stoploss": "35",
    #             "quantity": "3"
    #         }

    #         # Place the order directly using the connection
    #         # order_id = global_session_data['connection'].placeOrder(order_params)
    #         global_order_response = global_session_data['connection'].placeOrderFullResponse(
    #             order_params)     

    #         print("\nOrder Placement Successful!")
    #         # print(f"Order ID: {order_id}")
    #         print("Full Response:")
    #         print(global_order_response)

    #     except Exception as e:
    #         print(f"\nOrder Placement Failed: {str(e)}")
    # else:
    #     print("\nNo active connection - cannot place orders")


if __name__ == "__main__":
    main()
