# app.py
from typing import Iterable, Sequence, Any

from repositories import (
    EmployeeRepository,
    WorkDayRepository,
    UserAccountRepository,
)
from services import (
    authenticate,
    get_personal_report,
    mark_time_entry,
    generate_timesheet,
    export_timesheet_to_csv,
    get_department_of_employee,
    update_employee_data,
    create_user_with_role,
    create_employee,
)


def print_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    rows = list(rows)
    str_rows = [[str(x) for x in row] for row in rows]
    str_headers = [str(h) for h in headers]

    col_widths = []
    num_cols = len(headers)
    for col in range(num_cols):
        max_len = len(str_headers[col])
        for row in str_rows:
            if col < len(row):
                max_len = max(max_len, len(row[col]))
        col_widths.append(max_len)

    fmt = "  ".join("{:<" + str(w) + "}" for w in col_widths)

    print(fmt.format(*str_headers))
    print("  ".join("-" * w for w in col_widths))

    for row in str_rows:
        print(fmt.format(*row))


def input_dates() -> tuple[str, str]:
    start_date = input("Дата начала периода (YYYY-MM-DD): ").strip()
    end_date = input("Дата окончания периода (YYYY-MM-DD): ").strip()
    return start_date, end_date


def main_menu(user, role_names):
    while True:
        print("\n=== Главное меню ===")
        print(f"Вы вошли как: {user.login} (ID={user.user_id}), роли: {', '.join(sorted(role_names))}")
        print("0 - Выход")

        # Сотрудник
        if "Employee" in role_names:
            print("1 - Отметить приход")
            print("2 - Отметить уход")
            print("3 - Посмотреть личный отчёт")

        # HR
        if "HR" in role_names:
            print("4 - Редактировать данные сотрудника")
            print("5 - Сформировать табель по всей организации")

        # Руководитель
        if "Manager" in role_names:
            print("6 - Просмотреть отчёт по своему подразделению")

        # Админ
        if "Admin" in role_names:
            print("7 - Добавить пользователя для существующего сотрудника")
            print("8 - Сформировать табель и экспортировать в CSV")
            print("9 - Добавить НОВОГО сотрудника и сразу создать ему пользователя")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход из программы.")
            break

        # === Функции сотрудника ===
        if choice == "1" and "Employee" in role_names:
            mark_time_entry(user.employee_id, "IN", source="console")
            print("Приход отмечен.")
        elif choice == "2" and "Employee" in role_names:
            mark_time_entry(user.employee_id, "OUT", source="console")
            print("Уход отмечен.")
        elif choice == "3" and "Employee" in role_names:
            report = get_personal_report(user.employee_id)
            if not report:
                print("Данные отсутствуют.")
            else:
                print("\nЛичный отчёт:")
                print_table(["Дата", "Часы", "Кол-во отметок"], report)

        # === Функции HR ===
        elif choice == "4" and "HR" in role_names:
            try:
                emp_id = int(input("ID сотрудника для редактирования: ").strip())
            except ValueError:
                print("Некорректный ID.")
                continue
            new_pos = input("Новая должность (пусто — оставить прежнюю): ").strip()
            new_dep = input("Новый отдел (пусто — оставить прежний): ").strip()
            try:
                update_employee_data(
                    emp_id,
                    new_pos if new_pos else None,
                    new_dep if new_dep else None,
                )
                print("Данные обновлены.")
            except ValueError as e:
                print(e)

        elif choice == "5" and "HR" in role_names:
            print("\nФормирование табеля по всей организации")
            start_date, end_date = input_dates()
            rows = generate_timesheet(start_date, end_date, department=None)
            if not rows:
                print("Нет данных за указанный период.")
            else:
                print_table(["Отдел", "ФИО", "Дата", "Часы"], rows)
                ans = input("Экспортировать в CSV? (y/n): ").strip().lower()
                if ans == "y":
                    filename = input("Имя файла (например timesheet_all.csv): ").strip()
                    export_timesheet_to_csv(filename, rows)
                    print(f"Табель экспортирован в {filename}")

        # === Функции руководителя ===
        elif choice == "6" and "Manager" in role_names:
            dep = get_department_of_employee(user.employee_id)
            if not dep:
                print("Не удалось определить ваш отдел.")
            else:
                print(f"\nТабель по отделу: {dep}")
                start_date, end_date = input_dates()
                rows = generate_timesheet(start_date, end_date, department=dep)
                if not rows:
                    print("Нет данных за период.")
                else:
                    print_table(["Отдел", "ФИО", "Дата", "Часы"], rows)
                    ans = input("Экспортировать в CSV? (y/n): ").strip().lower()
                    if ans == "y":
                        filename = input("Имя файла (например dept_report.csv): ").strip()
                        export_timesheet_to_csv(filename, rows)
                        print(f"Отчёт отдела экспортирован в {filename}")

        # === Функции администратора ===
        elif choice == "7" and "Admin" in role_names:
            # создать пользователя для уже существующего сотрудника
            try:
                emp_id = int(input("ID существующего сотрудника: ").strip())
            except ValueError:
                print("Некорректный ID.")
                continue

            login = input("Логин: ").strip()
            password = input("Пароль: ").strip()
            print("Доступные роли: Employee, HR, Manager, Admin")
            role_name = input("Роль: ").strip()
            try:
                create_user_with_role(emp_id, login, password, role_name)
                print("Пользователь создан.")
            except ValueError as e:
                print(e)

        elif choice == "8" and "Admin" in role_names:
            print("\nГлобальный табель")
            start_date, end_date = input_dates()
            rows = generate_timesheet(start_date, end_date, department=None)
            if not rows:
                print("Нет данных за период.")
            else:
                print_table(["Отдел", "ФИО", "Дата", "Часы"], rows)
                filename = input("Имя CSV файла (например timesheet_global.csv): ").strip()
                export_timesheet_to_csv(filename, rows)
                print(f"Табель экспортирован в {filename}")

        elif choice == "9" and "Admin" in role_names:
            # полный цикл: создать сотрудника + учётку
            print("\n=== Добавление нового сотрудника ===")
            ln = input("Фамилия: ").strip()
            fn = input("Имя: ").strip()
            mn = input("Отчество (можно пусто): ").strip()
            pos = input("Должность: ").strip()
            dep = input("Отдел: ").strip()

            if not ln or not fn:
                print("Фамилия и имя обязательны.")
                continue

            emp_id = create_employee(
                last_name=ln,
                first_name=fn,
                middle_name=mn if mn else None,
                position=pos if pos else None,
                department=dep if dep else None,
            )
            print(f"Сотрудник создан с ID={emp_id}")

            print("\nСоздание учётной записи для этого сотрудника:")
            login = input("Логин: ").strip()
            password = input("Пароль: ").strip()
            print("Доступные роли: Employee, HR, Manager, Admin")
            role_name = input("Роль: ").strip()
            try:
                create_user_with_role(emp_id, login, password, role_name)
                print("Пользователь для нового сотрудника создан.")
            except ValueError as e:
                print(e)

        else:
            print("Неверный пункт или у вашей роли нет доступа.")


def main():
    print("=== Система учёта рабочего времени ===")

    for attempt in range(3):
        login = input("Логин: ").strip()
        password = input("Пароль: ").strip()

        auth_result = authenticate(login, password)
        if auth_result is None:
            print("Неверный логин или пароль, попробуйте ещё раз.")
        else:
            user, roles = auth_result
            role_names = {r.name for r in roles}
            if not role_names:
                print("У пользователя нет ролей. Доступ запрещён.")
                return

            print("\nУспешный вход.")
            main_menu(user, role_names)
            return

    print("Превышено количество попыток входа.")


if __name__ == "__main__":
    main()
