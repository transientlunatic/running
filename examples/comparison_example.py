"""
Example: Comparing multiple years or races using the running_results package.

This demonstrates advanced analysis using the RaceComparison class.
"""

from running_results import (
    CSVRaceData,
    TimeConverter,
    RaceStatistics,
    RaceComparison,
    RacePlotter
)
import pandas as pd


def load_gsr_data():
    """Load Great Scottish Run data for comparison."""
    data_2022 = CSVRaceData("gsr-results-final-2022.csv").fetch()
    data_2023 = CSVRaceData("gsr-results-provisional-2023.csv").fetch()
    
    # Both datasets should have 'Finish Time' column already in minutes
    # If not, you would convert them here
    
    return {
        '2022': data_2022,
        '2023': data_2023
    }


def main():
    print("Loading Great Scottish Run data...")
    
    try:
        datasets = load_gsr_data()
        print(f"Loaded {len(datasets)} years of data")
        
        # Create comparison object
        comparison = RaceComparison(datasets)
        
        # Compare summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS COMPARISON")
        print("="*60)
        print(comparison.compare_summary('Finish Time'))
        
        # Compare quantiles
        print("\n" + "="*60)
        print("QUANTILE COMPARISON")
        print("="*60)
        print(comparison.compare_quantiles('Finish Time'))
        
        # Percentile comparison table
        print("\n" + "="*60)
        print("PERCENTILE COMPARISON")
        print("="*60)
        print(comparison.percentile_comparison_table('Finish Time'))
        
        # Create comparison plots
        print("\nCreating comparison visualizations...")
        plotter = RacePlotter(use_kentigern_style=True)
        
        # Overlaid distributions
        plotter.plot_cumulative_distribution(
            [datasets['2022'], datasets['2023']],
            time_column='Finish Time',
            bins=range(60, 240, 1),
            labels=['2022', '2023'],
            save_path='gsr_comparison_cumulative.png'
        )
        print("  Saved: gsr_comparison_cumulative.png")
        
        # Individual year statistics
        for year, data in datasets.items():
            print(f"\n{year} Statistics:")
            stats = RaceStatistics(data)
            print(f"  Total runners: {len(data)}")
            print(f"  Median time: {stats.time_for_percentile(50):.2f} minutes")
            print(f"  Fastest: {data['Finish Time'].min():.2f} minutes")
            print(f"  Slowest: {data['Finish Time'].max():.2f} minutes")
        
        print("\nDone!")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find data files. {e}")
        print("Make sure gsr-results-final-2022.csv and gsr-results-provisional-2023.csv exist.")


if __name__ == "__main__":
    main()
