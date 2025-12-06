import sqlite3
import hashlib
import os

DB_NAME = "worktime.db"


def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def create_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn):
    cursor = conn.cursor()

    # Таблица сотрудников
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Employee (
        employee_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        last_name     TEXT NOT NULL,
        first_name    TEXT NOT NULL,
        middle_name   TEXT,
        position      TEXT,
        department    TEXT
    );
    """)

    # Рабочие дни
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS WorkDays (
        workday_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id   INTEGER NOT NULL,
        work_date     DATE NOT NULL,
        planned_start TIME,
        total_hours   REAL,
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
    );
    """)

    # Отметки времени
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TimeEntries (
        time_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
        workday_id    INTEGER NOT NULL,
        event_time    DATETIME NOT NULL,
        event_type    TEXT NOT NULL,
        source        TEXT,
        FOREIGN KEY (workday_id) REFERENCES WorkDays(workday_id)
    );
    """)

    # Типы отсутствия
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AbsenceType (
        absence_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL,
        is_paid         INTEGER,
        description     TEXT
    );
    """)

    # Конкретные отсутствия
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Absences (
        absence_id      INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id     INTEGER NOT NULL,
        absence_type_id INTEGER NOT NULL,
        date_from       DATE NOT NULL,
        date_to         DATE NOT NULL,
        status          TEXT,
        FOREIGN KEY (employee_id)     REFERENCES Employee(employee_id),
        FOREIGN KEY (absence_type_id) REFERENCES AbsenceType(absence_type_id)
    );
    """)

    # Роли
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Roles (
        role_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT NOT NULL,
        description TEXT
    );
    """)

    # Учётные записи пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserAccounts (
        user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id   INTEGER NOT NULL,
        login         TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        is_active     INTEGER,
        FOREIGN KEY (employee_id) REFERENCES Employee(employee_id)
    );
    """)

    # Связь M:N между UserAccounts и Roles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS UserRoles (
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, role_id),
        FOREIGN KEY (user_id) REFERENCES UserAccounts(user_id),
        FOREIGN KEY (role_id) REFERENCES Roles(role_id)
    );
    """)

    conn.commit()
    print("Таблицы созданы.")


def insert_test_data(conn):
    cursor = conn.cursor()

    # 4 сотрудника: Employee, HR, Manager, Admin
    cursor.executemany("""
    INSERT INTO Employee (last_name, first_name, middle_name, position, department)
    VALUES (?, ?, ?, ?, ?);
    """, [
        ("Иванов",   "Иван",   "Иванович",  "Разработчик",            "ИТ-отдел"),      # id=1 (Employee)
        ("Сидорова", "Анна",   "Сергеевна", "HR-менеджер",            "Отдел кадров"),  # id=2 (HR)
        ("Петров",   "Пётр",   "Петрович",  "Руководитель отдела",    "Отдел продаж"),  # id=3 (Manager)
        ("Смирнов",  "Алексей","Олегович",  "Системный администратор","ИТ-отдел"),      # id=4 (Admin)
    ])

    # Типы отсутствия
    cursor.executemany("""
    INSERT INTO AbsenceType (name, is_paid, description)
    VALUES (?, ?, ?);
    """, [
        ("Отпуск", 1, "Ежегодный оплачиваемый отпуск"),
        ("Больничный", 1, "Лист нетрудоспособности"),
        ("Командировка", 1, "Командировка по работе"),
        ("Отгул", 0, "Неоплачиваемый день"),
    ])

    # Роли
    cursor.executemany("""
    INSERT INTO Roles (name, description)
    VALUES (?, ?);
    """, [
        ("Employee", "Обычный сотрудник"),
        ("HR",       "Сотрудник отдела кадров"),
        ("Manager",  "Руководитель подразделения"),
        ("Admin",    "Администратор системы"),
    ])

    # Учётные записи пользователей (логин / пароль):
    # ivanov   / emp11
    # sidorova / hr33
    # petrov   / man22
    # smirnov  / adm44
    cursor.executemany("""
    INSERT INTO UserAccounts (employee_id, login, password_hash, is_active)
    VALUES (?, ?, ?, ?);
    """, [
        (1, "ivanov",   hash_password("emp11"),  1),  # Employee
        (2, "sidorova", hash_password("hr33"),   1),  # HR
        (3, "petrov",   hash_password("man22"),  1),  # Manager
        (4, "smirnov",  hash_password("adm44"),  1),  # Admin
    ])

    # Связи ролей
    cursor.executemany("""
    INSERT INTO UserRoles (user_id, role_id)
    VALUES (?, ?);
    """, [
        (1, 1),  # Иванов   -> Employee
        (2, 2),  # Сидорова -> HR
        (3, 3),  # Петров   -> Manager
        (4, 4),  # Смирнов  -> Admin
    ])

    # Рабочие дни
    cursor.executemany("""
    INSERT INTO WorkDays (employee_id, work_date, planned_start, total_hours)
    VALUES (?, ?, ?, ?);
    """, [
        (1, "2025-12-01", "09:00", 8.0),
        (1, "2025-12-02", "09:00", 7.5),
        (2, "2025-12-01", "09:00", 8.0),
        (3, "2025-12-01", "10:00", 7.0),
    ])

    # Пара отметок времени
    cursor.executemany("""
    INSERT INTO TimeEntries (workday_id, event_time, event_type, source)
    VALUES (?, ?, ?, ?);
    """, [
        (1, "2025-12-01 09:01", "IN",  "терминал"),
        (1, "2025-12-01 17:05", "OUT", "терминал"),
        (2, "2025-12-02 09:03", "IN",  "web"),
    ])

    conn.commit()
    print("Тестовые данные добавлены.")


def main():
    # если файл БД уже существует – удаляем, чтобы не было старых ID
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = create_connection()
    create_tables(conn)
    insert_test_data(conn)
    conn.close()
    print(f"Готово. База данных пересоздана в файле {DB_NAME!r}")


if __name__ == "__main__":
    main()
