"""
Трекер задач сотрудников отдела. v0.9.

Новое в v0.9:
  - Фильтр задач по периоду: пересечение [start..deadline] с [from..to]
  - Просроченные задачи показываются всегда, пока не закрыты
  - Отдельная тема трекера (trk-theme-light / trk-theme-dark) — на стороне UI
"""
import secrets
from pathlib import Path
from datetime import datetime, date, timedelta
from calendar import monthrange

__version__ = "0.9"
__description__ = "Трекер задач: календарь, свод, тепловая карта, отпуска, отделы"

DATA_FILE = 'task_tracker_data.json'

STATUS_LABELS = {
    'planned':     '📝 Запланировано',
    'in_progress': '🔵 В работе',
    'done':        '✅ Готово',
    'blocked':     '🔴 Заблокировано',
}
TASK_STATUS_LABELS = {
    'active':   'Активна',
    'done':     'Выполнена',
    'paused':   'Приостановлена',
    'archived': 'Архив',
}
WORK_WEEKDAYS = {0, 1, 2, 3, 4}

EMOJI_LIST = [
    '🚀','📋','💼','📊','📈','🎯','🔧','⚙️','💡','🔍','📝','✏️',
    '📁','📂','🗂️','📌','📍','🔖','🏷️','📎','🖇️','🔗','📅','📆',
    '⏰','⌛','⏳','👥','👤','🧑','👨💼','👩💼','🤝','💬','📞','📧',
    '✉️','📨','📩','📤','📥','📦','🗃️','🗄️','💻','🖥️','⌨️','🖱️',
    '💾','💿','📀','📱','☎️','🖨️','📡','📶','🔌','🔋','💡','🧮',
    '🧪','🧬','🔬','🔭','🎨','🎬','🎥','📷','📸','🎞️','📺','📻',
    '🎵','🎧','🎤','🏆','🏅','🥇','🎖️','🏵️','🎗️','🎁','🎈','🎉',
    '✨','⭐','🌟','💫','⚡','🔥','💥','❄️','☀️','🌤️','⛅','🌧️',
    '⚠️','❗','❓','✅','❌','➕','➖','✔️','↩️','🔄','🔃','🔁',
    '🟢','🟡','🔴','🟠','🔵','🟣','⚫','⚪','🟤','💚','💛','❤️',
]
PALETTE = [
    '#f5d76e','#f39c12','#e74c3c','#e91e63','#9b59b6','#673ab7',
    '#3f51b5','#2196f3','#00bcd4','#009688','#4caf50','#8bc34a',
    '#ff5722','#795548','#607d8b','#34495e','#7a9ab5','#2ecc71',
]

_RU_HOLIDAYS_TEMPLATE = [
    ('01-01', 'Новый год'),
    ('01-02', 'Новогодние каникулы'),
    ('01-03', 'Новогодние каникулы'),
    ('01-04', 'Новогодние каникулы'),
    ('01-05', 'Новогодние каникулы'),
    ('01-06', 'Новогодние каникулы'),
    ('01-07', 'Рождество Христово'),
    ('01-08', 'Новогодние каникулы'),
    ('02-23', 'День защитника Отечества'),
    ('03-08', 'Международный женский день'),
    ('05-01', 'Праздник Весны и Труда'),
    ('05-09', 'День Победы'),
    ('06-12', 'День России'),
    ('11-04', 'День народного единства'),
]


def _default_ru_holidays(year):
    out = {}
    for mmdd, name in _RU_HOLIDAYS_TEMPLATE:
        out[f'{year:04d}-{mmdd}'] = name
    return out


def _empty_data():
    today = date.today()
    holidays = {}
    holidays.update(_default_ru_holidays(today.year))
    holidays.update(_default_ru_holidays(today.year + 1))
    return {
        'employees': [], 'tasks': [], 'log': [], 'departments': [],
        'holidays': holidays,
        'meta': {
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'next_log_id': 1,
            'departments_migrated': False,
            'holidays_initialized': True,
        },
    }


def _slugify(name):
    s = str(name or '').strip().lower()
    out = []
    for ch in s:
        if ch.isascii() and ch.isalnum():
            out.append(ch)
        elif ch in (' ', '-', '_', '.'):
            out.append('_')
    return (''.join(out).strip('_') or 'item')[:40]


def _parse_ym(ym):
    try:
        y, m = ym.split('-')
        return int(y), int(m)
    except Exception:
        t = date.today()
        return t.year, t.month


def _valid_date(s):
    try:
        datetime.strptime(str(s), '%Y-%m-%d')
        return True
    except Exception:
        return False


def _in_vacation(emp, dk):
    if not emp:
        return False
    for v in emp.get('vacations', []) or []:
        f, t = v.get('from', ''), v.get('to', '')
        if f and t and f <= dk <= t:
            return True
    return False


def _is_overdue(task, today_iso):
    if not task:
        return False
    dl = task.get('deadline', '')
    st = task.get('status', 'active')
    return bool(dl) and dl < today_iso and st not in ('done', 'archived')


def _resolve_range(args):
    from_s = str(args.get('from', '') or '').strip()
    to_s = str(args.get('to', '') or '').strip()
    year = str(args.get('year', '') or '').strip()
    ym = str(args.get('ym', '') or '').strip()
    if from_s and to_s and _valid_date(from_s) and _valid_date(to_s):
        if from_s <= to_s:
            return from_s, to_s
        return to_s, from_s
    if year:
        try:
            y = int(year)
            return f'{y:04d}-01-01', f'{y:04d}-12-31'
        except Exception:
            pass
    if ym:
        y, m = _parse_ym(ym)
        last = monthrange(y, m)[1]
        return f'{y:04d}-{m:02d}-01', f'{y:04d}-{m:02d}-{last:02d}'
    t = date.today()
    return t.replace(day=1).strftime('%Y-%m-%d'), t.strftime('%Y-%m-%d')


def _calc_coverage(task, emp, logs_for_task_emp, today_d):
    """Считает покрытие по всей задаче (не по периоду).
    Возвращает (active_days, possible_days, coverage)."""
    if not task:
        return 0, 0, 0

    task_start = task.get('start_date') or ''
    task_deadline = task.get('deadline') or ''

    ts = None
    if task_start and _valid_date(task_start):
        try:
            ts = datetime.strptime(task_start, '%Y-%m-%d').date()
        except Exception:
            ts = None
    if ts is None and task.get('created_at'):
        try:
            ts = datetime.strptime(str(task['created_at'])[:10], '%Y-%m-%d').date()
        except Exception:
            ts = None

    te = None
    if task_deadline and _valid_date(task_deadline):
        try:
            te = datetime.strptime(task_deadline, '%Y-%m-%d').date()
        except Exception:
            te = None
    if te is None:
        te = today_d

    if te > today_d:
        te = today_d
    if ts is None:
        ts = today_d
    if ts > te:
        return 0, 0, 0

    active_dates = set()
    for l in logs_for_task_emp:
        dk = l.get('date', '')
        try:
            h = float(l.get('hours', 0) or 0)
        except (ValueError, TypeError):
            h = 0
        if h > 0 and _valid_date(dk):
            active_dates.add(dk)

    possible_days = 0
    cur = ts
    while cur <= te:
        dk = cur.strftime('%Y-%m-%d')
        if cur.weekday() in WORK_WEEKDAYS:
            if emp is None or not _in_vacation(emp, dk):
                possible_days += 1
        cur += timedelta(days=1)

    active_days = len(active_dates)
    coverage = round(100 * active_days / possible_days) if possible_days else 0
    return active_days, possible_days, coverage


def _task_matches_dept(task, dept_id, dept_emp_ids):
    if not dept_id:
        return True
    t_deps = set(task.get('department_ids') or [])
    if dept_id in t_deps:
        return True
    if not t_deps:
        for a in task.get('assignees', []) or []:
            if a in dept_emp_ids:
                return True
    return False


def _task_in_period(task, date_from, date_to, today_iso):
    """
    True, если задача должна быть показана за период [date_from, date_to]:
      1) Пересечение [start_date, deadline] с [from, to]
      2) ИЛИ задача просрочена (deadline < today и статус не done/archived)

    Правила пустых полей:
      - start_date пусто → 1900-01-01
      - deadline   пусто → today (не тянем бесконечно)
    """
    if not task:
        return False

    # Просроченная — показываем всегда
    if _is_overdue(task, today_iso):
        return True

    start = task.get('start_date') or '1900-01-01'
    end = task.get('deadline') or today_iso

    if not _valid_date(start):
        start = '1900-01-01'
    if not _valid_date(end):
        end = today_iso

    # Пересечение [start, end] и [date_from, date_to]
    return (start <= date_to) and (end >= date_from)


def _build_day_meta(all_days, holidays_map, today):
    out = {}
    for dk in all_days:
        try:
            wd = datetime.strptime(dk, '%Y-%m-%d').weekday()
        except Exception:
            wd = 0
        is_weekend = wd >= 5
        is_holiday = dk in holidays_map if isinstance(holidays_map, dict) else False
        hol_name = holidays_map.get(dk, '') if isinstance(holidays_map, dict) else ''
        out[dk] = {
            'date': dk,
            'weekday': wd,
            'is_weekend': is_weekend,
            'is_holiday': bool(is_holiday),
            'holiday_name': hol_name,
            'is_today': dk == today,
            'is_workday': not (is_weekend or is_holiday),
        }
    return out


