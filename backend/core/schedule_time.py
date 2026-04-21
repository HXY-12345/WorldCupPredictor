"""核心功能：统一处理赛程开球时间的北京时间存储、时区转换与 UTC 比较逻辑。"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

BEIJING_TIMEZONE = ZoneInfo("Asia/Shanghai")


def normalize_match_datetime_to_beijing(
    date_value: str | None,
    time_value: str | None,
    source_timezone: str | None = None,
) -> tuple[str | None, str | None]:
    """将带来源时区的比赛时间转换为北京时间。

    当来源时区缺失或时间格式无效时，返回原值，避免误改已经是北京时间的数据。
    """

    if not date_value or not time_value or not source_timezone:
        return date_value, time_value

    normalized_time = _normalize_time_string(time_value)
    if normalized_time is None:
        return date_value, time_value

    try:
        source_zone = ZoneInfo(source_timezone)
        source_datetime = datetime.fromisoformat(f"{date_value}T{normalized_time}:00").replace(
            tzinfo=source_zone
        )
    except Exception:
        return date_value, time_value

    beijing_datetime = source_datetime.astimezone(BEIJING_TIMEZONE)
    return beijing_datetime.date().isoformat(), beijing_datetime.strftime("%H:%M")


def resolve_stored_match_kickoff_to_utc(
    date_value: str | None,
    time_value: str | None,
) -> datetime | None:
    """将数据库中存储的北京时间赛程解释为 UTC 时间，用于赛前/赛后边界判断。"""

    if not date_value:
        return None

    normalized_time = _normalize_time_string(time_value) or "23:59"
    try:
        kickoff = datetime.fromisoformat(f"{date_value}T{normalized_time}:00").replace(
            tzinfo=BEIJING_TIMEZONE
        )
    except ValueError:
        return None

    return kickoff.astimezone(UTC)


def _normalize_time_string(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.strip()
    if len(normalized) == 5:
        hour, minute = normalized.split(":")
    elif len(normalized) == 8:
        hour, minute, _ = normalized.split(":")
    else:
        return None

    if not (hour.isdigit() and minute.isdigit()):
        return None

    return f"{int(hour):02d}:{int(minute):02d}"
