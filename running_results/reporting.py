"""
Report generation using otter-report.

Generates comprehensive HTML and PDF reports for race results,
including statistics, charts, and tables.
"""
import pandas as pd
from pathlib import Path
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

try:
    from otter import Report, Section, Table, Chart, Metric, Grid
    OTTER_AVAILABLE = True
except ImportError:
    OTTER_AVAILABLE = False
    # Define placeholder classes for type hints
    class Report: pass
    class Section: pass


def generate_race_report(
    results: pd.DataFrame,
    race_name: str,
    race_year: Optional[int] = None,
    output_path: str = 'race_report.html',
    output_format: str = 'html'
) -> None:
    """
    Generate a comprehensive race report.
    
    Args:
        results: DataFrame with race results
        race_name: Name of the race
        race_year: Specific year (None for all years)
        output_path: Output file path
        output_format: 'html' or 'pdf'
    """
    if not OTTER_AVAILABLE:
        raise ImportError("otter-report is not installed. Install with: pip install otter-report")
    
    # Filter finishers
    finishers = results[results['race_status'] == 'finished'].copy()
    
    # Calculate statistics
    total_starters = len(results)
    total_finishers = len(finishers)
    dnf_count = len(results[results['race_status'] == 'dnf'])
    
    # Create report
    year_str = f" ({race_year})" if race_year else " (All Years)"
    report = Report(title=f"{race_name}{year_str}")
    
    # Summary Section
    summary = Section("Race Summary")
    
    metrics = Grid([
        Metric("Total Starters", total_starters),
        Metric("Finishers", total_finishers),
        Metric("DNF", dnf_count),
        Metric("Finish Rate", f"{(total_finishers/total_starters*100):.1f}%")
    ])
    summary.add(metrics)
    
    if len(finishers) > 0:
        winning_time = finishers['finish_time_minutes'].min()
        median_time = finishers['finish_time_minutes'].median()
        
        time_metrics = Grid([
            Metric("Winning Time", f"{winning_time:.2f} min"),
            Metric("Median Time", f"{median_time:.2f} min"),
            Metric("Slowest Time", f"{finishers['finish_time_minutes'].max():.2f} min")
        ])
        summary.add(time_metrics)
    
    report.add(summary)
    
    # Top Finishers Section
    if len(finishers) > 0:
        top_section = Section("Top 10 Finishers")
        
        top_10 = finishers.nsmallest(10, 'finish_time_minutes')[
            ['position_overall', 'name', 'club', 'age_category', 'finish_time_minutes']
        ].copy()
        top_10['finish_time_minutes'] = top_10['finish_time_minutes'].apply(lambda x: f"{x:.2f}")
        top_10.columns = ['Pos', 'Name', 'Club', 'Category', 'Time (min)']
        
        top_section.add(Table(top_10))
        report.add(top_section)
    
    # Time Distribution Chart
    if len(finishers) > 0:
        chart_section = Section("Finish Time Distribution")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(finishers['finish_time_minutes'], bins=20, edgecolor='black', alpha=0.7)
        ax.set_xlabel('Finish Time (minutes)')
        ax.set_ylabel('Number of Runners')
        ax.set_title('Distribution of Finish Times')
        ax.grid(True, alpha=0.3)
        
        chart_section.add(Chart(fig))
        plt.close(fig)
        report.add(chart_section)
    
    # Club Analysis
    if 'club' in finishers.columns and finishers['club'].notna().sum() > 0:
        club_section = Section("Club Analysis")
        
        club_counts = finishers['club'].value_counts().head(10)
        
        if len(club_counts) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))
            club_counts.plot(kind='barh', ax=ax)
            ax.set_xlabel('Number of Runners')
            ax.set_ylabel('Club')
            ax.set_title('Top 10 Clubs by Participation')
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            
            club_section.add(Chart(fig))
            plt.close(fig)
            report.add(club_section)
    
    # Age Category Analysis
    if 'age_category' in finishers.columns and finishers['age_category'].notna().sum() > 0:
        category_section = Section("Age Category Analysis")
        
        category_stats = finishers.groupby('age_category').agg({
            'finish_time_minutes': ['count', 'mean', 'min']
        }).round(2)
        category_stats.columns = ['Count', 'Avg Time', 'Best Time']
        category_stats = category_stats.sort_values('Count', ascending=False).head(10)
        
        category_section.add(Table(category_stats.reset_index()))
        report.add(category_section)
    
    # Gender Split
    if 'gender' in finishers.columns and finishers['gender'].notna().sum() > 0:
        gender_section = Section("Gender Split")
        
        gender_counts = finishers['gender'].value_counts()
        
        if len(gender_counts) > 0:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%')
            ax.set_title('Gender Distribution')
            
            gender_section.add(Chart(fig))
            plt.close(fig)
            report.add(gender_section)
    
    # Generate output
    if output_format == 'html':
        report.to_html(output_path)
    elif output_format == 'pdf':
        report.to_pdf(output_path)
    else:
        raise ValueError(f"Unsupported format: {output_format}")


