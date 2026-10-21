"""Подробный лог событий реестра в plugin_events.log и .jsonl."""
import json
import threading
import shutil
from pathlib import Path
from datetime import datetime

__version__ = "2.0"
__description__ = "Подробный лог всех событий реестра (log + jsonl)"

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "plugin_events.log"
JSONL_FILE = BASE_DIR / "plugin_events.jsonl"
MAX_LOG_SIZE = 5 * 1024 * 1024
_LOCK = threading.Lock()


def _rotate_if_needed():
    try:
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            backup = LOG_FILE.with_suffix(LOG_FILE.suffix + '.1')
            if backup.exists():
                backup.unlink()
            shutil.move(str(LOG_FILE), str(backup))
        if JSONL_FILE.exists() and JSONL_FILE.stat().st_size > MAX_LOG_SIZE:
            backup = JSONL_FILE.with_suffix(JSONL_FILE.suffix + '.1')
            if backup.exists():
                backup.unlink()
            shutil.move(str(JSONL_FILE), str(backup))
    except Exception as e:
        print(f"[LOGGER] Ошибка ротации: {e}")


def _log(event, message, level='INFO', data=None):
    now = datetime.now()
    ts = now.strftime('%Y-%m-%d %H:%M:%S')
    ts_ms = now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    line = f"[{ts}] [{level:5}] {event:18} | {message}\n"
    obj = {'ts': ts_ms, 'level': level, 'event': event, 'message': message, 'data': data or {}}
    try:
        with _LOCK:
            _rotate_if_needed()
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(line)
            with open(JSONL_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"[LOGGER] Ошибка записи: {e}")


def _short(text, limit=80):
    if not text:
        return '—'
    text = str(text).replace('\n', ' ').strip()
    return text if len(text) <= limit else text[:limit - 1] + '…'


def on_startup():
    _log('STARTUP', 'Реестр запущен', data={'version': __version__})


def on_add(record_id, name, link, description, category, tags):
    _log('ADD', f'#{record_id} «{_short(name, 40)}» → {_short(link, 60)}', data={
        'id': record_id, 'name': name, 'link': link,
        'category': category or '', 'tags': tags or '',
        'desc_preview': _short(description, 120),
        'link_len': len(link) if link else 0,
    })


def on_edit(record_id, name, link, description, category, favorite, tags, changes):
    if changes:
        summary = ', '.join(changes.keys()); level = 'INFO'
    else:
        summary = 'без изменений'; level = 'DEBUG'
    details = {'id': record_id, 'name': name, 'fields': list((changes or {}).keys())}
    for field, diff in (changes or {}).items():
        details[f'{field}_from'] = _short(str(diff.get('from', '')), 80)
        details[f'{field}_to'] = _short(str(diff.get('to', '')), 80)
    _log('EDIT', f'#{record_id} «{_short(name, 40)}» — {summary}', level=level, data=details)


def on_delete(record_id, name, link, category):
    _log('DELETE', f'#{record_id} «{_short(name, 40)}» (в корзину)', level='WARN', data={
        'id': record_id, 'name': name, 'link': link, 'category': category or '',
    })


def on_hard_delete(record_id, name):
    _log('HARD-DELETE', f'#{record_id} «{_short(name, 40)}» — безвозвратно', level='WARN', data={
        'id': record_id, 'name': name,
    })


def on_restore(record_id, name):
    _log('RESTORE', f'#{record_id} «{_short(name, 40)}»', data={'id': record_id, 'name': name})


def on_move_to_group(record_id, from_group, to_group):
    _log('MOVE', f'#{record_id}: «{_short(from_group, 30)}» → «{_short(to_group, 30)}»', data={
        'id': record_id, 'from': from_group, 'to': to_group,
    })


def on_category_change(record_id, name, old_category, new_category):
    _log('CAT-CHANGE', f'#{record_id} «{_short(name, 40)}»: {old_category or "—"} → {new_category or "—"}', data={
        'id': record_id, 'name': name, 'old': old_category or '', 'new': new_category or '',
    })


