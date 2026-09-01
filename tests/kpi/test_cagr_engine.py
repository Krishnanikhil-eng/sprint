import pytest
from src.analytics.cagr import (
    calculate_cagr,
    calculate_series_cagr,
    FLAG_NORMAL,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
)

def test_cagr_positive_to_positive_normal():
    # 100 to 207.36 over 5 years => 15.7031% CAGR
    val, flag = calculate_cagr(100.0, 207.36, 5)
    assert val == 15.7031
    assert flag == FLAG_NORMAL

def test_cagr_decline_to_loss():
    val, flag = calculate_cagr(100.0, -50.0, 5)
    assert val is None
    assert flag == FLAG_DECLINE_TO_LOSS

def test_cagr_turnaround():
    val, flag = calculate_cagr(-50.0, 100.0, 5)
    assert val is None
    assert flag == FLAG_TURNAROUND

def test_cagr_both_negative():
    val, flag = calculate_cagr(-100.0, -50.0, 5)
    assert val is None
    assert flag == FLAG_BOTH_NEGATIVE

def test_cagr_zero_base():
    val, flag = calculate_cagr(0.0, 100.0, 5)
    assert val is None
    assert flag == FLAG_ZERO_BASE

def test_cagr_insufficient_data():
    val, flag = calculate_cagr(None, 100.0, 5)
    assert val is None
    assert flag == FLAG_INSUFFICIENT

    val2, flag2 = calculate_cagr(100.0, 200.0, 0)
    assert val2 is None
    assert flag2 == FLAG_INSUFFICIENT

def test_series_cagr():
    series = {2019: 100.0, 2024: 161.051}
    val, flag = calculate_series_cagr(series, 2024, 5)
    assert val == 10.0
    assert flag == FLAG_NORMAL
