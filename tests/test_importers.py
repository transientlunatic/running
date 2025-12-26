"""
Tests for running_results.importers module.
"""
import pytest
import pandas as pd
from io import StringIO
from running_results.importers import ResultsImporter, SmartImporter
from running_results.models import ColumnMapping


class TestResultsImporter:
    """Test the ResultsImporter class."""

    def test_from_text_csv(self, sample_csv_content):
        """Test importing from CSV text."""
        importer = ResultsImporter()
        df = importer.from_text(sample_csv_content)

        assert len(df) == 5
        assert 'Position' in df.columns
        assert 'Name' in df.columns
        assert df.loc[0, 'Name'] == 'John Smith'

    def test_from_text_tsv(self):
        """Test importing from TSV text."""
        tsv_content = "Pos\tName\tClub\tTime\n1\tJohn Smith\tEdinburgh\t31:45\n2\tJane Doe\tCarnethy\t32:10"
        importer = ResultsImporter()
        df = importer.from_text(tsv_content, delimiter='\t')

        assert len(df) == 2
        assert df.loc[0, 'Name'] == 'John Smith'

    def test_from_text_auto_delimiter(self):
        """Test auto-detecting delimiter."""
        csv_content = "Pos,Name,Time\n1,John Smith,31:45"
        tsv_content = "Pos\tName\tTime\n1\tJohn Smith\t31:45"

        importer = ResultsImporter()
        df_csv = importer.from_text(csv_content)
        df_tsv = importer.from_text(tsv_content)

        assert len(df_csv) == 1
        assert len(df_tsv) == 1

    def test_from_file_csv(self, temp_csv_file, sample_csv_content):
        """Test importing from CSV file."""
        # Write content to file
        with open(temp_csv_file, 'w') as f:
            f.write(sample_csv_content)

        importer = ResultsImporter()
        df = importer.from_file(temp_csv_file)

        assert len(df) == 5
        assert df.loc[0, 'Name'] == 'John Smith'

    def test_from_file_nonexistent(self):
        """Test importing from nonexistent file raises error."""
        importer = ResultsImporter()
        with pytest.raises(FileNotFoundError):
            importer.from_file('/nonexistent/file.csv')

    def test_session_has_user_agent(self):
        """Test that session has a User-Agent header."""
        importer = ResultsImporter()
        assert 'User-Agent' in importer.session.headers
        assert 'running-results' in importer.session.headers['User-Agent']


class TestSmartImporter:
    """Test the SmartImporter class."""

    def test_import_and_normalize_from_text(self, sample_csv_content):
        """Test importing and normalizing in one step."""
        mapping = ColumnMapping(
            position_overall='Position',
            name='Name',
            club='Club',
            finish_time='Time',
            age_category='Category'
        )

        importer = SmartImporter()
        df = importer.import_and_normalize(
            source=StringIO(sample_csv_content),
            column_mapping=mapping
        )

        assert len(df) == 5
        assert 'name' in df.columns  # Normalized column name
        assert 'finish_time_seconds' in df.columns
        assert df.loc[0, 'name'] == 'John Smith'

    def test_import_and_normalize_from_file(self, temp_csv_file, sample_csv_content):
        """Test importing and normalizing from file."""
        # Write content to file
        with open(temp_csv_file, 'w') as f:
            f.write(sample_csv_content)

        mapping = ColumnMapping(
            position_overall='Position',
            name='Name',
            finish_time='Time'
        )

        importer = SmartImporter()
        df = importer.import_and_normalize(
            source=temp_csv_file,
            column_mapping=mapping
        )

        assert len(df) == 5
        assert 'finish_time_seconds' in df.columns

    def test_import_with_auto_column_detection(self, sample_csv_content):
        """Test auto-detecting columns during import."""
        # This tests that common column names are recognized
        importer = SmartImporter()
        df = importer.import_and_normalize(source=StringIO(sample_csv_content))

        # Should still work even without explicit mapping for common column names
        assert len(df) == 5


class TestImporterHelpers:
    """Test helper methods in importers."""

    def test_detect_delimiter_comma(self):
        """Test detecting comma delimiter."""
        from running_results.importers import ResultsImporter
        importer = ResultsImporter()

        # Access the internal method if available, or test via from_text
        content = "A,B,C\n1,2,3"
        df = importer.from_text(content)
        assert len(df.columns) == 3

    def test_detect_delimiter_tab(self):
        """Test detecting tab delimiter."""
        from running_results.importers import ResultsImporter
        importer = ResultsImporter()

        content = "A\tB\tC\n1\t2\t3"
        df = importer.from_text(content)
        assert len(df.columns) == 3

    def test_empty_file_handling(self, temp_csv_file):
        """Test handling empty file."""
        # Create empty file
        with open(temp_csv_file, 'w') as f:
            f.write('')

        importer = ResultsImporter()
        # Should raise an error or return empty DataFrame
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            importer.from_file(temp_csv_file)
