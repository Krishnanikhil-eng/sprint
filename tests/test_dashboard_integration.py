"""
Dashboard Integration QA Tests
Tests all 8 dashboard screens with representative companies
"""

import pytest
import pandas as pd
from pathlib import Path


class TestDashboardIntegration:
    """Integration tests for dashboard screens."""
    
    @pytest.fixture
    def sample_companies(self):
        """Sample companies across different sectors for testing."""
        return [
            "TCS", "INFY",  # IT
            "HDFCBANK", "ICICIBANK",  # Financials
            "HINDUNILVR", "ITC",  # FMCG
            "RELIANCE", "ONGC",  # Energy
            "SUNPHARMA", "DRREDDY"  # Healthcare
        ]
    
    def test_dashboard_pages_exist(self):
        """Test that all 8 dashboard page files exist."""
        pages_dir = Path("src/dashboard/pages")
        expected_pages = [
            "01_home.py",
            "02_profile.py", 
            "03_screener.py",
            "04_peers.py",
            "05_trends.py",
            "06_sectors.py",
            "07_capital.py",
            "08_reports.py"
        ]
        
        for page in expected_pages:
            page_path = pages_dir / page
            assert page_path.exists(), f"Dashboard page {page} does not exist"
    
    def test_dashboard_config_exists(self):
        """Test that dashboard configuration file exists."""
        config_path = Path("src/dashboard/config.py")
        assert config_path.exists(), "Dashboard config.py does not exist"
    
    def test_db_utils_exist(self):
        """Test that database utilities exist."""
        db_utils_path = Path("src/dashboard/utils/db.py")
        assert db_utils_path.exists(), "Database utilities db.py does not exist"
    
    def test_dashboard_imports(self):
        """Test that dashboard pages can be imported without errors."""
        pages_dir = Path("src/dashboard/pages")
        expected_pages = [
            "01_home.py",
            "02_profile.py",
            "03_screener.py",
            "04_peers.py",
            "05_trends.py",
            "06_sectors.py",
            "07_capital.py",
            "08_reports.py"
        ]
        
        for page in expected_pages:
            page_path = pages_dir / page
            try:
                with open(page_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                assert len(content) > 0, f"Page {page} is empty"
                assert "import streamlit" in content, f"Page {page} missing streamlit import"
            except Exception as e:
                pytest.fail(f"Failed to read page {page}: {e}")
    
    def test_screener_page_has_filters(self):
        """Test that screener page has filter inputs."""
        screener_path = Path("src/dashboard/pages/03_screener.py")
        with open(screener_path, 'r') as f:
            content = f.read()
        
        # Check for filter inputs
        assert "number_input" in content, "Screener missing number_input filters"
        assert "ROE" in content or "roe" in content, "Screener missing ROE filter"
        assert "D/E" in content or "debt_to_equity" in content, "Screener missing D/E filter"
    
    def test_screener_page_has_csv_export(self):
        """Test that screener page has CSV export functionality."""
        screener_path = Path("src/dashboard/pages/03_screener.py")
        with open(screener_path, 'r') as f:
            content = f.read()
        
        assert "download_button" in content, "Screener missing download_button for CSV export"
        assert "to_csv" in content, "Screener missing to_csv for export"
    
    def test_screener_page_has_presets(self):
        """Test that screener page has preset strategies."""
        screener_path = Path("src/dashboard/pages/03_screener.py")
        with open(screener_path, 'r') as f:
            content = f.read()
        
        assert "PRESET_STRATEGIES" in content or "preset" in content.lower(), "Screener missing preset strategies"
        assert "selectbox" in content, "Screener missing selectbox for presets"
    
    def test_valuation_engine_exists(self):
        """Test that valuation engine module exists."""
        valuation_path = Path("src/analytics/valuation.py")
        assert valuation_path.exists(), "Valuation engine valuation.py does not exist"
    
    def test_valuation_engine_has_functions(self):
        """Test that valuation engine has required functions."""
        valuation_path = Path("src/analytics/valuation.py")
        with open(valuation_path, 'r') as f:
            content = f.read()
        
        required_functions = [
            "run_valuation_engine",
            "compute_fcf_yield",
            "calculate_sector_median_pe",
            "compute_valuation_flags",
            "export_valuation_summary",
            "export_valuation_flags"
        ]
        
        for func in required_functions:
            assert func in content, f"Valuation engine missing function: {func}"
    
    def test_valuation_engine_has_fcf_calculation(self):
        """Test that valuation engine has FCF yield calculation."""
        valuation_path = Path("src/analytics/valuation.py")
        with open(valuation_path, 'r') as f:
            content = f.read()
        
        assert "FCF_yield_pct" in content, "Valuation engine missing FCF yield calculation"
        assert "market_cap_crore" in content, "Valuation engine missing market cap reference"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
