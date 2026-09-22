from datetime import datetime

from time_context import assistant_time_context, date_label, now_local, time_label


def test_date_and_time_labels_match_local_clock():
    current = now_local()
    assert date_label() == current.strftime("%A, %d %B %Y")
    assert time_label() == current.strftime("%H:%M:%S")
    assert current.strftime("%A, %d %B %Y") in assistant_time_context()


def test_configured_timezone_override(monkeypatch):
    monkeypatch.setenv("LEVI_TIMEZONE", "Asia/Kolkata")
    current = now_local()
    assert current.tzinfo is not None
    assert current.tzname() in {"IST", "+0530"}
    assert current.strftime("%A, %d %B %Y") in assistant_time_context()
