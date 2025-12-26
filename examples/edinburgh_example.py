"""
Example: Fetching and analyzing Edinburgh Marathon data using the running_results package.

This script demonstrates how to use the package to replicate the Edinburgh Marathon 2024.ipynb analysis.
"""

from running_results import (
    PaginatedRaceDataFetcher,
    TimeConverter,
    RaceDataTransformer,
    RacePlotter,
    RaceStatistics,
    RaceComparison
)


def main():
    print("Fetching Edinburgh Marathon 2024 data...")
    print("This may take several minutes due to pagination...")
    
    # Fetch data from all pages
    fetcher = PaginatedRaceDataFetcher(
        url_template="https://www.edinburghmarathon.com/results?event={event}&gender={gender}&page={page}",
        page_start=1,
        max_pages=700,
        other_params={'event': [1007], 'gender': ['M', 'F', 'N']}
    )
    
    data = fetcher.fetch()
    print(f"Fetched {len(data)} rows of data")
    
    # Process data - website returns duplicate rows, take every other one
    data = data[::2]
    data = data.reset_index(drop=True)
    print(f"After deduplication: {len(data)} results")
    
    # Extract category from position string
    print("\nTransforming data...")
    transformer = RaceDataTransformer()
    data = transformer.extract_category_from_position(
        data,
        position_col='Position (Category)',
        category_col='Category'
    )
    
    # Convert times
    data['Chip Time (seconds)'] = data['Chip Time'].apply(TimeConverter.to_seconds)
    data['Chip Time (minutes)'] = data['Chip Time (seconds)'] / 60
    
    # Save to CSV
    data.to_csv("edinburgh-marathon-2024.csv", index=False)
    print("Saved to: edinburgh-marathon-2024.csv")
    
    # Calculate statistics
    print("\n" + "="*60)
    print("EDINBURGH MARATHON 2024 STATISTICS")
    print("="*60)
    
    stats = RaceStatistics(data)
    
    print("\nOverall Summary:")
    print(stats.summary_statistics('Chip Time (minutes)'))
    
    print("\nPercentile Table:")
    print(stats.percentile_table('Chip Time (minutes)', percentiles=[5, 10, 25, 50, 75, 90, 95]))
    
    print("\nGender Comparison:")
    print(stats.gender_comparison(
        gender_column='Category',
        time_column='Chip Time (minutes)'
    ))
    
    print("\nTop 10 Fastest Finishers:")
    top_10 = stats.top_performers(
        n=10,
        time_column='Chip Time (minutes)',
        columns=['Name', 'Chip Time', 'Category', 'Club']
    )
    print(top_10)
    
    # Create visualizations
    print("\nCreating visualizations...")
    plotter = RacePlotter(use_kentigern_style=True)
    
    # Overall distribution
    plotter.plot_finish_time_distribution(
        data,
        time_column='Chip Time (minutes)',
        bins=range(120, 500, 1),
        save_path='edinburgh_2024_finish_times.png'
    )
    print("  Saved: edinburgh_2024_finish_times.png")
    
    # Gender comparison
    plotter.plot_gender_comparison(
        data,
        time_column='Chip Time (minutes)',
        gender_column='Category',
        bins=range(120, 420, 1),
        save_path='edinburgh_2024_gender_comparison.png'
    )
    print("  Saved: edinburgh_2024_gender_comparison.png")
    
    # Cumulative distribution
    plotter.plot_cumulative_distribution(
        data,
        time_column='Chip Time (minutes)',
        bins=range(120, 420, 1),
        save_path='edinburgh_2024_cumulative.png'
    )
    print("  Saved: edinburgh_2024_cumulative.png")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
