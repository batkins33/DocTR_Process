"""Job Week and Job Month calculation functions for Issue #14.

These functions calculate the job week and job month based on the job start date
and a given ticket date, matching the legacy Excel format requirements.

Formats:
- Job Week: "Week 16 - (End 10/20/24)"
- Job Month: "004 - October 24"
"""
from datetime import date, timedelta
from typing import Optional


def calculate_job_week(ticket_date: date, job_start_date: date) -> str:
    """Calculate job week string in format: 'Week 16 - (End 10/20/24)'.
    
    Job weeks run Monday-Sunday. Week 1 starts on the Monday of the week
    containing the job start date.
    
    Args:
        ticket_date: Date of the ticket
        job_start_date: Project start date
    
    Returns:
        Formatted job week string
    
    Example:
        >>> calculate_job_week(date(2024, 10, 17), date(2024, 7, 1))
        'Week 16 - (End 10/20/24)'
    """
    # Find the Monday of the week containing job_start_date
    days_since_monday = job_start_date.weekday()  # 0=Monday, 6=Sunday
    week_1_start = job_start_date - timedelta(days=days_since_monday)
    
    # Calculate days since week 1 start
    days_diff = (ticket_date - week_1_start).days
    
    # Calculate week number (1-indexed)
    week_number = (days_diff // 7) + 1
    
    # Find the Sunday (end) of the ticket's week
    days_until_sunday = 6 - ticket_date.weekday()
    week_end = ticket_date + timedelta(days=days_until_sunday)
    
    # Format: "Week 16 - (End 10/20/24)"
    week_end_str = week_end.strftime("%m/%d/%y")
    return f"Week {week_number} - (End {week_end_str})"


def calculate_job_month(ticket_date: date, job_start_date: date) -> str:
    """Calculate job month string in format: '004 - October 24'.
    
    Job months are sequential from the job start date. Month 1 is the month
    containing the job start date.
    
    Args:
        ticket_date: Date of the ticket
        job_start_date: Project start date
    
    Returns:
        Formatted job month string
    
    Example:
        >>> calculate_job_month(date(2024, 10, 17), date(2024, 7, 1))
        '004 - October 24'
    """
    # Calculate months difference
    months_diff = (
        (ticket_date.year - job_start_date.year) * 12
        + (ticket_date.month - job_start_date.month)
    )
    
    # Job month is 1-indexed
    job_month_number = months_diff + 1
    
    # Format: "004 - October 24"
    month_name = ticket_date.strftime("%B")
    year_short = ticket_date.strftime("%y")
    return f"{job_month_number:03d} - {month_name} {year_short}"


def get_day_name(ticket_date: date) -> str:
    """Get abbreviated day name (Mon, Tue, Wed, etc.).
    
    Args:
        ticket_date: Date to get day name for
    
    Returns:
        Abbreviated day name
    
    Example:
        >>> get_day_name(date(2024, 10, 17))
        'Thu'
    """
    return ticket_date.strftime("%a")


def calculate_job_metrics(
    ticket_date: date,
    job_start_date: Optional[date] = None
) -> dict[str, str]:
    """Calculate all job date metrics for a ticket.
    
    Args:
        ticket_date: Date of the ticket
        job_start_date: Project start date (optional, defaults to 2024-07-01 for 24-105)
    
    Returns:
        Dictionary with day, job_week, and job_month
    
    Example:
        >>> calculate_job_metrics(date(2024, 10, 17))
        {
            'day': 'Thu',
            'job_week': 'Week 16 - (End 10/20/24)',
            'job_month': '004 - October 24'
        }
    """
    # Default to Project 24-105 start date if not provided
    if job_start_date is None:
        job_start_date = date(2024, 7, 1)
    
    return {
        'day': get_day_name(ticket_date),
        'job_week': calculate_job_week(ticket_date, job_start_date),
        'job_month': calculate_job_month(ticket_date, job_start_date)
    }