def on_click(record_id, name, link, click_count):
    _log('CLICK', f'#{record_id} «{_short(name, 40)}» — всего: {click_count}', data={
        'id': record_id, 'name': name, 'link': link, 'count': click_count,
    })


def on_import(source, added, extra):
    _log('IMPORT', f'источник={source} добавлено={added}', data={
        'source': source, 'added': added, 'extra': extra or {},
    })


def on_bulk_delete(count, ids):
    _log('BULK-DELETE', f'{count} записей', level='WARN', data={'count': count, 'ids': list(ids)[:100]})


def on_bulk_move(count, category, ids):
    _log('BULK-MOVE', f'{count} записей → «{_short(category, 40)}»', data={
        'count': count, 'category': category, 'ids': list(ids)[:100],
    })


def on_status_check_start():
    _log('STATUS-CHECK', 'проверка ссылок запущена')


def on_status_check_end(results):
    total = len(results) if results else 0
    by_status = {}
    for st in (results or {}).values():
        s = st.get('status', 'unknown') if isinstance(st, dict) else 'unknown'
        by_status[s] = by_status.get(s, 0) + 1
    _log('STATUS-CHECK', f'проверка завершена, обработано {total}: {by_status}',
         data={'total': total, 'by_status': by_status})


def on_category_rename(old_name, new_name, count):
    _log('CAT-RENAME', f'«{old_name}» → «{new_name}» ({count} записей)', data={
        'old': old_name, 'new': new_name, 'count': count,
    })


def on_category_delete(category, count):
    _log('CAT-DELETE', f'«{category}» ({count} записей)', level='WARN', data={
        'category': category, 'count': count,
    })


def on_group_rename(old_name, new_name, count):
    _log('GROUP-RENAME', f'«{old_name}» → «{new_name}» ({count} записей)', data={
        'old': old_name, 'new': new_name, 'count': count,
    })


def register(hooks, app, config, core=None):
    hooks['on_startup'].append(on_startup)
    hooks['on_add'].append(on_add)
    hooks['on_edit'].append(on_edit)
    hooks['on_delete'].append(on_delete)
    hooks['on_hard_delete'].append(on_hard_delete)
    hooks['on_restore'].append(on_restore)
    hooks['on_move_to_group'].append(on_move_to_group)
    hooks['on_category_change'].append(on_category_change)
    hooks['on_click'].append(on_click)
    hooks['on_import'].append(on_import)
    hooks['on_bulk_delete'].append(on_bulk_delete)
    hooks['on_bulk_move'].append(on_bulk_move)
    hooks['on_status_check_start'].append(on_status_check_start)
    hooks['on_status_check_end'].append(on_status_check_end)
    hooks['on_category_rename'].append(on_category_rename)
    hooks['on_category_delete'].append(on_category_delete)
    hooks['on_group_rename'].append(on_group_rename)

    @app.route('/my-plugin/log-tail')
    def log_tail():
        from flask import jsonify, request
        try:
            n = int(request.args.get('lines', 100))
        except Exception:
            n = 100
        n = max(1, min(1000, n))
        try:
            if not LOG_FILE.exists():
                return jsonify({'lines': [], 'total': 0})
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-n:]
            return jsonify({'lines': lines, 'total': len(lines)})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/my-plugin/log-stats')
    def log_stats():
        from flask import jsonify
        counts = {}
        size = 0
        try:
            if JSONL_FILE.exists():
                size = JSONL_FILE.stat().st_size
                with open(JSONL_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            obj = json.loads(line)
                            ev = obj.get('event', '?')
                            counts[ev] = counts.get(ev, 0) + 1
                        except Exception:
                            pass
        except Exception:
            pass
        return jsonify({
            'counts': counts, 'total': sum(counts.values()), 'file_size': size,
            'log_file': str(LOG_FILE.name), 'jsonl_file': str(JSONL_FILE.name),
        })