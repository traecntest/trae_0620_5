import random
import string
import uuid
from datetime import datetime, date
from typing import Optional


def generate_pickup_code() -> str:
    letters = string.ascii_uppercase[:6]
    letter = random.choice(letters)
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{letter}{numbers}"


_order_counter = 0


def generate_order_no() -> str:
    global _order_counter
    _order_counter += 1
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    counter_str = f"{_order_counter:06d}"
    random_str = ''.join(random.choices(string.digits, k=2))
    return f"ORD{date_str}{time_str}{counter_str}{random_str}"


def get_pickup_time(meal_period: str) -> str:
    time_map = {
        "breakfast": "07:00-08:30",
        "lunch": "11:30-12:30",
        "dinner": "17:30-18:30"
    }
    return time_map.get(meal_period, "11:30-12:30")


def get_meal_period_name(period: str) -> str:
    name_map = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐"
    }
    return name_map.get(period, period)


def is_weekend(d: Optional[date] = None) -> bool:
    if d is None:
        d = date.today()
    return d.weekday() >= 5


def get_season(d: Optional[date] = None) -> int:
    if d is None:
        d = date.today()
    month = d.month
    if month in [3, 4, 5]:
        return 0
    elif month in [6, 7, 8]:
        return 1
    elif month in [9, 10, 11]:
        return 2
    else:
        return 3


HOLIDAYS_2024 = [
    "2024-01-01", "2024-02-10", "2024-02-11", "2024-02-12", "2024-02-13",
    "2024-02-14", "2024-02-15", "2024-02-16", "2024-02-17", "2024-04-04",
    "2024-04-05", "2024-04-06", "2024-05-01", "2024-05-02", "2024-05-03",
    "2024-05-04", "2024-05-05", "2024-06-08", "2024-06-09", "2024-06-10",
    "2024-09-15", "2024-09-16", "2024-09-17", "2024-10-01", "2024-10-02",
    "2024-10-03", "2024-10-04", "2024-10-05", "2024-10-06", "2024-10-07"
]


def is_holiday(d: Optional[date] = None) -> bool:
    if d is None:
        d = date.today()
    return d.strftime("%Y-%m-%d") in HOLIDAYS_2024
