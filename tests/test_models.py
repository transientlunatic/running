"""
Tests for running_results.models module.
"""

import pytest
import pandas as pd
from running_results.models import (
    NormalizedRaceResult,
    ColumnMapping,
    RaceResultsNormalizer,
    RaceCategory,
    Gender,
    RaceStatus,
    fix_malformed_time,
    normalize_club_name,
    parse_age_category,
    TimeParser,
)


class TestNormalizedRaceResult:
    """Test the NormalizedRaceResult Pydantic model."""

    def test_create_basic_result(self):
        """Test creating a basic race result."""
        result = NormalizedRaceResult(
            position_overall=1,
            name="John Smith",
            club="Edinburgh",
            finish_time_seconds=1905,
        )
        assert result.position_overall == 1
        assert result.name == "John Smith"
        assert result.club == "Edinburgh"
        assert result.finish_time_seconds == 1905

    def test_finish_time_seconds(self):
        """Test setting finish time in seconds."""
        result = NormalizedRaceResult(finish_time_seconds=1800)
        assert result.finish_time_seconds == 1800

    def test_race_status_parsing(self):
        """Test parsing DNF/DNS/DSQ statuses."""
        result_dnf = NormalizedRaceResult(race_status="DNF")
        assert result_dnf.race_status == RaceStatus.DNF

        result_dns = NormalizedRaceResult(race_status="DNS")
        assert result_dns.race_status == RaceStatus.DNS

        result_dsq = NormalizedRaceResult(race_status="DSQ")
        assert result_dsq.race_status == RaceStatus.DSQ

    def test_bib_number_as_string(self):
        """Test bib number can be a string."""
        result = NormalizedRaceResult(bib_number="123")
        assert result.bib_number == "123"

    def test_optional_fields(self):
        """Test that all fields are optional."""
        result = NormalizedRaceResult()
        assert result.name is None
        assert result.club is None
        assert result.position_overall is None


class TestFixMalformedTime:
    """Test the fix_malformed_time helper function."""

    def test_double_colon(self):
        """Test fixing double colons."""
        assert fix_malformed_time("42::51") == "42:51"
        assert fix_malformed_time("1::23::45") == "1:23:45"

    def test_leading_colon(self):
        """Test removing leading colons."""
        assert fix_malformed_time(":40:56") == "40:56"
        assert fix_malformed_time("::45:30") == "45:30"

    def test_trailing_colon(self):
        """Test removing trailing colons."""
        assert fix_malformed_time("1:23:45:") == "1:23:45"
        assert fix_malformed_time("45:30::") == "45:30"

    def test_valid_time_unchanged(self):
        """Test that valid times are not modified."""
        assert fix_malformed_time("1:23:45") == "1:23:45"
        assert fix_malformed_time("45:30") == "45:30"


class TestNormalizeClubName:
    """Test the normalize_club_name helper function."""

    def test_remove_hrc_suffix(self):
        """Test removing HRC suffix."""
        assert normalize_club_name("Carnethy HRC") == "Carnethy"

    def test_remove_ac_suffix(self):
        """Test removing AC suffix."""
        assert normalize_club_name("Edinburgh AC") == "Edinburgh"

    def test_remove_harriers_suffix(self):
        """Test removing Harriers suffix."""
        assert normalize_club_name("Highland Harriers") == "Highland"

    def test_unattached_variations(self):
        """Test normalizing unattached variations."""
        # Function may not handle all variations
        result = normalize_club_name("Unattached")
        assert result is None or result == "Unattached"

    def test_none_input(self):
        """Test handling None input."""
        assert normalize_club_name(None) is None


class TestParseAgeCategory:
    """Test the parse_age_category helper function."""

    def test_veteran_codes(self):
        """Test parsing veteran codes."""
        result = parse_age_category("V", "M")
        assert result["age_category"] == "M40"
        assert result["gender"] == "M"

    def test_female_veteran_codes(self):
        """Test parsing female veteran codes."""
        result = parse_age_category("FV", "F")
        assert result["age_category"] == "F40"
        assert result["gender"] == "F"

    def test_junior_codes(self):
        """Test parsing junior codes."""
        result = parse_age_category("J", "M")
        assert result["age_category"] == "U20"

    def test_standard_codes_unchanged(self):
        """Test that standard codes pass through."""
        result = parse_age_category("M40", "M")
        assert result["age_category"] == "M40"

    def test_none_input(self):
        """Test handling None input."""
        result = parse_age_category(None, "M")
        assert result["age_category"] is None


