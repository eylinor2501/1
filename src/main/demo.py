# demo.py
from typing import Iterable, Sequence, Any

from repositories import (
    EmployeeRepository,
    WorkDayRepository,
    TimeEntryRepository,
    AbsenceRepository,
    UserAccountRepository,
)
from services import (
    get_employee_with_workdays,
    get_workday_with_entries,
    get_absences_for_employee,
    get_roles_for_user,
)


def print_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    """
    Простой табличный вывод в консоль.
    headers – список названий колонок
    rows – список строк (кортежей / списков значений)
    """
    rows = list(rows)
    # приводим всё к строкам
    str_rows = [[str(x) for x in row] for row in rows]
    str_headers = [str(h) for h in headers]

    # ширина колонок = максимум из заголовка и всех значений
    col_widths = []
    num_cols = len(headers)
    for col in range(num_cols):
        max_len = len(str_headers[col])
        for row in str_rows:
            if col < len(row):
                max_len = max(max_len, len(row[col]))
        col_widths.append(max_len)

    # формируем форматную строку
    fmt = "  ".join("{:<" + str(w) + "}" for w in col_widths)

    # печать заголовка
    print(fmt.format(*str_headers))
    # разделитель
    print("  ".join("-" * w for w in col_widths))

    # печать строк
    for row in str_rows:
        print(fmt.format(*row))


def section(title: str) -> None:
    print()
    print("=" * (len(title) + 4))
    print(f"= {title} =")
    print("=" * (len(title) + 4))


def main():
    # === Все сотрудники ===
    section("Все сотрудники")
    employees = EmployeeRepository.get_all()
    emp_rows = [
        (
            e.employee_id,
            f"{e.last_name} {e.first_name} {e.middle_name or ''}".strip(),
            e.position or "",
            e.department or "",
        )
        for e in employees
    ]
    print_table(
        ["ID", "ФИО", "Должность", "Отдел"],
        emp_rows,
    )

    # === Сотрудник + его рабочие дни ===
    section("Сотрудник 1 + его рабочие дни")
    emp, days = get_employee_with_workdays(1)
    print(f"Сотрудник: {emp.last_name} {emp.first_name} {emp.middle_name or ''} "
          f"(ID={emp.employee_id})")
    if days:
        day_rows = [
            (d.workday_id, d.work_date, d.planned_start or "", d.total_hours or "")
            for d in days
        ]
        print_table(["ID дня", "Дата", "План. начало", "Часы"], day_rows)
    else:
        print("Рабочих дней нет.")

    # === Один рабочий день + события ===
    section("WorkDay 1 + события")
    wd, entries = get_workday_with_entries(1)
    print(f"Рабочий день ID={wd.workday_id}, дата {wd.work_date}")
    if entries:
        entry_rows = [
            (te.time_entry_id, te.event_time, te.event_type, te.source or "")
            for te in entries
        ]
        print_table(["ID события", "Время", "Тип", "Источник"], entry_rows)
    else:
        print("Событий нет.")

    # === Отсутствия сотрудника ===
    section("Отсутствия сотрудника 1")
    abs_pairs = get_absences_for_employee(1)
    if abs_pairs:
        abs_rows = [
            (
                a.absence_id,
                type_name,
                a.date_from,
                a.date_to,
                a.status or "",
            )
            for a, type_name in abs_pairs
        ]
        print_table(
            ["ID", "Тип", "С даты", "По дату", "Статус"],
            abs_rows,
        )
    else:
        print("Отсутствий нет.")

    # === Все аккаунты пользователей ===
    section("Учётные записи пользователей")
    accounts = UserAccountRepository.get_all()
    acc_rows = [
        (
            acc.user_id,
            acc.login,
            acc.employee_id,
            "активен" if acc.is_active else "заблокирован",
        )
        for acc in accounts
    ]
    print_table(["ID", "Логин", "ID сотрудника", "Статус"], acc_rows)

    # === Роли пользователя ===
    section("Роли пользователя 3")
    roles = get_roles_for_user(3)
    if roles:
        role_rows = [(r.role_id, r.name, r.description or "") for r in roles]
        print_table(["ID роли", "Название", "Описание"], role_rows)
    else:
        print("У пользователя нет ролей.")


if __name__ == "__main__":
    main()
