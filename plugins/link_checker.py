"""Проверка доступности ссылок через HTTP HEAD с пулом потоков и SSE-прогрессом."""
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

__version__ = "2.0"
__description__ = "Проверка статуса ссылок (HEAD, пул потоков, прогресс)"

try:
    import urllib.request as urlreq
    import urllib.error as urlerr
    HAS_URLLIB = True
except Exception:
    HAS_URLLIB = False

_status_lock = threading.Lock()
_check_lock = threading.Lock()
_check_running = False
_status_file = None

MAX_WORKERS = 16
CHECK_TIMEOUT = 6

# Состояние прогресса (потокобезопасно читается из SSE)
_STATE = {
    'running': False,
    'finished': False,
    'total': 0,
    'done': 0,
    'ok': 0,
    'warn': 0,
    'error': 0,            # счётчик ссылок со статусом error
    'timeout': 0,
    'unknown': 0,
    'started_at': None,
    'finished_at': None,
    'last_message': '',
    'error_message': '',   # текст последней ошибки (было 'error' — конфликт)
}


def _state_snapshot():
    with _check_lock:
        return dict(_STATE)


def _state_update(**kwargs):
    with _check_lock:
        _STATE.update(kwargs)


def _state_increment(status):
    with _check_lock:
        _STATE['done'] = _STATE.get('done', 0) + 1
        if status in _STATE:
            _STATE[status] = _STATE.get(status, 0) + 1


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
        req = urlreq.Request(url, method='HEAD', headers={'User-Agent': 'ReestrBot/2.0'})
        with urlreq.urlopen(req, timeout=CHECK_TIMEOUT) as resp:
            return {'status': 'ok', 'code': resp.status}
    except urlerr.HTTPError as e:
        if e.code in (401, 403):
            return {'status': 'warn', 'code': e.code}
        return {'status': 'error', 'code': e.code}
    except Exception:
        return {'status': 'timeout', 'code': None}


