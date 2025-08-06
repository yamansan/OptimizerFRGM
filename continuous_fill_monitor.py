#!/usr/bin/env python
"""
Continuous Fill Monitor for Trading Technologies REST API.
Based on fill_download (1).py but adapted for the existing codebase infrastructure.
Continuously downloads filled orders and maintains them in CSV format.
"""

import os
import sys
import csv
import json
import time
import signal
import logging
import requests
import threading
import pandas as pd
from datetime import datetime, timedelta
from threading import Thread, Lock, Event
import argparse
from config import CONTINUOUS_FILLS_CSV

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
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "output", "ladder")
DEFAULT_POLL_INTERVAL = 60  # seconds between checks
DEFAULT_MAX_RETRIES = 5

# Global state
stop_event = Event()
lock = Lock()
logger = logging.getLogger(__name__)

# Global caches for performance
market_enums_cache = {}
user_info_cache = {}

def setup_logging(log_to_file=True, log_to_console=True):
    """Setup logging configuration."""
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = logging.Formatter(fmt=log_format)
    
    # Set up root logger
    logger.setLevel(logging.INFO)
    
    if log_to_file:
        # Create logs directory
        log_dir = os.path.join(OUTPUT_DIR, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        log_file = os.path.join(log_dir, f"fill_monitor_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    
    if log_to_console:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

def signal_handler(signum, frame):
    """Handle interrupt signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    stop_event.set()

def convert_tt_timestamp_to_readable(timestamp_ns):
    """Convert TT nanosecond timestamp to readable format."""
    if not timestamp_ns:
        return None, None
    
    try:
        # Convert nanoseconds to seconds
        seconds = int(timestamp_ns) // 1_000_000_000
        # Get milliseconds from remaining nanoseconds
        milliseconds = (int(timestamp_ns) % 1_000_000_000) // 1_000_000
        
        # Create datetime object
        dt = datetime.fromtimestamp(seconds)
        
        # Format date and time
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H:%M:%S') + f'.{milliseconds:03d}'
        
        return date_str, time_str
    except (ValueError, TypeError):
        return None, None

def get_instrument_name(instrument_id, token_manager, cache={}):
    """Get instrument name from ID with caching."""
    if instrument_id in cache:
        return cache[instrument_id]
    
    try:
        url = f"{TT_API_BASE_URL}/ttpds/{token_manager.env_path_segment}/instrument/{instrument_id}"
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token_manager.get_token()}"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            name = data.get('instrument', [{}])[0].get('alias', f'Unknown_{instrument_id}')
            cache[instrument_id] = name
            return name
    except Exception as e:
        logger.warning(f"Failed to get instrument name for {instrument_id}: {e}")
    
    cache[instrument_id] = f'Unknown_{instrument_id}'
    return cache[instrument_id]

def get_market_enums(token_manager):
    """Get market enums with caching."""
    global market_enums_cache
    
    if market_enums_cache:
        return market_enums_cache
    
    try:
        # Get market names
        markets_url = f"{TT_API_BASE_URL}/ttpds/{token_manager.env_path_segment}/markets"
        request_id = token_manager.create_request_id()
        headers = {
            "x-api-key": token_manager.api_key,
            "accept": "application/json",
            "Authorization": f"Bearer {token_manager.get_token()}"
        }
        params = {"requestId": request_id}
        
        response = requests.get(markets_url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_enums_cache['markets'] = {str(info['id']): info['name'] for info in data.get('markets', [])}
            logger.info("Successfully loaded market enums")
            return market_enums_cache
    except Exception as e:
        logger.warning(f"Failed to get market enums: {e}")
        market_enums_cache['markets'] = {}
    
    return market_enums_cache

def get_user_info(user_id, token_manager):
    """Get user info with caching."""
    global user_info_cache
    
    if user_id in user_info_cache:
        return user_info_cache[user_id]
    
    if not user_id or user_id == 0:
        user_info_cache[user_id] = {'alias': '', 'company': {'name': ''}}
        return user_info_cache[user_id]
    
    try:
        url = f"{TT_API_BASE_URL}/ttuser/{token_manager.env_path_segment}/user/{user_id}"
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
            user_data = data.get('user', [{}])[0]
            user_info_cache[user_id] = user_data
            return user_data
    except Exception as e:
        logger.warning(f"Failed to get user info for {user_id}: {e}")
    
    # Fallback data
    user_info_cache[user_id] = {
        'alias': f'user_id:{user_id}',
        'company': {'name': f'user_id:{user_id}'}
    }
    return user_info_cache[user_id]

def get_contract_name(instrument_id, token_manager):
    """Get contract name (alias) from instrument ID."""
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
            return data.get('instrument', [{}])[0].get('alias', f'Unknown_{instrument_id}')
    except Exception as e:
        logger.warning(f"Failed to get contract name for {instrument_id}: {e}")
    
    return f'Unknown_{instrument_id}'

class FillMonitor:
    """Main class for monitoring and processing fills."""
    
    def __init__(self, poll_interval=60, max_retries=5, output_file=None):
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.token_manager = None
        self.last_timestamp = None
        self.csv_file = output_file or CONTINUOUS_FILLS_CSV 
        self.csv_lock = Lock()
        
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Initialize CSV file with headers
        self.init_csv_file()
    
    def init_csv_file(self):
        """Initialize CSV file with headers."""
        headers = [
            'Date', 'Time', 'InstrumentId', 'InstrumentName', 'Side', 'SideName',
            'Quantity', 'Price', 'OrderId', 'AccountId', 'MarketId',
            'TransactTime', 'TimeStamp', 'ExecId', 'OrderStatus',
            'Exchange', 'Contract', 'Originator', 'CurrentUser'
        ]
        
        # Only write headers if file doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            logger.info(f"Initialized CSV file: {self.csv_file}")
        else:
            # Check if existing file has new columns, if not, we need to update it
            try:
                df = pd.read_csv(self.csv_file, nrows=1)
                existing_columns = df.columns.tolist()
                if not all(col in existing_columns for col in ['Exchange', 'Contract', 'Originator', 'CurrentUser']):
                    logger.info("Updating existing CSV file with new columns...")
                    # Read existing data
                    df_full = pd.read_csv(self.csv_file)
                    # Add missing columns with empty values
                    for col in ['Exchange', 'Contract', 'Originator', 'CurrentUser']:
                        if col not in df_full.columns:
                            df_full[col] = ''
                    # Reorder columns to match new header order
                    df_full = df_full[headers]
                    # Write back to file
                    df_full.to_csv(self.csv_file, index=False)
                    logger.info("Successfully updated CSV file with new columns")
            except Exception as e:
                logger.warning(f"Could not update existing CSV file: {e}")
                # If update fails, just continue with current structure
    
    def setup_token_manager(self):
        """Initialize token manager."""
        try:
            self.token_manager = TTTokenManager(
                api_key=TT_SIM_API_KEY if ENVIRONMENT == "SIM" else TT_API_KEY,
                api_secret=TT_SIM_API_SECRET if ENVIRONMENT == "SIM" else TT_API_SECRET,
                app_name=APP_NAME,
                company_name=COMPANY_NAME,
                environment=ENVIRONMENT,
                token_file_base=TOKEN_FILE
            )
            
            # Test token acquisition
            token = self.token_manager.get_token()
            if not token:
                raise Exception("Failed to acquire initial token")
                
            logger.info("Token manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup token manager: {e}")
            return False
    
    def fetch_fills(self, min_timestamp=None):
        """Fetch fills from TT API."""
        try:
            # Build API request
            service = "ttledger"
            endpoint = "/fills"
            url = f"{TT_API_BASE_URL}/{service}/{self.token_manager.env_path_segment}{endpoint}"
            
            # Create request parameters
            request_id = self.token_manager.create_request_id()
            params = {"requestId": request_id}
            
            # Add timestamp filter if specified
            if min_timestamp:
                params["minTimestamp"] = min_timestamp
                logger.debug(f"Fetching fills from timestamp: {min_timestamp}")
            
            headers = {
                "x-api-key": self.token_manager.api_key,
                "accept": "application/json",
                "Authorization": f"Bearer {self.token_manager.get_token()}"
            }
            
            logger.debug(f"Making API request to: {url}")
            
            # Make the API request
            response = requests.get(url, headers=headers, params=params, timeout=30)    
            response.raise_for_status()
            
            # Parse response
            api_response = response.json()
            fills_data = api_response.get('fills', [])
            
            # Handle case where response is directly a list
            if not fills_data and isinstance(api_response, list):
                fills_data = api_response
            
            logger.info(f"Retrieved {len(fills_data)} fills from API")
            return fills_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching fills: {e}")
            return None
    
    def process_fill(self, fill_data):
        """Process a single fill and return formatted data."""
        try:
            # Extract basic data
            timestamp = fill_data.get('timeStamp')
            date_str, time_str = convert_tt_timestamp_to_readable(timestamp)
            
            instrument_id = fill_data.get('instrumentId')
            instrument_name = get_instrument_name(instrument_id, self.token_manager)
            
            side = fill_data.get('side')
            side_name = 'BUY' if side == 1 else 'SELL' if side == 2 else 'UNKNOWN'
            
            # Get additional information
            # Exchange - from market ID
            market_id = fill_data.get('marketId')
            exchange = ''
            if market_id:
                enums = get_market_enums(self.token_manager)
                exchange = enums.get('markets', {}).get(str(market_id), '')
            
            # Contract - from instrument alias
            contract = get_contract_name(instrument_id, self.token_manager) if instrument_id else ''
            
            # Originator - from user ID
            user_id = fill_data.get('userId')
            originator = ''
            if user_id and user_id != 0:
                user_info = get_user_info(user_id, self.token_manager)
                originator = user_info.get('alias', '')
            
            # Current User - from current user ID
            curr_user_id = fill_data.get('currUserId')
            current_user = ''
            if curr_user_id and curr_user_id != 0:
                curr_user_info = get_user_info(curr_user_id, self.token_manager)
                current_user = curr_user_info.get('alias', '')
            
            # Format the row
            row = [
                date_str or '',
                time_str or '',
                instrument_id or '',
                instrument_name or '',
                side or '',
                side_name,
                fill_data.get('lastQty', ''),
                fill_data.get('lastPx', ''),
                fill_data.get('orderId', ''),
                fill_data.get('accountId', ''),
                fill_data.get('marketId', ''),
                fill_data.get('transactTime', ''),
                timestamp or '',
                fill_data.get('execID', ''),
                fill_data.get('ordStatus', ''),
                exchange,
                contract,
                originator,
                current_user
            ]
            
            return row
            
        except Exception as e:
            logger.error(f"Error processing fill: {e}")
            return None
    
    def get_existing_row_hashes(self):
        """Get hashes of existing rows for efficient duplicate checking."""
        existing_hashes = set()
        
        try:
            if os.path.exists(self.csv_file):
                with open(self.csv_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    
                    for row in reader:
                        row_hash = hash(tuple(str(item) for item in row))
                        existing_hashes.add(row_hash)
        
        except Exception as e:
            logger.warning(f"Could not read existing rows for duplicate checking: {e}")
        
        return existing_hashes

    def save_fills_to_csv(self, fills_data):
        """Save fills data to CSV file with duplicate prevention."""
        if not fills_data:
            return 0
        
        try:
            with self.csv_lock:
                # Get existing row hashes for duplicate checking
                existing_row_hashes = self.get_existing_row_hashes()
                
                with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    saved_count = 0
                    for fill in fills_data:
                        row = self.process_fill(fill)
                        if row:
                            # Create a hash of the row for comparison
                            row_hash = hash(tuple(str(item) for item in row))
                            
                            # Check if this exact row already exists
                            if row_hash not in existing_row_hashes:
                                writer.writerow(row)
                                existing_row_hashes.add(row_hash)  # Add to set to prevent duplicates in this batch
                                saved_count += 1
                    
                    # Force write to disk
                    f.flush()
                    os.fsync(f.fileno())
            
            logger.info(f"Saved {saved_count} new unique fills to CSV")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            return 0
    
    def get_latest_timestamp_from_csv(self):
        """Get the latest timestamp from existing CSV to avoid duplicates."""
        try:
            if not os.path.exists(self.csv_file):
                return None
            
            # Read the CSV and find the latest timestamp
            df = pd.read_csv(self.csv_file)
            if 'TimeStamp' in df.columns and not df.empty:
                # Filter out empty timestamps and get the maximum
                timestamps = df['TimeStamp'].dropna()
                if not timestamps.empty:
                    return int(max(timestamps))
            
        except Exception as e:
            logger.warning(f"Could not read latest timestamp from CSV: {e}")
        
        return None
    
    def run(self):
        """Main monitoring loop."""
        logger.info("Starting Fill Monitor...")
        
        # Setup token manager
        if not self.setup_token_manager():
            logger.error("Failed to setup token manager, exiting")
            return
        
        # Get starting timestamp to avoid duplicates
        if self.last_timestamp is None:
            self.last_timestamp = self.get_latest_timestamp_from_csv()
            if self.last_timestamp:
                logger.info(f"Resuming from timestamp: {self.last_timestamp}")
        
        consecutive_errors = 0
        
        while not stop_event.is_set():
            try:
                logger.debug("Fetching new fills...")
                
                # Fetch fills
                fills = self.fetch_fills(min_timestamp=self.last_timestamp)
                
                if fills is None:
                    consecutive_errors += 1
                    if consecutive_errors >= self.max_retries:
                        logger.error(f"Max retries ({self.max_retries}) reached, stopping")
                        break
                    
                    logger.warning(f"API error #{consecutive_errors}, retrying in {self.poll_interval} seconds")
                    time.sleep(self.poll_interval)
                    continue
                
                # Reset error counter on success
                consecutive_errors = 0
                
                if fills:
                    # Sort fills by timestamp to ensure chronological order
                    fills.sort(key=lambda x: int(x.get('timeStamp', 0)))
                    
                    # Filter out fills we've already processed
                    new_fills = []
                    for fill in fills:
                        fill_timestamp = int(fill.get('timeStamp', 0))
                        if self.last_timestamp is None or fill_timestamp > self.last_timestamp:
                            new_fills.append(fill)
                    
                    if new_fills:
                        saved_count = self.save_fills_to_csv(new_fills)
                        
                        # Update last timestamp
                        self.last_timestamp = int(new_fills[-1].get('timeStamp', 0))
                        
                        logger.info(f"Processed {saved_count} new fills. Latest timestamp: {self.last_timestamp}")
                    else:
                        logger.debug("No new fills since last check")
                else:
                    logger.debug("No fills returned from API")
                
                # Wait before next poll
                logger.debug(f"Waiting {self.poll_interval} seconds before next check...")
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt, stopping...")
                break
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Unexpected error in main loop: {e}")
                
                if consecutive_errors >= self.max_retries:
                    logger.error("Too many consecutive errors, stopping.")
                    break
                
                time.sleep(self.poll_interval)
        
        logger.info("Fill monitor stopped.")

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Continuous Fill Monitor for Trading Technologies REST API",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--interval', 
        type=int, 
        default=DEFAULT_POLL_INTERVAL,
        help=f'Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL})'
    )
    
    parser.add_argument(
        '--output', 
        type=str,
        help='Output CSV filename (default: auto-generated with date)'
    )
    
    parser.add_argument(
        '--max-retries', 
        type=int, 
        default=DEFAULT_MAX_RETRIES,
        help=f'Maximum consecutive API failures before stopping (default: {DEFAULT_MAX_RETRIES})'
    )
    
    parser.add_argument(
        '--no-log-file', 
        action='store_true',
        help='Disable logging to file'
    )
    
    parser.add_argument(
        '--quiet', 
        action='store_true',
        help='Disable console logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(
        log_to_file=not args.no_log_file, 
        log_to_console=not args.quiet
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("TT Continuous Fill Monitor")
    logger.info("=" * 60)
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Poll interval: {args.interval} seconds")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Max retries: {args.max_retries}")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop monitoring")
    logger.info("=" * 60)
    
    # Create and run monitor
    monitor = FillMonitor(
        poll_interval=args.interval,
        max_retries=args.max_retries,
        output_file=args.output
    )
    
    try:
        monitor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    
    logger.info("Monitoring session completed.")

if __name__ == "__main__":
    main()