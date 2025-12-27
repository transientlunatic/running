"""
Example: Normalizing race results for general analysis.

This script demonstrates how to use Pydantic models to normalize
race results from different sources into a unified schema that
enables writing general-purpose analysis code.
"""

import pandas as pd
from running_results import (
    ColumnMapping,
    RaceResultsNormalizer,
    RaceCategory,
    normalize_race_results,
)


def main():
    """Demonstrate race results normalization."""
    
    print("=" * 70)
    print("RACE RESULTS NORMALIZATION EXAMPLE")
    print("=" * 70)
    
    # Example 1: Edinburgh Marathon with chip times
    print("\n1. Edinburgh Marathon 2024")
    print("-" * 70)
    
    edinburgh_df = pd.read_csv('edinburgh-marathon-2024.csv')
    print(f"Loaded {len(edinburgh_df)} results")
    print(f"Original columns: {edinburgh_df.columns.tolist()[:5]}...")
    
    mapping = ColumnMapping(
        position_overall='Position (Overall)',
        position_category='Position (Category)',
        name='Name Number',
        club='Club',
        chip_time_seconds='Chip Time (seconds)',
        gun_time_seconds='Gun Time (seconds)',
        age_category='Category'
    )
    
    edinburgh_normalized = normalize_race_results(
        edinburgh_df,
        mapping=mapping,
        race_name='Edinburgh Marathon 2024',
        race_year=2024,
        race_category='marathon',
        return_dataframe=True
    )
    
    print(f"✓ Normalized to standard schema")
    print(f"  Sample: {edinburgh_normalized.iloc[0]['name']} - "
          f"{edinburgh_normalized.iloc[0]['chip_time_minutes']:.1f} min")
    
    # Example 2: Great Scottish Run with different format
    print("\n2. Great Scottish Run 2022")
    print("-" * 70)
    
    gsr_df = pd.read_csv('gsr-results-final-2022.csv')
    print(f"Loaded {len(gsr_df)} results")
    print(f"Original columns: {gsr_df.columns.tolist()}")
    
    gsr_mapping = ColumnMapping(
        position_overall='Pos',
        name='Name',
        bib_number='Bib',
        club='Club',
        finish_time_minutes='Finish Time'
    )
    
    gsr_normalized = normalize_race_results(
        gsr_df,
        mapping=gsr_mapping,
        race_name='Great Scottish Run 2022',
        race_year=2022,
        race_category='10k',
        return_dataframe=True
    )
    
    print(f"✓ Normalized to standard schema")
    print(f"  Sample: {gsr_normalized.iloc[0]['name']} - "
          f"{gsr_normalized.iloc[0]['finish_time_minutes']:.1f} min")
    
    # Example 3: General analysis code that works on both
    print("\n3. General Analysis (works on both races)")
    print("-" * 70)
    
    def basic_race_stats(df):
        """Analysis that works on ANY normalized race results."""
        time_col = 'finish_time_minutes' if 'finish_time_minutes' in df.columns \
                   else 'chip_time_minutes'
        times = df[time_col].dropna()
        return {
            'finishers': len(df),
            'mean_time_min': times.mean(),
            'median_time_min': times.median(),
            'clubs': df['club'].nunique()
        }
    
    edin_stats = basic_race_stats(edinburgh_normalized)
    gsr_stats = basic_race_stats(gsr_normalized)
    
    print(f"Edinburgh Marathon:")
    print(f"  Finishers: {edin_stats['finishers']}")
    print(f"  Mean time: {edin_stats['mean_time_min']:.0f} minutes")
    print(f"  Clubs: {edin_stats['clubs']}")
    
    print(f"\nGreat Scottish Run:")
    print(f"  Finishers: {gsr_stats['finishers']}")
    print(f"  Mean time: {gsr_stats['mean_time_min']:.0f} minutes")
    print(f"  Clubs: {gsr_stats['clubs']}")
    
    print("\n" + "=" * 70)
    print("✓ SUCCESS: Different race formats analyzed with same code!")
    print("=" * 70)


if __name__ == '__main__':
    main()
