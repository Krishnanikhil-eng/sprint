"""
API Load Testing & Dashboard Profiling Tests (Day 43).
Measures request throughput, multi-threading stability, and latency limits.
"""

import time
import concurrent.futures
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_concurrent_api_load_performance():
    """Validates 10 concurrent API requests execute within 10 seconds."""
    urls = [
        "/api/v1/health",
        "/api/v1/companies",
        "/api/v1/screener?min_roe=15.0",
        "/api/v1/sectors",
        "/api/v1/peers",
        "/api/v1/portfolio/stats",
        "/api/v1/companies/TCS",
        "/api/v1/companies/RELIANCE/ratios",
        "/api/v1/companies/HDFCBANK/documents",
        "/api/v1/market-cap/INFY"
    ]

    start_time = time.time()
    results = []

    def fetch_url(url: str):
        res = client.get(url)
        return res.status_code, res.elapsed.total_seconds() if hasattr(res, "elapsed") else 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_url, url) for url in urls]
        for f in concurrent.futures.as_completed(futures):
            code, duration = f.result()
            results.append((code, duration))

    total_time = time.time() - start_time
    assert total_time < 10.0, f"Load test exceeded limit: {total_time:.2f}s"
    for code, _ in results:
        assert code == 200


def test_company_profile_loading_latency():
    """Validates 5 company profile loads complete within 3 seconds."""
    tickers = ["TCS", "RELIANCE", "HDFCBANK", "INFY", "ICICIBANK"]
    start_time = time.time()

    for t in tickers:
        res = client.get(f"/api/v1/companies/{t}")
        assert res.status_code == 200

    total_time = time.time() - start_time
    assert total_time < 3.0, f"Profile loading latency exceeded limit: {total_time:.2f}s"
