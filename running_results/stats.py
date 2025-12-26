"""
Statistical analysis utilities for race results.

This module provides functions for calculating common race statistics
and generating summary tables.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union


class RaceStatistics:
    """
    Calculate and present statistics for race results.
    
    Provides methods for quantile analysis, category breakdowns,
    and other common race statistics.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with race data.
        
        Args:
            data: DataFrame containing race results
        """
        self.data = data
    
    def quantiles(
        self,
        column: str = 'FinishTime (minutes)',
        q: Optional[Union[List[float], np.ndarray]] = None
    ) -> pd.Series:
        """
        Calculate quantiles for finish times.
        
        Args:
            column: Column to calculate quantiles for
            q: Quantile values (0-1). Default is 5% to 100% in 20 steps.
            
        Returns:
            Series with quantile values
            
        Example:
            >>> stats = RaceStatistics(data)
            >>> stats.quantiles()
        """
        if q is None:
            q = np.linspace(0.05, 1, 20)
            
        return self.data[column].quantile(q)
    
    def summary_statistics(
        self,
        column: str = 'FinishTime (minutes)'
    ) -> pd.Series:
        """
        Get summary statistics (mean, median, std, etc.).
        
        Args:
            column: Column to summarize
            
        Returns:
            Series with summary statistics
        """
        return self.data[column].describe()
    
    def category_breakdown(
        self,
        category_column: str = 'RunnerCategory',
        time_column: str = 'FinishTime (minutes)',
        stats: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get statistics broken down by category.
        
        Args:
            category_column: Column containing categories
            time_column: Column with times to analyze
            stats: List of statistics to calculate (mean, median, count, etc.)
            
        Returns:
            DataFrame with statistics per category
        """
        if stats is None:
            stats = ['count', 'mean', 'median', 'std', 'min', 'max']
        
        grouped = self.data.groupby(category_column)[time_column]
        
        result = pd.DataFrame()
        for stat in stats:
            if stat == 'median':
                result[stat] = grouped.median()
            else:
                result[stat] = grouped.agg(stat)
                
        return result.sort_values('mean')
    
    def percentile_for_time(
        self,
        time: float,
        time_column: str = 'FinishTime (minutes)'
    ) -> float:
        """
        Find what percentile a given time represents.
        
        Args:
            time: Time value to check
            time_column: Column with finish times
            
        Returns:
            Percentile (0-100) for the given time
            
        Example:
            >>> stats.percentile_for_time(180)  # What percentile is 3 hours?
            75.5
        """
        faster = (self.data[time_column] <= time).sum()
        total = len(self.data[time_column].dropna())
        return 100 * faster / total
    
    def time_for_percentile(
        self,
        percentile: float,
        time_column: str = 'FinishTime (minutes)'
    ) -> float:
        """
        Find the time at a given percentile.
        
        Args:
            percentile: Percentile to find (0-100)
            time_column: Column with finish times
            
        Returns:
            Time value at the given percentile
            
        Example:
            >>> stats.time_for_percentile(50)  # Median time
            165.3
        """
        return self.data[time_column].quantile(percentile / 100)
    
    def gender_comparison(
        self,
        gender_column: str = 'Gender',
        time_column: str = 'FinishTime (minutes)',
        male_value: str = 'M',
        female_value: str = 'F'
    ) -> pd.DataFrame:
        """
        Compare statistics between genders.
        
        Args:
            gender_column: Column with gender data
            time_column: Column with finish times
            male_value: Value representing male
            female_value: Value representing female
            
        Returns:
            DataFrame comparing gender statistics
        """
        # Handle category-based gender (e.g., "M40")
        if gender_column == 'Category':
            male_data = self.data[self.data[gender_column].apply(
                lambda x: str(x)[-1] == male_value if pd.notna(x) else False
            )]
            female_data = self.data[self.data[gender_column].apply(
                lambda x: str(x)[-1] == female_value if pd.notna(x) else False
            )]
        else:
            male_data = self.data[self.data[gender_column] == male_value]
            female_data = self.data[self.data[gender_column] == female_value]
        
        comparison = pd.DataFrame({
            'Male': male_data[time_column].describe(),
            'Female': female_data[time_column].describe()
        })
        
        comparison['Difference'] = comparison['Female'] - comparison['Male']
        
        return comparison
    
    def club_comparison(
        self,
        club_column: str = 'Club',
        time_column: str = 'FinishTime (minutes)'
    ) -> pd.DataFrame:
        """
        Compare statistics between club and non-club runners.
        
        Args:
            club_column: Column indicating club membership
            time_column: Column with finish times
            
        Returns:
            DataFrame comparing club vs non-club statistics
        """
        club_runners = self.data[~self.data[club_column].isna()]
        non_club_runners = self.data[self.data[club_column].isna()]
        
        comparison = pd.DataFrame({
            'Club': club_runners[time_column].describe(),
            'Non-Club': non_club_runners[time_column].describe()
        })
        
        comparison['Difference'] = comparison['Non-Club'] - comparison['Club']
        
        return comparison
    
    def top_performers(
        self,
        n: int = 10,
        time_column: str = 'FinishTime (minutes)',
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get top N fastest finishers.
        
        Args:
            n: Number of top performers to return
            time_column: Column with finish times
            columns: Columns to include in output
            
        Returns:
            DataFrame with top performers
        """
        if columns is None:
            columns = [col for col in self.data.columns if col != time_column]
            columns = [time_column] + columns
            
        return self.data.nsmallest(n, time_column)[columns]
    
    def percentile_table(
        self,
        time_column: str = 'FinishTime (minutes)',
        percentiles: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Create a table of finish times at various percentiles.
        
        Args:
            time_column: Column with finish times
            percentiles: List of percentiles to include (0-100)
            
        Returns:
            DataFrame with percentile table
        """
        if percentiles is None:
            percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        results = []
        for p in percentiles:
            time = self.time_for_percentile(p, time_column)
            results.append({
                'Percentile': f'{p}%',
                'Time (minutes)': round(time, 2)
            })
            
        return pd.DataFrame(results)
    
    def year_over_year_comparison(
        self,
        year_column: str = 'year',
        time_column: str = 'FinishTime (minutes)',
        stat: str = 'median'
    ) -> pd.DataFrame:
        """
        Compare statistics across years.
        
        Args:
            year_column: Column with year data
            time_column: Column with finish times
            stat: Statistic to compare (mean, median, count, etc.)
            
        Returns:
            DataFrame with year-over-year comparison
        """
        grouped = self.data.groupby(year_column)[time_column]
        
        comparison = pd.DataFrame({
            'count': grouped.count(),
            stat: grouped.agg(stat)
        })
        
        comparison['change'] = comparison[stat].diff()
        comparison['pct_change'] = comparison[stat].pct_change() * 100
        
        return comparison


class RaceComparison:
    """
    Compare statistics between multiple races or datasets.
    """
    
    def __init__(self, datasets: Dict[str, pd.DataFrame]):
        """
        Initialize with multiple datasets.
        
        Args:
            datasets: Dictionary mapping names to DataFrames
        """
        self.datasets = datasets
        self.stats = {name: RaceStatistics(data) for name, data in datasets.items()}
    
    def compare_quantiles(
        self,
        column: str = 'FinishTime (minutes)',
        q: Optional[Union[List[float], np.ndarray]] = None
    ) -> pd.DataFrame:
        """
        Compare quantiles across all datasets.
        
        Args:
            column: Column to compare
            q: Quantile values
            
        Returns:
            DataFrame with quantiles for each dataset
        """
        result = pd.DataFrame()
        
        for name, stat_obj in self.stats.items():
            result[name] = stat_obj.quantiles(column, q)
            
        return result
    
    def compare_summary(
        self,
        column: str = 'FinishTime (minutes)'
    ) -> pd.DataFrame:
        """
        Compare summary statistics across datasets.
        
        Args:
            column: Column to summarize
            
        Returns:
            DataFrame with summary statistics for each dataset
        """
        result = pd.DataFrame()
        
        for name, stat_obj in self.stats.items():
            result[name] = stat_obj.summary_statistics(column)
            
        return result
    
    def percentile_comparison_table(
        self,
        time_column: str = 'FinishTime (minutes)',
        percentiles: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Create comparison table of percentiles across datasets.
        
        Args:
            time_column: Column with finish times
            percentiles: Percentiles to include
            
        Returns:
            DataFrame comparing percentiles
        """
        if percentiles is None:
            percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        result = pd.DataFrame()
        result['Percentile'] = [f'{p}%' for p in percentiles]
        
        for name, stat_obj in self.stats.items():
            times = [stat_obj.time_for_percentile(p, time_column) for p in percentiles]
            result[name] = [round(t, 2) for t in times]
            
        return result.set_index('Percentile')