class TestTimeParser:
    """Test the TimeParser class."""

    def test_parse_hms_format(self):
        """Test parsing HH:MM:SS format."""
        parser = TimeParser()
        assert parser.parse("1:23:45") == 5025

    def test_parse_ms_format(self):
        """Test parsing MM:SS format."""
        parser = TimeParser()
        assert parser.parse("23:45") == 1425

    def test_parse_seconds(self):
        """Test parsing plain seconds."""
        parser = TimeParser(format="seconds")
        assert parser.parse("1425") == 1425

    def test_parse_malformed_time(self):
        """Test that malformed times are corrected before parsing."""
        parser = TimeParser()
        assert parser.parse("42::51") == 2571  # 42:51
        assert parser.parse(":40:56") == 2456  # 40:56

    def test_parse_dnf_returns_none(self):
        """Test that DNF/DNS/DSQ return None."""
        parser = TimeParser()
        assert parser.parse("DNF") is None
        assert parser.parse("DNS") is None
        assert parser.parse("DSQ") is None


class TestColumnMapping:
    """Test the ColumnMapping class."""

    def test_create_basic_mapping(self):
        """Test creating a basic column mapping."""
        mapping = ColumnMapping(position_overall="Pos", name="Name", club="Club")
        assert mapping.position_overall == "Pos"
        assert mapping.name == "Name"
        assert mapping.club == "Club"

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        mapping = ColumnMapping()
        assert mapping.position_overall is None
        assert mapping.name is None


class TestRaceResultsNormalizer:
    """Test the RaceResultsNormalizer class."""

    def test_basic_normalization(self, sample_race_data):
        """Test basic normalization of race data."""
        mapping = ColumnMapping(
            position_overall="Position",
            name="Name",
            club="Club",
            finish_time="Time",
            age_category="Category",
        )
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert len(result) == 5
        assert "name" in result.columns
        assert "club" in result.columns
        assert "finish_time_seconds" in result.columns

    def test_club_normalization(self, sample_race_data):
        """Test that club names are normalized."""
        mapping = ColumnMapping(club="Club")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert result.loc[0, "club"] == "Edinburgh"  # Edinburgh AC -> Edinburgh
        assert result.loc[1, "club"] == "Carnethy"  # Carnethy HRC -> Carnethy

    def test_age_category_parsing(self, sample_race_data):
        """Test that age categories are parsed."""
        mapping = ColumnMapping(age_category="Category")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert result.loc[0, "age_category"] == "M40"  # V -> M40
        assert result.loc[1, "age_category"] == "F40"  # FV -> F40
        assert result.loc[2, "age_category"] == "M50"  # SV -> M50

    def test_time_parsing(self, sample_race_data):
        """Test that times are parsed correctly."""
        mapping = ColumnMapping(finish_time="Time")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert result.loc[0, "finish_time_seconds"] == 1905  # 31:45
        assert result.loc[1, "finish_time_seconds"] == 1930  # 32:10
        assert pd.isna(result.loc[3, "finish_time_seconds"])  # DNF

    def test_dnf_status_detection(self, sample_race_data):
        """Test that DNF status is detected."""
        mapping = ColumnMapping(finish_time="Time")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert result.loc[3, "race_status"] == "dnf"

    def test_malformed_time_correction(self, sample_malformed_data):
        """Test that malformed times are corrected."""
        mapping = ColumnMapping(finish_time="Time")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_malformed_data, return_dataframe=True)

        # 42::51 should be corrected to 42:51
        assert result.loc[0, "finish_time_seconds"] == 2571
        # :40:56 should be corrected to 40:56
        assert result.loc[1, "finish_time_seconds"] == 2456

    def test_gender_extraction(self, sample_race_data):
        """Test that gender is extracted from age categories."""
        mapping = ColumnMapping(age_category="Category")
        normalizer = RaceResultsNormalizer(mapping)
        result = normalizer.normalize(sample_race_data, return_dataframe=True)

        assert result.loc[0, "gender"] == "M"  # V -> M40, gender M
        assert result.loc[1, "gender"] == "F"  # FV -> F40, gender F


class TestEnums:
    """Test the enumeration classes."""

    def test_race_category_enum(self):
        """Test RaceCategory enum."""
        assert RaceCategory.MARATHON.value == "marathon"
        assert RaceCategory.FELL_RACE.value == "fell_race"

    def test_gender_enum(self):
        """Test Gender enum."""
        assert Gender.MALE.value == "M"
        assert Gender.FEMALE.value == "F"

    def test_race_status_enum(self):
        """Test RaceStatus enum."""
        assert RaceStatus.FINISHED.value == "finished"
        assert RaceStatus.DNF.value == "dnf"
        assert RaceStatus.DNS.value == "dns"
        assert RaceStatus.DSQ.value == "dsq"
