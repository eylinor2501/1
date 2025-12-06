from typing import List, Tuple, Optional
import hashlib
from datetime import datetime
import csv

from db import get_connection
from models import Employee, WorkDay, TimeEntry, Absence, Role


# ====== Базовые выборки (п.4.1) ======

def get_employee_with_workdays(employee_id: int) -> Tuple[Employee, List[WorkDay]]:
    from repositories import EmployeeRepository, WorkDayRepository

    employee = EmployeeRepository.get_by_id(employee_id)
    if employee is None:
        raise ValueError("Сотрудник не найден")

    workdays = WorkDayRepository.get_for_employee(employee_id)
    return employee, workdays


def get_workday_with_entries(workday_id: int) -> Tuple[WorkDay, List[TimeEntry]]:
    from repositories import TimeEntryRepository

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM WorkDays WHERE workday_id = ?", (workday_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise ValueError("Рабочий день не найден")

    workday = WorkDay(
        workday_id=row["workday_id"],
        employee_id=row["employee_id"],
        work_date=row["work_date"],
        planned_start=row["planned_start"],
        total_hours=row["total_hours"],
    )

    entries = TimeEntryRepository.get_for_workday(workday_id)
    return workday, entries


def get_absences_for_employee(employee_id: int) -> List[Tuple[Absence, str]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.*, t.name AS type_name
        FROM Absences a
        JOIN AbsenceType t ON a.absence_type_id = t.absence_type_id
        WHERE a.employee_id = ?
        ORDER BY a.date_from
    """, (employee_id,))
    rows = cur.fetchall()
    conn.close()

    result: List[Tuple[Absence, str]] = []
    for row in rows:
        abs_obj = Absence(
            absence_id=row["absence_id"],
            employee_id=row["employee_id"],
            absence_type_id=row["absence_type_id"],
            date_from=row["date_from"],
            date_to=row["date_to"],
            status=row["status"],
        )
        result.append((abs_obj, row["type_name"]))
    return result


def get_roles_for_user(user_id: int) -> List[Role]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.role_id, r.name, r.description
        FROM Roles r
        JOIN UserRoles ur ON ur.role_id = r.role_id
        WHERE ur.user_id = ?
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    return [
        Role(
            role_id=row["role_id"],
            name=row["name"],
            description=row["description"],
        )
        for row in rows
    ]


# ====== Авторизация ======

def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def authenticate(login: str, password: str):
    """
    Авторизация по логину и паролю.
    Возвращает (UserAccount, список Role) или None.
    """
    from repositories import UserAccountRepository  # локальный импорт

    account = UserAccountRepository.get_by_login(login)
    if account is None:
        return None

    if account.is_active is not None and not account.is_active:
        return None

    if account.password_hash != hash_password(password):
        return None

    roles = get_roles_for_user(account.user_id)
    return account, roles


# ====== Функции по use-case диаграмме ======

def mark_time_entry(employee_id: int, event_type: str, source: str = "manual") -> None:
    """
    Отметить приход/уход сотрудника.
    event_type: 'IN' или 'OUT'.
    """
    conn = get_connection()
    cur = conn.cursor()

    today = datetime.now().date().isoformat()

    # Ищем/создаём рабочий день на сегодня
    cur.execute("""
        SELECT workday_id FROM WorkDays
        WHERE employee_id = ? AND work_date = ?
    """, (employee_id, today))
    row = cur.fetchone()

    if row:
        workday_id = row["workday_id"]
    else:
        cur.execute("""
            INSERT INTO WorkDays (employee_id, work_date, planned_start, total_hours)
            VALUES (?, ?, ?, ?)
        """, (employee_id, today, None, None))
        workday_id = cur.lastrowid

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO TimeEntries (workday_id, event_time, event_type, source)
        VALUES (?, ?, ?, ?)
    """, (workday_id, now_str, event_type, source))

    conn.commit()
    conn.close()


