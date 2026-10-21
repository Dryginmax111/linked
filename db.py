"""SQLite-хранилище для реестра ссылок.

Активируется в settings.json → "data_backend": "sqlite".

Логика первого запуска:
  1. Если reestr.db не существует и есть реестр.xlsx — импортируем данные.
  2. Если БД пустая и xlsx нет — создаём пустую схему.
  3. Если БД уже есть — используем её.

xlsx-файл поддерживается как зеркало: после каждого сохранения в БД
автоматически пишется копия в xlsx (для совместимости и бэкапа).

WAL-режим позволяет работать с файлом по сети 2–5 пользователям.
Для больше — переключение на PostgreSQL (тот же интерфейс).
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path


class SqliteStorage:
    """Обёртка над SQLite. Предоставляет интерфейс to_workbook / from_workbook,
    чтобы app.py продолжал работать с openpyxl Workbook."""

    def __init__(self, db_path: str, headers: list):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.headers = list(headers)
        self.lock = threading.RLock()
        self._init_schema()

    # ------------------------------------------------------------
    # Соединение
    # ------------------------------------------------------------
    def _connect(self):
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=20,
            isolation_level=None,  # autocommit; транзакции вручную
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA synchronous=NORMAL')
            conn.execute('PRAGMA busy_timeout=15000')
        except sqlite3.OperationalError:
            # Сетевые диски могут не поддерживать WAL — падаем на DELETE
            try:
                conn.execute('PRAGMA journal_mode=DELETE')
            except Exception:
                pass
        return conn
        
    @contextmanager
    def _conn_ctx(self):
        """Соединение с гарантированным закрытием."""
        conn = self._connect()
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass
    # ------------------------------------------------------------
    # Схема
    # ------------------------------------------------------------
    def _init_schema(self):
        with self.lock, self._conn_ctx() as conn:
            # Все колонки, кроме id, как TEXT/INTEGER
            col_defs = []
            for h in self.headers:
                if h == 'id':
                    continue
                sql_type = 'INTEGER' if h in ('favorite', 'order_index', 'click_count') else 'TEXT'
                col_defs.append(f'"{h}" {sql_type}')
            sql = f'''CREATE TABLE IF NOT EXISTS records (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                {", ".join(col_defs)}
            )'''
            conn.execute(sql)
            for col in ('name_del', 'category', 'deleted_at', 'updated_at'):
                if col in self.headers:
                    try:
                        conn.execute(
                            f'CREATE INDEX IF NOT EXISTS idx_{col} ON records("{col}")'
                        )
                    except Exception:
                        pass
            # meta-таблица
            conn.execute('''CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )''')

    # ------------------------------------------------------------
    # Проверки
    # ------------------------------------------------------------
    def is_empty(self) -> bool:
        with self.lock, self._conn_ctx() as conn:
            cur = conn.execute('SELECT COUNT(*) FROM records')
            return (cur.fetchone() or [0])[0] == 0

    def count(self) -> int:
        with self.lock, self._conn_ctx() as conn:
            cur = conn.execute('SELECT COUNT(*) FROM records')
            return (cur.fetchone() or [0])[0]

    # ------------------------------------------------------------
    # Чтение в Workbook
    # ------------------------------------------------------------
    def to_workbook(self):
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        if ws is None:
            ws = wb.create_sheet("Sheet")
        ws.append(self.headers)
        with self.lock, self._conn_ctx() as conn:
            cols = ', '.join(f'"{h}"' for h in self.headers)
            cur = conn.execute(f'SELECT {cols} FROM records ORDER BY "id" ASC')
            for row in cur:
                ws.append([self._to_cell(row[h]) for h in self.headers])
        return wb

    @staticmethod
    def _to_cell(v):
        """Конвертирует SQLite-значение в приемлемое для openpyxl."""
        if v is None:
            return ''
        return v

    # ------------------------------------------------------------
    # Запись из Workbook (полная замена)
    # ------------------------------------------------------------
    def from_workbook(self, wb):
        ws = wb.active or wb.create_sheet("Sheet")
        header_row = [c.value for c in ws[1]] if ws.max_row >= 1 else []
        col_idx = {name: i for i, name in enumerate(header_row) if name}

        insert_cols = [h for h in self.headers if h != 'id']
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row is None or all(v is None or v == '' for v in row):
                continue
            rec = {}
            for h in insert_cols:
                i = col_idx.get(h)
                rec[h] = row[i] if (i is not None and i < len(row)) else None
            id_val = None
            if 'id' in col_idx and col_idx['id'] < len(row):
                id_val = row[col_idx['id']]
            rows.append((id_val, rec))

        with self.lock, self._conn_ctx() as conn:
            conn.execute('BEGIN IMMEDIATE')
            try:
                conn.execute('DELETE FROM records')
                if rows:
                    cols_sql = ', '.join(f'"{c}"' for c in insert_cols)
                    ph = ', '.join('?' * len(insert_cols))
                    data = [
                        tuple(self._norm(rec.get(c)) for c in insert_cols)
                        for _, rec in rows
                    ]
                    conn.executemany(
                        f'INSERT INTO records ({cols_sql}) VALUES ({ph})',
                        data
                    )

                    # Забираем rowid новых строк в порядке вставки
                    cur = conn.execute('SELECT rowid FROM records ORDER BY rowid ASC')
                    rowids = [r[0] for r in cur.fetchall()]

                    # Восстанавливаем исходные id по позиции
                    for (id_val, _), rid in zip(rows, rowids):
                        if id_val is None:
                            continue
                        try:
                            int_id = int(id_val)
                        except (ValueError, TypeError):
                            continue
                        conn.execute(
                            'UPDATE records SET "id"=? WHERE rowid=?',
                            (int_id, rid)
                        )

                    # Сбрасываем AUTOINCREMENT счётчик под фактический MAX(id)
                    try:
                        cur = conn.execute('SELECT MAX("id") FROM records')
                        r = cur.fetchone()
                        max_id = r[0] if r and r[0] is not None else 0
                        conn.execute('DELETE FROM sqlite_sequence WHERE name=\'records\'')
                        if max_id:
                            conn.execute(
                                "INSERT INTO sqlite_sequence(name, seq) VALUES('records', ?)",
                                (max_id,)
                            )
                    except sqlite3.OperationalError:
                        pass

                conn.execute('COMMIT')
            except Exception:
                try:
                    conn.execute('ROLLBACK')
                except Exception:
                    pass
                raise

    @staticmethod
    def _norm(v):
        if v is None:
            return None
        if isinstance(v, (int, float, str, bytes)):
            return v
        return str(v)

    # ------------------------------------------------------------
    # Импорт из xlsx (одноразовый)
    # ------------------------------------------------------------
    def import_from_xlsx(self, xlsx_path: str) -> int:
        from openpyxl import load_workbook
        p = Path(xlsx_path)
        if not p.exists():
            raise FileNotFoundError(f'Не найден файл: {xlsx_path}')
        wb = load_workbook(str(p))
        ws = wb.active
        n = max(0, (ws.max_row or 1) - 1) if ws else 0
        self.from_workbook(wb)
        self.set_meta('imported_from', str(p))
        self.set_meta('imported_at', __import__('datetime').datetime.now().isoformat())
        return n

    # ------------------------------------------------------------
    # Meta
    # ------------------------------------------------------------
    def set_meta(self, key: str, value: str):
        with self.lock, self._conn_ctx() as conn:
            conn.execute(
                'INSERT INTO meta(key, value) VALUES (?, ?) '
                'ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                (str(key), str(value))
            )

    def get_meta(self, key: str, default=None):
        with self.lock, self._conn_ctx() as conn:
            cur = conn.execute('SELECT value FROM meta WHERE key=?', (str(key),))
            row = cur.fetchone()
            return row['value'] if row else default

    # ------------------------------------------------------------
    # Диагностика
    # ------------------------------------------------------------
    def info(self) -> dict:
        try:
            size = self.db_path.stat().st_size
        except Exception:
            size = 0
        return {
            'db_path': str(self.db_path),
            'size_bytes': size,
            'count': self.count(),
            'wal_mode': self._is_wal(),
            'imported_from': self.get_meta('imported_from', ''),
            'imported_at': self.get_meta('imported_at', ''),
        }

    def _is_wal(self) -> bool:
        try:
            with self.lock, self._conn_ctx() as conn:
                cur = conn.execute('PRAGMA journal_mode')
                row = cur.fetchone()
                return bool(row and str(row[0]).lower() == 'wal')
        except Exception:
            return False


def open_storage(db_path: str, headers: list) -> SqliteStorage:
    return SqliteStorage(db_path, headers)