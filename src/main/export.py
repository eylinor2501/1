import sqlite3
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None
    print("Внимание: модуль PyYAML не установлен, файл data.yaml создан не будет.")

DB_NAME = "worktime.db"          # наша лабораторная БД
OUT_DIR = Path("out")            # папка для выгрузок

JSON_PATH = OUT_DIR / "data.json"
CSV_PATH = OUT_DIR / "data.csv"
XML_PATH = OUT_DIR / "data.xml"
YAML_PATH = OUT_DIR / "data.yaml"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_employee_workdays() -> list[sqlite3.Row]:
    """
    Достаём Employee + WorkDays.
    ВАЖНО: все поля WorkDays алиасим с префиксом workday_ —
    дальше по этому префиксу строим вложенный объект.
    """
    sql = """
        SELECT
            e.employee_id        AS employee_id,
            e.last_name          AS last_name,
            e.first_name         AS first_name,
            e.middle_name        AS middle_name,
            e.position           AS position,
            e.department         AS department,
            w.workday_id         AS workday_id,
            w.work_date          AS workday_date,
            w.planned_start      AS workday_planned_start,
            w.total_hours        AS workday_total_hours
        FROM Employee e
        LEFT JOIN WorkDays w ON w.employee_id = e.employee_id
        ORDER BY e.employee_id, w.work_date
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows


def build_nested_structure(rows: list[sqlite3.Row]) -> list[dict]:
    """
    Из плоских строк (employee + workday) делаем:
    [
      {
        employee_id: ...,
        ...,
        workdays: [
          {workday_id: ..., date: ..., ...},
          ...
        ]
      },
      ...
    ]
    """
    employees: dict[int, dict] = {}

    for row in rows:
        row_dict = dict(row)
        emp_id = row_dict["employee_id"]

        # разделяем поля сотрудника и рабочие дни
        emp_data: dict = {}
        workday_data: dict = {}

        for key, value in row_dict.items():
            if key.startswith("workday_") or key == "workday_id":
                # поле рабочего дня
                # workday_date -> date, workday_total_hours -> total_hours и т.п.
                if key == "workday_id":
                    wd_key = "id"
                elif key.startswith("workday_"):
                    wd_key = key[len("workday_") :]
                else:
                    wd_key = key
                workday_data[wd_key] = value
            else:
                # поле сотрудника
                emp_data[key] = value

        # создаём сотрудника, если его ещё нет
        if emp_id not in employees:
            employees[emp_id] = emp_data
            employees[emp_id]["workdays"] = []

        # если есть реальный рабочий день (а не сплошные NULL)
        if any(v is not None for v in workday_data.values()):
            employees[emp_id]["workdays"].append(workday_data)

    return list(employees.values())


def ensure_out_dir():
    OUT_DIR.mkdir(exist_ok=True)


def export_json(data: list[dict]):
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"JSON сохранён в {JSON_PATH}")


def export_csv(rows: list[sqlite3.Row]):
    """
    Для CSV делаем плоскую структуру — каждая строка это
    employee + один workday (как есть в rows).
    """
    if not rows:
        print("Нет данных для CSV.")
        return

    fieldnames = rows[0].keys()

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    print(f"CSV сохранён в {CSV_PATH}")


def export_xml(data: list[dict]):
    root = ET.Element("employees")

    for emp in data:
        emp_elem = ET.SubElement(root, "employee")

        # поля сотрудника (всё, кроме workdays)
        for key, value in emp.items():
            if key == "workdays":
                continue
            child = ET.SubElement(emp_elem, key)
            child.text = "" if value is None else str(value)

        # вложенный список рабочих дней
        wds_elem = ET.SubElement(emp_elem, "workdays")
        for wd in emp.get("workdays", []):
            wd_elem = ET.SubElement(wds_elem, "workday")
            for k, v in wd.items():
                c = ET.SubElement(wd_elem, k)
                c.text = "" if v is None else str(v)

    tree = ET.ElementTree(root)
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)
    print(f"XML сохранён в {XML_PATH}")


def export_yaml(data: list[dict]):
    if yaml is None:
        print("PyYAML не установлен, YAML не будет создан.")
        return
    with YAML_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
    print(f"YAML сохранён в {YAML_PATH}")


def main():
    ensure_out_dir()
    rows = fetch_employee_workdays()
    nested = build_nested_structure(rows)

    export_json(nested)
    export_csv(rows)
    export_xml(nested)
    export_yaml(nested)

    print("Экспорт завершён.")


if __name__ == "__main__":
    main()
