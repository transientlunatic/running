"""
Database storage for race results.

Provides SQLite-based persistent storage for normalized race results,
allowing tracking of races across multiple years.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from .models import NormalizedRaceResult, RaceCategory


class RaceResultsDatabase:
    """
    SQLite database for storing and querying race results.
    
    Features:
    - Store normalized race results persistently
    - Track races across multiple years
    - Query by race, year, runner, club
    - Export to DataFrame for analysis
    
    Example:
        >>> db = RaceResultsDatabase('race_results.db')
        >>> db.add_results(normalized_results, race_name='Tinto', race_year=2024)
        >>> tinto_all = db.get_race_results('Tinto')
        >>> tinto_2024 = db.get_race_results('Tinto', year=2024)
    """
    
    def __init__(self, db_path: str = 'race_results.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Store db_path as a plain string to satisfy equality checks in tests
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema if it doesn't exist."""
        cursor = self.conn.cursor()
        
        # Races table - tracks unique races
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS races (
                race_id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_name TEXT NOT NULL,
                race_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(race_name)
            )
        ''')
        
        # Race editions table - specific year/date for each race
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS race_editions (
                edition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                race_id INTEGER NOT NULL,
                race_year INTEGER,
                race_date TEXT,
                source_url TEXT,
                source_file TEXT,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (race_id) REFERENCES races(race_id),
                UNIQUE(race_id, race_year)
            )
        ''')
        
        # Results table - individual runner results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                edition_id INTEGER NOT NULL,
                position_overall INTEGER,
                position_gender INTEGER,
                position_category INTEGER,
                name TEXT,
                bib_number TEXT,
                gender TEXT,
                age_category TEXT,
                club TEXT,
                race_status TEXT,
                finish_time_seconds REAL,
                finish_time_minutes REAL,
                chip_time_seconds REAL,
                chip_time_minutes REAL,
                gun_time_seconds REAL,
                gun_time_minutes REAL,
                metadata TEXT,
                FOREIGN KEY (edition_id) REFERENCES race_editions(edition_id)
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_name ON results(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_club ON results(club)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_race_editions_year ON race_editions(race_year)')
        
        self.conn.commit()
    
    def add_race(self, race_name: str, race_category: Optional[str] = None) -> int:
        """
        Add or get a race.
        
        Args:
            race_name: Name of the race
            race_category: Category (e.g., 'marathon', 'fell_race')
            
        Returns:
            race_id
        """
        cursor = self.conn.cursor()
        
        # Try to insert, or get existing
        cursor.execute(
            'INSERT OR IGNORE INTO races (race_name, race_category) VALUES (?, ?)',
            (race_name, race_category)
        )
        
        cursor.execute('SELECT race_id FROM races WHERE race_name = ?', (race_name,))
        result = cursor.fetchone()
        self.conn.commit()
        
        return result[0]
    
    def add_race_edition(
        self,
        race_id: int,
        race_year: Optional[int] = None,
        race_date: Optional[str] = None,
        source_url: Optional[str] = None,
        source_file: Optional[str] = None,
        *,
        year: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a race edition (specific year/instance).
        
        Args:
            race_id: ID of the parent race
            race_year: Year of the race
            race_date: Date of the race (ISO format)
            source_url: URL where results were fetched
            source_file: File where results were imported from
            year: Alias for race_year to match test expectations
            metadata: Optional edition-level metadata (accepted but not stored)
            
        Returns:
            edition_id
        """
        cursor = self.conn.cursor()

        # Allow passing `year` as an alias for `race_year`
        if year is not None and race_year is None:
            race_year = year
        
        cursor.execute('''
            INSERT OR REPLACE INTO race_editions 
            (race_id, race_year, race_date, source_url, source_file)
            VALUES (?, ?, ?, ?, ?)
        ''', (race_id, race_year, race_date, source_url, source_file))
        
        edition_id = cursor.lastrowid
        self.conn.commit()
        
        return edition_id
    
    def add_results(
        self,
        results: List[NormalizedRaceResult],
        edition_id: Optional[int] = None,
        race_name: Optional[str] = None,
        race_year: Optional[int] = None,
        race_category: Optional[str] = None,
        source_url: Optional[str] = None,
        source_file: Optional[str] = None,
    ) -> int:
        """
        Add race results to the database.
        
        Args:
            results: List of NormalizedRaceResult objects
            edition_id: Existing race edition ID to attach results to (preferred)
            race_name: Name of the race (used if edition_id not provided)
            race_year: Year of the race (used if edition_id not provided)
            race_category: Race category (used if creating race)
            source_url: URL where results came from (stored on edition if created)
            source_file: File where results came from (stored on edition if created)
            
        Returns:
            Number of results added
        """
        # If an edition_id is not provided, create/get race and edition
        if edition_id is None:
            if race_name is None:
                raise ValueError("race_name must be provided when edition_id is None")
            race_id = self.add_race(race_name, race_category)
            edition_id = self.add_race_edition(
                race_id, race_year, None, source_url, source_file
            )
        
        # Add results
        cursor = self.conn.cursor()
        count = 0
        
        for result in results:
            # Convert metadata dict to JSON if present
            metadata_json = None
            if hasattr(result, 'metadata') and result.metadata:
                metadata_json = json.dumps(result.metadata)
            
            cursor.execute('''
                INSERT INTO results (
                    edition_id, position_overall, position_gender, position_category,
                    name, bib_number, gender, age_category, club, race_status,
                    finish_time_seconds, finish_time_minutes,
                    chip_time_seconds, chip_time_minutes,
                    gun_time_seconds, gun_time_minutes, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                edition_id,
                result.position_overall,
                result.position_gender,
                result.position_category,
                result.name,
                result.bib_number,
                result.gender,
                result.age_category,
                result.club,
                result.race_status,
                result.finish_time_seconds,
                result.finish_time_minutes,
                result.chip_time_seconds,
                result.chip_time_minutes,
                result.gun_time_seconds,
                result.gun_time_minutes,
                metadata_json
            ))
            count += 1
        
        self.conn.commit()
        return count
    
    def get_race_results(
        self,
        race_name: Optional[str] = None,
        year: Optional[int] = None,
        runner_name: Optional[str] = None,
        club: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Query race results.
        
        Args:
            race_name: Filter by race name
            year: Filter by year
            runner_name: Filter by runner name (partial match)
            club: Filter by club (partial match)
            
        Returns:
            DataFrame with results
        """
        query = '''
            SELECT 
                r.race_name,
                e.race_year,
                e.race_date,
                e.source_url,
                res.position_overall,
                res.position_gender,
                res.position_category,
                res.name,
                res.bib_number,
                res.gender,
                res.age_category,
                res.club,
                UPPER(res.race_status) as race_status,
                res.finish_time_seconds,
                res.finish_time_minutes,
                res.chip_time_seconds,
                res.chip_time_minutes,
                res.gun_time_seconds,
                res.gun_time_minutes
            FROM results res
            JOIN race_editions e ON res.edition_id = e.edition_id
            JOIN races r ON e.race_id = r.race_id
            WHERE 1=1
        '''
        
        params = []
        
        if race_name:
            query += ' AND r.race_name = ?'
            params.append(race_name)
        
        if year:
            query += ' AND e.race_year = ?'
            params.append(year)
        
        if runner_name:
            query += ' AND res.name LIKE ?'
            params.append(f'%{runner_name}%')
        
        if club:
            query += ' AND res.club LIKE ?'
            params.append(f'%{club}%')
        
        # Ensure rows with NULL position (e.g., DNF) are ordered after finishers
        query += ' ORDER BY e.race_year, (res.position_overall IS NULL), res.position_overall'
        
        df = pd.read_sql_query(query, self.conn, params=params)
        # Cast position columns to nullable integers to avoid float display
        for col in ['position_overall', 'position_gender', 'position_category']:
            if col in df.columns:
                df[col] = df[col].astype('Int64')
        return df
    
    def get_races(self) -> pd.DataFrame:
        """Get list of all races in database."""
        query = '''
            SELECT 
                r.race_name,
                r.race_category,
                COUNT(DISTINCT e.race_year) as num_years,
                MIN(e.race_year) as first_year,
                MAX(e.race_year) as last_year,
                COUNT(res.result_id) as total_results
            FROM races r
            LEFT JOIN race_editions e ON r.race_id = e.race_id
            LEFT JOIN results res ON e.edition_id = res.edition_id
            GROUP BY r.race_id, r.race_name, r.race_category
            ORDER BY r.race_name
        '''
        return pd.read_sql_query(query, self.conn)
    
    def get_runner_history(self, runner_name: str, race_name: Optional[str] = None) -> pd.DataFrame:
        """
        Get a runner's results history.
        
        Args:
            runner_name: Runner name (partial match)
            race_name: Optional filter by specific race
            
        Returns:
            DataFrame with runner's results over time
        """
        return self.get_race_results(race_name=race_name, runner_name=runner_name)
    
    def get_elo_rankings(self, year: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Get Elo rankings for runners.
        
        Args:
            year: Specific year (None = all-time)
            limit: Maximum number to return
            
        Returns:
            DataFrame with rankings
        """
        from .ranking import EloRanking
        elo = EloRanking(self.conn)
        return elo.get_rankings(year=year, limit=limit)
    
    def calculate_rankings(self, race_name: Optional[str] = None, race_year: Optional[int] = None, recalculate: bool = False):
        """
        Calculate or update Elo rankings.
        
        Ratings accumulate across all of a runner's races in chronological order.
        
        Args:
            race_name: Specific race (None = all races)
            race_year: Specific year (None = all years)
            recalculate: If True, recalculate all ratings from scratch
        """
        from .ranking import EloRanking
        elo = EloRanking(self.conn)
        elo.calculate_race_ratings(race_name=race_name, race_year=race_year, recalculate=recalculate)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
