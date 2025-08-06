import matplotlib.pyplot as plt
import numpy as np
import os
import sys

# Add the workspace root to Python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, workspace_root)


from Optimizer.risk_utils import (
    zn_to_decimal,
    decimal_to_zn,  # noqa: F401 – exposed for convenience
    levels_crossed,
    TECH_LEVELS_DEC,
)

BE_low = 4
BE_high = 6

def breakeven(price, technical_dict):
    """
    Piecewise linear breakeven function.
    
    Args:
        price: The price to evaluate breakeven at
        current_price: Current market price (starting point)
        technical_dict: Dictionary containing technical levels, must have "Strong Support" and "Strong Resistance" keys
    
    Returns:
        Breakeven value as a float
    """
    strong_support = technical_dict["Strong Support"] if isinstance(technical_dict["Strong Support"], float) else zn_to_decimal(technical_dict["Strong Support"])
    strong_resistance = technical_dict["Strong Resistance"] if isinstance(technical_dict["Strong Resistance"], float) else zn_to_decimal(technical_dict["Strong Resistance"])
    size_up_long_price = technical_dict["Size Up Long Price"] if isinstance(technical_dict["Size Up Long Price"], float) else zn_to_decimal(technical_dict["Size Up Long Price"])
    size_up_short_price = technical_dict["Size Up Short Price"] if isinstance(technical_dict["Size Up Short Price"], float) else zn_to_decimal(technical_dict["Size Up Short Price"])
    
    # If price is at or below strong support, return constant value of 3
    if price <= strong_support:
        return -BE_low
    
    # If price is between current price and strong support, interpolate linearly
    if (price <= size_up_long_price) and (price >= strong_support):
        slope = (-BE_low + BE_high) / (strong_support - size_up_long_price)
        return -BE_high + slope * (price - size_up_long_price)
    
    # If price is between current price and strong resistance, interpolate linearly
    if (price <= strong_resistance) and (price >= size_up_short_price):
        slope = (-BE_low + BE_high) / (strong_resistance - size_up_short_price)
        return (-BE_high + slope * (price - size_up_short_price))*(-1)
    
    # If price is at or above strong resistance, return constant value of -3
    if price >= strong_resistance:
        return BE_low
    
    # If price is exactly at current price, return 5
    return None


if __name__ == "__main__":
    # Example parameters
    #current_price = 111.0
    technical_dict = {"Size Up Long Price": "111'00", "Size Up Short Price": "111'02", "Strong Resistance": "111'10", "Strong Support": "110'26"}
    
    # Create price range for plotting
    price_range = np.linspace(110, 112, 200)
    
    # Calculate breakeven values
    breakeven_values = [breakeven(p, technical_dict) for p in price_range]
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.plot(price_range, breakeven_values, 'b-', linewidth=2, label='Breakeven Curve')
    
    # Mark key points
    """

    plt.axvline(x=current_price, color='g', linestyle='--', alpha=0.7, label=f'Current Price ({current_price})')
    plt.axvline(x=technical_dict["Strong Support"], color='r', linestyle='--', alpha=0.7, label=f'Strong Support ({technical_dict["Strong Support"]})')
    plt.axvline(x=technical_dict["Strong Resistance"], color='m', linestyle='--', alpha=0.7, label=f'Strong Resistance ({technical_dict["Strong Resistance"]})')
    plt.axhline(y=5, color='g', linestyle=':', alpha=0.5)
    plt.axhline(y=3, color='r', linestyle=':', alpha=0.5)
    """
    # Add annotations
    """
    plt.annotate('(Current Price, 5)', xy=(current_price, 5), xytext=(current_price + 2, 5.2),
                arrowprops=dict(arrowstyle='->', color='green', alpha=0.7))
    plt.annotate('(Strong Support, 3)', xy=(technical_dict["Strong Support"], 3), xytext=(technical_dict["Strong Support"] + 2, 3.2),
                arrowprops=dict(arrowstyle='->', color='red', alpha=0.7))
    plt.annotate('(Size Up Long Price, 5)', xy=(technical_dict["Size Up Long Price"], 5), xytext=(technical_dict["Size Up Long Price"] + 2, 5.2),
                arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7))
    plt.annotate('(Size Up Short Price, 3)', xy=(technical_dict["Size Up Short Price"], 3), xytext=(technical_dict["Size Up Short Price"] + 2, 3.2),
                arrowprops=dict(arrowstyle='->', color='orange', alpha=0.7))
    """
    plt.xlabel('Price')
    plt.ylabel('Breakeven Value')
    plt.title('Breakeven Curve - Piecewise Linear Function')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show() 
    print("Hi")

    #print(breakeven(111.0, technical_dict))