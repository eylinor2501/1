import sqlite3

DB_NAME = "worktime.db"

def main():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Employee;")
    rows = cursor.fetchall()

    print("Содержимое таблицы Employee:")
    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    main()
