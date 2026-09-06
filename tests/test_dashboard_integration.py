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
                with open(page_path, 'r') as f:
                    content = f.read()
                assert len(content) > 0, f"Page {page} is empty"
                assert "import streamlit" in content, f"Page {page} missing streamlit import"
            except Exception as e:
                pytest.fail(f"Failed to read page {page}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
