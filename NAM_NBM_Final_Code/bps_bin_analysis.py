import pickle
import pandas as pd
import numpy as np
from shared_functions import preprocess_data, dip_distribution_data_only, rise_distribution_data_only
import os
from collections import defaultdict

def create_bps_bins(dips_bps, rises_bps, bin_size=1.0, max_bps=20):
    """
    Create bps bins and count dips/rises in each bin
    
    Args:
        dips_bps: List of dip values in basis points
        rises_bps: List of rise values in basis points  
        bin_size: Size of each bin in basis points (default 1.0)
        max_bps: Maximum bps to consider (default 20)
    
    Returns:
        DataFrame with columns: bin_start, bin_end, dip_count, rise_count
    """
    
    # Create bins
    bins = []
    for i in range(0, int(max_bps), int(bin_size)):
        bin_start = i
        bin_end = i + bin_size
        bins.append((bin_start, bin_end))
    
    # Count dips and rises in each bin
    results = []
    for bin_start, bin_end in bins:
        # Count dips in this bin
        dip_count = sum(1 for dip in dips_bps if bin_start <= dip < bin_end)
        
        # Count rises in this bin  
        rise_count = sum(1 for rise in rises_bps if bin_start <= rise < bin_end)
        
        results.append({
            'bin_start': bin_start,
            'bin_end': bin_end,
            'bin_label': f"{bin_start}-{bin_end}",
            'dip_count': dip_count,
            'rise_count': rise_count,
            'total_count': dip_count + rise_count
        })
    
    return pd.DataFrame(results)

def analyze_all_breakevens(df1_path, df2_path, bin_size=1.0, max_bps=20):
    """
    Analyze all breakeven levels and create bps bin analysis
    """
    print("Preprocessing data...")
    df, nan_ranges, cols_to_null = preprocess_data(df1_path, df2_path)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load existing percentile tables if they exist
    nbm_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NBM.pkl')
    nam_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NAM.pkl')
    
    all_dips = []
    all_rises = []
    
    breakeven_levels = [1, 1.5, 2, 2.5, 3, 4, 5]
    
    for breakeven in breakeven_levels:
        breakeven_decimal = breakeven / 16
        
        print(f"Processing breakeven = {breakeven}/16...")
        
        # Get dips and rises for this breakeven
        dips_bps = dip_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)
        rises_bps = rise_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)
        
        # Add to overall lists
        all_dips.extend(dips_bps)
        all_rises.extend(rises_bps)
        
        print(f"  Found {len(dips_bps)} dips, {len(rises_bps)} rises")
    
    print(f"\nTotal: {len(all_dips)} dips, {len(all_rises)} rises")
    
    # Create bps bins analysis
    bps_df = create_bps_bins(all_dips, all_rises, bin_size, max_bps)
    
    # Save results
    output_path = os.path.join(script_dir, 'bps_bin_analysis.csv')
    bps_df.to_csv(output_path, index=False)
    
    print(f"\nBPS bin analysis saved to: {output_path}")
    
    # Display summary
    print("\n=== BPS BIN ANALYSIS SUMMARY ===")
    print(f"Bin size: {bin_size} bps")
    print(f"Max bps: {max_bps}")
    print(f"Total dips: {len(all_dips)}")
    print(f"Total rises: {len(all_rises)}")
    
    # Show bins with data
    print("\nBins with data:")
    for _, row in bps_df[bps_df['total_count'] > 0].iterrows():
        print(f"  {row['bin_label']}: {row['dip_count']} dips, {row['rise_count']} rises")
    
    return bps_df, all_dips, all_rises

def analyze_single_breakeven(df1_path, df2_path, breakeven, bin_size=1.0, max_bps=20):
    """
    Analyze a single breakeven level
    """
    print(f"Analyzing breakeven = {breakeven}/16...")
    
    df, nan_ranges, cols_to_null = preprocess_data(df1_path, df2_path)
    breakeven_decimal = breakeven / 16
    
    # Get dips and rises
    dips_bps = dip_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)
    rises_bps = rise_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)
    
    # Create bps bins analysis
    bps_df = create_bps_bins(dips_bps, rises_bps, bin_size, max_bps)
    
    # Save results
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, f'bps_bin_analysis_breakeven_{breakeven}.csv')
    bps_df.to_csv(output_path, index=False)
    
    print(f"BPS bin analysis for breakeven {breakeven} saved to: {output_path}")
    
    return bps_df, dips_bps, rises_bps

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Your file paths (relative to script location)
    df1_path = os.path.join(script_dir, 'ZN_1h_events_tagged_target_tz_nonevents.csv')
    df2_path = os.path.join(script_dir, 'Intraday_data_ZN_1h_2022-12-20_to_2025-06-11.csv')
    
    # Analyze all breakeven levels combined
    bps_df, all_dips, all_rises = analyze_all_breakevens(df1_path, df2_path, bin_size=1.0, max_bps=20)
    
    # Also analyze individual breakeven levels
    for breakeven in [1, 1.5, 2, 2.5, 3, 4, 5]:
        analyze_single_breakeven(df1_path, df2_path, breakeven, bin_size=1.0, max_bps=20) 