def get_personal_report(employee_id: int) -> List[Tuple[str, float, int]]:
    """Личный отчёт: (дата, часы, количество отметок)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.work_date,
               IFNULL(w.total_hours, 0) AS total_hours,
               COUNT(t.time_entry_id) AS events_count
        FROM WorkDays w
        LEFT JOIN TimeEntries t ON t.workday_id = w.workday_id
        WHERE w.employee_id = ?
        GROUP BY w.work_date, w.total_hours
        ORDER BY w.work_date;
    """, (employee_id,))
    rows = cur.fetchall()
    conn.close()
    return [(row["work_date"], row["total_hours"], row["events_count"]) for row in rows]


def generate_timesheet(start_date: str,
                       end_date: str,
                       department: Optional[str] = None) -> List[Tuple[str, str, str, float]]:
    """
    Сформировать табель: (отдел, ФИО, дата, часы).
    Если department=None — по всей организации.
    """
    conn = get_connection()
    cur = conn.cursor()

    sql = """
        SELECT e.department AS department,
               e.last_name || ' ' || e.first_name || ' ' || IFNULL(e.middle_name, '') AS full_name,
               w.work_date,
               IFNULL(w.total_hours, 0) AS hours
        FROM WorkDays w
        JOIN Employee e ON e.employee_id = w.employee_id
        WHERE w.work_date BETWEEN ? AND ?
    """
    params: List = [start_date, end_date]

    if department is not None:
        sql += " AND e.department = ?"
        params.append(department)

    sql += " ORDER BY department, full_name, w.work_date;"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    return [
        (row["department"], row["full_name"], row["work_date"], row["hours"])
        for row in rows
    ]


def export_timesheet_to_csv(filename: str, rows: List[Tuple[str, str, str, float]]) -> None:
    """Экспорт табеля в CSV (откроется в Excel)."""
    headers = ["Отдел", "ФИО", "Дата", "Часы"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerows(rows)


def get_department_of_employee(employee_id: int) -> Optional[str]:
    """Получить отдел сотрудника (для руководителя)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT department FROM Employee WHERE employee_id = ?", (employee_id,))
    row = cur.fetchone()
    conn.close()
    return row["department"] if row else None


def update_employee_data(employee_id: int,
                         position: Optional[str],
                         department: Optional[str]) -> None:
    """HR: обновить должность/отдел сотрудника."""
    from repositories import EmployeeRepository

    emp = EmployeeRepository.get_by_id(employee_id)
    if emp is None:
        raise ValueError("Сотрудник не найден")

    if position:
        emp.position = position
    if department:
        emp.department = department

    EmployeeRepository.update(emp)


def create_employee(last_name: str,
                    first_name: str,
                    middle_name: Optional[str],
                    position: Optional[str],
                    department: Optional[str]) -> int:
    """
    Админ: создать нового сотрудника (строку в Employee).
    Возвращает employee_id.
    """
    from repositories import EmployeeRepository

    emp = Employee(
        employee_id=None,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        position=position,
        department=department,
    )
    new_id = EmployeeRepository.create(emp)
    return new_id


def create_user_with_role(employee_id: int,
                          login: str,
                          password: str,
                          role_name: str) -> None:
    """Админ: создать нового пользователя (UserAccounts + UserRoles) для уже существующего сотрудника."""
    from models import UserAccount
    from repositories import (
        UserAccountRepository,
        UserRoleRepository,
        EmployeeRepository,
    )

    # 1) Проверяем, что сотрудник существует
    emp = EmployeeRepository.get_by_id(employee_id)
    if emp is None:
        raise ValueError(f"Сотрудник с ID={employee_id} не найден. Сначала добавьте сотрудника в Employee.")

    # 2) Проверяем уникальность логина
    existing = UserAccountRepository.get_by_login(login)
    if existing is not None:
        raise ValueError(f"Логин '{login}' уже используется.")

    # 3) Находим роль
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role_id FROM Roles WHERE name = ?", (role_name,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise ValueError(f"Роль '{role_name}' не найдена. Используйте: Employee, HR, Manager, Admin.")

    role_id = row["role_id"]

    # 4) Создаём учётную запись
    account = UserAccount(
        user_id=None,
        employee_id=employee_id,
        login=login,
        password_hash=hash_password(password),
        is_active=True,
    )
    new_id = UserAccountRepository.create(account)

    # 5) Привязываем роль
    UserRoleRepository.add_role_to_user(new_id, role_id)
