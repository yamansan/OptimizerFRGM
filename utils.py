import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import time
import math
import pickle
import requests

def get_last_trade_state_event(file_path: str) -> dict:
    """Get the last row of the trade state events CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        trade_dict = last_row.to_dict()
        
        return trade_dict
    except Exception as e:
        print(f"Error reading trade state events: {e}")
        return {}


def get_technical_dict(file_path: str) -> dict:
    """Get the last row of the technical dict CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        technical_dict = last_row.to_dict()
        
        return technical_dict
    except Exception as e:
        print(f"Error reading technical dict: {e}")
        return {}


def get_last_net_position(file_path: str) -> dict:
    """Get the last row of the net position streaming CSV as a dictionary."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        net_position_dict = last_row.to_dict()
        
        return net_position_dict
    except Exception as e:
        print(f"Error reading net position streaming: {e}")
        return {}


def get_current_price(file_path: str) -> float:
    """Get the current price from the price streaming CSV."""
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        df = df.dropna(subset=["price"])
        # Get the last row
        last_row = df.iloc[-1]
        
        # Convert the last row to a dictionary
        last_row_dict = last_row.to_dict()
        
        current_price = last_row_dict["price"]

        if isinstance(current_price, str):
            current_price = float(current_price)
        
        return current_price
    except Exception as e:
        print(f"Error reading price streaming: {e}")
        return 0