# repositories.py
from typing import List, Optional
from db import get_connection
from models import (
    Employee, WorkDay, TimeEntry, Absence, Role, UserAccount, UserRole
)
class EmployeeRepository:

    @staticmethod
    def create(employee: Employee) -> int:
        #Добавить сотрудника. Возвращает новый employee_id
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Employee (last_name, first_name, middle_name, position, department)
            VALUES (?, ?, ?, ?, ?)
        """, (employee.last_name,
              employee.first_name,
              employee.middle_name,
              employee.position,
              employee.department))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_by_id(employee_id: int) -> Optional[Employee]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Employee WHERE employee_id = ?", (employee_id,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return Employee(
            employee_id=row["employee_id"],
            last_name=row["last_name"],
            first_name=row["first_name"],
            middle_name=row["middle_name"],
            position=row["position"],
            department=row["department"],
        )

    @staticmethod
    def get_all() -> List[Employee]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM Employee")
        rows = cur.fetchall()
        conn.close()
        return [
            Employee(
                employee_id=row["employee_id"],
                last_name=row["last_name"],
                first_name=row["first_name"],
                middle_name=row["middle_name"],
                position=row["position"],
                department=row["department"],
            )
            for row in rows
        ]

    @staticmethod
    def update(employee: Employee) -> None:
        #Обновить данные сотрудника по его employee_id
        if employee.employee_id is None:
            raise ValueError("employee_id is required for update")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Employee
            SET last_name = ?, first_name = ?, middle_name = ?,
                position = ?, department = ?
            WHERE employee_id = ?
        """, (employee.last_name,
              employee.first_name,
              employee.middle_name,
              employee.position,
              employee.department,
              employee.employee_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(employee_id: int) -> None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Employee WHERE employee_id = ?", (employee_id,))
        conn.commit()
        conn.close()
class WorkDayRepository:

    @staticmethod
    def create(workday: WorkDay) -> int:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO WorkDays (employee_id, work_date, planned_start, total_hours)
            VALUES (?, ?, ?, ?)
        """, (workday.employee_id,
              workday.work_date,
              workday.planned_start,
              workday.total_hours))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_for_employee(employee_id: int) -> list[WorkDay]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM WorkDays
            WHERE employee_id = ?
            ORDER BY work_date
        """, (employee_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            WorkDay(
                workday_id=row["workday_id"],
                employee_id=row["employee_id"],
                work_date=row["work_date"],
                planned_start=row["planned_start"],
                total_hours=row["total_hours"],
            )
            for row in rows
        ]


class TimeEntryRepository:

    @staticmethod
    def create(entry: TimeEntry) -> int:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO TimeEntries (workday_id, event_time, event_type, source)
            VALUES (?, ?, ?, ?)
        """, (entry.workday_id,
              entry.event_time,
              entry.event_type,
              entry.source))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_for_workday(workday_id: int) -> list[TimeEntry]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM TimeEntries
            WHERE workday_id = ?
            ORDER BY event_time
        """, (workday_id,))
        rows = cur.fetchall()
        conn.close()
        return [
            TimeEntry(
                time_entry_id=row["time_entry_id"],
                workday_id=row["workday_id"],
                event_time=row["event_time"],
                event_type=row["event_type"],
                source=row["source"],
            )
            for row in rows
        ]
# ---------- Absence CRUD ----------

