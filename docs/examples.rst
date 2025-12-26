Examples
========

This page provides practical examples of using the running-results package.

Example 1: Normalizing Tinto Hill Race Results
-----------------------------------------------

.. code-block:: python

   from running_results.models import RaceResultsNormalizer, ColumnMapping
   import pandas as pd
   import glob

   # Load all years of Tinto data
   all_data = []
   for year in range(1985, 2004):
       try:
           df = pd.read_csv(f'tinto/{year}.csv')
           df['race_year'] = year
           all_data.append(df)
       except FileNotFoundError:
           continue

   combined = pd.concat(all_data, ignore_index=True)

   # Define mapping
   mapping = ColumnMapping(
       position_overall='Position',
       name='Name',
       club='Club',
       finish_time='Time'
   )

   # Normalize
   normalizer = RaceResultsNormalizer(mapping)
   normalized = normalizer.normalize(combined)

   # Save
   normalized.to_parquet('tinto_normalized.parquet')

Example 2: Building a Race Database
------------------------------------

.. code-block:: python

   from running_results import RaceResultsManager

   # Initialize database
   with RaceResultsManager('scotland_races.db') as manager:
       # Add Tinto results
       for year in range(1985, 2024):
           try:
               count = manager.add_from_file(
                   f'tinto/{year}.csv',
                   race_name='Tinto Hill Race',
                   race_year=year,
                   race_category='fell_race'
               )
               print(f"Tinto {year}: {count} results")
           except FileNotFoundError:
               pass

       # Add Edinburgh Marathon
       count = manager.add_from_file(
           'edinburgh-marathon-2024.csv',
           race_name='Edinburgh Marathon',
           race_year=2024,
           race_category='marathon'
       )
       print(f"Edinburgh Marathon 2024: {count} results")

       # List all races
       print(manager.list_races())

Example 3: Analyzing Runner Performance
----------------------------------------

.. code-block:: python

   from running_results import RaceResultsManager
   import matplotlib.pyplot as plt

   with RaceResultsManager('scotland_races.db') as manager:
       # Get a runner's complete history in one race
       history = manager.get_runner_history(
           'Alan Farningham',
           'Tinto Hill Race'
       )

       # Plot performance over time
       plt.figure(figsize=(10, 6))
       plt.plot(history['race_year'], history['finish_time_minutes'], 'o-')
       plt.xlabel('Year')
       plt.ylabel('Finish Time (minutes)')
       plt.title('Alan Farningham - Tinto Hill Race Performance')
       plt.grid(True)
       plt.show()

       # Get position trends
       plt.figure(figsize=(10, 6))
       plt.plot(history['race_year'], history['position_overall'], 'o-')
       plt.xlabel('Year')
       plt.ylabel('Overall Position')
       plt.title('Alan Farningham - Tinto Hill Race Position')
       plt.gca().invert_yaxis()  # Lower position is better
       plt.grid(True)
       plt.show()

Example 4: Club Analysis
-------------------------

.. code-block:: python

   from running_results import RaceResultsManager
   import pandas as pd

   with RaceResultsManager('scotland_races.db') as manager:
       # Get all Tinto results
       tinto = manager.get_race('Tinto Hill Race')

       # Analyze club participation over time
       club_by_year = tinto.groupby(['race_year', 'club']).size().unstack(fill_value=0)

       # Top clubs by total participation
       club_totals = tinto['club'].value_counts().head(10)
       print("Top 10 clubs by participation:")
       print(club_totals)

       # Club with most wins
       winners = tinto[tinto['position_overall'] == 1]
       winning_clubs = winners['club'].value_counts()
       print("\nClub wins:")
       print(winning_clubs)

       # Average finish time by club (for clubs with 10+ results)
       club_stats = tinto.groupby('club').agg({
           'finish_time_minutes': ['mean', 'count']
       }).round(2)
       club_stats = club_stats[club_stats[('finish_time_minutes', 'count')] >= 10]
       club_stats = club_stats.sort_values(('finish_time_minutes', 'mean'))
       print("\nFastest clubs (10+ runners):")
       print(club_stats.head(10))

Example 5: Web Scraping Results
--------------------------------

