"""
Tests for the CLI module.

Tests all click commands using CliRunner.
"""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from running_results.cli import cli


class TestCLI:
    """Test the command line interface."""

    def test_cli_help(self):
        """Test main CLI help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Running Results" in result.output

    def test_cli_version(self):
        """Test version flag (--version not implemented)."""
        runner = CliRunner()
        # Click requires version to be set up, skip this test or implement it
        pass

    def test_add_command_help(self):
        """Test add command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["add", "--help"])
        assert result.exit_code == 0
        assert "Add race results from a file" in result.output

    def test_import_url_help(self):
        """Test import-url command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["import-url", "--help"])
        assert result.exit_code == 0
        assert "Import race results from a URL" in result.output

    def test_list_races_help(self):
        """Test list-races command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["list-races", "--help"])
        assert result.exit_code == 0
        assert "List all races" in result.output

    def test_query_help(self):
        """Test query command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["query", "--help"])
        assert result.exit_code == 0
        assert "Query race results" in result.output

    def test_report_help(self):
        """Test report command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0
        assert "comprehensive race report" in result.output

    def test_compare_help(self):
        """Test compare command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--help"])
        assert result.exit_code == 0
        assert "Generate a multi-year comparison" in result.output

    def test_runner_help(self):
        """Test runner command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["runner", "--help"])
        assert result.exit_code == 0
        assert "Generate a runner history report" in result.output


