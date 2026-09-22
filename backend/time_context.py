"""Canonical local date/time context for assistant responses."""
from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def now_local() -> datetime:
    """Return the configured local time, or the host machine's local time."""
    timezone_name = os.getenv("LEVI_TIMEZONE", "").strip()
    if timezone_name:
        try:
            return datetime.now(ZoneInfo(timezone_name))
        except ZoneInfoNotFoundError:
            pass
    return datetime.now().astimezone()


def date_label() -> str:
    """Return the current local date in an unambiguous human-readable format."""
    return now_local().strftime("%A, %d %B %Y")


def time_label() -> str:
    """Return the current local time for status and assistant context."""
    return now_local().strftime("%H:%M:%S")


def assistant_time_context() -> str:
    """Return authoritative time context for the model system prompt."""
    current = now_local()
    timezone_name = current.tzname() or "local time"
    return (
        f"Current local date: {current.strftime('%A, %d %B %Y')}. "
        f"Current local time: {current.strftime('%H:%M:%S')} ({timezone_name})."
    )
