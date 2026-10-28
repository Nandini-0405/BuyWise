import sqlite3

conn = sqlite3.connect('database/buywise.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)

for table in tables:
    t_name = table[0]
    cursor.execute(f"PRAGMA table_info('{t_name}');")
    print(f'\nSchema for {t_name}:')
    for col in cursor.fetchall():
        print(col)