class TestAddCommand:
    """Test the add command."""

    def test_add_csv_file(self, sample_csv_file, temp_db):
        """Test adding results from CSV file."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(temp_db),
                "add",
                str(sample_csv_file),
                "--name",
                "Test Race",
                "--year",
                "2024",
            ],
        )
        if result.exit_code != 0:
            print(f"Error output: {result.output}")
            print(
                f"Exception: {result.exception if hasattr(result, 'exception') else 'None'}"
            )
        assert result.exit_code == 0
        assert "Successfully added" in result.output

    def test_add_missing_race_name(self, sample_csv_file, temp_db):
        """Test add without race name."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(temp_db), "add", str(sample_csv_file), "--year", "2024"]
        )
        assert result.exit_code != 0

    def test_add_missing_race_year(self, sample_csv_file, temp_db):
        """Test add without race year."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--db", str(temp_db), "add", str(sample_csv_file), "--name", "Test Race"],
        )
        assert result.exit_code != 0

    def test_add_with_metadata(self, sample_csv_file, temp_db):
        """Test add with full metadata."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(temp_db),
                "add",
                str(sample_csv_file),
                "--name",
                "Test Race",
                "--year",
                "2024",
                "--category",
                "road_race",
            ],
        )
        assert result.exit_code == 0
        assert "Successfully added" in result.output

    def test_add_with_custom_mapping(self, temp_db, tmp_path):
        """Test add with custom column mapping."""
        # Create a CSV with custom columns
        csv_file = tmp_path / "custom.csv"
        csv_file.write_text("Runner,Team,Time\nJohn Smith,Test AC,42:51\n")

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(temp_db),
                "add",
                str(csv_file),
                "--name",
                "Test Race",
                "--year",
                "2024",
            ],
        )
        assert result.exit_code == 0

    def test_add_nonexistent_file(self, temp_db):
        """Test add with non-existent file."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(temp_db),
                "add",
                "nonexistent.csv",
                "--name",
                "Test Race",
                "--year",
                "2024",
            ],
        )
        assert result.exit_code != 0


class TestListRacesCommand:
    """Test the list-races command."""

    def test_list_empty_database(self, temp_db):
        """Test listing races from empty database."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(temp_db), "list-races"])
        assert result.exit_code == 0
        assert "No races found" in result.output

    def test_list_with_races(self, populated_db):
        """Test listing races with data."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(populated_db), "list-races"])
        assert result.exit_code == 0
        assert "Test Race" in result.output


class TestQueryCommand:
    """Test the query command."""

    def test_query_all_results(self, populated_db):
        """Test querying all results."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(populated_db), "query"])
        assert result.exit_code == 0

    def test_query_by_race_name(self, populated_db):
        """Test querying by race name."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(populated_db), "query", "--name", "Test Race"]
        )
        assert result.exit_code == 0

    def test_query_by_year(self, populated_db):
        """Test querying by year."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "query",
                "--name",
                "Test Race",
                "--year",
                "2024",
            ],
        )
        assert result.exit_code == 0

    def test_query_by_runner(self, populated_db):
        """Test querying by runner name."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(populated_db), "query", "--runner", "John"]
        )
        assert result.exit_code == 0

    def test_query_by_club(self, populated_db):
        """Test querying by club."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(populated_db), "query", "--club", "Test AC"]
        )
        assert result.exit_code == 0

    def test_query_export_csv(self, populated_db, tmp_path):
        """Test exporting query results to CSV."""
        output_file = tmp_path / "export.csv"
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "query",
                "--name",
                "Test Race",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Exported" in result.output

    def test_query_no_results(self, populated_db):
        """Test query with no matching results."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(populated_db), "query", "--runner", "Nonexistent Runner"]
        )
        assert result.exit_code == 0
        assert "No results found" in result.output


class TestReportCommand:
    """Test the report command."""

    def test_report_help(self):
        """Test report command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["report", "--help"])
        assert result.exit_code == 0

    def test_report_missing_race_name(self, populated_db):
        """Test report without race name."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(populated_db), "report"])
        assert result.exit_code != 0

    def test_report_html(self, populated_db, tmp_path, monkeypatch):
        """Test generating HTML report."""
        output_file = tmp_path / "report.html"

        # Mock otter-report if not available
        def mock_generate_race_report(*args, **kwargs):
            output_path = kwargs.get("output_path", "race_report.html")
            Path(output_path).write_text("<html>Mock Report</html>")

        from running_results import reporting

        monkeypatch.setattr(
            reporting, "generate_race_report", mock_generate_race_report
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "report",
                "Test Race",
                "--year",
                "2024",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists() or "generated" in result.output.lower()

    def test_report_pdf(self, populated_db, tmp_path, monkeypatch):
        """Test generating PDF report."""
        output_file = tmp_path / "report.pdf"

        def mock_generate_race_report(*args, **kwargs):
            output_path = kwargs.get("output_path", "race_report.pdf")
            Path(output_path).write_text("Mock PDF")

        from running_results import reporting

        monkeypatch.setattr(
            reporting, "generate_race_report", mock_generate_race_report
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "report",
                "Test Race",
                "--year",
                "2024",
                "--format",
                "pdf",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0


class TestCompareCommand:
    """Test the compare command."""

    def test_compare_help(self):
        """Test compare command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["compare", "--help"])
        assert result.exit_code == 0

    def test_compare_missing_race_name(self, populated_db):
        """Test compare without race name."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(populated_db), "compare"])
        assert result.exit_code != 0

    def test_compare_success(self, populated_db, tmp_path, monkeypatch):
        """Test generating comparison report."""
        output_file = tmp_path / "comparison.html"

        def mock_generate_comparison_report(*args, **kwargs):
            output_path = kwargs.get("output_path", "comparison_report.html")
            Path(output_path).write_text("<html>Mock Comparison</html>")

        from running_results import reporting

        monkeypatch.setattr(
            reporting, "generate_comparison_report", mock_generate_comparison_report
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "compare",
                "Test Race",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0


class TestRunnerCommand:
    """Test the runner command."""

    def test_runner_help(self):
        """Test runner command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["runner", "--help"])
        assert result.exit_code == 0

    def test_runner_missing_name(self, populated_db):
        """Test runner without name."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--db", str(populated_db), "runner"])
        assert result.exit_code != 0

    def test_runner_success(self, populated_db, tmp_path, monkeypatch):
        """Test generating runner report."""
        output_file = tmp_path / "runner.html"

        def mock_generate_runner_report(*args, **kwargs):
            output_path = kwargs.get("output_path", "runner_report.html")
            Path(output_path).write_text("<html>Mock Runner Report</html>")

        from running_results import reporting

        monkeypatch.setattr(
            reporting, "generate_runner_report", mock_generate_runner_report
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--db",
                str(populated_db),
                "runner",
                "John Smith",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_runner_not_found(self, populated_db):
        """Test runner with no matching results."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--db", str(populated_db), "runner", "Nonexistent Runner"]
        )
        assert result.exit_code != 0
        assert "No results found" in result.output
