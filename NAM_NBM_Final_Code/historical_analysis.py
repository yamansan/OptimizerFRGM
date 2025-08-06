import pickle
import pandas as pd
import numpy as np
from shared_functions import preprocess_data, dip_distribution_data_only, rise_distribution_data_only
import os

def generate_dip_distributions(df1_path, df2_path):
    """Generate dip distributions from historical data"""
    print("Preprocessing data...")
    df, nan_ranges, cols_to_null = preprocess_data(df1_path, df2_path)

    print("Generating dip distributions...")
    distributions = {}

    # Ensure the output directory exists
    os.makedirs('distributions', exist_ok=True)

    for breakeven in [1, 1.5, 2, 2.5, 3, 4, 5]:
        breakeven_decimal = breakeven / 16

        print(f"Processing max_rise = {breakeven}/16...")
        dips_bps = dip_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)

        if len(dips_bps) > 0:
            distributions[breakeven] = dips_bps
            print(f"  Found {len(dips_bps)} dips")

    return distributions, df, nan_ranges

def generate_rise_distributions(df1_path, df2_path):
    """Generate rise distributions from historical data"""
    print("Preprocessing data...")
    df, nan_ranges, cols_to_null = preprocess_data(df1_path, df2_path)

    print("Generating rise distributions...")
    distributions = {}

    # Ensure the output directory exists
    os.makedirs('distributions', exist_ok=True)

    for breakeven in [1, 1.5, 2, 2.5, 3, 4, 5]:
        breakeven_decimal = breakeven / 16

        print(f"Processing max_rise = {breakeven}/16...")
        rises_bps = rise_distribution_data_only(df, breakeven_decimal, breakeven_decimal, nan_ranges)

        if len(rises_bps) > 0:
            distributions[breakeven] = rises_bps
            print(f"  Found {len(rises_bps)} rise")

    return distributions, df, nan_ranges


def save_percentile_lookup_tables_NBM(distributions):
    """Save percentile lookup tables"""
    percentile_tables = {}
    
    print(f"🔍 DEBUG NBM: Processing {len(distributions)} distributions: {list(distributions.keys())}")

    for breakeven, dips_bps in distributions.items():
        print(f"🔍 DEBUG NBM: Processing breakeven {breakeven}, samples: {len(dips_bps)}")
        sorted_dips = np.sort(dips_bps)
        percentiles = np.linspace(0, 100, len(sorted_dips))

        percentile_tables[breakeven] = {
            'dips': sorted_dips,
            'percentiles': percentiles,
            'stats': {
                'count': len(dips_bps),
                'mean': np.mean(dips_bps),
                'p95': np.percentile(dips_bps, 95),
                'p99': np.percentile(dips_bps, 99)
            }
        }
        print(f"🔍 DEBUG NBM: Added breakeven {breakeven} to percentile_tables")

    print(f"🔍 DEBUG NBM: Final percentile_tables keys before saving: {list(percentile_tables.keys())}")
    
    # Save relative to script directory, not current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NBM.pkl')
    
    with open(output_path, 'wb') as f:
        pickle.dump(percentile_tables, f)

    print("NBM Percentile tables saved!")
    return percentile_tables

def save_percentile_lookup_tables_NAM(distributions):
    """Save percentile lookup tables"""
    percentile_tables = {}
    
    print(f"🔍 DEBUG NAM: Processing {len(distributions)} distributions: {list(distributions.keys())}")

    for breakeven, rises_bps in distributions.items():
        print(f"🔍 DEBUG NAM: Processing breakeven {breakeven}, samples: {len(rises_bps)}")
        sorted_rises = np.sort(rises_bps)
        percentiles = np.linspace(0, 100, len(sorted_rises))

        percentile_tables[breakeven] = {
            'rises': sorted_rises,
            'percentiles': percentiles,
            'stats': {
                'count': len(rises_bps),
                'mean': np.mean(rises_bps),
                'p95': np.percentile(rises_bps, 95),
                'p99': np.percentile(rises_bps, 99)
            }
        }
        print(f"🔍 DEBUG NAM: Added breakeven {breakeven} to percentile_tables")

    print(f"🔍 DEBUG NAM: Final percentile_tables keys before saving: {list(percentile_tables.keys())}")
    
    # Save relative to script directory, not current working directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'distributions', 'percentile_tables_NAM.pkl')
    
    with open(output_path, 'wb') as f:
        pickle.dump(percentile_tables, f)

    print("NAM Percentile tables saved!")
    return percentile_tables


def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Your file paths (relative to script location)
    df1_path = os.path.join(script_dir, 'ZN_1h_events_tagged_target_tz_nonevents.csv')
    df2_path = os.path.join(script_dir, 'Intraday_data_ZN_1h_2022-12-20_to_2025-06-11.csv')

    # Generate DIP distributions
    distributions, df, nan_ranges = generate_dip_distributions(df1_path, df2_path)
    print(f"🔍 DEBUG: DIP distributions keys before saving: {list(distributions.keys())}")
    percentile_tables = save_percentile_lookup_tables_NBM(distributions)

    # Generate RISE distributions
    distributions, df, nan_ranges = generate_rise_distributions(df1_path, df2_path)
    print(f"🔍 DEBUG: RISE distributions keys before saving: {list(distributions.keys())}")
    percentile_tables = save_percentile_lookup_tables_NAM(distributions)

if __name__ == "__main__":
    main()