def _run_check(core):
    """Запускается в отдельном потоке. Параллельно проверяет все ссылки."""
    global _check_running
    with _status_lock:
        if _check_running:
            return False
        _check_running = True

    try:
        core.run_hook('on_status_check_start')

        wb = core.read_workbook()
        ws = wb.active
        cache = core.load_json(_status_file, {})
        if not isinstance(cache, dict):
            cache = {}

        # Собираем список задач
        tasks = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            rid = core.safe_int(row[0], -1)
            if rid < 0:
                continue
            if core.safe_str(row[10]) if len(row) > 10 else '':
                continue
            link = core.safe_str(row[2])
            if not link:
                continue
            tasks.append((rid, link))

        _state_update(
            running=True, finished=False,
            total=len(tasks), done=0,
            ok=0, warn=0, error=0, timeout=0, unknown=0,
            started_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            finished_at=None, last_message='', error_message=''
        )

        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(_check_one, url): rid for rid, url in tasks}
            for fut in as_completed(futures):
                rid = futures[fut]
                try:
                    result = fut.result()
                except Exception as e:
                    result = {'status': 'unknown', 'code': None}
                cache[str(rid)] = {
                    'status': result['status'],
                    'code': result['code'],
                    'ts': now_ts,
                }
                _state_increment(result['status'])
                if _STATE['done'] % 25 == 0:
                    _STATE['last_message'] = f"Обработано {_STATE['done']} из {_STATE['total']}"

        core.save_json(_status_file, cache)
        core.run_hook('on_status_check_end', results=dict(cache))
        _state_update(
            running=False, finished=True,
            finished_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            last_message=f"Завершено: {_STATE['done']} ссылок"
        )
    except Exception as e:
        _state_update(
            running=False, finished=True,
            error_message=str(e),
            last_message=f"Ошибка: {e}",
            finished_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    finally:
        with _status_lock:
            _check_running = False

    return True


def register(hooks, app, config, core):
    from flask import jsonify, request, Response
    global _status_file
    _status_file = str(Path(core.BASE_DIR) / 'status_cache.json')

    # ------------------ API ------------------

    @app.route('/check_all_links', methods=['POST'])
    def check_all_links():
        if not HAS_URLLIB:
            return jsonify({'success': False, 'error': 'urllib недоступен'}), 500
        with _status_lock:
            if _check_running:
                return jsonify({'success': False, 'error': 'Проверка уже идёт'}), 409
        threading.Thread(target=_run_check, args=(core,), daemon=True).start()
        return jsonify({'success': True, 'message': 'Проверка запущена'})

    @app.route('/check_all_links/progress')
    def check_all_links_progress():
        return jsonify(_state_snapshot())

    @app.route('/check_all_links/stream')
    def check_all_links_stream():
        """SSE-поток прогресса. Заканчивается, когда running=False и finished=True."""
        def gen():
            last_payload = None
            while True:
                snap = _state_snapshot()
                payload = json.dumps(snap, ensure_ascii=False)
                if payload != last_payload:
                    last_payload = payload
                    yield f"data: {payload}\n\n"
                # условие завершения потока
                if snap.get('finished') and not snap.get('running'):
                    yield "event: done\ndata: {}\n\n"
                    break
                # ограничим жизнь потока 10 минутами
                time.sleep(0.4)

        resp = Response(gen(), mimetype='text/event-stream')
        resp.headers['Cache-Control'] = 'no-cache'
        resp.headers['X-Accel-Buffering'] = 'no'
        resp.headers['Connection'] = 'keep-alive'
        return resp

    @app.route('/check_all_links/stop', methods=['POST'])
    def check_all_links_stop():
        # Реальной остановки пула не делаем, но сбрасываем флаг,
        # чтобы UI мог отцепиться от стрима
        _state_update(finished=True, last_message='Остановлено пользователем')
        return jsonify({'success': True})

    @app.route('/check_one_link/<int:rid>', methods=['POST'])
    def check_one_link(rid):
        rec = core.get_record_by_id(rid)
        if not rec:
            return jsonify({'success': False, 'error': 'Не найдена'}), 404
        result = _check_one(rec['link_del'])
        cache = core.load_json(_status_file, {})
        if not isinstance(cache, dict):
            cache = {}
        cache[str(rid)] = {
            'status': result['status'], 'code': result['code'],
            'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
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

    # ------------------ UI ------------------

    hooks['ui_tools_tab'].append({
        'id': 'check_links_btn', 'icon': '🔍',
        'label': 'Проверить ссылки', 'action': 'js',
        'js': 'window.__pluginLinkCheck && window.__pluginLinkCheck()',
    })

    hooks['ui_scripts'].append({'html': '''<script>
window.__pluginLinkCheck = function() {
    var btn = document.querySelector('[data-plugin-js*="__pluginLinkCheck"]');
    if (btn) { btn.disabled = true; btn.style.opacity = '0.5'; }

    fetch('/check_all_links', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}'
    })
    .then(function(r) {
        if (r.status === 409) {
            if (typeof showNotification === 'function')
                showNotification('ℹ️ Проверка уже идёт', 'success');
            return {success: true};
        }
        return r.json();
    })
    .then(function(d) {
        if (!d.success) {
            if (typeof showNotification === 'function')
                showNotification('❌ ' + (d.error || '?'), 'error');
            if (btn) { btn.disabled = false; btn.style.opacity = ''; }
            return;
        }
        if (typeof showNotification === 'function')
            showNotification('🔍 Проверка запущена', 'success');
        openProgressModal();
        startSSE(btn);
    })
    .catch(function() {
        if (btn) { btn.disabled = false; btn.style.opacity = ''; }
    });
};

function openProgressModal() {
    // Создаём модалку прогресса на лету
    var id = 'pluginLinkCheckProgressModal';
    var old = document.getElementById(id);
    if (old) old.remove();
    var modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = id;
    modal.style.zIndex = '3500';
    modal.innerHTML =
        '<div class="modal-content" style="max-width:480px;">' +
        '<h2>🔍 Проверка ссылок</h2>' +
        '<div id="linkCheckBarWrap" style="margin:14px 0;">' +
        '  <div style="background:rgba(128,128,128,0.15); height:20px; border-radius:10px; overflow:hidden;">' +
        '    <div id="linkCheckBarFill" style="height:100%; width:0%; background:linear-gradient(90deg,#2ecc71,#27ae60); border-radius:10px; transition:width 0.3s;"></div>' +
        '  </div>' +
        '  <div id="linkCheckStats" style="margin-top:10px; font-size:0.9rem; color:var(--text-color);">Ожидание...</div>' +
        '  <div id="linkCheckLegend" style="margin-top:10px; font-size:0.8rem; color:var(--meta-color); display:flex; gap:12px; flex-wrap:wrap;">' +
        '    <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#2ecc71;"></span> OK: <b id="lcOk">0</b></span>' +
        '    <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#f1c40f;"></span> Warn: <b id="lcWarn">0</b></span>' +
        '    <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#e74c3c;"></span> Error: <b id="lcErr">0</b></span>' +
        '    <span><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#7a9ab5;"></span> Timeout: <b id="lcTo">0</b></span>' +
        '  </div>' +
        '</div>' +
        '<div class="modal-actions">' +
        '  <button type="button" class="btn btn-secondary" id="lcCloseBtn">Скрыть</button>' +
        '  <button type="button" class="btn btn-danger" id="lcStopBtn">Остановить</button>' +
        '</div></div>';
    document.body.appendChild(modal);

    document.getElementById('lcCloseBtn').addEventListener('click', function() {
        modal.remove();
    });
    document.getElementById('lcStopBtn').addEventListener('click', function() {
        fetch('/check_all_links/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: '{}'
        }).finally(function() {
            modal.remove();
        });
    });
    modal.addEventListener('click', function(e) {
        if (e.target === modal) modal.remove();
    });
}

function updateProgress(snap) {
    var fill = document.getElementById('linkCheckBarFill');
    var stats = document.getElementById('linkCheckStats');
    var ok = document.getElementById('lcOk');
    var warn = document.getElementById('lcWarn');
    var err = document.getElementById('lcErr');
    var to = document.getElementById('lcTo');
    if (!stats) return;
    var pct = snap.total > 0 ? Math.round((snap.done / snap.total) * 100) : 0;
    if (fill) fill.style.width = pct + '%';
    stats.textContent = 'Обработано ' + snap.done + ' из ' + snap.total + ' (' + pct + '%)';
    if (ok) ok.textContent = snap.ok || 0;
    if (warn) warn.textContent = snap.warn || 0;
    if (err) err.textContent = snap.error || 0;      // ← счётчик, как и было
    if (to) to.textContent = snap.timeout || 0;
    if (snap.error_message) {
        stats.textContent += ' · ❌ ' + snap.error_message;
    }
}

function startSSE(btn) {
    if (typeof EventSource === 'undefined') {
        // Fallback — polling
        pollProgress(btn);
        return;
    }
    var es = new EventSource('/check_all_links/stream');
    es.onmessage = function(e) {
        try {
            var snap = JSON.parse(e.data);
            updateProgress(snap);
        } catch(err) {}
    };
    es.addEventListener('done', function() {
        es.close();
        if (btn) { btn.disabled = false; btn.style.opacity = ''; }
        if (typeof showNotification === 'function')
            showNotification('✅ Проверка завершена', 'success');
        // Обновляем статусы в карточках
        refreshStatuses();
    });
    es.onerror = function() {
        es.close();
        if (btn) { btn.disabled = false; btn.style.opacity = ''; }
    };
}

function pollProgress(btn) {
    var iv = setInterval(function() {
        fetch('/check_all_links/progress')
            .then(function(r) { return r.json(); })
            .then(function(snap) {
                updateProgress(snap);
                if (snap.finished && !snap.running) {
                    clearInterval(iv);
                    if (btn) { btn.disabled = false; btn.style.opacity = ''; }
                    if (typeof showNotification === 'function')
                        showNotification('✅ Проверка завершена', 'success');
                    refreshStatuses();
                }
            });
    }, 1000);
}

function refreshStatuses() {
    fetch('/get_statuses').then(function(r) { return r.json(); }).then(function(cache) {
        window.__statusCache = cache;
        document.querySelectorAll('.link-item').forEach(function(li) {
            var id = li.getAttribute('data-id');
            var st = cache[id];
            if (st) li.setAttribute('data-status', st.status || 'unknown');
        });
    }).catch(function() {});
}

document.addEventListener('DOMContentLoaded', function() {
    fetch('/get_statuses').then(function(r) { return r.json(); }).then(function(cache) {
        window.__statusCache = cache;
        document.querySelectorAll('.link-item').forEach(function(li) {
            var id = li.getAttribute('data-id');
            var st = cache[id];
            if (st) li.setAttribute('data-status', st.status || 'unknown');
        });
    }).catch(function() {});
});
</script>'''})

    # При выключении — не даём висеть потоку
    def _on_shutdown():
        _state_update(finished=True, running=False, last_message='Shutdown')

    hooks['on_shutdown'].append(_on_shutdown)