.. code-block:: python

   from running_results import RaceResultsManager

   with RaceResultsManager('races.db') as manager:
       # Import from a results webpage
       try:
           count = manager.add_from_url(
               url='https://example.com/parkrun/results/2024-12-25/',
               race_name='Glasgow Parkrun',
               race_year=2024,
               race_category='parkrun',
               race_date='2024-12-25'
           )
           print(f"Imported {count} results from web")
       except Exception as e:
           print(f"Import failed: {e}")

Example 6: Comparing Race Years
--------------------------------

.. code-block:: python

   from running_results import RaceResultsManager
   import matplotlib.pyplot as plt

   with RaceResultsManager('scotland_races.db') as manager:
       # Get multiple years
       results_2000 = manager.get_race('Tinto Hill Race', race_year=2000)
       results_2003 = manager.get_race('Tinto Hill Race', race_year=2003)

       # Compare finish time distributions
       fig, axes = plt.subplots(1, 2, figsize=(15, 5))

       axes[0].hist(results_2000['finish_time_minutes'], bins=20, alpha=0.7)
       axes[0].set_title('Tinto 2000 - Finish Times')
       axes[0].set_xlabel('Time (minutes)')
       axes[0].set_ylabel('Number of runners')

       axes[1].hist(results_2003['finish_time_minutes'], bins=20, alpha=0.7)
       axes[1].set_title('Tinto 2003 - Finish Times')
       axes[1].set_xlabel('Time (minutes)')
       axes[1].set_ylabel('Number of runners')

       plt.tight_layout()
       plt.show()

       # Statistical comparison
       print(f"2000: {len(results_2000)} finishers, "
             f"mean {results_2000['finish_time_minutes'].mean():.2f} min")
       print(f"2003: {len(results_2003)} finishers, "
             f"mean {results_2003['finish_time_minutes'].mean():.2f} min")

Example 7: Age Category Analysis
---------------------------------

.. code-block:: python

   from running_results import RaceResultsManager
   import pandas as pd

   with RaceResultsManager('scotland_races.db') as manager:
       # Get race results
       results = manager.get_race('Tinto Hill Race')

       # Filter to valid finishers with age category
       finishers = results[
           (results['race_status'] == 'FINISHED') &
           (results['age_category'].notna())
       ]

       # Group by age category
       category_stats = finishers.groupby('age_category').agg({
           'finish_time_minutes': ['mean', 'median', 'count']
       }).round(2)

       category_stats.columns = ['Mean Time', 'Median Time', 'Count']
       category_stats = category_stats.sort_values('Mean Time')

       print("Performance by age category:")
       print(category_stats)

       # Gender comparison
       gender_stats = finishers.groupby('gender').agg({
           'finish_time_minutes': ['mean', 'median', 'count']
       }).round(2)

       print("\nPerformance by gender:")
       print(gender_stats)

Example 8: Creating Custom Reports
-----------------------------------

.. code-block:: python

   from running_results import RaceResultsManager
   import pandas as pd

   def create_race_report(db_path, race_name, year):
       \"\"\"Create a comprehensive race report.\"\"\"
       with RaceResultsManager(db_path) as manager:
           results = manager.get_race(race_name, race_year=year)
           finishers = results[results['race_status'] == 'FINISHED']

           report = {
               'Race': race_name,
               'Year': year,
               'Total Starters': len(results),
               'Finishers': len(finishers),
               'DNF': len(results[results['race_status'] == 'DNF']),
               'Winner': finishers.loc[finishers['position_overall'] == 1, 'name'].values[0],
               'Winning Time': f"{finishers['finish_time_minutes'].min():.2f} min",
               'Median Time': f"{finishers['finish_time_minutes'].median():.2f} min",
               'Clubs Represented': finishers['club'].nunique(),
               'Largest Club': finishers['club'].mode().values[0] if len(finishers) > 0 else 'N/A'
           }

           return pd.Series(report)

   # Generate reports for multiple years
   reports = []
   for year in range(2000, 2004):
       report = create_race_report('scotland_races.db', 'Tinto Hill Race', year)
       reports.append(report)

   summary = pd.DataFrame(reports)
   print(summary)

See Also
--------

* :doc:`quickstart` - Getting started guide
* :doc:`api/manager` - Manager API reference
* :doc:`api/models` - Data models reference