class AbsenceRepository:

    @staticmethod
    def create(absence: Absence) -> int:

        #Создать запись об отсутствии.
        #Возвращает новый absence_id.

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Absences (employee_id, absence_type_id, date_from, date_to, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            absence.employee_id,
            absence.absence_type_id,
            absence.date_from,
            absence.date_to,
            absence.status,
        ))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_for_employee(employee_id: int) -> List[Absence]:
        #Получить все отсутствия конкретного сотрудника.
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM Absences
            WHERE employee_id = ?
            ORDER BY date_from
        """, (employee_id,))
        rows = cur.fetchall()
        conn.close()

        return [
            Absence(
                absence_id=row["absence_id"],
                employee_id=row["employee_id"],
                absence_type_id=row["absence_type_id"],
                date_from=row["date_from"],
                date_to=row["date_to"],
                status=row["status"],
            )
            for row in rows
        ]

    @staticmethod
    def update_status(absence_id: int, new_status: str) -> None:
        #Обновить статус отсутствия (например, Requested → Approved).
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE Absences
            SET status = ?
            WHERE absence_id = ?
        """, (new_status, absence_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(absence_id: int) -> None:
        #Удалить запись об отсутствии.
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Absences WHERE absence_id = ?", (absence_id,))
        conn.commit()
        conn.close()


# ---------- UserAccount CRUD ----------

class UserAccountRepository:

    @staticmethod
    def create(account: UserAccount) -> int:

        #Создаём учётную запись пользователя.
        #Возвращает новый user_id.

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO UserAccounts (employee_id, login, password_hash, is_active)
            VALUES (?, ?, ?, ?)
        """, (
            account.employee_id,
            account.login,
            account.password_hash,
            int(account.is_active) if account.is_active is not None else 1,
        ))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    @staticmethod
    def get_by_id(user_id: int) -> Optional[UserAccount]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserAccounts WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return UserAccount(
            user_id=row["user_id"],
            employee_id=row["employee_id"],
            login=row["login"],
            password_hash=row["password_hash"],
            is_active=bool(row["is_active"]) if row["is_active"] is not None else None,
        )

    @staticmethod
    def get_by_login(login: str) -> Optional[UserAccount]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserAccounts WHERE login = ?", (login,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            return None
        return UserAccount(
            user_id=row["user_id"],
            employee_id=row["employee_id"],
            login=row["login"],
            password_hash=row["password_hash"],
            is_active=bool(row["is_active"]) if row["is_active"] is not None else None,
        )

    @staticmethod
    def get_all() -> List[UserAccount]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM UserAccounts")
        rows = cur.fetchall()
        conn.close()

        return [
            UserAccount(
                user_id=row["user_id"],
                employee_id=row["employee_id"],
                login=row["login"],
                password_hash=row["password_hash"],
                is_active=bool(row["is_active"]) if row["is_active"] is not None else None,
            )
            for row in rows
        ]

    @staticmethod
    def update(account: UserAccount) -> None:
        """Обновить данные учётной записи (по user_id)."""
        if account.user_id is None:
            raise ValueError("user_id is required for update")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE UserAccounts
            SET employee_id = ?, login = ?, password_hash = ?, is_active = ?
            WHERE user_id = ?
        """, (
            account.employee_id,
            account.login,
            account.password_hash,
            int(account.is_active) if account.is_active is not None else 1,
            account.user_id,
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(user_id: int) -> None:
        #Удалить учётную запись.
        conn = get_connection()
        cur = conn.cursor()
        # сначала удалим все связи ролей этого пользователя
        cur.execute("DELETE FROM UserRoles WHERE user_id = ?", (user_id,))
        cur.execute("DELETE FROM UserAccounts WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()



class UserRoleRepository:

    @staticmethod
    def add_role_to_user(user_id: int, role_id: int) -> None:
        #Назначить пользователю роль (создать запись в UserRoles)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO UserRoles (user_id, role_id)
            VALUES (?, ?)
        """, (user_id, role_id))
        conn.commit()
        conn.close()

    @staticmethod
    def remove_role_from_user(user_id: int, role_id: int) -> None:
        #Убрать у пользователя конкретную роль.
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM UserRoles
            WHERE user_id = ? AND role_id = ?
        """, (user_id, role_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_role_ids_for_user(user_id: int) -> List[int]:
        #Получить список ID ролей, назначенных пользователю
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT role_id FROM UserRoles WHERE user_id = ?", (user_id,))
        rows = cur.fetchall()
        conn.close()
        return [row["role_id"] for row in rows]

    @staticmethod
    def delete_all_for_user(user_id: int) -> None:
        #Удалить все роли пользователя (очистить UserRoles для него)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM UserRoles WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