def generate_comparison_report(
    results: pd.DataFrame,
    race_name: str,
    output_path: str = 'comparison_report.html'
) -> None:
    """
    Generate a multi-year comparison report.
    
    Args:
        results: DataFrame with results from multiple years
        race_name: Name of the race
        output_path: Output file path
    """
    if not OTTER_AVAILABLE:
        raise ImportError("otter-report is not installed. Install with: pip install otter-report")
    
    report = Report(title=f"{race_name} - Multi-Year Comparison")
    
    # Overview
    overview = Section("Overview")
    
    years = sorted(results['race_year'].unique())
    metrics = Grid([
        Metric("Years Covered", f"{min(years)}-{max(years)}"),
        Metric("Total Editions", len(years)),
        Metric("Total Results", len(results))
    ])
    overview.add(metrics)
    report.add(overview)
    
    # Year-by-year statistics
    stats_section = Section("Year-by-Year Statistics")
    
    yearly_stats = []
    for year in years:
        year_data = results[results['race_year'] == year]
        finishers = year_data[year_data['race_status'] == 'finished']
        
        stats = {
            'Year': year,
            'Starters': len(year_data),
            'Finishers': len(finishers),
            'DNF': len(year_data[year_data['race_status'] == 'dnf']),
        }
        
        if len(finishers) > 0:
            stats['Winning Time'] = f"{finishers['finish_time_minutes'].min():.2f}"
            stats['Median Time'] = f"{finishers['finish_time_minutes'].median():.2f}"
        else:
            stats['Winning Time'] = 'N/A'
            stats['Median Time'] = 'N/A'
        
        yearly_stats.append(stats)
    
    stats_df = pd.DataFrame(yearly_stats)
    stats_section.add(Table(stats_df))
    report.add(stats_section)
    
    # Participation trend
    trend_section = Section("Participation Trend")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    yearly_counts = results.groupby('race_year').size()
    ax.plot(yearly_counts.index, yearly_counts.values, marker='o', linewidth=2)
    ax.set_xlabel('Year')
    ax.set_ylabel('Number of Participants')
    ax.set_title('Participation Over Time')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    trend_section.add(Chart(fig))
    plt.close(fig)
    report.add(trend_section)
    
    # Winning time trend
    finishers = results[results['race_status'] == 'finished']
    if len(finishers) > 0:
        winning_section = Section("Winning Time Trend")
        
        winning_times = finishers.groupby('race_year')['finish_time_minutes'].min()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(winning_times.index, winning_times.values, marker='o', linewidth=2, color='red')
        ax.set_xlabel('Year')
        ax.set_ylabel('Winning Time (minutes)')
        ax.set_title('Winning Time Evolution')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        winning_section.add(Chart(fig))
        plt.close(fig)
        report.add(winning_section)
    
    report.to_html(output_path)


def generate_runner_report(
    history: pd.DataFrame,
    runner_name: str,
    output_path: str = 'runner_report.html'
) -> None:
    """
    Generate a runner history report.
    
    Args:
        history: DataFrame with runner's race history
        runner_name: Runner's name
        output_path: Output file path
    """
    if not OTTER_AVAILABLE:
        raise ImportError("otter-report is not installed. Install with: pip install otter-report")
    
    report = Report(title=f"Runner Report: {runner_name}")
    
    # Overview
    overview = Section("Overview")
    
    total_races = len(history)
    finishes = len(history[history['race_status'] == 'finished'])
    
    metrics = Grid([
        Metric("Total Races", total_races),
        Metric("Finishes", finishes),
        Metric("DNF", len(history[history['race_status'] == 'dnf']))
    ])
    overview.add(metrics)
    
    if finishes > 0:
        finishers = history[history['race_status'] == 'finished']
        perf_metrics = Grid([
            Metric("Best Time", f"{finishers['finish_time_minutes'].min():.2f} min"),
            Metric("Average Time", f"{finishers['finish_time_minutes'].mean():.2f} min"),
            Metric("Best Position", int(finishers['position_overall'].min()))
        ])
        overview.add(perf_metrics)
    
    report.add(overview)
    
    # Race history table
    history_section = Section("Race History")
    
    history_display = history[[
        'race_year', 'race_name', 'position_overall', 'finish_time_minutes', 'club', 'age_category'
    ]].copy()
    history_display['finish_time_minutes'] = history_display['finish_time_minutes'].apply(
        lambda x: f"{x:.2f}" if pd.notna(x) else 'DNF'
    )
    history_display.columns = ['Year', 'Race', 'Position', 'Time (min)', 'Club', 'Category']
    history_display = history_display.sort_values('Year', ascending=False)
    
    history_section.add(Table(history_display))
    report.add(history_section)
    
    # Performance trend
    finishers = history[history['race_status'] == 'finished'].copy()
    if len(finishers) > 1:
        trend_section = Section("Performance Trend")
        
        finishers = finishers.sort_values('race_year')
        
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(finishers['race_year'], finishers['finish_time_minutes'], marker='o', linewidth=2)
        ax.set_xlabel('Year')
        ax.set_ylabel('Finish Time (minutes)')
        ax.set_title('Performance Over Time')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        trend_section.add(Chart(fig))
        plt.close(fig)
        report.add(trend_section)
    
    report.to_html(output_path)
