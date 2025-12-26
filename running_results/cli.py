"""
Command-line interface for managing race results.

Provides commands for importing race results, querying the database,
and generating reports using otter-report.
"""
import click
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

from .manager import RaceResultsManager
from .models import RaceCategory


@click.group()
@click.option('--db', default='race_results.db', help='Database file path')
@click.pass_context
def cli(ctx, db):
    """
    Running Results - Manage and analyze race results.
    
    A comprehensive tool for importing, storing, and analyzing
    running race results across multiple years.
    """
    ctx.ensure_object(dict)
    ctx.obj['DB_PATH'] = db


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--name', required=True, help='Race name')
@click.option('--year', type=int, required=True, help='Race year')
@click.option('--category', type=click.Choice([c.value for c in RaceCategory]), 
              default='road_race', help='Race category')
@click.pass_context
def add(ctx, file_path, name, year, category):
    """
    Add race results from a file.
    
    Supports CSV, TSV, Excel, and HTML files.
    
    Example:
        running-results add tinto_2024.csv --name "Tinto Hill Race" --year 2024 --category fell_race
    """
    db_path = ctx.obj['DB_PATH']
    
    with RaceResultsManager(db_path) as manager:
        try:
            count = manager.add_from_file(
                file_path=file_path,
                race_name=name,
                race_year=year,
                race_category=category
            )
            click.echo(f"✓ Successfully added {count} results to {name} ({year})")
        except Exception as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--name', required=True, help='Race name')
@click.option('--year', type=int, required=True, help='Race year')
@click.option('--category', type=click.Choice([c.value for c in RaceCategory]),
              default='road_race', help='Race category')
@click.option('--table-selector', help='CSS selector for results table')
@click.pass_context
def import_url(ctx, url, name, year, category, table_selector):
    """
    Import race results from a URL.
    
    Scrapes HTML tables from web pages.
    
    Example:
        running-results import-url https://example.com/results.html --name "Parkrun" --year 2024
    """
    db_path = ctx.obj['DB_PATH']
    
    with RaceResultsManager(db_path) as manager:
        try:
            count = manager.add_from_url(
                url=url,
                race_name=name,
                race_year=year,
                race_category=category,
                table_selector=table_selector
            )
            click.echo(f"✓ Successfully imported {count} results from {url}")
        except Exception as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.pass_context
def list_races(ctx):
    """
    List all races in the database.
    
    Shows summary information including years covered and total results.
    """
    db_path = ctx.obj['DB_PATH']
    
    with RaceResultsManager(db_path) as manager:
        races = manager.list_races()
        
        if len(races) == 0:
            click.echo("No races found in database.")
            return
        
        click.echo(f"\nFound {len(races)} race(s):\n")
        
        for _, race in races.iterrows():
            click.echo(f"  {race['race_name']} ({race['race_category']})")
            click.echo(f"    Years: {race['first_year']}-{race['last_year']} ({race['num_years']} editions)")
            click.echo(f"    Total results: {race['total_results']}")
            click.echo()


@cli.command()
@click.option('--name', help='Race name')
@click.option('--year', type=int, help='Race year')
@click.option('--runner', help='Runner name')
@click.option('--club', help='Club name')
@click.option('--output', type=click.Path(), help='Output file (CSV)')
@click.pass_context
def query(ctx, name, year, runner, club, output):
    """
    Query race results.
    
    Filter by race name, year, runner, or club.
    
    Example:
        running-results query --name "Tinto Hill Race" --year 2024
        running-results query --club Carnethy --output carnethy_results.csv
    """
    db_path = ctx.obj['DB_PATH']
    
    if name:
        with RaceResultsManager(db_path) as manager:
            results = manager.get_race(name, year=year)
    elif runner:
        with RaceResultsManager(db_path) as manager:
            results = manager.get_runner_history(runner, race_name=name)
    else:
        with RaceResultsManager(db_path) as manager:
            results = manager.search_results(
                race_name=name,
                club=club
            )
    
    if len(results) == 0:
        click.echo("No results found.")
        return
    
    if output:
        results.to_csv(output, index=False)
        click.echo(f"✓ Exported {len(results)} results to {output}")
    else:
        click.echo(f"\nFound {len(results)} result(s):\n")
        # Display first 20 rows
        display_df = results.head(20)
        click.echo(display_df.to_string(index=False))
        if len(results) > 20:
            click.echo(f"\n... and {len(results) - 20} more rows")