def _migrate_departments(d):
    existing_ids = {dep.get('id', '') for dep in d['departments']}
    for e in d['employees']:
        dept_name = (e.get('department') or '').strip()
        if not dept_name:
            e.setdefault('department_id', '')
            continue
        if e.get('department_id'):
            continue
        dep_id = None
        for dep in d['departments']:
            if dep.get('name', '') == dept_name:
                dep_id = dep['id']
                break
        if not dep_id:
            base = _slugify(dept_name) or 'dept'
            dep_id = base
            i = 1
            while dep_id in existing_ids:
                i += 1
                dep_id = f'{base}_{i}'
            d['departments'].append({'id': dep_id, 'name': dept_name, 'color': '#7a9ab5'})
            existing_ids.add(dep_id)
        e['department_id'] = dep_id
    for t in d['tasks']:
        old_id = t.pop('department_id', None)
        if 'department_ids' not in t:
            if isinstance(old_id, str) and old_id:
                t['department_ids'] = [old_id]
            elif isinstance(old_id, list):
                t['department_ids'] = [x for x in old_id if isinstance(x, str) and x]
            else:
                t['department_ids'] = []
        else:
            if not isinstance(t['department_ids'], list):
                t['department_ids'] = []


def register(hooks, app, config, core):
    from flask import request, jsonify, session, Response

    data_path = Path(core.BASE_DIR) / DATA_FILE

    def _load_data():
        d = core.load_json(str(data_path), None)
        if not isinstance(d, dict):
            d = _empty_data()
        d.setdefault('employees', [])
        d.setdefault('tasks', [])
        d.setdefault('log', [])
        d.setdefault('departments', [])
        d.setdefault('holidays', {})
        d.setdefault('meta', {})
        if not isinstance(d['employees'], list):
            d['employees'] = []
        if not isinstance(d['tasks'], list):
            d['tasks'] = []
        if not isinstance(d['log'], list):
            d['log'] = []
        if not isinstance(d['departments'], list):
            d['departments'] = []
        if not isinstance(d['holidays'], dict):
            d['holidays'] = {}
        d['meta'].setdefault('next_log_id', 1)
        d['meta'].setdefault('departments_migrated', False)
        d['meta'].setdefault('holidays_initialized', False)
        for e in d['employees']:
            e.setdefault('vacations', [])
            if not isinstance(e['vacations'], list):
                e['vacations'] = []
            e.setdefault('department', '')
            e.setdefault('department_id', '')
        for t in d['tasks']:
            t.setdefault('assignees', [])
            if not isinstance(t['assignees'], list):
                t['assignees'] = []
            t.setdefault('status', 'active')
            t.setdefault('start_date', '')
            if not t['start_date'] and t.get('created_at'):
                t['start_date'] = str(t['created_at'])[:10]
            if 'department_ids' not in t or not isinstance(t['department_ids'], list):
                old_id = t.pop('department_id', None)
                if isinstance(old_id, str) and old_id:
                    t['department_ids'] = [old_id]
                elif isinstance(old_id, list):
                    t['department_ids'] = [x for x in old_id if isinstance(x, str) and x]
                else:
                    t['department_ids'] = []
            else:
                t.pop('department_id', None)
        if not d['meta'].get('departments_migrated'):
            try:
                _migrate_departments(d)
            except Exception as e:
                print(f'[tracker] migrate_departments failed: {e}')
            d['meta']['departments_migrated'] = True
            _save_data(d)
        if not d['meta'].get('holidays_initialized'):
            try:
                today = date.today()
                for y in (today.year, today.year + 1):
                    for k, v in _default_ru_holidays(y).items():
                        d['holidays'].setdefault(k, v)
            except Exception as e:
                print(f'[tracker] holidays init failed: {e}')
            d['meta']['holidays_initialized'] = True
            _save_data(d)
        return d

    def _save_data(d):
        core.save_json(str(data_path), d)

    def _ensure_csrf():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        return session['csrf_token']

    def _emp_map(d):
        return {e['id']: e for e in d['employees']}

    def _task_map(d):
        return {t['id']: t for t in d['tasks']}

    # ============================================================
    # СТРАНИЦА
    # ============================================================
    @app.route('/tasks')
    def tasks_page():
        return Response(_render_tracker_html(_ensure_csrf()), mimetype='text/html')

    # ============================================================
    # STATE
    # ============================================================
    @app.route('/api/tracker/state', methods=['GET'])
    def api_state():
        d = _load_data()
        today = date.today().strftime('%Y-%m-%d')
        tasks = []
        for t in d['tasks']:
            tt = dict(t)
            tt['overdue'] = _is_overdue(t, today)
            tasks.append(tt)
        return jsonify({
            'success': True,
            'employees': d['employees'],
            'tasks': tasks,
            'log': d['log'],
            'departments': d['departments'],
            'holidays': d['holidays'],
            'log_count': len(d['log']),
            'status_labels': STATUS_LABELS,
            'task_status_labels': TASK_STATUS_LABELS,
            'palette': PALETTE,
            'emoji': EMOJI_LIST,
            'today': today,
            'work_weekdays': list(WORK_WEEKDAYS),
        })

    # ============================================================
    # ПРАЗДНИКИ
    # ============================================================
    @app.route('/api/tracker/holiday/save', methods=['POST'])
    def api_holiday_save():
        body = request.get_json() or {}
        dk = str(body.get('date', '')).strip()
        name = str(body.get('name', '')).strip()[:100]
        if not _valid_date(dk):
            return jsonify({'success': False, 'error': 'Некорректная дата'}), 400
        if not name:
            name = 'Праздник'
        d = _load_data()
        d['holidays'][dk] = name
        _save_data(d)
        return jsonify({'success': True})

    @app.route('/api/tracker/holiday/delete', methods=['POST'])
    def api_holiday_delete():
        body = request.get_json() or {}
        dk = str(body.get('date', '')).strip()
        if not _valid_date(dk):
            return jsonify({'success': False, 'error': 'Некорректная дата'}), 400
        d = _load_data()
        d['holidays'].pop(dk, None)
        _save_data(d)
        return jsonify({'success': True})

    # ============================================================
    # СОТРУДНИКИ
    # ============================================================
    @app.route('/api/tracker/employee/save', methods=['POST'])
    def api_employee_save():
        body = request.get_json() or {}
        emp_id = str(body.get('id', '')).strip()
        name = str(body.get('name', '')).strip()[:100]
        color = str(body.get('color', '')).strip()[:20]
        role = str(body.get('role', '')).strip()[:50]
        department_id = str(body.get('department_id', '')).strip()
        if not name:
            return jsonify({'success': False, 'error': 'Имя обязательно'}), 400
        d = _load_data()
        department = ''
        if department_id:
            for dep in d['departments']:
                if dep.get('id') == department_id:
                    department = dep.get('name', '')
                    break
            if not department:
                department_id = ''
        if not emp_id:
            base = _slugify(name)
            emp_id = base
            i = 1
            existing = {e.get('id') for e in d['employees']}
            while emp_id in existing:
                i += 1
                emp_id = f'{base}_{i}'
            d['employees'].append({
                'id': emp_id, 'name': name,
                'color': color or '#00897b', 'role': role,
                'department_id': department_id, 'department': department,
                'vacations': [],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
            created = True
        else:
            found = False
            for e in d['employees']:
                if e.get('id') == emp_id:
                    e['name'] = name
                    e['color'] = color or e.get('color') or '#00897b'
                    e['role'] = role
                    e['department_id'] = department_id
                    e['department'] = department
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404
            created = False
        _save_data(d)
        core.log_action('tracker_employee_save', None, name, {'id': emp_id, 'created': created})
        return jsonify({'success': True, 'id': emp_id, 'created': created})

    @app.route('/api/tracker/employee/delete', methods=['POST'])
    def api_employee_delete():
        body = request.get_json() or {}
        emp_id = str(body.get('id', '')).strip()
        if not emp_id:
            return jsonify({'success': False, 'error': 'Не указан id'}), 400
        d = _load_data()
        before = len(d['employees'])
        d['employees'] = [e for e in d['employees'] if e.get('id') != emp_id]
        deleted = before - len(d['employees'])
        log_affected = sum(1 for l in d['log'] if l.get('employee_id') == emp_id)
        for t in d['tasks']:
            if emp_id in t.get('assignees', []):
                t['assignees'] = [a for a in t['assignees'] if a != emp_id]
        _save_data(d)
        return jsonify({'success': True, 'deleted': deleted, 'log_affected': log_affected})

    @app.route('/api/tracker/employee/vacation/add', methods=['POST'])
    def api_vacation_add():
        body = request.get_json() or {}
        emp_id = str(body.get('employee_id', '')).strip()
        date_from = str(body.get('from', '')).strip()
        date_to = str(body.get('to', '')).strip()
        comment = str(body.get('comment', '')).strip()[:200]
        if not emp_id:
            return jsonify({'success': False, 'error': 'Не указан сотрудник'}), 400
        if not _valid_date(date_from) or not _valid_date(date_to):
            return jsonify({'success': False, 'error': 'Некорректные даты'}), 400
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        d = _load_data()
        emp = None
        for e in d['employees']:
            if e.get('id') == emp_id:
                emp = e
                break
        if not emp:
            return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404
        emp.setdefault('vacations', [])
        for v in emp['vacations']:
            if not (date_to < v.get('from', '') or date_from > v.get('to', '')):
                return jsonify({'success': False, 'error': 'Пересекается с другим периодом'}), 400
        emp['vacations'].append({'from': date_from, 'to': date_to, 'comment': comment})
        emp['vacations'].sort(key=lambda v: v.get('from', ''))
        _save_data(d)
        return jsonify({'success': True})

    @app.route('/api/tracker/employee/vacation/delete', methods=['POST'])
    def api_vacation_delete():
        body = request.get_json() or {}
        emp_id = str(body.get('employee_id', '')).strip()
        try:
            idx = int(body.get('index'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Некорректный index'}), 400
        d = _load_data()
        for e in d['employees']:
            if e.get('id') == emp_id:
                vac = e.get('vacations', [])
                if 0 <= idx < len(vac):
                    vac.pop(idx)
                    _save_data(d)
                    return jsonify({'success': True})
                return jsonify({'success': False, 'error': 'Период не найден'}), 404
        return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404

    # ============================================================
    # ОТДЕЛЫ
    # ============================================================
    @app.route('/api/tracker/department/save', methods=['POST'])
    def api_department_save():
        body = request.get_json() or {}
        dep_id = str(body.get('id', '')).strip()
        name = str(body.get('name', '')).strip()[:80]
        color = str(body.get('color', '')).strip()[:20]
        if not name:
            return jsonify({'success': False, 'error': 'Название обязательно'}), 400
        d = _load_data()
        if not dep_id:
            base = _slugify(name) or 'dept'
            dep_id = base
            i = 1
            existing = {dep.get('id') for dep in d['departments']}
            while dep_id in existing:
                i += 1
                dep_id = f'{base}_{i}'
            d['departments'].append({'id': dep_id, 'name': name, 'color': color or '#00897b'})
            created = True
        else:
            found = False
            for dep in d['departments']:
                if dep.get('id') == dep_id:
                    dep['name'] = name
                    dep['color'] = color or dep.get('color') or '#00897b'
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Отдел не найден'}), 404
            for e in d['employees']:
                if e.get('department_id') == dep_id:
                    e['department'] = name
            created = False
        _save_data(d)
        return jsonify({'success': True, 'id': dep_id, 'created': created})

    @app.route('/api/tracker/department/delete', methods=['POST'])
    def api_department_delete():
        body = request.get_json() or {}
        dep_id = str(body.get('id', '')).strip()
        if not dep_id:
            return jsonify({'success': False, 'error': 'Не указан id'}), 400
        d = _load_data()
        affected = 0
        for e in d['employees']:
            if e.get('department_id') == dep_id:
                e['department_id'] = ''
                e['department'] = ''
                affected += 1
        tasks_affected = 0
        for t in d['tasks']:
            if dep_id in t.get('department_ids', []):
                t['department_ids'] = [x for x in t['department_ids'] if x != dep_id]
                tasks_affected += 1
        before = len(d['departments'])
        d['departments'] = [dep for dep in d['departments'] if dep.get('id') != dep_id]
        deleted = before - len(d['departments'])
        _save_data(d)
        return jsonify({
            'success': True,
            'deleted': deleted,
            'employees_affected': affected,
            'tasks_affected': tasks_affected,
        })

    # ============================================================
    # ЗАДАЧИ
    # ============================================================
    @app.route('/api/tracker/task/save', methods=['POST'])
    def api_task_save():
        body = request.get_json() or {}
        task_id = str(body.get('id', '')).strip()
        name = str(body.get('name', '')).strip()[:200]
        icon = str(body.get('icon', '')).strip()[:8] or '📋'
        description = str(body.get('description', '')).strip()[:2000]
        status = str(body.get('status', 'active')).strip()[:20]
        deadline = str(body.get('deadline', '')).strip()[:20]
        start_date = str(body.get('start_date', '')).strip()[:20]
        if start_date and not _valid_date(start_date):
            start_date = ''
        folder = str(body.get('folder', '')).strip()[:500]
        order_ref = str(body.get('order_ref', '')).strip()[:200]

        tags_raw = body.get('tags', [])
        if isinstance(tags_raw, str):
            tags = [t.strip() for t in tags_raw.split(',') if t.strip()][:20]
        elif isinstance(tags_raw, list):
            tags = [str(t).strip()[:40] for t in tags_raw if str(t).strip()][:20]
        else:
            tags = []

        assignees_raw = body.get('assignees', [])
        assignees = [str(a).strip() for a in assignees_raw if str(a).strip()] if isinstance(assignees_raw, list) else []

        dep_ids_raw = body.get('department_ids', None)
        if dep_ids_raw is None:
            old_dep = body.get('department_id', '')
            if isinstance(old_dep, str) and old_dep:
                dep_ids_raw = [old_dep]
            else:
                dep_ids_raw = []
        if isinstance(dep_ids_raw, str):
            dep_ids_raw = [dep_ids_raw.strip()] if dep_ids_raw.strip() else []
        if not isinstance(dep_ids_raw, list):
            dep_ids_raw = []
        dep_ids = [str(x).strip() for x in dep_ids_raw if str(x).strip()]

        if not name:
            return jsonify({'success': False, 'error': 'Название обязательно'}), 400
        if status not in TASK_STATUS_LABELS:
            status = 'active'
        d = _load_data()
        valid_dep_ids = {dep['id'] for dep in d['departments']}
        dep_ids = [x for x in dep_ids if x in valid_dep_ids]

        emp_ids = {e['id'] for e in d['employees']}
        if dep_ids:
            allowed_emps = {e['id'] for e in d['employees'] if e.get('department_id') in dep_ids}
            assignees = [a for a in assignees if a in allowed_emps]
        else:
            assignees = [a for a in assignees if a in emp_ids]

        if not task_id:
            base = _slugify(name)
            task_id = base
            i = 1
            existing = {t.get('id') for t in d['tasks']}
            while task_id in existing:
                i += 1
                task_id = f'{base}_{i}'
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if not start_date:
                start_date = now_str[:10]
            d['tasks'].append({
                'id': task_id, 'name': name, 'icon': icon,
                'description': description, 'status': status,
                'start_date': start_date,
                'deadline': deadline,
                'folder': folder, 'order_ref': order_ref,
                'tags': tags, 'assignees': assignees,
                'department_ids': dep_ids,
                'created_at': now_str,
            })
            created = True
        else:
            found = False
            for t in d['tasks']:
                if t.get('id') == task_id:
                    t.update({
                        'name': name, 'icon': icon, 'description': description,
                        'status': status, 'deadline': deadline, 'folder': folder,
                        'order_ref': order_ref, 'tags': tags, 'assignees': assignees,
                        'department_ids': dep_ids,
                    })
                    if start_date:
                        t['start_date'] = start_date
                    t.pop('department_id', None)
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Задача не найдена'}), 404
            created = False
        _save_data(d)
        core.log_action('tracker_task_save', None, name, {'id': task_id, 'created': created})
        return jsonify({'success': True, 'id': task_id, 'created': created})

    @app.route('/api/tracker/task/delete', methods=['POST'])
    def api_task_delete():
        body = request.get_json() or {}
        task_id = str(body.get('id', '')).strip()
        if not task_id:
            return jsonify({'success': False, 'error': 'Не указан id'}), 400
        d = _load_data()
        before = len(d['tasks'])
        d['tasks'] = [t for t in d['tasks'] if t.get('id') != task_id]
        deleted = before - len(d['tasks'])
        log_affected = sum(1 for l in d['log'] if l.get('task_id') == task_id)
        _save_data(d)
        return jsonify({'success': True, 'deleted': deleted, 'log_affected': log_affected})

    # ============================================================
    # ОТМЕТКИ
    # ============================================================
    @app.route('/api/tracker/log/save', methods=['POST'])
    def api_log_save():
        body = request.get_json() or {}
        log_id_raw = body.get('id')
        employee_id = str(body.get('employee_id', '')).strip()
        task_id = str(body.get('task_id', '')).strip()
        date_str = str(body.get('date', '')).strip()
        comment = str(body.get('comment', '')).strip()[:2000]
        status = str(body.get('status', 'in_progress')).strip()[:20]
        link = str(body.get('link', '')).strip()[:500]
        try:
            hours = float(body.get('hours', 0) or 0)
        except (ValueError, TypeError):
            hours = 0
        hours = max(0.0, min(24.0, hours))
        hours = round(hours * 4) / 4

        if not employee_id:
            return jsonify({'success': False, 'error': 'Выберите сотрудника'}), 400
        if not task_id:
            return jsonify({'success': False, 'error': 'Выберите задачу'}), 400
        if not _valid_date(date_str):
            return jsonify({'success': False, 'error': 'Некорректная дата'}), 400
        if status not in STATUS_LABELS:
            status = 'in_progress'
        d = _load_data()
        if not any(e.get('id') == employee_id for e in d['employees']):
            return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404
        if not any(t.get('id') == task_id for t in d['tasks']):
            return jsonify({'success': False, 'error': 'Задача не найдена'}), 404
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if log_id_raw:
            try:
                log_id = int(log_id_raw)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Некорректный id'}), 400
            found = False
            for l in d['log']:
                if l.get('id') == log_id:
                    l.update({
                        'employee_id': employee_id, 'task_id': task_id,
                        'date': date_str, 'hours': hours, 'comment': comment,
                        'status': status, 'link': link, 'updated_at': now,
                    })
                    found = True
                    break
            if not found:
                return jsonify({'success': False, 'error': 'Отметка не найдена'}), 404
            created = False
        else:
            new_id = int(d['meta'].get('next_log_id', 1))
            d['meta']['next_log_id'] = new_id + 1
            d['log'].append({
                'id': new_id, 'employee_id': employee_id, 'task_id': task_id,
                'date': date_str, 'hours': hours, 'comment': comment,
                'status': status, 'link': link, 'created_at': now,
            })
            created = True
        _save_data(d)
        return jsonify({'success': True, 'created': created})

    @app.route('/api/tracker/log/delete', methods=['POST'])
    def api_log_delete():
        body = request.get_json() or {}
        try:
            log_id = int(body.get('id'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Некорректный id'}), 400
        d = _load_data()
        before = len(d['log'])
        d['log'] = [l for l in d['log'] if l.get('id') != log_id]
        _save_data(d)
        return jsonify({'success': True, 'deleted': before - len(d['log'])})

    @app.route('/api/tracker/log/copy_day', methods=['POST'])
    def api_log_copy_day():
        body = request.get_json() or {}
        src = str(body.get('source', '')).strip()
        dst = str(body.get('target', '')).strip()
        emp_filter = str(body.get('employee', '')).strip()
        if not _valid_date(src) or not _valid_date(dst):
            return jsonify({'success': False, 'error': 'Некорректные даты'}), 400
        if src == dst:
            return jsonify({'success': False, 'error': 'Даты совпадают'}), 400
        d = _load_data()
        copied = 0
        for l in d['log']:
            if l.get('date') != src:
                continue
            if emp_filter and l.get('employee_id') != emp_filter:
                continue
            new_id = int(d['meta'].get('next_log_id', 1))
            d['meta']['next_log_id'] = new_id + 1
            d['log'].append({
                'id': new_id, 'employee_id': l.get('employee_id'),
                'task_id': l.get('task_id'), 'date': dst,
                'hours': l.get('hours', 0), 'comment': l.get('comment', ''),
                'status': l.get('status', 'in_progress'), 'link': l.get('link', ''),
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'copied_from': l.get('id'),
            })
            copied += 1
        _save_data(d)
        return jsonify({'success': True, 'copied': copied})

    @app.route('/api/tracker/log/clear_day', methods=['POST'])
    def api_log_clear_day():
        body = request.get_json() or {}
        dk = str(body.get('date', '')).strip()
        emp_filter = str(body.get('employee', '')).strip()
        if not _valid_date(dk):
            return jsonify({'success': False, 'error': 'Некорректная дата'}), 400
        d = _load_data()
        before = len(d['log'])
        d['log'] = [
            l for l in d['log']
            if not (l.get('date') == dk and (not emp_filter or l.get('employee_id') == emp_filter))
        ]
        deleted = before - len(d['log'])
        _save_data(d)
        return jsonify({'success': True, 'deleted': deleted})

    # ============================================================
    # КАЛЕНДАРЬ
    # ============================================================
    @app.route('/api/tracker/calendar', methods=['GET'])
    def api_calendar():
        ym = request.args.get('ym', '').strip()
        emp_filter = request.args.get('employee', '').strip()
        dept_filter = request.args.get('department', '').strip()
        y, m = _parse_ym(ym)
        first_day = date(y, m, 1)
        last_day = date(y, m, monthrange(y, m)[1])
        start = first_day - timedelta(days=first_day.weekday())
        end = last_day + timedelta(days=(6 - last_day.weekday()))
        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        today = date.today().strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        employees_list = d['employees']
        if dept_filter:
            employees_list = [e for e in employees_list if e.get('department_id') == dept_filter]
        if emp_filter:
            employees_list = [e for e in employees_list if e['id'] == emp_filter]
        allowed_ids = {e['id'] for e in employees_list}

        days = {}
        cur = start
        while cur <= end:
            dk = cur.strftime('%Y-%m-%d')
            vacation_emps = [e['id'] for e in employees_list if _in_vacation(e, dk)]
            is_holiday = dk in holidays_map
            is_weekend = cur.weekday() >= 5
            days[dk] = {
                'date': dk, 'in_month': (cur.month == m and cur.year == y),
                'weekday': cur.weekday(),
                'is_workday': (cur.weekday() in WORK_WEEKDAYS) and not is_holiday,
                'is_weekend': is_weekend,
                'is_holiday': bool(is_holiday),
                'holiday_name': holidays_map.get(dk, ''),
                'entries': [], 'total_hours': 0.0,
                'employees': [], 'missing': [],
                'vacation': vacation_emps, 'overdue_tasks': [],
            }
            cur += timedelta(days=1)

        for l in d['log']:
            ldate = l.get('date', '')
            if ldate not in days:
                continue
            if l.get('employee_id') not in allowed_ids:
                continue
            emp = em.get(l.get('employee_id')) or {'id': l.get('employee_id'), 'name': '— удалён —', 'color': '#888888'}
            task = tm.get(l.get('task_id')) or {'id': l.get('task_id'), 'name': '— удалена —', 'icon': '❓'}
            entry = {
                'id': l.get('id'),
                'employee_id': emp['id'],
                'employee_name': emp.get('name', ''),
                'employee_color': emp.get('color', '#888888'),
                'employee_department': emp.get('department', ''),
                'task_id': task['id'],
                'task_name': task.get('name', ''),
                'task_icon': task.get('icon', '📋'),
                'task_start_date': task.get('start_date', ''),
                'task_deadline': task.get('deadline', ''),
                'task_created_at': task.get('created_at', ''),
                'hours': float(l.get('hours', 0) or 0),
                'comment': l.get('comment', ''),
                'status': l.get('status', 'done'),
                'status_label': STATUS_LABELS.get(l.get('status', 'done'), ''),
                'link': l.get('link', ''),
                'overdue': _is_overdue(task, today),
            }
            days[ldate]['entries'].append(entry)
            days[ldate]['total_hours'] += entry['hours']
            if emp['id'] not in days[ldate]['employees']:
                days[ldate]['employees'].append(emp['id'])

        for t in d['tasks']:
            if not _is_overdue(t, today):
                continue
            dl = t.get('deadline', '')
            if dl in days:
                days[dl]['overdue_tasks'].append({
                    'id': t['id'], 'name': t.get('name', ''),
                    'icon': t.get('icon', '📋'),
                })

        for dk, day in days.items():
            if not day['is_workday'] or dk > today:
                continue
            for e in employees_list:
                if e['id'] in day['employees']:
                    continue
                if _in_vacation(e, dk):
                    continue
                day['missing'].append({
                    'id': e['id'], 'name': e.get('name', ''),
                    'color': e.get('color', '#888888'),
                    'department': e.get('department', ''),
                })

        for dk in days:
            days[dk]['entries'].sort(key=lambda x: -x['hours'])
            days[dk]['total_hours'] = round(days[dk]['total_hours'] * 4) / 4

        return jsonify({
            'success': True, 'year': y, 'month': m,
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d'),
            'days': list(days.values()),
            'employees': d['employees'],
            'holidays': holidays_map,
        })

    # ============================================================
    # КАРТОЧКА СОТРУДНИКА ЗА ДЕНЬ
    # ============================================================
    @app.route('/api/tracker/employee/day', methods=['GET'])
    def api_employee_day():
        emp_id = request.args.get('employee', '').strip()
        dk = request.args.get('date', '').strip()
        if not emp_id or not _valid_date(dk):
            return jsonify({'success': False, 'error': 'Нужны employee и date'}), 400
        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        emp = em.get(emp_id)
        if not emp:
            return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404
        today = date.today().strftime('%Y-%m-%d')
        entries = []
        total = 0.0
        for l in d['log']:
            if l.get('employee_id') != emp_id or l.get('date') != dk:
                continue
            task = tm.get(l.get('task_id')) or {'id': l.get('task_id'), 'name': '— удалена —', 'icon': '❓'}
            entries.append({
                'id': l.get('id'),
                'task_id': task['id'],
                'task_name': task.get('name', ''),
                'task_icon': task.get('icon', '📋'),
                'task_start_date': task.get('start_date', ''),
                'task_deadline': task.get('deadline', ''),
                'hours': float(l.get('hours', 0) or 0),
                'comment': l.get('comment', ''),
                'status': l.get('status', 'done'),
                'status_label': STATUS_LABELS.get(l.get('status', 'done'), ''),
                'link': l.get('link', ''),
                'overdue': _is_overdue(task, today),
            })
            total += float(l.get('hours', 0) or 0)
        entries.sort(key=lambda x: -x['hours'])
        return jsonify({
            'success': True,
            'employee': {
                'id': emp['id'], 'name': emp.get('name', ''),
                'color': emp.get('color', '#888888'),
                'role': emp.get('role', ''),
                'department': emp.get('department', ''),
            },
            'date': dk,
            'entries': entries,
            'total_hours': round(total * 4) / 4,
            'in_vacation': _in_vacation(emp, dk),
            'is_workday': datetime.strptime(dk, '%Y-%m-%d').weekday() in WORK_WEEKDAYS,
        })

    # ============================================================
    # СВОД (компактный / подробный)
    # ============================================================
    @app.route('/api/tracker/summary', methods=['GET'])
    def api_summary():
        date_from = request.args.get('from', '').strip()
        date_to = request.args.get('to', '').strip()
        emp_filter = request.args.get('employee', '').strip()
        task_filter = request.args.get('task', '').strip()
        dept_filter = request.args.get('department', '').strip()
        view = request.args.get('view', 'compact').strip().lower()
        if view not in ('compact', 'full'):
            view = 'compact'
        if not _valid_date(date_from):
            t = date.today()
            date_from = t.replace(day=1).strftime('%Y-%m-%d')
        if not _valid_date(date_to):
            date_to = date.today().strftime('%Y-%m-%d')
        df = datetime.strptime(date_from, '%Y-%m-%d').date()
        dt_ = datetime.strptime(date_to, '%Y-%m-%d').date()
        if df > dt_:
            df, dt_ = dt_, df

        all_days = []
        cur = df
        while cur <= dt_:
            all_days.append(cur.strftime('%Y-%m-%d'))
            cur += timedelta(days=1)

        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        today = date.today().strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        dept_emp_ids = None
        if dept_filter:
            dept_emp_ids = {e['id'] for e in d['employees'] if e.get('department_id') == dept_filter}

        matrix = {}
        for l in d['log']:
            ldate = l.get('date', '')
            if ldate < date_from or ldate > date_to:
                continue
            if emp_filter and l.get('employee_id') != emp_filter:
                continue
            if dept_emp_ids is not None and l.get('employee_id') not in dept_emp_ids:
                continue
            if task_filter and l.get('task_id') != task_filter:
                continue
            eid = l.get('employee_id')
            tid = l.get('task_id')
            matrix.setdefault(eid, {}).setdefault(ldate, {}).setdefault(tid, []).append(l)

        # Пары (eid, tid) из назначений, отфильтрованные по периоду/просрочке
        assigned = set()
        for t in d['tasks']:
            if task_filter and t['id'] != task_filter:
                continue
            if dept_filter:
                if not _task_matches_dept(t, dept_filter, dept_emp_ids or set()):
                    continue
            # Фильтр по периоду / просрочке
            if not _task_in_period(t, date_from, date_to, today):
                continue
            for eid in t.get('assignees', []):
                if emp_filter and eid != emp_filter:
                    continue
                if dept_emp_ids is not None and eid not in dept_emp_ids:
                    continue
                assigned.add((eid, t['id']))

        # Также принудительно добавляем задачи, у которых есть отметки за период — они всегда в своде
        all_pairs = set(matrix_pairs := set()) | assigned
        for eid, by_date in matrix.items():
            for dk, by_task in by_date.items():
                for tid in by_task.keys():
                    all_pairs.add((eid, tid))

        by_emp = {}
        for (eid, tid) in all_pairs:
            by_emp.setdefault(eid, set()).add(tid)

        rows = []
        for eid, tids in by_emp.items():
            emp = em.get(eid) or {'id': eid, 'name': '— удалён —', 'color': '#888888'}
            cells = {}
            total = 0.0
            for tid in sorted(tids):
                task = tm.get(tid) or {'id': tid, 'name': '— удалена —', 'icon': '❓'}
                by_date = matrix.get(eid, {})
                for dk in all_days:
                    entries = by_date.get(dk, {}).get(tid, [])
                    if not entries:
                        continue
                    h = sum(float(e.get('hours', 0) or 0) for e in entries)
                    cell = cells.setdefault(dk, {'date': dk, 'hours': 0.0, 'tasks': []})
                    cell['hours'] += h
                    cell['tasks'].append({
                        'task_id': tid,
                        'task_name': task.get('name', ''),
                        'task_icon': task.get('icon', '📋'),
                        'task_status': task.get('status', 'active'),
                        'deadline': task.get('deadline', ''),
                        'overdue': _is_overdue(task, today),
                        'hours': round(h * 4) / 4,
                        'entries': [{
                            'id': e.get('id'),
                            'comment': e.get('comment', ''),
                            'status': e.get('status', 'done'),
                            'status_label': STATUS_LABELS.get(e.get('status', 'done'), ''),
                            'link': e.get('link', ''),
                            'hours': float(e.get('hours', 0) or 0),
                        } for e in entries],
                    })
                    total += h
            for dk in cells:
                cells[dk]['hours'] = round(cells[dk]['hours'] * 4) / 4
                cells[dk]['tasks'].sort(key=lambda x: -x['hours'])
            rows.append({
                'employee_id': eid,
                'employee_name': emp.get('name', ''),
                'employee_color': emp.get('color', '#888888'),
                'employee_department': emp.get('department', ''),
                'cells': cells,
                'total_hours': round(total * 4) / 4,
            })
        rows.sort(key=lambda r: r['employee_name'].lower())

        day_totals = {dk: 0.0 for dk in all_days}
        for r in rows:
            for dk, cell in r['cells'].items():
                if dk in day_totals:
                    day_totals[dk] += cell['hours']
        for dk in day_totals:
            day_totals[dk] = round(day_totals[dk] * 4) / 4
        grand_total = round(sum(day_totals.values()) * 4) / 4

        task_agg = {}
        for r in rows:
            for dk, cell in r['cells'].items():
                for t in cell['tasks']:
                    tid = t['task_id']
                    if tid not in task_agg:
                        task_agg[tid] = {
                            'task_id': tid, 'task_name': t['task_name'],
                            'task_icon': t['task_icon'], 'hours': 0.0, 'count': 0,
                        }
                    task_agg[tid]['hours'] += t['hours']
                    task_agg[tid]['count'] += len(t['entries'])
        top_tasks = sorted(task_agg.values(), key=lambda x: -x['hours'])[:10]
        for t in top_tasks:
            t['hours'] = round(t['hours'] * 4) / 4

        vacations_in_period = []
        for e in d['employees']:
            if dept_emp_ids is not None and e['id'] not in dept_emp_ids:
                continue
            for v in e.get('vacations', []) or []:
                vf, vt = v.get('from', ''), v.get('to', '')
                if vt < date_from or vf > date_to:
                    continue
                vacations_in_period.append({
                    'employee_id': e['id'],
                    'employee_name': e.get('name', ''),
                    'employee_color': e.get('color', '#888888'),
                    'from': vf, 'to': vt,
                    'comment': v.get('comment', ''),
                })

        day_meta = _build_day_meta(all_days, holidays_map, today)

        return jsonify({
            'success': True, 'from': date_from, 'to': date_to, 'view': view,
            'days': all_days, 'rows': rows,
            'day_totals': day_totals, 'grand_total': grand_total,
            'top_tasks': top_tasks, 'vacations': vacations_in_period,
            'day_meta': day_meta,
        })

    # ============================================================
    # SUMMARY GRID
    # ============================================================
    @app.route('/api/tracker/summary_grid', methods=['GET'])
    def api_summary_grid():
        date_from = request.args.get('from', '').strip()
        date_to = request.args.get('to', '').strip()
        emp_filter = request.args.get('employee', '').strip()
        task_filter = request.args.get('task', '').strip()
        dept_filter = request.args.get('department', '').strip()
        if not _valid_date(date_from):
            t = date.today()
            date_from = t.replace(day=1).strftime('%Y-%m-%d')
        if not _valid_date(date_to):
            date_to = date.today().strftime('%Y-%m-%d')
        df = datetime.strptime(date_from, '%Y-%m-%d').date()
        dt_ = datetime.strptime(date_to, '%Y-%m-%d').date()
        if df > dt_:
            df, dt_ = dt_, df
        all_days = []
        cur = df
        while cur <= dt_:
            all_days.append(cur.strftime('%Y-%m-%d'))
            cur += timedelta(days=1)

        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        today = date.today().strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        dept_emp_ids = None
        if dept_filter:
            dept_emp_ids = {e['id'] for e in d['employees'] if e.get('department_id') == dept_filter}

        # Пары из отметок за период
        pairs = {}
        for l in d['log']:
            ldate = l.get('date', '')
            if ldate < date_from or ldate > date_to:
                continue
            eid = l.get('employee_id')
            tid = l.get('task_id')
            if emp_filter and eid != emp_filter:
                continue
            if dept_emp_ids is not None and eid not in dept_emp_ids:
                continue
            if task_filter and tid != task_filter:
                continue
            pairs.setdefault((eid, tid), {}).setdefault(ldate, []).append(l)

        # Пары из назначений, отфильтрованные по периоду/просрочке
        assigned = set()
        for t in d['tasks']:
            if task_filter and t['id'] != task_filter:
                continue
            if dept_filter:
                if not _task_matches_dept(t, dept_filter, dept_emp_ids or set()):
                    continue
            # Ключевой фильтр
            if not _task_in_period(t, date_from, date_to, today):
                continue
            for eid in t.get('assignees', []):
                if emp_filter and eid != emp_filter:
                    continue
                if dept_emp_ids is not None and eid not in dept_emp_ids:
                    continue
                assigned.add((eid, t['id']))

        # Если по задаче есть отметки за период — она уже в pairs. Объединяем.
        # Просроченные задачи без отметок и без назначения на этого сотрудника — не показываем.
        all_pairs = set(pairs.keys()) | assigned
        by_emp = {}
        for (eid, tid) in all_pairs:
            by_emp.setdefault(eid, set()).add(tid)

        priority = {'done': 4, 'in_progress': 3, 'blocked': 2, 'planned': 1}
        rows = []
        for eid, tids in by_emp.items():
            emp = em.get(eid) or {'id': eid, 'name': '— удалён —', 'color': '#888888'}
            task_rows = []
            emp_total = 0.0
            for tid in sorted(tids):
                task = tm.get(tid) or {'id': tid, 'name': '— удалена —', 'icon': '❓'}
                cells = {}
                task_total = 0.0
                day_entries = pairs.get((eid, tid), {})
                for dk in all_days:
                    entries = day_entries.get(dk, [])
                    if not entries:
                        continue
                    h = sum(float(e.get('hours', 0) or 0) for e in entries)
                    statuses = [e.get('status', 'done') for e in entries]
                    dom = max(statuses, key=lambda s: priority.get(s, 0))
                    cells[dk] = {
                        'hours': round(h * 4) / 4,
                        'status': dom,
                        'status_label': STATUS_LABELS.get(dom, ''),
                        'entries': [{
                            'id': e.get('id'),
                            'comment': e.get('comment', ''),
                            'status': e.get('status', 'done'),
                            'status_label': STATUS_LABELS.get(e.get('status', 'done'), ''),
                            'link': e.get('link', ''),
                            'hours': float(e.get('hours', 0) or 0),
                        } for e in entries],
                    }
                    task_total += h
                task_rows.append({
                    'task_id': tid, 'task_name': task.get('name', ''),
                    'task_icon': task.get('icon', '📋'),
                    'task_status': task.get('status', 'active'),
                    'start_date': task.get('start_date', ''),
                    'deadline': task.get('deadline', ''),
                    'overdue': _is_overdue(task, today),
                    'cells': cells,
                    'total_hours': round(task_total * 4) / 4,
                })
            task_rows.sort(key=lambda x: (-x['total_hours'], x['task_name'].lower()))
            emp_total = sum(t['total_hours'] for t in task_rows)
            rows.append({
                'employee_id': eid,
                'employee_name': emp.get('name', ''),
                'employee_color': emp.get('color', '#888888'),
                'employee_department': emp.get('department', ''),
                'tasks': task_rows,
                'total_hours': round(emp_total * 4) / 4,
            })
        rows.sort(key=lambda r: r['employee_name'].lower())

        vacations_days = {}
        for e in d['employees']:
            if dept_emp_ids is not None and e['id'] not in dept_emp_ids:
                continue
            for v in e.get('vacations', []) or []:
                vf, vt = v.get('from', ''), v.get('to', '')
                if not vf or not vt:
                    continue
                s = max(vf, date_from)
                ee = min(vt, date_to)
                if s > ee:
                    continue
                cur_v = datetime.strptime(s, '%Y-%m-%d').date()
                end_v = datetime.strptime(ee, '%Y-%m-%d').date()
                while cur_v <= end_v:
                    vacations_days.setdefault(e['id'], set()).add(cur_v.strftime('%Y-%m-%d'))
                    cur_v += timedelta(days=1)
        for r in rows:
            r['vacation_days'] = sorted(vacations_days.get(r['employee_id'], set()))

        day_totals = {dk: 0.0 for dk in all_days}
        for r in rows:
            for t in r['tasks']:
                for dk, c in t['cells'].items():
                    if dk in day_totals:
                        day_totals[dk] += c['hours']
        for dk in day_totals:
            day_totals[dk] = round(day_totals[dk] * 4) / 4
        grand_total = round(sum(day_totals.values()) * 4) / 4

        task_agg = {}
        for r in rows:
            for t in r['tasks']:
                tid = t['task_id']
                if tid not in task_agg:
                    task_agg[tid] = {
                        'task_id': tid, 'task_name': t['task_name'],
                        'task_icon': t['task_icon'], 'hours': 0.0, 'count': 0,
                    }
                task_agg[tid]['hours'] += t['total_hours']
                for dk, c in t['cells'].items():
                    task_agg[tid]['count'] += len(c['entries'])
        top_tasks = sorted(task_agg.values(), key=lambda x: -x['hours'])[:10]
        for t in top_tasks:
            t['hours'] = round(t['hours'] * 4) / 4

        vacations_in_period = []
        for e in d['employees']:
            if dept_emp_ids is not None and e['id'] not in dept_emp_ids:
                continue
            for v in e.get('vacations', []) or []:
                vf, vt = v.get('from', ''), v.get('to', '')
                if vt < date_from or vf > date_to:
                    continue
                vacations_in_period.append({
                    'employee_id': e['id'],
                    'employee_name': e.get('name', ''),
                    'employee_color': e.get('color', '#888888'),
                    'from': vf, 'to': vt,
                    'comment': v.get('comment', ''),
                })

        day_meta = _build_day_meta(all_days, holidays_map, today)

        return jsonify({
            'success': True, 'from': date_from, 'to': date_to,
            'days': all_days, 'rows': rows,
            'day_totals': day_totals, 'grand_total': grand_total,
            'top_tasks': top_tasks, 'vacations': vacations_in_period,
            'day_meta': day_meta,
        })

    # ============================================================
    # КАРТОЧКА СОТРУДНИКА
    # ============================================================
    @app.route('/api/tracker/employee/card', methods=['GET'])
    def api_employee_card():
        emp_id = request.args.get('employee', '').strip()
        if not emp_id:
            return jsonify({'success': False, 'error': 'Нужен employee'}), 400
        from_s, to_s = _resolve_range(request.args)
        df = datetime.strptime(from_s, '%Y-%m-%d').date()
        dt_ = datetime.strptime(to_s, '%Y-%m-%d').date()
        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        emp = em.get(emp_id)
        if not emp:
            return jsonify({'success': False, 'error': 'Сотрудник не найден'}), 404
        today_d = date.today()
        today = today_d.strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        # Задачи, релевантные для показа (пересечение или просрочка)
        relevant_tids = set()
        for t in d['tasks']:
            if emp_id not in t.get('assignees', []):
                # Сотрудник не назначен, но могут быть отметки — учтём ниже
                pass
            if _task_in_period(t, from_s, to_s, today):
                if emp_id in t.get('assignees', []):
                    relevant_tids.add(t['id'])

        by_date = {}
        by_task = {}
        for l in d['log']:
            if l.get('employee_id') != emp_id:
                continue
            ldate = l.get('date', '')
            if not ldate or ldate < from_s or ldate > to_s:
                continue
            h = float(l.get('hours', 0) or 0)
            by_date[ldate] = by_date.get(ldate, 0.0) + h
            tid = l.get('task_id')
            by_task.setdefault(tid, {})[ldate] = by_task.get(tid, {}).get(ldate, 0.0) + h
            relevant_tids.add(tid)

        all_day_cells = []
        max_h = 0.0
        total_hours = 0.0
        cur = df
        while cur <= dt_:
            dk = cur.strftime('%Y-%m-%d')
            wd = cur.weekday()
            is_weekend = wd >= 5
            is_holiday = dk in holidays_map
            is_workday = (wd in WORK_WEEKDAYS) and not is_holiday
            is_vac = _in_vacation(emp, dk)
            h = round(by_date.get(dk, 0.0) * 4) / 4
            if h > max_h:
                max_h = h
            total_hours += h
            missing = (is_workday and not is_vac and dk <= today and h == 0)
            all_day_cells.append({
                'date': dk, 'hours': h,
                'is_workday': is_workday, 'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'holiday_name': holidays_map.get(dk, ''),
                'is_vacation': is_vac,
                'missing': missing, 'is_today': dk == today,
            })
            cur += timedelta(days=1)

        tasks_out = []
        for tid in relevant_tids:
            task = tm.get(tid) or {'id': tid, 'name': '— удалена —', 'icon': '❓'}
            task_start = task.get('start_date') or ''
            task_deadline = task.get('deadline') or ''
            cells_raw = by_task.get(tid, {})

            all_logs_for_task_emp = [
                l for l in d['log']
                if l.get('employee_id') == emp_id and l.get('task_id') == tid
            ]
            active_days, possible_days, coverage = _calc_coverage(
                task, emp, all_logs_for_task_emp, today_d
            )

            # Для отображения — обрезаем по периоду запроса
            ts, te = None, None
            if task_start and _valid_date(task_start):
                try: ts = datetime.strptime(task_start, '%Y-%m-%d').date()
                except Exception: ts = None
            if ts is None:
                ts = df
            if task_deadline and _valid_date(task_deadline):
                try: te = datetime.strptime(task_deadline, '%Y-%m-%d').date()
                except Exception: te = None
            if te is None:
                te = today_d
            # Просроченные тянутся до today
            if task_deadline and _valid_date(task_deadline) and task_deadline < today and task.get('status') not in ('done', 'archived'):
                te = today_d
            ts_show = max(ts, df)
            te_show = min(te, dt_)
            if ts_show > te_show:
                ts_show, te_show = df, dt_
            task_cells = []
            cur = ts_show
            while cur <= te_show:
                dk = cur.strftime('%Y-%m-%d')
                h = round(cells_raw.get(dk, 0.0) * 4) / 4
                wd = cur.weekday()
                is_weekend = wd >= 5
                is_holiday = dk in holidays_map
                task_cells.append({
                    'date': dk, 'hours': h,
                    'is_workday': (wd in WORK_WEEKDAYS) and not is_holiday,
                    'is_weekend': is_weekend,
                    'is_holiday': is_holiday,
                    'is_today': dk == today,
                })
                cur += timedelta(days=1)

            task_total = sum(cells_raw.values())
            tasks_out.append({
                'task_id': tid,
                'task_name': task.get('name', ''),
                'task_icon': task.get('icon', '📋'),
                'overdue': _is_overdue(task, today),
                'start_date': task_start,
                'deadline': task_deadline,
                'status': task.get('status', 'active'),
                'total_hours': round(task_total * 4) / 4,
                'active_days': active_days,
                'possible_days': possible_days,
                'coverage': coverage,
                'cells': task_cells,
            })
        tasks_out.sort(key=lambda x: (-x['total_hours'], x['task_name'].lower()))

        return jsonify({
            'success': True, 'from': from_s, 'to': to_s,
            'employee': {
                'id': emp['id'], 'name': emp.get('name', ''),
                'color': emp.get('color', '#888888'),
                'role': emp.get('role', ''),
                'department': emp.get('department', ''),
            },
            'cells': all_day_cells, 'tasks': tasks_out,
            'total_hours': round(total_hours * 4) / 4,
            'max_hours': max_h,
        })

    # ============================================================
    # КАРТОЧКА ЗАДАЧИ
    # ============================================================
    @app.route('/api/tracker/task/card', methods=['GET'])
    def api_task_card():
        task_id = request.args.get('task', '').strip()
        emp_filter = request.args.get('employee', '').strip()
        if not task_id:
            return jsonify({'success': False, 'error': 'Нужен task'}), 400
        from_s, to_s = _resolve_range(request.args)
        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        task = tm.get(task_id)
        if not task:
            return jsonify({'success': False, 'error': 'Задача не найдена'}), 404
        today_d = date.today()
        today = today_d.strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        task_start = task.get('start_date') or from_s
        task_deadline = task.get('deadline') or to_s
        try:
            ts = datetime.strptime(task_start, '%Y-%m-%d').date() if _valid_date(task_start) else datetime.strptime(from_s, '%Y-%m-%d').date()
        except Exception:
            ts = datetime.strptime(from_s, '%Y-%m-%d').date()
        try:
            te = datetime.strptime(task_deadline, '%Y-%m-%d').date() if _valid_date(task_deadline) else datetime.strptime(to_s, '%Y-%m-%d').date()
        except Exception:
            te = datetime.strptime(to_s, '%Y-%m-%d').date()
        # Просроченная — тянем до today
        if task_deadline and _valid_date(task_deadline) and task_deadline < today and task.get('status') not in ('done', 'archived'):
            te = today_d
        df = datetime.strptime(from_s, '%Y-%m-%d').date()
        dt_ = datetime.strptime(to_s, '%Y-%m-%d').date()
        ts_show = max(ts, df)
        te_show = min(te, dt_)
        if ts_show > te_show:
            ts_show, te_show = df, dt_

        matrix = {}
        total_hours = 0.0
        for l in d['log']:
            if l.get('task_id') != task_id:
                continue
            if emp_filter and l.get('employee_id') != emp_filter:
                continue
            ldate = l.get('date', '')
            if not ldate or ldate < from_s or ldate > to_s:
                continue
            eid = l.get('employee_id')
            h = float(l.get('hours', 0) or 0)
            matrix.setdefault(eid, {})
            matrix[eid][ldate] = matrix[eid].get(ldate, 0.0) + h
            total_hours += h

        combined = {}
        for eid, cells_raw in matrix.items():
            for dk, h in cells_raw.items():
                combined[dk] = combined.get(dk, 0.0) + h

        combined_cells = []
        max_h = 0.0
        cur = ts_show
        while cur <= te_show:
            dk = cur.strftime('%Y-%m-%d')
            h = round(combined.get(dk, 0.0) * 4) / 4
            if h > max_h:
                max_h = h
            wd = cur.weekday()
            is_weekend = wd >= 5
            is_holiday = dk in holidays_map
            combined_cells.append({
                'date': dk, 'hours': h,
                'is_workday': (wd in WORK_WEEKDAYS) and not is_holiday,
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'is_today': dk == today,
            })
            cur += timedelta(days=1)

        rows = []
        for eid, cells_raw in matrix.items():
            emp = em.get(eid) or {'id': eid, 'name': '— удалён —', 'color': '#888888'}
            total = sum(cells_raw.values())
            active_days = len([1 for h in cells_raw.values() if h > 0])
            rows.append({
                'employee_id': eid,
                'employee_name': emp.get('name', ''),
                'employee_color': emp.get('color', '#888888'),
                'employee_department': emp.get('department', ''),
                'total_hours': round(total * 4) / 4,
                'active_days': active_days,
            })
        rows.sort(key=lambda x: -x['total_hours'])

        all_logs_for_task = [l for l in d['log'] if l.get('task_id') == task_id]
        active_days_all, possible_days, coverage = _calc_coverage(task, None, all_logs_for_task, today_d)

        return jsonify({
            'success': True, 'from': from_s, 'to': to_s,
            'task': {
                'id': task['id'], 'name': task.get('name', ''),
                'icon': task.get('icon', '📋'),
                'status': task.get('status', 'active'),
                'start_date': task.get('start_date', ''),
                'deadline': task.get('deadline', ''),
                'overdue': _is_overdue(task, today),
                'description': task.get('description', ''),
            },
            'cells': combined_cells, 'max_hours': max_h,
            'employees': rows,
            'total_hours': round(total_hours * 4) / 4,
            'active_days': active_days_all,
            'possible_days': possible_days,
            'coverage': coverage,
        })

    # ============================================================
    # СТАТИСТИКА
    # ============================================================
    @app.route('/api/tracker/stats', methods=['GET'])
    def api_stats():
        date_from = request.args.get('from', '').strip()
        date_to = request.args.get('to', '').strip()
        emp_filter = request.args.get('employee', '').strip()
        dept_filter = request.args.get('department', '').strip()
        if not _valid_date(date_from):
            t = date.today()
            date_from = t.replace(day=1).strftime('%Y-%m-%d')
        if not _valid_date(date_to):
            date_to = date.today().strftime('%Y-%m-%d')
        df = datetime.strptime(date_from, '%Y-%m-%d').date()
        dt_ = datetime.strptime(date_to, '%Y-%m-%d').date()
        if df > dt_:
            df, dt_ = dt_, df

        d = _load_data()
        em = _emp_map(d)
        tm = _task_map(d)
        today = date.today().strftime('%Y-%m-%d')

        emp_ids = set()
        for e in d['employees']:
            if emp_filter and e['id'] != emp_filter:
                continue
            if dept_filter and e.get('department_id', '') != dept_filter:
                continue
            emp_ids.add(e['id'])

        dept_emp_ids = None
        if dept_filter:
            dept_emp_ids = {e['id'] for e in d['employees'] if e.get('department_id') == dept_filter}

        logs_period = [
            l for l in d['log']
            if date_from <= l.get('date', '') <= date_to
            and l.get('employee_id') in emp_ids
        ]
        hours_by_emp = {}
        for l in logs_period:
            eid = l.get('employee_id')
            hours_by_emp[eid] = hours_by_emp.get(eid, 0.0) + float(l.get('hours', 0) or 0)

        by_employee = []
        for e in d['employees']:
            if e['id'] not in emp_ids:
                continue
            eid = e['id']
            task_ids_assigned = {t['id'] for t in d['tasks'] if eid in t.get('assignees', [])}
            task_ids_logs = {l.get('task_id') for l in logs_period if l.get('employee_id') == eid}
            task_ids = task_ids_assigned | task_ids_logs
            tasks_relevant = [tm[tid] for tid in task_ids if tid in tm]
            assigned = tasks_relevant
            done_cnt = sum(1 for t in assigned if t.get('status') == 'done')
            active_cnt = sum(1 for t in assigned if t.get('status') == 'active')
            overdue_cnt = sum(1 for t in assigned if _is_overdue(t, today))
            done_logs_tasks = set()
            inprog_logs_tasks = set()
            early_done = set()
            for l in logs_period:
                if l.get('employee_id') != eid:
                    continue
                tid = l.get('task_id')
                st = l.get('status', 'done')
                if st == 'done':
                    done_logs_tasks.add(tid)
                elif st == 'in_progress':
                    inprog_logs_tasks.add(tid)
                task = tm.get(tid)
                if st == 'done' and task and task.get('deadline') and l.get('date', '') <= task['deadline']:
                    early_done.add(tid)
            vac_days = 0
            for v in e.get('vacations', []) or []:
                vf, vt = v.get('from', ''), v.get('to', '')
                if not vf or not vt:
                    continue
                s = max(vf, date_from)
                ee = min(vt, date_to)
                if s <= ee:
                    vac_days += (datetime.strptime(ee, '%Y-%m-%d') - datetime.strptime(s, '%Y-%m-%d')).days + 1
            by_employee.append({
                'employee_id': eid,
                'employee_name': e.get('name', ''),
                'employee_color': e.get('color', '#888888'),
                'employee_department': e.get('department', ''),
                'hours': round(hours_by_emp.get(eid, 0.0) * 4) / 4,
                'total_tasks': len(assigned),
                'done_tasks': done_cnt,
                'active_tasks': active_cnt,
                'overdue_tasks': overdue_cnt,
                'worked_done': len(done_logs_tasks),
                'worked_in_progress': len(inprog_logs_tasks),
                'early_done': len(early_done),
                'vacation_days': vac_days,
            })
        by_employee.sort(key=lambda r: r['employee_name'].lower())

        by_task = []
        for t in d['tasks']:
            tid = t['id']
            assigned_to_filtered = [a for a in t.get('assignees', []) if a in emp_ids]
            logs_for_task = [l for l in logs_period if l.get('task_id') == tid]
            if dept_filter and dept_emp_ids is not None:
                if not _task_matches_dept(t, dept_filter, dept_emp_ids):
                    if not assigned_to_filtered and not logs_for_task:
                        continue
            if not assigned_to_filtered and not logs_for_task:
                continue
            workers = set(l['employee_id'] for l in logs_for_task)
            total_h = sum(float(l.get('hours', 0) or 0) for l in logs_for_task)
            any_done = any(l.get('status') == 'done' for l in logs_for_task)
            any_inprog = any(l.get('status') == 'in_progress' for l in logs_for_task)
            by_task.append({
                'task_id': tid, 'task_name': t.get('name', ''),
                'task_icon': t.get('icon', '📋'),
                'status': t.get('status', 'active'),
                'deadline': t.get('deadline', ''),
                'overdue': _is_overdue(t, today),
                'assigned_count': len(assigned_to_filtered),
                'workers_count': len(workers),
                'hours': round(total_h * 4) / 4,
                'any_done': any_done,
                'any_in_progress': any_inprog,
            })
        by_task.sort(key=lambda r: -r['hours'])

        overall = {
            'employees_count': len(by_employee),
            'tasks_total': sum(r['total_tasks'] for r in by_employee),
            'tasks_done': sum(r['done_tasks'] for r in by_employee),
            'tasks_active': sum(r['active_tasks'] for r in by_employee),
            'tasks_overdue': sum(r['overdue_tasks'] for r in by_employee),
            'early_done': sum(r['early_done'] for r in by_employee),
            'hours_total': round(sum(r['hours'] for r in by_employee) * 4) / 4,
        }

        overdue_details = []
        for t in d['tasks']:
            if not _is_overdue(t, today):
                continue
            assigned_emps = [e for e in d['employees'] if e['id'] in t.get('assignees', [])]
            if dept_filter:
                assigned_emps = [e for e in assigned_emps if e.get('department_id') == dept_filter]
            if emp_filter:
                assigned_emps = [e for e in assigned_emps if e['id'] == emp_filter]
            if (emp_filter or dept_filter) and not assigned_emps:
                continue
            try:
                days_overdue = (date.today() - datetime.strptime(t.get('deadline', ''), '%Y-%m-%d').date()).days
            except Exception:
                days_overdue = 0
            overdue_details.append({
                'task_id': t['id'],
                'task_name': t.get('name', ''),
                'task_icon': t.get('icon', '📋'),
                'deadline': t.get('deadline', ''),
                'days_overdue': days_overdue,
                'status': t.get('status', 'active'),
                'assignees': [{
                    'id': e['id'], 'name': e.get('name', ''),
                    'color': e.get('color', '#888888'),
                } for e in assigned_emps],
            })
        overdue_details.sort(key=lambda x: -x['days_overdue'])

        return jsonify({
            'success': True, 'from': date_from, 'to': date_to,
            'by_employee': by_employee, 'by_task': by_task,
            'overall': overall, 'overdue_details': overdue_details,
        })

    # ============================================================
    # HEATMAP
    # ============================================================
    @app.route('/api/tracker/heatmap', methods=['GET'])
    def api_heatmap():
        dept_filter = request.args.get('department', '').strip()
        from_s, to_s = _resolve_range(request.args)
        df = datetime.strptime(from_s, '%Y-%m-%d').date()
        dt_ = datetime.strptime(to_s, '%Y-%m-%d').date()
        d = _load_data()
        em = _emp_map(d)
        today = date.today().strftime('%Y-%m-%d')
        holidays_map = d.get('holidays') or {}

        all_cells = []
        cur = df
        while cur <= dt_:
            all_cells.append(cur.strftime('%Y-%m-%d'))
            cur += timedelta(days=1)

        employees = d['employees']
        if dept_filter:
            employees = [e for e in employees if e.get('department_id') == dept_filter]

        matrix = {}
        for l in d['log']:
            ldate = l.get('date', '')
            if not ldate or ldate < from_s or ldate > to_s:
                continue
            eid = l.get('employee_id')
            if dept_filter:
                emp = em.get(eid)
                if not emp or emp.get('department_id') != dept_filter:
                    continue
            matrix.setdefault(eid, {})
            matrix[eid][ldate] = matrix[eid].get(ldate, 0.0) + float(l.get('hours', 0) or 0)

        rows = []
        max_h = 0.0
        for emp in employees:
            eid = emp['id']
            cells = []
            total = 0.0
            for dk in all_cells:
                try:
                    wd = datetime.strptime(dk, '%Y-%m-%d').weekday()
                except Exception:
                    wd = 0
                is_weekend = wd >= 5
                is_holiday = dk in holidays_map
                is_workday = (wd in WORK_WEEKDAYS) and not is_holiday
                is_vac = _in_vacation(emp, dk)
                h = round(matrix.get(eid, {}).get(dk, 0.0) * 4) / 4
                if h > max_h:
                    max_h = h
                total += h
                missing = (is_workday and not is_vac and dk <= today and h == 0)
                cells.append({
                    'date': dk, 'hours': h,
                    'is_workday': is_workday, 'is_vacation': is_vac,
                    'is_weekend': is_weekend, 'is_holiday': is_holiday,
                    'missing': missing, 'is_today': dk == today,
                })
            rows.append({
                'employee_id': eid,
                'employee_name': emp.get('name', ''),
                'employee_color': emp.get('color', '#888888'),
                'employee_department': emp.get('department', ''),
                'cells': cells,
                'total_hours': round(total * 4) / 4,
            })
        rows.sort(key=lambda r: r['employee_name'].lower())
        return jsonify({
            'success': True, 'from': from_s, 'to': to_s,
            'days': all_cells,
            'rows': rows,
            'max_hours': max_h,
        })

    # ============================================================
    # UI-слот
    # ============================================================
    hooks['ui_sidebar'].append({
        'id': 'openTaskTrackerBtn',
        'icon': '📅',
        'label': 'Трекер задач',
        'action': 'link',
        'url': '/tasks',
    })


# ============================================================
# ЗАГРУЗКА UI-МОДУЛЯ
# ============================================================
_UI_MODULE_CACHE = {'module': None}


def _render_tracker_html(csrf_token):
    import importlib.util
    if _UI_MODULE_CACHE['module'] is None:
        ui_path = Path(__file__).parent / 'task_tracker_ui.py'
        if not ui_path.exists():
            return (
                '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Ошибка</title>'
                '</head><body style="font-family:sans-serif;padding:20px;color:#e74c3c;">'
                '<h1>⚠️ Не найден файл task_tracker_ui.py</h1>'
                '<p>Ожидался путь: <code>' + str(ui_path) + '</code></p>'
                '</body></html>'
            )
        spec = importlib.util.spec_from_file_location('task_tracker_ui', str(ui_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _UI_MODULE_CACHE['module'] = mod
    return _UI_MODULE_CACHE['module'].render(csrf_token)

