from __future__ import annotations

import sqlite3


def main(db_path: str = '.data/enterprise_memory.db') -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('tables:', cur.fetchall())
    for t in ('companies', 'documents', 'decisions', 'risks'):
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            print(t, cur.fetchone()[0])
        except Exception as e:
            print(t, 'ERROR', e)
    conn.close()


if __name__ == '__main__':
    main()
