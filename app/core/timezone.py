from datetime import datetime, timedelta, timezone

# Fixed UTC-4 offset used by the worker for logs and DB timestamps.
UTC_MINUS_4 = timezone(timedelta(hours=-4))


def now_utc_minus_4() -> datetime:
    return datetime.now(UTC_MINUS_4)


def now_utc_minus_4_naive() -> datetime:
    # Oracle DATE/TIMESTAMP columns often expect naive datetimes from the driver.
    return now_utc_minus_4().replace(tzinfo=None)
