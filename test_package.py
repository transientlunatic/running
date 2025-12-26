"""
Simple test to verify the package can be imported and basic functionality works.
"""

def test_imports():
    """Test that all main modules can be imported."""
    try:
        from running_results import (
            RaceDataFetcher,
            CSVRaceData,
            TimeConverter,
            ColumnStandardizer,
            NameParser,
            RaceDataTransformer,
            KentigernPlot,
            RacePlotter,
            RaceStatistics,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_time_converter():
    """Test TimeConverter functionality."""
    try:
        from running_results import TimeConverter
        
        # Test conversion to seconds
        assert TimeConverter.to_seconds("1:23:45") == 5025
        assert TimeConverter.to_seconds("23:45") == 1425
        
        # Test conversion back
        assert TimeConverter.from_seconds(5025) == "01:23:45"
        
        # Test to minutes
        assert TimeConverter.to_minutes("1:30:00") == 90.0
        
        print("✓ TimeConverter tests passed")
        return True
    except AssertionError as e:
        print(f"✗ TimeConverter test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ TimeConverter error: {e}")
        return False


def test_column_standardizer():
    """Test ColumnStandardizer functionality."""
    try:
        from running_results import ColumnStandardizer
        import pandas as pd
        
        # Create test dataframe
        df = pd.DataFrame({
            'Position': [1, 2, 3],
            'Time': ['1:00:00', '1:05:00', '1:10:00'],
            'Cat.': ['M40', 'F35', 'M50']
        })
        
        standardizer = ColumnStandardizer()
        df_std = standardizer.standardize(df)
        
        assert 'RunnerPosition' in df_std.columns
        assert 'FinishTime' in df_std.columns
        assert 'RunnerCategory' in df_std.columns
        
        print("✓ ColumnStandardizer tests passed")
        return True
    except AssertionError as e:
        print(f"✗ ColumnStandardizer test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ ColumnStandardizer error: {e}")
        return False


def test_race_statistics():
    """Test RaceStatistics functionality."""
    try:
        from running_results import RaceStatistics
        import pandas as pd
        import numpy as np
        
        # Create test data
        data = pd.DataFrame({
            'FinishTime (minutes)': np.random.normal(180, 30, 1000)
        })
        
        stats = RaceStatistics(data)
        
        # Test percentile calculation
        median = stats.time_for_percentile(50)
        assert 150 < median < 210  # Should be around 180
        
        # Test quantiles
        quantiles = stats.quantiles()
        assert len(quantiles) > 0
        
        print("✓ RaceStatistics tests passed")
        return True
    except AssertionError as e:
        print(f"✗ RaceStatistics test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ RaceStatistics error: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Running Running Results Package Tests")
    print("="*60)
    print()
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("TimeConverter", test_time_converter()))
    results.append(("ColumnStandardizer", test_column_standardizer()))
    results.append(("RaceStatistics", test_race_statistics()))
    
    print()
    print("="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    return all(p for _, p in results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
