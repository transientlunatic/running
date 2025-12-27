"""
Runner ranking system using Elo rating.

Provides functionality to:
- Identify and deduplicate runners across races
- Calculate Elo ratings based on race finishes
- Track runner progression over time
"""

import sqlite3
import pandas as pd
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import math


class RunnerRegistry:
    """
    Manage unique runner identification and deduplication.
    
    Runners are identified by:
    1. Name and club (primary key)
    2. With consistency checking (same name + club combo across races)
    
    Example:
        >>> registry = RunnerRegistry(db_conn)
        >>> runner_id = registry.get_or_create_runner('John Doe', 'Carnethy')
        >>> similar = registry.find_similar_runners('John Doe')
    """
    
    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize runner registry.
        
        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
        self._create_tables()
    
    def _create_tables(self):
        """Create runner and ranking tables."""
        cursor = self.conn.cursor()
        
        # Runners table - unique runners identified by name + club
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runners (
                runner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                club TEXT,
                first_seen_year INTEGER,
                last_seen_year INTEGER,
                appearance_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, club)
            )
        ''')
        
        # Elo ratings - track rating over time
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS elo_ratings (
                rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                runner_id INTEGER NOT NULL,
                race_year INTEGER NOT NULL,
                rating REAL DEFAULT 1500,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                games_dnf INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (runner_id) REFERENCES runners(runner_id),
                UNIQUE(runner_id, race_year)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runners_name ON runners(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_runners_club ON runners(club)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_elo_runner_year ON elo_ratings(runner_id, race_year)')
        
        self.conn.commit()
    
    def get_or_create_runner(
        self,
        name: str,
        club: Optional[str] = None,
        year: Optional[int] = None,
        increment_appearance: bool = True
    ) -> int:
        """
        Get or create a runner record.
        
        Args:
            name: Runner name
            club: Running club (optional, helps with deduplication)
            year: Year of appearance (for tracking first/last seen)
            increment_appearance: If True, increment appearance_count (default: True)
            
        Returns:
            runner_id
        """
        cursor = self.conn.cursor()
        
        # Normalize inputs
        name = name.strip() if name else None
        club = club.strip() if club else None
        
        if not name:
            return None
        
        # Try to insert new runner
        cursor.execute(
            '''INSERT OR IGNORE INTO runners 
               (name, club, first_seen_year, last_seen_year, appearance_count) 
               VALUES (?, ?, ?, ?, 0)''',
            (name, club, year, year)
        )
        
        # Get runner_id
        cursor.execute(
            'SELECT runner_id FROM runners WHERE name = ? AND club IS ?',
            (name, club)
        )
        result = cursor.fetchone()
        
        if result:
            runner_id = result[0]
            # Update last_seen_year and optionally appearance_count
            if year:
                if increment_appearance:
                    cursor.execute(
                        '''UPDATE runners 
                           SET last_seen_year = MAX(last_seen_year, ?), 
                               appearance_count = appearance_count + 1
                           WHERE runner_id = ?''',
                        (year, runner_id)
                    )
                else:
                    cursor.execute(
                        '''UPDATE runners 
                           SET last_seen_year = MAX(last_seen_year, ?)
                           WHERE runner_id = ?''',
                        (year, runner_id)
                    )
            self.conn.commit()
            return runner_id
        
        return None
    
    def find_similar_runners(self, name: str, fuzzy: bool = False) -> List[Dict]:
        """
        Find runners with similar names.
        
        Args:
            name: Runner name to search for
            fuzzy: If True, use fuzzy matching (substring, etc.)
            
        Returns:
            List of runner dicts with runner_id, name, club, appearance_count, first_seen_year, last_seen_year
        """
        cursor = self.conn.cursor()
        name = name.strip()
        
        if fuzzy:
            # Fuzzy: contains or is contained in
            query = '''
                SELECT runner_id, name, club, appearance_count, first_seen_year, last_seen_year
                FROM runners
                WHERE name LIKE ? OR ? LIKE name
                ORDER BY appearance_count DESC
            '''
            pattern = f'%{name}%'
            cursor.execute(query, (pattern, pattern))
        else:
            # Exact match
            cursor.execute(
                '''SELECT runner_id, name, club, appearance_count, first_seen_year, last_seen_year
                   FROM runners WHERE name = ?''',
                (name,)
            )
        
        columns = ['runner_id', 'name', 'club', 'appearance_count', 'first_seen_year', 'last_seen_year']
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


class EloRanking:
    """
    Elo rating system for runners.
    
    Standard Elo formula adapted for running:
    - Initial rating: 1500
    - K-factor: 32 (determines magnitude of rating changes)
    - Expected score based on rating difference
    - Finishes ranked by position (lower position = better)
    
    Example:
        >>> elo = EloRanking(db_conn)
        >>> elo.calculate_race_ratings('Tinto', 2024)
        >>> rating = elo.get_runner_rating('John Doe', 'Carnethy', 2024)
    """
    
    # Elo parameters
    INITIAL_RATING = 1500
    K_FACTOR = 32
    
    def __init__(self, db_conn: sqlite3.Connection):
        """
        Initialize Elo rating system.
        
        Args:
            db_conn: SQLite database connection
        """
        self.conn = db_conn
        self.registry = RunnerRegistry(db_conn)
    
    def calculate_race_ratings(
        self,
        race_name: Optional[str] = None,
        race_year: Optional[int] = None,
        recalculate: bool = False
    ):
        """
        Calculate or update Elo ratings based on race results.
        
        Processes all races in chronological order, accumulating ratings across
        a runner's entire career. Each race updates their rating based on their
        performance relative to other runners in that race.
        
        Args:
            race_name: Specific race to process (None = all races)
            race_year: Specific year (None = all years)
            recalculate: If True, recalculate all ratings from scratch
        """
        cursor = self.conn.cursor()
        
        # Build query to get results
        query = '''
            SELECT 
                r.result_id,
                r.name, 
                r.club,
                r.position_overall,
                r.race_status,
                re.race_year,
                re.race_date,
                re.edition_id,
                ra.race_name
            FROM results r
            JOIN race_editions re ON r.edition_id = re.edition_id
            JOIN races ra ON re.race_id = ra.race_id
            WHERE r.race_status = 'finished'
        '''
        
        params = []
        if race_name:
            query += ' AND ra.race_name = ?'
            params.append(race_name)
        if race_year:
            query += ' AND re.race_year = ?'
            params.append(race_year)
        
        # CRITICAL: Order by date, then position - processes races chronologically
        query += ' ORDER BY re.race_date ASC, re.race_year ASC, r.position_overall ASC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if not results:
            return
        
        # If recalculating, clear existing ratings
        if recalculate:
            cursor.execute('DELETE FROM elo_ratings')
            self.conn.commit()
        
        # Group results by race (edition_id) in chronological order
        races_by_edition = {}
        race_order = []  # Track order of editions
        
        for result in results:
            (result_id, name, club, position, status, year, date, edition_id, race_name) = result
            
            if edition_id not in races_by_edition:
                races_by_edition[edition_id] = {
                    'year': year,
                    'date': date,
                    'race_name': race_name,
                    'runners': []
                }
                race_order.append(edition_id)
            
            races_by_edition[edition_id]['runners'].append((name, club, position))
        
        # Process each race in chronological order
        # Ratings accumulate: each race updates from the previous race result
        for edition_id in race_order:
            race_info = races_by_edition[edition_id]
            self._update_race_elo(
                race_info['year'],
                race_info['runners'],
                date=race_info['date']
            )
    
    def _update_race_elo(self, year: int, runners: List[Tuple[str, str, int]], date: Optional[str] = None):
        """
        Update Elo ratings for runners in a specific race.
        
        Ratings accumulate across races. Each runner's rating is carried forward
        from previous races, or initialized to INITIAL_RATING if this is their first race.
        
        Args:
            year: Race year
            runners: List of (name, club, position) tuples, sorted by position
            date: Race date (optional, for ordering)
        """
        cursor = self.conn.cursor()
        
        # Ensure all runners exist (without incrementing appearance_count)
        runner_ids = []
        for name, club, _ in runners:
            runner_id = self.registry.get_or_create_runner(name, club, year, increment_appearance=False)
            runner_ids.append(runner_id)
        
        # Now increment appearance_count once per unique runner
        for name, club, _ in runners:
            cursor.execute(
                '''UPDATE runners 
                   SET appearance_count = appearance_count + 1
                   WHERE name = ? AND club IS ?''',
                (name, club)
            )
        self.conn.commit()
        
        # Get current ratings for all runners (carry forward from previous races)
        # Initialize to INITIAL_RATING if no previous rating exists
        current_ratings = {}
        for runner_id in runner_ids:
            cursor.execute(
                '''SELECT rating FROM elo_ratings 
                   WHERE runner_id = ? 
                   ORDER BY race_year DESC 
                   LIMIT 1''',
                (runner_id,)
            )
            result = cursor.fetchone()
            current_ratings[runner_id] = result[0] if result else self.INITIAL_RATING
        
        # Create new rating entries for this race/year
        # These will store the updated ratings after this race
        for runner_id in runner_ids:
            cursor.execute(
                '''INSERT OR IGNORE INTO elo_ratings (runner_id, race_year, rating, games_played)
                   VALUES (?, ?, ?, 0)''',
                (runner_id, year, current_ratings[runner_id])
            )
        self.conn.commit()
        
        # Pair each runner with all other runners
        # Each directed comparison is a "game" where the better finisher "wins"
        # Note: This creates O(N²) games for N runners in a race
        # E.g., with 157 finishers, each runner plays 156 games (one vs each other runner)
        # But they participate in 312 directed matches: 156 where they won/lost + 156 where opponent won/lost
        # We count "games_played" as total directed comparisons for match density tracking
        for i, (name_i, club_i, pos_i) in enumerate(runners):
            runner_id_i = runner_ids[i]
            
            # Get current rating
            cursor.execute(
                'SELECT rating FROM elo_ratings WHERE runner_id = ? AND race_year = ?',
                (runner_id_i, year)
            )
            result = cursor.fetchone()
            rating_i = result[0] if result else self.INITIAL_RATING
            
            # Compare with all other runners
            for j, (name_j, club_j, pos_j) in enumerate(runners):
                if i == j:
                    continue
                
                runner_id_j = runner_ids[j]
                
                # Get opponent rating
                cursor.execute(
                    'SELECT rating FROM elo_ratings WHERE runner_id = ? AND race_year = ?',
                    (runner_id_j, year)
                )
                result = cursor.fetchone()
                rating_j = result[0] if result else self.INITIAL_RATING
                
                # Determine who won (lower position = better = win)
                if pos_i < pos_j:
                    # Runner i won
                    score_i = 1.0
                    score_j = 0.0
                else:
                    # Runner j won
                    score_i = 0.0
                    score_j = 1.0
                
                # Calculate expected scores
                expected_i = self._expected_score(rating_i, rating_j)
                expected_j = self._expected_score(rating_j, rating_i)
                
                # Calculate new ratings
                new_rating_i = rating_i + self.K_FACTOR * (score_i - expected_i)
                new_rating_j = rating_j + self.K_FACTOR * (score_j - expected_j)
                
                # Update ratings
                cursor.execute(
                    '''UPDATE elo_ratings 
                       SET rating = ?, games_played = games_played + 1
                       WHERE runner_id = ? AND race_year = ?''',
                    (new_rating_i, runner_id_i, year)
                )
                
                cursor.execute(
                    '''UPDATE elo_ratings 
                       SET rating = ?, games_played = games_played + 1
                       WHERE runner_id = ? AND race_year = ?''',
                    (new_rating_j, runner_id_j, year)
                )
                
                rating_i = new_rating_i
                rating_j = new_rating_j
        
        self.conn.commit()
    
    @staticmethod
    def _expected_score(rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for player A against player B.
        
        Args:
            rating_a: Rating of player A
            rating_b: Rating of player B
            
        Returns:
            Expected score (0-1)
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def get_runner_rating(
        self,
        name: str,
        club: Optional[str] = None,
        year: Optional[int] = None
    ) -> Optional[float]:
        """
        Get Elo rating for a runner.
        
        Args:
            name: Runner name
            club: Running club (optional)
            year: Specific year (None = latest)
            
        Returns:
            Elo rating or None if not found
        """
        cursor = self.conn.cursor()
        
        # Find runner
        cursor.execute(
            'SELECT runner_id FROM runners WHERE name = ? AND club IS ?',
            (name, club)
        )
        result = cursor.fetchone()
        if not result:
            return None
        
        runner_id = result[0]
        
        if year:
            # Get rating for specific year
            cursor.execute(
                'SELECT rating FROM elo_ratings WHERE runner_id = ? AND race_year = ?',
                (runner_id, year)
            )
        else:
            # Get latest rating
            cursor.execute(
                'SELECT rating FROM elo_ratings WHERE runner_id = ? ORDER BY race_year DESC LIMIT 1',
                (runner_id,)
            )
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_rankings(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
        min_games: int = 1
    ) -> pd.DataFrame:
        """
        Get overall rankings.
        
        Args:
            year: Specific year - returns most recent rating as of that year (None = all-time)
            limit: Maximum number of runners to return
            min_games: Minimum games played to be included
            
        Returns:
            DataFrame with runner rankings
        """
        if year:
            # Get most recent rating as of the specified year, and count races up to that year
            query = '''
                WITH latest_ratings AS (
                    SELECT 
                        runner_id,
                        race_year,
                        rating,
                        games_played,
                        ROW_NUMBER() OVER (PARTITION BY runner_id ORDER BY race_year DESC) as rn
                    FROM elo_ratings
                    WHERE race_year <= ?
                        AND games_played >= ?
                )
                SELECT 
                    r.runner_id,
                    r.name,
                    r.club,
                    lr.race_year,
                    lr.rating,
                    lr.games_played,
                    r.appearance_count,
                    (
                        SELECT COUNT(DISTINCT re.edition_id)
                        FROM results res
                        JOIN race_editions re ON res.edition_id = re.edition_id
                        WHERE res.name = r.name
                          AND COALESCE(res.club, '') = COALESCE(r.club, '')
                          AND re.race_year <= lr.race_year
                    ) AS races_count
                FROM runners r
                JOIN latest_ratings lr ON r.runner_id = lr.runner_id
                WHERE lr.rn = 1
                ORDER BY lr.rating DESC
            '''
            params = [year, min_games]
        else:
            # Get the very latest rating for each runner (all-time), and count all races
            query = '''
                WITH latest_ratings AS (
                    SELECT 
                        runner_id,
                        race_year,
                        rating,
                        games_played,
                        ROW_NUMBER() OVER (PARTITION BY runner_id ORDER BY race_year DESC) as rn
                    FROM elo_ratings
                    WHERE games_played >= ?
                )
                SELECT 
                    r.runner_id,
                    r.name,
                    r.club,
                    lr.race_year,
                    lr.rating,
                    lr.games_played,
                    r.appearance_count,
                    (
                        SELECT COUNT(DISTINCT res.edition_id)
                        FROM results res
                        WHERE res.name = r.name
                          AND COALESCE(res.club, '') = COALESCE(r.club, '')
                    ) AS races_count
                FROM runners r
                JOIN latest_ratings lr ON r.runner_id = lr.runner_id
                WHERE lr.rn = 1
                ORDER BY lr.rating DESC
            '''
            params = [min_games]
        
        if limit:
            query += f' LIMIT {limit}'
        
        return pd.read_sql_query(query, self.conn, params=params)
