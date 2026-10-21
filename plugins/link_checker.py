"""Проверка доступности ссылок через HTTP HEAD."""
import threading
from datetime import datetime
from pathlib import Path

__version__ = "1.0"
__description__ = "Проверка статуса ссылок (HEAD)"

try:
    import urllib.request as urlreq
    import urllib.error as urlerr
    HAS_URLLIB = True
except Exception:
    HAS_URLLIB = False

_status_lock = threading.Lock()
_check_running = False
_status_file = None


def _check_one(url):
    if not HAS_URLLIB or not url:
        return {'status': 'unknown', 'code': None}
    if not (url.startswith('http://') or url.startswith('https://')):
        return {'status': 'unknown', 'code': None}
    try:
        from urllib.parse import urlparse
        if not urlparse(url).netloc:
            return {'status': 'unknown', 'code': None}
    except Exception:
        return {'status': 'unknown', 'code': None}
    try:
        req = urlreq.Request(url, method='HEAD', headers={'User-Agent': 'ReestrBot/1.0'})
        with urlreq.urlopen(req, timeout=4) as resp:
            return {'status': 'ok', 'code': resp.status}
    except urlerr.HTTPError as e:
        if e.code in (401, 403):
            return {'status': 'warn', 'code': e.code}
        return {'status': 'error', 'code': e.code}
    except Exception:
        return {'status': 'timeout', 'code': None}


def _run_check(core):
    global _check_running
    with _status_lock:
        if _check_running:
            return False
        _check_running = True
    core.run_hook('on_status_check_start')
    try:
        wb = core.read_workbook(); ws = wb.active
        cache = core.load_json(_status_file, {})
        if not isinstance(cache, dict):
            cache = {}
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for row in ws.iter_rows(min_row=2, values_only=True):
            rid = core.safe_int(row[0], -1)
            if rid < 0:
                continue
            if core.safe_str(row[10]) if len(row) > 10 else '':
                continue
            link = core.safe_str(row[2])
            if not link:
                continue
            result = _check_one(link)
            cache[str(rid)] = {'status': result['status'], 'code': result['code'], 'ts': now}
        core.save_json(_status_file, cache)
        core.run_hook('on_status_check_end', results=dict(cache))
    finally:
        with _status_lock:
            _check_running = False
    return True


def register(hooks, app, config, core):
    from flask import jsonify, request
    global _status_file
    _status_file = str(Path(core.BASE_DIR) / 'status_cache.json')

    @app.route('/check_all_links', methods=['POST'])
    def check_all_links():
        if not HAS_URLLIB:
            return jsonify({'success': False, 'error': 'urllib недоступен'}), 500
        threading.Thread(target=_run_check, args=(core,), daemon=True).start()
        return jsonify({'success': True, 'message': 'Проверка запущена'})

    @app.route('/check_one_link/<int:rid>', methods=['POST'])
    def check_one_link(rid):
        rec = core.get_record_by_id(rid)
        if not rec:
            return jsonify({'success': False, 'error': 'Не найдена'}), 404
        result = _check_one(rec['link_del'])
        cache = core.load_json(_status_file, {})
        if not isinstance(cache, dict):
            cache = {}
        cache[str(rid)] = {'status': result['status'], 'code': result['code'],
                           'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        core.save_json(_status_file, cache)
        return jsonify({'success': True, 'status': result['status'], 'code': result['code']})

    @app.route('/get_statuses')
    def get_statuses():
        return jsonify(core.load_json(_status_file, {}))

    @app.route('/get_health_stats')
    def get_health_stats():
        cache = core.load_json(_status_file, {})
        if not isinstance(cache, dict):
            cache = {}
        counts = {'ok': 0, 'warn': 0, 'error': 0, 'timeout': 0, 'unknown': 0}
        total = 0
        latest = ''
        for st in cache.values():
            status = st.get('status', 'unknown') if isinstance(st, dict) else 'unknown'
            if status not in counts:
                status = 'unknown'
            counts[status] += 1
            total += 1
            ts = st.get('ts', '') if isinstance(st, dict) else ''
            if ts > latest:
                latest = ts
        result = dict(counts)
        result['total'] = total
        result['percent_ok'] = round(counts['ok'] / total * 100) if total else 0
        result['last_check'] = latest
        return jsonify(result)

    hooks['ui_tools_tab'].append({
        'id': 'check_links_btn', 'icon': '🔍',
        'label': 'Проверить ссылки', 'action': 'js',
        'js': 'window.__pluginLinkCheck && window.__pluginLinkCheck()',
    })

    hooks['ui_scripts'].append({'html': '''<script>
window.__pluginLinkCheck = function() {
    const btn = document.querySelector('[data-plugin-js*="__pluginLinkCheck"]');
    if (btn) { btn.disabled = true; btn.style.opacity = '0.5'; }
    window.reestrFetch('/check_all_links', {method: 'POST'})
        .then(r => r.json())
        .then(d => {
            if (!d.success) { alert('Ошибка: ' + (d.error || '?')); return; }
            if (typeof showNotification === 'function') showNotification('🔍 Проверка запущена...', 'success');
            let attempts = 0;
            const poll = setInterval(() => {
                attempts++;
                fetch('/get_statuses').then(r => r.json()).then(cache => {
                    window.__statusCache = cache;
                    document.querySelectorAll('.link-item').forEach(li => {
                        const id = li.getAttribute('data-id');
                        const st = cache[id];
                        if (st) li.setAttribute('data-status', st.status || 'unknown');
                    });
                    if (typeof window.__state !== 'undefined' && window.__state.applyFilters) {
                        try { window.__state.applyFilters(); } catch(e) {}
                    }
                    if (attempts >= 10) {
                        clearInterval(poll);
                        if (btn) { btn.disabled = false; btn.style.opacity = ''; }
                        if (typeof showNotification === 'function') showNotification('✅ Проверка завершена', 'success');
                    }
                });
            }, 2000);
            setTimeout(() => {
                clearInterval(poll);
                if (btn) { btn.disabled = false; btn.style.opacity = ''; }
            }, 30000);
        })
        .catch(() => { if (btn) { btn.disabled = false; btn.style.opacity = ''; } });
};
document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_statuses').then(r => r.json()).then(cache => {
        window.__statusCache = cache;
        document.querySelectorAll('.link-item').forEach(li => {
            const id = li.getAttribute('data-id');
            const st = cache[id];
            if (st) li.setAttribute('data-status', st.status || 'unknown');
        });
    }).catch(() => {});
});
</script>'''})