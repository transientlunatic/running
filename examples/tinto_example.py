"""
Example: Fetching and analyzing Tinto Hill Race data using the running_results package.

This script demonstrates how to use the package to replicate the Tinto.ipynb analysis.
"""

from running_results import (
    MultiYearRaceData,
    ColumnStandardizer,
    NameParser,
    RaceDataTransformer,
    RacePlotter,
    RaceStatistics
)


def main():
    print("Fetching Tinto Hill Race data...")
    
    # Fetch multiple years of data
    fetcher = MultiYearRaceData(
        url_template="https://carnethy.com/ri_results/tinto/t_{year}.htm",
        years=range(1985, 2005),  # Adjust range as needed
        table_index=-2,
        on_error='warn'
    )
    
    data = fetcher.fetch()
    print(f"Fetched {len(data)} results")
    
    # Transform data
    print("\nTransforming data...")
    transformer = RaceDataTransformer()
    
    # Clean header row (use first row as column names)
    data = transformer.clean_header_row(data, header_row_index=0)
    
    # Parse names
    data = NameParser.add_name_columns(data, name_column='Name')
    
    # Standardize columns with custom mappings for Tinto-specific columns
    standardizer = ColumnStandardizer({
        'Position': 'RunnerPosition',
        'Posn': 'RunnerPosition',
        'Pos.': 'RunnerPosition',
        'Place': 'RunnerPosition',
        'Race No. ': 'RaceNumber',
        'Category': 'RunnerCategory',
        'Cat.': 'RunnerCategory',
        'Cat': 'RunnerCategory',
        'Time': 'FinishTime',
        'Tiime': 'FinishTime',
        'Club': 'Club',
    })
    
    data = standardizer.standardize(data)
    
    # Select relevant columns
    columns = ['RunnerPosition', 'Surname', 'Firstname', 'Club', 'RunnerCategory', 'FinishTime', 'year']
    data = transformer.select_columns(data, columns)
    
    # Add time conversions
    data = transformer.add_time_conversions(data, time_column='FinishTime')
    
    # Save to CSV files by year
    print("\nSaving data by year...")
    for year in data['year'].unique():
        year_data = data[data['year'] == year]
        year_data.to_csv(f'tinto/{int(year)}.csv', index=False)
        print(f"  Saved {len(year_data)} results for {int(year)}")
    
    # Calculate statistics
    print("\n" + "="*50)
    print("TINTO HILL RACE STATISTICS")
    print("="*50)
    
    stats = RaceStatistics(data)
    
    print("\nOverall Summary:")
    print(stats.summary_statistics('FinishTime (minutes)'))
    
    print("\nPercentile Table:")
    print(stats.percentile_table('FinishTime (minutes)'))
    
    print("\nYear-over-Year Comparison:")
    print(stats.year_over_year_comparison(
        year_column='year',
        time_column='FinishTime (minutes)',
        stat='median'
    ))
    
    # Create visualizations
    print("\nCreating visualizations...")
    plotter = RacePlotter(use_kentigern_style=True)
    
    plotter.plot_finish_time_distribution(
        data,
        time_column='FinishTime (minutes)',
        bins=range(30, 150, 1),
        save_path='tinto_finish_times.png'
    )
    print("  Saved: tinto_finish_times.png")
    
    plotter.plot_cumulative_distribution(
        data,
        time_column='FinishTime (minutes)',
        bins=range(30, 150, 1),
        save_path='tinto_cumulative.png'
    )
    print("  Saved: tinto_cumulative.png")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
