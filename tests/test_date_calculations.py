"""Tests for Job Week/Month calculation functions (Issue #14)."""
from datetime import date

from src.truck_tickets.utils.date_calculations import (
    calculate_job_week,
    calculate_job_month,
    get_day_name,
    calculate_job_metrics
)


def test_calculate_job_week_basic():
    """Test basic job week calculation."""
    # Project 24-105 started July 1, 2024 (Monday)
    job_start = date(2024, 7, 1)
    
    # Week 1: July 1-7 (Mon-Sun)
    assert calculate_job_week(date(2024, 7, 1), job_start) == "Week 1 - (End 07/07/24)"
    assert calculate_job_week(date(2024, 7, 7), job_start) == "Week 1 - (End 07/07/24)"
    
    # Week 2: July 8-14
    assert calculate_job_week(date(2024, 7, 8), job_start) == "Week 2 - (End 07/14/24)"
    
    # Week 16: October 14-20
    assert calculate_job_week(date(2024, 10, 17), job_start) == "Week 16 - (End 10/20/24)"


def test_calculate_job_week_mid_week_start():
    """Test job week when project starts mid-week."""
    # Project starts on Wednesday, July 3, 2024
    job_start = date(2024, 7, 3)
    
    # Week 1 should start on Monday, July 1
    # So July 3 is still Week 1, ending Sunday July 7
    assert calculate_job_week(date(2024, 7, 3), job_start) == "Week 1 - (End 07/07/24)"
    assert calculate_job_week(date(2024, 7, 7), job_start) == "Week 1 - (End 07/07/24)"


def test_calculate_job_month_basic():
    """Test basic job month calculation."""
    # Project 24-105 started July 1, 2024
    job_start = date(2024, 7, 1)
    
    # Month 1: July 2024
    assert calculate_job_month(date(2024, 7, 1), job_start) == "001 - July 24"
    assert calculate_job_month(date(2024, 7, 15), job_start) == "001 - July 24"
    assert calculate_job_month(date(2024, 7, 31), job_start) == "001 - July 24"
    
    # Month 2: August 2024
    assert calculate_job_month(date(2024, 8, 1), job_start) == "002 - August 24"
    assert calculate_job_month(date(2024, 8, 15), job_start) == "002 - August 24"
    
    # Month 3: September 2024
    assert calculate_job_month(date(2024, 9, 15), job_start) == "003 - September 24"
    
    # Month 4: October 2024
    assert calculate_job_month(date(2024, 10, 17), job_start) == "004 - October 24"


def test_calculate_job_month_year_boundary():
    """Test job month calculation across year boundary."""
    # Project starts December 2024
    job_start = date(2024, 12, 1)
    
    # Month 1: December 2024
    assert calculate_job_month(date(2024, 12, 15), job_start) == "001 - December 24"
    
    # Month 2: January 2025
    assert calculate_job_month(date(2025, 1, 15), job_start) == "002 - January 25"
    
    # Month 3: February 2025
    assert calculate_job_month(date(2025, 2, 15), job_start) == "003 - February 25"


def test_get_day_name():
    """Test day name abbreviation."""
    assert get_day_name(date(2024, 10, 14)) == "Mon"
    assert get_day_name(date(2024, 10, 15)) == "Tue"
    assert get_day_name(date(2024, 10, 16)) == "Wed"
    assert get_day_name(date(2024, 10, 17)) == "Thu"
    assert get_day_name(date(2024, 10, 18)) == "Fri"
    assert get_day_name(date(2024, 10, 19)) == "Sat"
    assert get_day_name(date(2024, 10, 20)) == "Sun"


def test_calculate_job_metrics():
    """Test combined job metrics calculation."""
    job_start = date(2024, 7, 1)
    ticket_date = date(2024, 10, 17)
    
    metrics = calculate_job_metrics(ticket_date, job_start)
    
    assert metrics['day'] == "Thu"
    assert metrics['job_week'] == "Week 16 - (End 10/20/24)"
    assert metrics['job_month'] == "004 - October 24"


def test_calculate_job_metrics_default_start_date():
    """Test job metrics with default start date."""
    # Should default to 2024-07-01 for Project 24-105
    ticket_date = date(2024, 10, 17)
    
    metrics = calculate_job_metrics(ticket_date)
    
    assert metrics['day'] == "Thu"
    assert metrics['job_week'] == "Week 16 - (End 10/20/24)"
    assert metrics['job_month'] == "004 - October 24"


def test_job_week_long_project():
    """Test job week for a long-running project."""
    job_start = date(2024, 1, 1)
    
    # Week 52 (approximately 1 year)
    late_date = date(2024, 12, 30)
    result = calculate_job_week(late_date, job_start)
    
    # Should be around Week 53
    assert "Week 53" in result or "Week 52" in result


def test_job_month_long_project():
    """Test job month for a long-running project."""
    job_start = date(2024, 1, 1)
    
    # Month 12 (December)
    late_date = date(2024, 12, 15)
    result = calculate_job_month(late_date, job_start)
    
    assert result == "012 - December 24"