@cli.command()
@click.argument('race_name')
@click.option('--year', type=int, help='Specific year (default: all years)')
@click.option('--output', type=click.Path(), default='race_report.html', help='Output file')
@click.option('--format', type=click.Choice(['html', 'pdf']), default='html', help='Output format')
@click.pass_context
def report(ctx, race_name, year, output, format):
    """
    Generate a comprehensive race report.
    
    Creates an HTML or PDF report with statistics, charts, and tables
    using otter-report.
    
    Example:
        running-results report "Tinto Hill Race" --year 2024
        running-results report "Edinburgh Marathon" --output marathon_report.html
    """
    db_path = ctx.obj['DB_PATH']
    
    try:
        from .reporting import generate_race_report
    except ImportError:
        click.echo("✗ Error: otter-report not installed. Install with: pip install otter-report", err=True)
        sys.exit(1)
    
    with RaceResultsManager(db_path) as manager:
        results = manager.get_race(race_name, year=year)
        
        if len(results) == 0:
            click.echo(f"✗ No results found for {race_name}" + (f" ({year})" if year else ""), err=True)
            sys.exit(1)
        
        click.echo(f"Generating report for {race_name}" + (f" ({year})" if year else "") + "...")
        
        try:
            generate_race_report(
                results=results,
                race_name=race_name,
                race_year=year,
                output_path=output,
                output_format=format
            )
            click.echo(f"✓ Report generated: {output}")
        except Exception as e:
            click.echo(f"✗ Error generating report: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.argument('race_name')
@click.option('--output', type=click.Path(), default='comparison_report.html', help='Output file')
@click.pass_context
def compare(ctx, race_name, output):
    """
    Generate a multi-year comparison report.
    
    Compares statistics and trends across all years of a race.
    
    Example:
        running-results compare "Tinto Hill Race" --output tinto_comparison.html
    """
    db_path = ctx.obj['DB_PATH']
    
    try:
        from .reporting import generate_comparison_report
    except ImportError:
        click.echo("✗ Error: otter-report not installed. Install with: pip install otter-report", err=True)
        sys.exit(1)
    
    with RaceResultsManager(db_path) as manager:
        results = manager.get_race(race_name)
        
        if len(results) == 0:
            click.echo(f"✗ No results found for {race_name}", err=True)
            sys.exit(1)
        
        years = results['race_year'].nunique()
        click.echo(f"Generating comparison report for {race_name} ({years} years)...")
        
        try:
            generate_comparison_report(
                results=results,
                race_name=race_name,
                output_path=output
            )
            click.echo(f"✓ Report generated: {output}")
        except Exception as e:
            click.echo(f"✗ Error generating report: {e}", err=True)
            sys.exit(1)


@cli.command()
@click.argument('runner_name')
@click.option('--race', help='Filter by race name')
@click.option('--output', type=click.Path(), default='runner_report.html', help='Output file')
@click.pass_context
def runner(ctx, runner_name, race, output):
    """
    Generate a runner history report.
    
    Shows a runner's performance over time across races.
    
    Example:
        running-results runner "John Smith" --race "Tinto Hill Race"
    """
    db_path = ctx.obj['DB_PATH']
    
    try:
        from .reporting import generate_runner_report
    except ImportError:
        click.echo("✗ Error: otter-report not installed. Install with: pip install otter-report", err=True)
        sys.exit(1)
    
    with RaceResultsManager(db_path) as manager:
        history = manager.get_runner_history(runner_name, race_name=race)
        
        if len(history) == 0:
            click.echo(f"✗ No results found for {runner_name}", err=True)
            sys.exit(1)
        
        click.echo(f"Generating report for {runner_name}...")
        
        try:
            generate_runner_report(
                history=history,
                runner_name=runner_name,
                output_path=output
            )
            click.echo(f"✓ Report generated: {output}")
        except Exception as e:
            click.echo(f"✗ Error generating report: {e}", err=True)
            sys.exit(1)


if __name__ == '__main__':
    cli(obj={})
