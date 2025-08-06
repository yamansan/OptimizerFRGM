import requests
import json
from datetime import datetime
import sys
import os

# Add the workspace root to Python path
workspace_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_root)

from lib.trading.tt_api import (
    TTTokenManager, 
    TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
    APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
)

# Constants
TT_API_BASE_URL = "https://ttrestapi.trade.tt"

def get_working_orders():
    """
    Fetch working orders from TT API and return them as a list.
    
    Returns:
        list: List of working orders or empty list if error
    """
    print(f"Fetching working orders from TT API (Environment: {ENVIRONMENT})")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Initialize token manager
        token_manager = TTTokenManager(
            api_key=TT_SIM_API_KEY if ENVIRONMENT == "SIM" else TT_API_KEY,
            api_secret=TT_SIM_API_SECRET if ENVIRONMENT == "SIM" else TT_API_SECRET,
            app_name=APP_NAME,
            company_name=COMPANY_NAME,
            environment=ENVIRONMENT,
            token_file_base=TOKEN_FILE
        )
        
        # Get token
        token = token_manager.get_token()
        if not token:
            print("ERROR: Failed to acquire TT API token")
            return []
        
        # Build API request
        service = "ttledger"
        endpoint = "/orders"  # Fetches working orders by default
        url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
        
        request_id = token_manager.create_request_id()
        params = {"requestId": request_id}
        
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        print(f"Making API request to: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse response
        api_response = response.json()
        orders_data = api_response.get('orders', [])
        if not orders_data and isinstance(api_response, list):
            orders_data = api_response
        
        # Filter for working orders (status '1') with valid data
        working_orders = []
        for order in orders_data:
            if (isinstance(order, dict) and 
                order.get('orderStatus') == '1' and 
                isinstance(order.get('price'), (int, float)) and 
                isinstance(order.get('leavesQuantity'), (int, float)) and 
                order.get('leavesQuantity') > 0 and 
                order.get('side') in ['1', '2']):
                
                working_orders.append({
                    'price': float(order['price']),
                    'quantity': float(order['leavesQuantity']),
                    'side': 'BUY' if order.get('side') == '1' else 'SELL',
                    'instrument': order.get('instrumentName', 'Unknown'),
                    'orderId': order.get('orderId', ''),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        print(f"Found {len(working_orders)} working orders")
        return working_orders
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
        if http_err.response:
            print(f"Response text: {http_err.response.text}")
        return []
    except Exception as e:
        print(f"Error fetching working orders: {e}")
        return []

def print_working_orders(orders):
    """
    Print working orders in a formatted table.
    
    Args:
        orders (list): List of working order dictionaries
    """
    if not orders:
        print("No working orders found.")
        return
    
    print(f"\n{'='*80}")
    print(f"WORKING ORDERS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    print(f"{'Instrument':<12} {'Side':<4} {'Quantity':<8} {'Price':<12} {'Order ID':<15}")
    print(f"{'-'*80}")
    
    for order in orders:
        print(f"{order['instrument']:<12} {order['side']:<4} {order['quantity']:<8.0f} {order['price']:<12.6f} {order['orderId']:<15}")
    
    print(f"{'-'*80}")
    print(f"Total: {len(orders)} working orders")

if __name__ == "__main__":
    # Fetch and display working orders
    orders = get_working_orders()
    print_working_orders(orders) 