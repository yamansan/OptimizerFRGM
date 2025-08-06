#!/usr/bin/env python
"""
Live Position Monitor for Trading Technologies REST API.
Retrieves current positions using the ttmonitor service.
"""

import os
import sys
import json
import requests
from datetime import datetime
import argparse

# Add the lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

try:
    from trading.tt_api import (
        TTTokenManager, 
        TT_API_KEY, TT_API_SECRET, TT_SIM_API_KEY, TT_SIM_API_SECRET,
        APP_NAME, COMPANY_NAME, ENVIRONMENT, TOKEN_FILE
    )
    print("Successfully imported TT API tools")
except ImportError as e:
    print(f"Error importing TT API tools: {e}")
    sys.exit(1)

# Constants
TT_API_BASE_URL = "https://ttrestapi.trade.tt"

def get_positions(token_manager, account_id=None):
    """
    Retrieve current positions from TT API.
    
    Args:
        token_manager: TTTokenManager instance
        account_id (str, optional): Specific account ID to filter positions
        
    Returns:
        dict: API response containing position data
    """
    try:
        # Build API request URL
        service = "ttmonitor"
        if account_id:
            endpoint = f"/position/{account_id}"
        else:
            endpoint = "/position"
        
        url = f"{TT_API_BASE_URL}/{service}/{token_manager.env_path_segment}{endpoint}"
        
        # Create request parameters
        request_id = token_manager.create_request_id()
        params = {"requestId": request_id}
        
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token_manager.get_token()}"
        }
        
        print(f"Making API request to: {url}")
        
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=30)    
        response.raise_for_status()
        
        # Parse response
        api_response = response.json()
        
        print(f"Response status: {api_response.get('status', 'Unknown')}")
        return api_response
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching positions: {e}")
        return None

def get_instrument_info(instrument_id, token_manager):
    """Get instrument info including name and market ID."""
    try:
        url = f"{TT_API_BASE_URL}/ttpds/{token_manager.env_path_segment}/instrument/{instrument_id}"
        request_id = token_manager.create_request_id()
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token_manager.get_token()}"
        }
        params = {"requestId": request_id}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            instrument_data = data.get('instrument', [{}])[0]
            return {
                'alias': instrument_data.get('alias', f'Unknown_{instrument_id}'),
                'marketId': instrument_data.get('marketId', None)
            }
    except Exception as e:
        print(f"Failed to get instrument info for {instrument_id}: {e}")
    
    return {'alias': f'Unknown_{instrument_id}', 'marketId': None}

def get_market_name(market_id, token_manager, cache={}):
    """Get market name from market ID with caching."""
    if market_id in cache:
        return cache[market_id]
    
    try:
        url = f"{TT_API_BASE_URL}/ttpds/{token_manager.env_path_segment}/markets"
        request_id = token_manager.create_request_id()
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token_manager.get_token()}"
        }
        params = {"requestId": request_id}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            markets = {str(market['id']): market['name'] for market in data.get('markets', [])}
            cache.update(markets)
            return cache.get(str(market_id), f'Unknown_Market_{market_id}')
    except Exception as e:
        print(f"Failed to get market info: {e}")
    
    return f'Unknown_Market_{market_id}'

def display_positions(positions_data, token_manager):
    """Display positions in a readable format, filtered for CME exchange only."""
    if not positions_data or positions_data.get('status') != 'Ok':
        print("No valid position data received")
        return
    
    positions = positions_data.get('positions', [])
    if not positions:
        print("No positions found")
        return
    
    # Filter positions for CME exchange only
    cme_positions = []
    for position in positions:
        instrument_id = position.get('instrumentId', '')
        if instrument_id:
            instrument_info = get_instrument_info(instrument_id, token_manager)
            market_id = instrument_info.get('marketId')
            if market_id:
                market_name = get_market_name(market_id, token_manager)
                # Only include CME positions (not CME_Delayed)
                if market_name == 'CME':
                    position['_contract_name'] = instrument_info.get('alias', 'Unknown')
                    position['_market_name'] = market_name
                    cme_positions.append(position)
    
    if not cme_positions:
        print("No CME positions found (filtering out CME_Delayed)")
        return
    
    print(f"\n=== CME Positions Only ({len(cme_positions)} total) ===")
    print(f"{'Contract':<15} {'BuyQty':<10} {'SellQty':<10} {'SOD':<10} {'NetPos':<10} {'P/L':<15} {'Realized P/L':<15} {'Exchange':<10}")
    print("-" * 110)
    
    total_net_position = 0
    zn_sep25_found = False
    
    for position in cme_positions:
        contract_name = position.get('_contract_name', 'Unknown')
        market_name = position.get('_market_name', 'Unknown')
        
        # Extract position data
        buy_qty = position.get('buyFillQty', 0)
        sell_qty = position.get('sellFillQty', 0)
        sod_pos = position.get('sodNetPos', 0)
        net_pos = position.get('netPosition', 0)
        pnl = position.get('pnl', 0)
        realized_pnl = position.get('realizedPnl', 0)
        
        # Check if this is ZN Sep25
        if 'ZN Sep25' in contract_name or 'ZN Sep 25' in contract_name:
            zn_sep25_found = True
            print(f"{contract_name:<15} {buy_qty:<10.0f} {sell_qty:<10.0f} {sod_pos:<10.0f} {net_pos:<10.0f} {pnl:<15.2f} {realized_pnl:<15.2f} {market_name:<10} ⭐")
        else:
            print(f"{contract_name:<15} {buy_qty:<10.0f} {sell_qty:<10.0f} {sod_pos:<10.0f} {net_pos:<10.0f} {pnl:<15.2f} {realized_pnl:<15.2f} {market_name:<10}")
        
        total_net_position += net_pos
    
    print("-" * 110)
    print(f"Total CME net position: {total_net_position}")
    
    if zn_sep25_found:
        print("\n⭐ = ZN Sep25 position found")
    else:
        print("\n⚠️  ZN Sep25 position not found in CME results")

def main():
    """Main function to retrieve and display positions."""
    parser = argparse.ArgumentParser(description='Retrieve live positions from TT API')
    parser.add_argument('--account-id', help='Specific account ID to filter positions')
    parser.add_argument('--json', action='store_true', help='Output raw JSON response')
    
    args = parser.parse_args()
    
    print("=== TT Live Position Monitor ===")
    print(f"Environment: {ENVIRONMENT}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
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
        
        # Get authentication token
        token = token_manager.get_token()
        if not token:
            print("Failed to acquire TT API token.")
            return
            
        print("Token manager initialized successfully")
        
        # Retrieve positions
        positions_data = get_positions(token_manager, args.account_id)
        print("positions_data:", positions_data)
        if args.json:
            # Output raw JSON
            print("\n=== Raw JSON Response ===")
            print(json.dumps(positions_data, indent=2))
        else:
            # Display formatted positions
            display_positions(positions_data, token_manager)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 