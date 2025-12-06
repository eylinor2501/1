# models.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Employee:
    employee_id: Optional[int]
    last_name: str
    first_name: str
    middle_name: Optional[str]
    position: Optional[str]
    department: Optional[str]


@dataclass
class WorkDay:
    workday_id: Optional[int]
    employee_id: int
    work_date: str          # 'YYYY-MM-DD'
    planned_start: Optional[str]  # 'HH:MM'
    total_hours: Optional[float]


@dataclass
class TimeEntry:
    time_entry_id: Optional[int]
    workday_id: int
    event_time: str         # 'YYYY-MM-DD HH:MM:SS'
    event_type: str
    source: Optional[str]


@dataclass
class AbsenceType:
    absence_type_id: Optional[int]
    name: str
    is_paid: Optional[bool]
    description: Optional[str]


@dataclass
class Absence:
    absence_id: Optional[int]
    employee_id: int
    absence_type_id: int
    date_from: str          # 'YYYY-MM-DD'
    date_to: str            # 'YYYY-MM-DD'
    status: Optional[str]


@dataclass
class Role:
    role_id: Optional[int]
    name: str
    description: Optional[str]


@dataclass
class UserAccount:
    user_id: Optional[int]
    employee_id: int
    login: str
    password_hash: str
    is_active: Optional[bool]


@dataclass
class UserRole:
    user_id: int
    role_id: int
