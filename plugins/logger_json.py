"""Расширенный журнал действий: фильтры, статистика, экспорт."""
from pathlib import Path
from datetime import datetime, timedelta
import json
import csv
import io

__version__ = "2.0"
__description__ = "Расширенный журнал действий: фильтры, экспорт, статистика"


# Все возможные типы событий
ALL_ACTIONS = [
    'add', 'edit', 'soft_delete', 'restore', 'restore_from_trash',
    'purge_trash', 'empty_record',
    'bulk_delete', 'bulk_move', 'bulk_favorite', 'bulk_tags', 'bulk_undo',
    'rename_category', 'rename_group', 'delete_category', 'sort_group',
    'update_group_icon', 'edit_desc', 'edit_category', 'move_to_group',
    'import_xlsx', 'import_bookmarks', 'import_pocket',
    'storage_import_xlsx', 'storage_export_xlsx', 'storage_reset',
    'trash_auto_purge',
]

ACTION_LABELS = {
    'add': '➕ Добавление',
    'edit': '✏️ Изменение',
    'soft_delete': '🗑 Удаление',
    'restore': '↩ Восстановление',
    'restore_from_trash': '↩ Восстановление',
    'purge_trash': '🧹 Очистка корзины',
    'empty_record': '💥 Удаление навсегда',
    'bulk_delete': '🗑 Массовое удаление',
    'bulk_move': '📁 Массовое перемещение',
    'bulk_favorite': '⭐ Массовое избранное',
    'bulk_tags': '🔖 Массовые теги',
    'bulk_undo': '↩ Откат массовой операции',
    'rename_category': '✏️ Категория переименована',
    'rename_group': '✏️ Группа переименована',
    'delete_category': '🗑 Категория удалена',
    'sort_group': '⇅ Сортировка',
    'update_group_icon': '🎨 Иконка группы',
    'edit_desc': '📝 Описание',
    'edit_category': '🏷️ Категория',
    'move_to_group': '📁 Перемещение',
    'import_xlsx': '📥 Импорт XLSX',
    'import_bookmarks': '🌐 Импорт закладок',
    'import_pocket': '📖 Импорт Pocket',
    'storage_import_xlsx': '💾 Импорт в хранилище',
    'storage_export_xlsx': '💾 Экспорт из хранилища',
    'storage_reset': '💥 Очистка хранилища',
    'trash_auto_purge': '🧹 Автоочистка корзины',
}

ACTION_COLORS = {
    'add': '#2ecc71',
    'edit': '#3498db',
    'soft_delete': '#e74c3c',
    'restore': '#16a085',
    'restore_from_trash': '#16a085',
    'purge_trash': '#c0392b',
    'empty_record': '#c0392b',
    'bulk_delete': '#e74c3c',
    'bulk_move': '#9b59b6',
    'bulk_favorite': '#f1c40f',
    'bulk_tags': '#e67e22',
    'bulk_undo': '#1abc9c',
    'rename_category': '#3498db',
    'rename_group': '#3498db',
    'delete_category': '#e74c3c',
    'sort_group': '#95a5a6',
    'update_group_icon': '#9b59b6',
    'edit_desc': '#5dade2',
    'edit_category': '#5dade2',
    'move_to_group': '#9b59b6',
    'import_xlsx': '#27ae60',
    'import_bookmarks': '#27ae60',
    'import_pocket': '#27ae60',
    'storage_import_xlsx': '#27ae60',
    'storage_export_xlsx': '#8e44ad',
    'storage_reset': '#c0392b',
    'trash_auto_purge': '#7f8c8d',
}


def register(hooks, app, config, core):
    from flask import jsonify, request, Response
    _logs_file = str(Path(core.BASE_DIR) / 'logs.json')

    # ============================================================
    # Загрузка / фильтрация
    # ============================================================
    def _load():
        data = core.load_json(_logs_file, [])
        return data if isinstance(data, list) else []

    def _safe_int(v, default=0):
        return core.safe_int(v, default)

    def _filter(logs, params):
        """Фильтрация списка логов по параметрам запроса."""
        rid = (params.get('record_id') or '').strip()
        action = (params.get('action') or '').strip()
        q = (params.get('q') or '').strip().lower()
        date_from = (params.get('date_from') or '').strip()
        date_to = (params.get('date_to') or '').strip()

        if rid:
            try:
                rid_num = int(rid)
                logs = [l for l in logs if _safe_int(l.get('id', 0), 0) == rid_num]
            except (ValueError, TypeError):
                pass

        if action:
            actions_set = set(a.strip() for a in action.split(',') if a.strip())
            logs = [l for l in logs if l.get('action') in actions_set]

        if q:
            def matches(l):
                haystack = ' '.join([
                    str(l.get('name', '')),
                    str(l.get('action', '')),
                    str(l.get('id', '')),
                    json.dumps(l.get('details', {}), ensure_ascii=False),
                ]).lower()
                return q in haystack
            logs = [l for l in logs if matches(l)]

        if date_from:
            logs = [l for l in logs if str(l.get('ts', ''))[:10] >= date_from]
        if date_to:
            logs = [l for l in logs if str(l.get('ts', ''))[:10] <= date_to]

        return logs

    def _sort(logs, sort_dir):
        """sort_dir = 'asc' или 'desc'. По умолчанию новые сверху."""
        return sorted(logs, key=lambda x: str(x.get('ts', '')), reverse=(sort_dir != 'asc'))

    # ============================================================
    # API: список с фильтрами
    # ============================================================
    @app.route('/get_logs')
    def get_logs():
        try:
            limit = max(1, min(2000, int(request.args.get('limit', 100))))
        except (ValueError, TypeError):
            limit = 100
        try:
            offset = max(0, int(request.args.get('offset', 0)))
        except (ValueError, TypeError):
            offset = 0
        sort_dir = (request.args.get('sort', 'desc') or 'desc').lower()
        if sort_dir not in ('asc', 'desc'):
            sort_dir = 'desc'

        logs = _load()
        total_before = len(logs)
        logs = _filter(logs, request.args)
        logs = _sort(logs, sort_dir)
        total_after = len(logs)
        page = logs[offset:offset + limit]

        return jsonify({
            'success': True,
            'logs': page,
            'total': total_after,
            'total_unfiltered': total_before,
            'offset': offset,
            'limit': limit,
            'has_more': offset + limit < total_after,
        })

    # ============================================================
    # API: статистика
    # ============================================================
    @app.route('/get_logs_stats')
    def get_logs_stats():
        logs = _load()
        now = datetime.now()

        counts = {}
        by_day = {}
        top_records = {}  # id -> {'name': ..., 'count': N}
        total = len(logs)

        for l in logs:
            a = l.get('action', '?')
            counts[a] = counts.get(a, 0) + 1

            ts = str(l.get('ts', ''))
            day = ts[:10] if len(ts) >= 10 else ''
            if day:
                by_day[day] = by_day.get(day, 0) + 1

            rid = l.get('id')
            if rid is not None:
                rid = _safe_int(rid, -1)
                if rid > 0:
                    name = str(l.get('name', '') or '')
                    info = top_records.setdefault(rid, {'id': rid, 'name': name, 'count': 0})
                    info['count'] += 1
                    if name and not info['name']:
                        info['name'] = name

        # Активность за последние 30 дней (с дырками)
        activity = []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            activity.append({'day': d, 'count': by_day.get(d, 0)})

        top = sorted(top_records.values(), key=lambda x: -x['count'])[:10]

        # Разбивка по категориям действий
        by_group = {
            'create': sum(v for k, v in counts.items() if k in ('add',)),
            'edit': sum(v for k, v in counts.items()
                        if k in ('edit', 'edit_desc', 'edit_category', 'move_to_group',
                                 'rename_category', 'rename_group', 'sort_group',
                                 'update_group_icon', 'bulk_move', 'bulk_tags', 'bulk_favorite')),
            'delete': sum(v for k, v in counts.items()
                          if k in ('soft_delete', 'hard_delete', 'empty_record',
                                   'bulk_delete', 'purge_trash', 'trash_auto_purge',
                                   'delete_category')),
            'restore': sum(v for k, v in counts.items() if 'restore' in k),
            'import_export': sum(v for k, v in counts.items()
                                 if 'import' in k or 'export' in k),
        }

        # Сколько записей уникальных
        unique_records = len([1 for k in top_records if k])

        # Самое старое и свежее
        if logs:
            sorted_ts = sorted(str(l.get('ts', '')) for l in logs)
            first_ts = sorted_ts[0]
            last_ts = sorted_ts[-1]
        else:
            first_ts = last_ts = ''

        return jsonify({
            'success': True,
            'total': total,
            'counts': counts,
            'by_group': by_group,
            'by_day': activity,
            'top_records': top,
            'unique_records': unique_records,
            'first_ts': first_ts,
            'last_ts': last_ts,
        })

    # ============================================================
    # API: экспорт JSON / CSV
    # ============================================================
    @app.route('/export_logs')
    def export_logs():
        fmt = (request.args.get('format', 'json') or 'json').lower()
        if fmt not in ('json', 'csv'):
            return 'format: json или csv', 400

        logs = _filter(_load(), request.args)
        logs = _sort(logs, 'desc')

        ts_now = datetime.now().strftime('%Y%m%d_%H%M%S')

        if fmt == 'json':
            content = json.dumps({
                'exported_at': datetime.now().isoformat(),
                'total': len(logs),
                'logs': logs,
            }, ensure_ascii=False, indent=2)
            mimetype = 'application/json; charset=utf-8'
            filename = f'logs_{ts_now}.json'
        else:
            buf = io.StringIO()
            w = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            w.writerow(['ts', 'action', 'action_label', 'id', 'name', 'details'])
            for l in logs:
                details = l.get('details', {})
                details_str = json.dumps(details, ensure_ascii=False) if details else ''
                w.writerow([
                    l.get('ts', ''),
                    l.get('action', ''),
                    ACTION_LABELS.get(l.get('action', ''), l.get('action', '')),
                    l.get('id', ''),
                    l.get('name', ''),
                    details_str,
                ])
            content = '\ufeff' + buf.getvalue()
            mimetype = 'text/csv; charset=utf-8'
            filename = f'logs_{ts_now}.csv'

        from urllib.parse import quote
        r = Response(content, mimetype=mimetype)
        r.headers['Content-Disposition'] = (
            f'attachment; filename="{filename}"; '
            f"filename*=UTF-8''{quote(filename)}"
        )
        return r

    # ============================================================
    # API: очистка журнала
    # ============================================================
    @app.route('/clear_logs', methods=['POST'])
    def clear_logs():
        data = request.get_json() or {}
        if str(data.get('confirm', '')) != 'YES_CLEAR_LOGS':
            return jsonify({'success': False, 'error': 'Требуется confirm=YES_CLEAR_LOGS'}), 400
        try:
            with open(_logs_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': True})

    # ============================================================
    # API: история одной записи (совместимость)
    # ============================================================
    @app.route('/get_record_history/<int:rid>')
    def get_record_history(rid):
        logs = _load()
        logs = [l for l in logs if _safe_int(l.get('id', 0), 0) == rid]
        logs.sort(key=lambda x: str(x.get('ts', '')), reverse=True)
        return jsonify(logs)

    # ============================================================
    # UI-слоты
    # ============================================================
    hooks['ui_tools_tab'].append({
        'id': 'show_logs_btn', 'icon': '📜',
        'label': 'Журнал действий', 'action': 'js',
        'js': 'window.__logsOpen && window.__logsOpen()',
    })

    # Сериализуем словари в JSON для передачи в JS
    labels_json = json.dumps(ACTION_LABELS, ensure_ascii=False)
    colors_json = json.dumps(ACTION_COLORS, ensure_ascii=False)
    all_actions_json = json.dumps(ALL_ACTIONS, ensure_ascii=False)

    hooks['ui_modals'].append({
        'id': 'pluginLogsModal',
        'title': '📜 Журнал действий',
        'width': 'wide',
        'html': '''
<div style="display:flex; gap:14px; flex-wrap:wrap; align-items:flex-start;">

  <!-- Левая колонка: фильтры и статистика -->
  <div style="flex:0 0 240px; min-width:220px; display:flex; flex-direction:column; gap:10px;">

    <div class="logs-filter-group">
      <label class="logs-filter-label">🔍 Поиск</label>
      <input type="text" id="logsFilterQuery" placeholder="имя, ID, детали..."
             style="width:100%; padding:6px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.85rem; outline:none;">
    </div>

    <div class="logs-filter-group">
      <label class="logs-filter-label">📅 Дата с</label>
      <input type="date" id="logsFilterDateFrom"
             style="width:100%; padding:6px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.85rem; outline:none;">
    </div>

    <div class="logs-filter-group">
      <label class="logs-filter-label">📅 Дата по</label>
      <input type="date" id="logsFilterDateTo"
             style="width:100%; padding:6px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.85rem; outline:none;">
    </div>

    <div class="logs-filter-group">
      <label class="logs-filter-label">🎯 ID записи</label>
      <input type="number" id="logsFilterRecordId" placeholder="например 42"
             style="width:100%; padding:6px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.85rem; outline:none;">
    </div>

    <div class="logs-filter-group">
      <label class="logs-filter-label" style="display:flex; justify-content:space-between;">
        <span>🎬 Действия</span>
        <span>
          <button type="button" class="logs-mini-btn" id="logsSelectAllActions">все</button>
          <button type="button" class="logs-mini-btn" id="logsClearActions">снять</button>
        </span>
      </label>
      <div id="logsActionsList" class="logs-actions-list"></div>
    </div>

    <div style="display:flex; gap:6px; margin-top:6px;">
      <button type="button" class="data-btn" id="logsApplyFiltersBtn"
              style="flex:1; justify-content:center; font-size:0.78rem;">
        <span class="data-icon">✓</span><span>Применить</span>
      </button>
      <button type="button" class="data-btn" id="logsResetFiltersBtn"
              style="flex:0 0 auto; padding:6px 10px; font-size:0.78rem;">
        <span class="data-icon">↺</span>
      </button>
    </div>

    <!-- Мини-статистика -->
    <div class="logs-stats-box" id="logsStatsBox">
      <div style="color:var(--meta-color); text-align:center; font-size:0.75rem; padding:8px 0;">
        Загрузка статистики...
      </div>
    </div>

  </div>

  <!-- Правая колонка: лента -->
  <div style="flex:1; min-width:0; display:flex; flex-direction:column; gap:8px;">

    <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
      <span style="color:var(--meta-color); font-size:0.8rem;">
        Показано: <b id="logsCountShown">0</b> из <b id="logsCountTotal">0</b>
      </span>
      <span style="flex:1;"></span>
      <select id="logsSortSelect"
              style="padding:4px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.78rem;">
        <option value="desc">↓ Новые сверху</option>
        <option value="asc">↑ Старые сверху</option>
      </select>
      <select id="logsLimitSelect"
              style="padding:4px 10px; border:1px solid var(--input-border); border-radius:8px; background:var(--input-bg); color:var(--text-color); font-size:0.78rem;">
        <option value="50">50 / стр.</option>
        <option value="100" selected>100 / стр.</option>
        <option value="250">250 / стр.</option>
        <option value="500">500 / стр.</option>
      </select>
    </div>

    <div class="logs-list" id="logsList">
      <p style="color:var(--meta-color); text-align:center; padding:20px 0;">Загрузка...</p>
    </div>

    <div style="display:flex; gap:6px; justify-content:center; align-items:center; margin-top:6px;">
      <button type="button" class="data-btn" id="logsPrevBtn" disabled>
        <span>◀</span><span>Назад</span>
      </button>
      <span style="color:var(--meta-color); font-size:0.8rem;" id="logsPageInfo">—</span>
      <button type="button" class="data-btn" id="logsNextBtn" disabled>
        <span>Вперёд</span><span>▶</span>
      </button>
    </div>

  </div>

</div>

<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:14px;">
  <button type="button" class="data-btn" id="logsExportJsonBtn">
    <span class="data-icon">📤</span><span>Экспорт JSON</span>
  </button>
  <button type="button" class="data-btn" id="logsExportCsvBtn">
    <span class="data-icon">📊</span><span>Экспорт CSV</span>
  </button>
  <button type="button" class="data-btn" id="logsAutoRefreshBtn"
          style="border-color:var(--filter-btn-active-color);">
    <span class="data-icon">🔄</span><span id="logsAutoRefreshLabel">Авто-обновление: выкл</span>
  </button>
  <button type="button" class="data-btn" id="logsClearBtn"
          style="margin-left:auto; color:#e74c3c; border-color:rgba(231,76,60,0.4);">
    <span class="data-icon">🗑</span><span>Очистить журнал</span>
  </button>
  <button type="button" class="btn btn-secondary"
          onclick="closePluginModal('pluginLogsModal')">Закрыть</button>
</div>

<!-- Модалка деталей события -->
<div id="logsDetailModal" class="modal" style="z-index:3600;">
  <div class="modal-content" style="max-width:640px;">
    <h2 id="logsDetailTitle">Детали события</h2>
    <div id="logsDetailBody" style="font-size:0.9rem; line-height:1.6;"></div>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary"
              onclick="document.getElementById('logsDetailModal').classList.remove('active')">Закрыть</button>
    </div>
  </div>
</div>
'''
    })

    # ============================================================
    # UI-скрипты
    # ============================================================
    hooks['ui_scripts'].append({'html': '''<script>
(function() {
    var ACTION_LABELS = ''' + labels_json + ''';
    var ACTION_COLORS = ''' + colors_json + ''';
    var ALL_ACTIONS = ''' + all_actions_json + ''';

    var state = {
        offset: 0,
        limit: 100,
        sort: 'desc',
        autoRefresh: false,
        autoRefreshTimer: null,
        currentHasMore: false,
        currentTotal: 0,
    };

    function $(id) { return document.getElementById(id); }

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function buildFilterQuery() {
        var parts = [];
        var q = ($('logsFilterQuery') || {}).value || '';
        if (q.trim()) parts.push('q=' + encodeURIComponent(q.trim()));
        var df = ($('logsFilterDateFrom') || {}).value || '';
        if (df) parts.push('date_from=' + encodeURIComponent(df));
        var dt = ($('logsFilterDateTo') || {}).value || '';
        if (dt) parts.push('date_to=' + encodeURIComponent(dt));
        var rid = ($('logsFilterRecordId') || {}).value || '';
        if (rid) parts.push('record_id=' + encodeURIComponent(rid));
        var actions = [];
        document.querySelectorAll('#logsActionsList input[type="checkbox"]:checked').forEach(function(cb) {
            actions.push(cb.value);
        });
        if (actions.length && actions.length < ALL_ACTIONS.length) {
            parts.push('action=' + encodeURIComponent(actions.join(',')));
        }
        parts.push('limit=' + state.limit);
        parts.push('offset=' + state.offset);
        parts.push('sort=' + state.sort);
        return parts.join('&');
    }

    function renderActionsList() {
        var container = $('logsActionsList');
        if (!container) return;
        var html = '';
        ALL_ACTIONS.forEach(function(a) {
            var color = ACTION_COLORS[a] || '#888';
            var label = ACTION_LABELS[a] || a;
            html += '<label class="logs-action-item">'
                + '<input type="checkbox" value="' + esc(a) + '" checked>'
                + '<span class="logs-action-dot" style="background:' + color + ';"></span>'
                + '<span class="logs-action-label">' + esc(label) + '</span>'
                + '</label>';
        });
        container.innerHTML = html;
    }

    function loadLogs() {
        var list = $('logsList');
        if (!list) return;
        list.innerHTML = '<p style="color:var(--meta-color); text-align:center; padding:20px 0;">Загрузка...</p>';

        fetch('/get_logs?' + buildFilterQuery())
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (!d.success) {
                    list.innerHTML = '<p style="color:#e74c3c; text-align:center;">Ошибка загрузки</p>';
                    return;
                }
                state.currentHasMore = d.has_more;
                state.currentTotal = d.total;

                var shown = $('logsCountShown');
                var total = $('logsCountTotal');
                if (shown) shown.textContent = (d.logs || []).length;
                if (total) total.textContent = d.total || 0;

                if (!d.logs || !d.logs.length) {
                    list.innerHTML = '<p style="color:var(--meta-color); text-align:center; padding:20px 0;">'
                        + (d.total_unfiltered === 0 ? 'Журнал пуст' : 'Ничего не найдено по фильтрам')
                        + '</p>';
                    updatePagination(d);
                    return;
                }

                list.innerHTML = d.logs.map(renderLogItem).join('');
                bindLogItemClicks();
                updatePagination(d);
            })
            .catch(function() {
                list.innerHTML = '<p style="color:#e74c3c; text-align:center;">Ошибка сети</p>';
            });
    }

    function renderLogItem(l) {
        var action = l.action || '?';
        var label = ACTION_LABELS[action] || action;
        var color = ACTION_COLORS[action] || '#888';
        var ts = l.ts || '';
        var name = l.name || '';
        var id = l.id != null ? l.id : '';

        // Краткое описание details
        var summary = '';
        var d = l.details || {};
        if (d.count !== undefined) summary += '×' + d.count;
        if (d.category) summary += (summary ? ' · ' : '') + '→ ' + d.category;
        if (d.new_name) summary += (summary ? ' · ' : '') + '→ ' + d.new_name;
        if (d.to) summary += (summary ? ' · ' : '') + '→ ' + d.to;
        if (d.from && d.to) summary = '«' + d.from + '» → «' + d.to + '»';
        else if (d.from) summary += (summary ? ' · ' : '') + 'из «' + d.from + '»';

        var hasDetails = d && Object.keys(d).length > 0;

        return '<div class="logs-item" data-action="' + esc(action) + '" '
            + 'data-json="' + esc(JSON.stringify(l)) + '"'
            + (hasDetails ? ' data-clickable="1"' : '') + '>'
            + '<span class="logs-item-ts">' + esc(ts) + '</span>'
            + '<span class="logs-item-action" style="background:' + color + '22; color:' + color + '; border-color:' + color + '55;">'
            + esc(label)
            + '</span>'
            + (id !== '' ? '<span class="logs-item-id">#' + esc(id) + '</span>' : '')
            + '<span class="logs-item-name">' + esc(name) + '</span>'
            + (summary ? '<span class="logs-item-summary">' + esc(summary) + '</span>' : '')
            + (hasDetails ? '<span class="logs-item-chevron">▸</span>' : '')
            + '</div>';
    }

    function bindLogItemClicks() {
        document.querySelectorAll('#logsList .logs-item[data-clickable="1"]').forEach(function(el) {
            el.addEventListener('click', function() {
                try {
                    var l = JSON.parse(this.getAttribute('data-json'));
                    showLogDetails(l);
                } catch (e) {}
            });
        });
    }

    function showLogDetails(l) {
        var modal = $('logsDetailModal');
        var title = $('logsDetailTitle');
        var body = $('logsDetailBody');
        if (!modal || !body) return;

        var action = l.action || '?';
        var label = ACTION_LABELS[action] || action;
        var color = ACTION_COLORS[action] || '#888';

        if (title) {
            title.innerHTML = '<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:'
                + color + '; margin-right:8px;"></span>' + esc(label);
        }

        var html = '';
        html += '<div class="logs-detail-row"><span class="logs-detail-key">Время</span><span>'
            + esc(l.ts || '') + '</span></div>';
        html += '<div class="logs-detail-row"><span class="logs-detail-key">Действие</span><span><code>'
            + esc(action) + '</code></span></div>';
        if (l.id != null) {
            html += '<div class="logs-detail-row"><span class="logs-detail-key">ID записи</span><span>'
                + esc(l.id) + '</span></div>';
        }
        if (l.name) {
            html += '<div class="logs-detail-row"><span class="logs-detail-key">Название</span><span>'
                + esc(l.name) + '</span></div>';
        }

        var d = l.details || {};
        if (d && Object.keys(d).length) {
            html += '<div style="margin-top:12px; padding-top:12px; border-top:1px dashed var(--card-border);">';
            html += '<div class="logs-detail-key" style="margin-bottom:8px;">Детали</div>';

            // Специальная обработка changes (edit)
            if (d.changes && typeof d.changes === 'object') {
                Object.keys(d.changes).forEach(function(field) {
                    var ch = d.changes[field] || {};
                    html += '<div class="logs-diff-row">'
                        + '<span class="logs-diff-field">' + esc(field) + '</span>'
                        + '<span class="logs-diff-from">' + esc(ch.from || '—') + '</span>'
                        + '<span class="logs-diff-arrow">→</span>'
                        + '<span class="logs-diff-to">' + esc(ch.to || '—') + '</span>'
                        + '</div>';
                });
                // Остальные поля details, кроме changes
                Object.keys(d).forEach(function(k) {
                    if (k === 'changes') return;
                    html += renderDetailField(k, d[k]);
                });
            } else {
                Object.keys(d).forEach(function(k) {
                    html += renderDetailField(k, d[k]);
                });
            }
            html += '</div>';
        }

        body.innerHTML = html;
        modal.classList.add('active');
    }

    function renderDetailField(key, value) {
        var valStr;
        if (typeof value === 'object' && value !== null) {
            valStr = '<code style="font-size:0.8rem;">' + esc(JSON.stringify(value)) + '</code>';
        } else {
            valStr = esc(String(value == null ? '' : value));
        }
        return '<div class="logs-detail-row"><span class="logs-detail-key">' + esc(key) + '</span><span>' + valStr + '</span></div>';
    }

    function updatePagination(d) {
        var prev = $('logsPrevBtn');
        var next = $('logsNextBtn');
        var info = $('logsPageInfo');
        if (prev) prev.disabled = (state.offset <= 0);
        if (next) next.disabled = !d.has_more;
        if (info) {
            var from = d.total === 0 ? 0 : (state.offset + 1);
            var to = Math.min(state.offset + state.limit, d.total);
            info.textContent = from + '–' + to + ' из ' + d.total;
        }
    }

    function loadStats() {
        var box = $('logsStatsBox');
        if (!box) return;
        fetch('/get_logs_stats')
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (!d.success) {
                    box.innerHTML = '<div style="color:#e74c3c; font-size:0.75rem; text-align:center;">Ошибка</div>';
                    return;
                }
                var html = '';
                html += '<div class="logs-stat-row"><span>Всего событий</span><b>' + d.total + '</b></div>';
                html += '<div class="logs-stat-row"><span>Уникальных записей</span><b>' + d.unique_records + '</b></div>';

                var bg = d.by_group || {};
                if (bg.create || bg.edit || bg.delete || bg.restore || bg.import_export) {
                    html += '<div style="margin-top:8px; padding-top:8px; border-top:1px dashed var(--card-border);">';
                    html += '<div class="logs-stat-group-label">По группам</div>';
                    html += '<div class="logs-stat-row"><span>➕ Создание</span><b>' + (bg.create || 0) + '</b></div>';
                    html += '<div class="logs-stat-row"><span>✏️ Изменение</span><b>' + (bg.edit || 0) + '</b></div>';
                    html += '<div class="logs-stat-row"><span>🗑 Удаление</span><b>' + (bg.delete || 0) + '</b></div>';
                    html += '<div class="logs-stat-row"><span>↩ Восстановление</span><b>' + (bg.restore || 0) + '</b></div>';
                    html += '<div class="logs-stat-row"><span>📥 Импорт/экспорт</span><b>' + (bg.import_export || 0) + '</b></div>';
                    html += '</div>';
                }

                if (d.top_records && d.top_records.length) {
                    html += '<div style="margin-top:8px; padding-top:8px; border-top:1px dashed var(--card-border);">';
                    html += '<div class="logs-stat-group-label">🔥 Топ активных</div>';
                    d.top_records.slice(0, 5).forEach(function(rec) {
                        var displayName = rec.name || ('#' + rec.id);
                        html += '<div class="logs-stat-row" title="' + esc(displayName) + '">'
                            + '<span style="overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">' + esc(displayName) + '</span>'
                            + '<b>' + rec.count + '</b>'
                            + '</div>';
                    });
                    html += '</div>';
                }

                // Мини-бар активности
                var days = d.by_day || [];
                var maxCount = Math.max.apply(null, days.map(function(x) { return x.count; }).concat([1]));
                html += '<div style="margin-top:8px; padding-top:8px; border-top:1px dashed var(--card-border);">';
                html += '<div class="logs-stat-group-label">Активность за 30 дней</div>';
                html += '<div style="display:flex; align-items:flex-end; gap:1px; height:32px;">';
                days.forEach(function(x) {
                    var h = x.count === 0 ? 2 : Math.max(2, Math.round(x.count / maxCount * 32));
                    var alpha = x.count === 0 ? 0.1 : 0.4 + (x.count / maxCount) * 0.6;
                    html += '<div title="' + x.day + ': ' + x.count + '" '
                        + 'style="flex:1; height:' + h + 'px; background:var(--accent); opacity:' + alpha.toFixed(2)
                        + '; border-radius:1px; min-width:2px;"></div>';
                });
                html += '</div>';
                html += '</div>';

                if (d.first_ts || d.last_ts) {
                    html += '<div style="margin-top:8px; padding-top:8px; border-top:1px dashed var(--card-border); font-size:0.7rem; color:var(--meta-color);">';
                    if (d.first_ts) html += '<div>Первое: ' + esc(d.first_ts) + '</div>';
                    if (d.last_ts) html += '<div>Последнее: ' + esc(d.last_ts) + '</div>';
                    html += '</div>';
                }

                box.innerHTML = html;
            })
            .catch(function() {
                box.innerHTML = '<div style="color:#e74c3c; font-size:0.75rem; text-align:center;">Ошибка</div>';
            });
    }

    function autoRefreshTick() {
        if (!state.autoRefresh) return;
        loadLogs();
        loadStats();
    }

    function setAutoRefresh(on) {
        state.autoRefresh = !!on;
        var label = $('logsAutoRefreshLabel');
        var btn = $('logsAutoRefreshBtn');
        if (state.autoRefreshTimer) {
            clearInterval(state.autoRefreshTimer);
            state.autoRefreshTimer = null;
        }
        if (state.autoRefresh) {
            state.autoRefreshTimer = setInterval(autoRefreshTick, 15000);
            if (label) label.textContent = 'Авто-обновление: вкл';
            if (btn) btn.style.background = 'var(--filter-btn-active-bg)';
        } else {
            if (label) label.textContent = 'Авто-обновление: выкл';
            if (btn) btn.style.background = '';
        }
    }

    // ============================================================
    // Публичная функция открытия
    // ============================================================
    window.__logsOpen = function(opts) {
        opts = opts || {};
        var modal = $('pluginLogsModal');
        if (!modal) return;
        // Сброс пагинации
        state.offset = 0;
        // Если передан record_id — применить фильтр по нему
        var ridInput = $('logsFilterRecordId');
        if (ridInput) ridInput.value = opts.record_id != null ? opts.record_id : '';

        modal.classList.add('active');
        loadLogs();
        loadStats();
    };

    // ============================================================
    // Инициализация
    // ============================================================
    document.addEventListener('DOMContentLoaded', function() {
        renderActionsList();


        var applyBtn = $('logsApplyFiltersBtn');
        if (applyBtn) applyBtn.addEventListener('click', function() {
            state.offset = 0;
            loadLogs();
        });

        var resetBtn = $('logsResetFiltersBtn');
        if (resetBtn) resetBtn.addEventListener('click', function() {
            var q = $('logsFilterQuery'); if (q) q.value = '';
            var df = $('logsFilterDateFrom'); if (df) df.value = '';
            var dt = $('logsFilterDateTo'); if (dt) dt.value = '';
            var rid = $('logsFilterRecordId'); if (rid) rid.value = '';
            document.querySelectorAll('#logsActionsList input[type="checkbox"]').forEach(function(cb) {
                cb.checked = true;
            });
            state.offset = 0;
            loadLogs();
        });

        var selectAllBtn = $('logsSelectAllActions');
        if (selectAllBtn) selectAllBtn.addEventListener('click', function() {
            document.querySelectorAll('#logsActionsList input[type="checkbox"]').forEach(function(cb) {
                cb.checked = true;
            });
        });
        var clearAllBtn = $('logsClearActions');
        if (clearAllBtn) clearAllBtn.addEventListener('click', function() {
            document.querySelectorAll('#logsActionsList input[type="checkbox"]').forEach(function(cb) {
                cb.checked = false;
            });
        });

        var sortSel = $('logsSortSelect');
        if (sortSel) sortSel.addEventListener('change', function() {
            state.sort = this.value;
            state.offset = 0;
            loadLogs();
        });
        var limitSel = $('logsLimitSelect');
        if (limitSel) limitSel.addEventListener('change', function() {
            state.limit = parseInt(this.value) || 100;
            state.offset = 0;
            loadLogs();
        });

        var prevBtn = $('logsPrevBtn');
        if (prevBtn) prevBtn.addEventListener('click', function() {
            state.offset = Math.max(0, state.offset - state.limit);
            loadLogs();
        });
        var nextBtn = $('logsNextBtn');
        if (nextBtn) nextBtn.addEventListener('click', function() {
            state.offset += state.limit;
            loadLogs();
        });

        var expJson = $('logsExportJsonBtn');
        if (expJson) expJson.addEventListener('click', function() {
            var q = buildFilterQuery().replace(/limit=\\d+/, 'limit=10000');
            window.open('/export_logs?format=json&' + q, '_blank');
        });
        var expCsv = $('logsExportCsvBtn');
        if (expCsv) expCsv.addEventListener('click', function() {
            var q = buildFilterQuery().replace(/limit=\\d+/, 'limit=10000');
            window.open('/export_logs?format=csv&' + q, '_blank');
        });

        var arBtn = $('logsAutoRefreshBtn');
        if (arBtn) arBtn.addEventListener('click', function() {
            setAutoRefresh(!state.autoRefresh);
        });

        var clearBtn = $('logsClearBtn');
        if (clearBtn) clearBtn.addEventListener('click', function() {
            var answer = prompt(
                'Это удалит ВСЕ записи журнала без возможности восстановления.\\n\\n' +
                'Для подтверждения введите: YES_CLEAR_LOGS'
            );
            if (answer !== 'YES_CLEAR_LOGS') {
                if (typeof showNotification === 'function') showNotification('Отменено', 'success');
                return;
            }
            fetch('/clear_logs', {
                method: 'POST',
                headers: Object.assign(
                    {'Content-Type': 'application/json'},
                    (window.reestrCsrfHeader && window.reestrCsrfHeader()) || {}
                ),
                body: JSON.stringify({confirm: 'YES_CLEAR_LOGS'})
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    if (typeof showNotification === 'function') showNotification('✅ Журнал очищен', 'success');
                    state.offset = 0;
                    loadLogs();
                    loadStats();
                } else {
                    if (typeof showNotification === 'function') showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            })
            .catch(function() {
                if (typeof showNotification === 'function') showNotification('❌ Ошибка сети', 'error');
            });
        });

        // Enter в поиске — применить
        var qInput = $('logsFilterQuery');
        if (qInput) qInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); state.offset = 0; loadLogs(); }
        });

        // Ctrl+L — открыть журнал
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'l') {
                var tag = (e.target && e.target.tagName) || '';
                var isEditable = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
                if (isEditable) return;
                e.preventDefault();
                window.__logsOpen();
            }
        });

        // Автофокус на поиске при открытии
        var modal = $('pluginLogsModal');
        if (modal) {
            var obs = new MutationObserver(function(muts) {
                muts.forEach(function(m) {
                    if (m.attributeName === 'class' && modal.classList.contains('active')) {
                        setTimeout(function() {
                            var q = $('logsFilterQuery');
                            if (q) q.focus();
                        }, 100);
                    }
                });
            });
            obs.observe(modal, { attributes: true, attributeFilter: ['class'] });
        }
    });
})();
</script>'''})

    # ============================================================
    # Стили
    # ============================================================
    hooks['ui_styles'].append({'html': '''<style>
.logs-filter-group { display:flex; flex-direction:column; gap:4px; }
.logs-filter-label {
    font-size:0.7rem; color:var(--meta-color);
    text-transform:uppercase; letter-spacing:0.5px; font-weight:700;
}
.logs-actions-list {
    max-height:180px; overflow-y:auto;
    padding:6px 8px; background:var(--input-bg);
    border:1px solid var(--card-border); border-radius:8px;
    display:flex; flex-direction:column; gap:2px;
}
.logs-action-item {
    display:flex; align-items:center; gap:6px;
    font-size:0.75rem; color:var(--text-color);
    padding:2px 4px; border-radius:5px; cursor:pointer;
}
.logs-action-item:hover { background:var(--filter-btn-active-bg); }
.logs-action-item input[type="checkbox"] {
    margin:0; cursor:pointer; accent-color:var(--accent);
}
.logs-action-dot {
    width:8px; height:8px; border-radius:50%;
    flex-shrink:0; box-shadow:0 0 4px currentColor;
}
.logs-action-label { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

.logs-mini-btn {
    background:transparent; border:1px solid var(--filter-btn-border);
    color:var(--filter-btn-color); font-size:0.65rem;
    padding:1px 6px; border-radius:5px; cursor:pointer;
    margin-left:2px;
}
.logs-mini-btn:hover {
    background:var(--filter-btn-active-bg);
    color:var(--filter-btn-active-color);
    border-color:var(--filter-btn-active-color);
}

.logs-stats-box {
    padding:10px; background:var(--input-bg);
    border:1px solid var(--card-border); border-radius:10px;
    font-size:0.75rem;
}
.logs-stat-row {
    display:flex; justify-content:space-between; gap:8px;
    padding:2px 0; align-items:center;
}
.logs-stat-row b { color:var(--accent); font-variant-numeric:tabular-nums; }
.logs-stat-group-label {
    font-size:0.65rem; color:var(--meta-color);
    text-transform:uppercase; letter-spacing:0.5px;
    font-weight:700; margin-bottom:4px;
}

.logs-list {
    display:flex; flex-direction:column; gap:4px;
    max-height:55vh; overflow-y:auto;
    padding:6px; background:rgba(0,0,0,0.1);
    border:1px solid var(--card-border); border-radius:10px;
    min-height:200px;
}

.logs-item {
    display:flex; align-items:center; gap:8px;
    padding:6px 10px; border-radius:8px;
    background:var(--input-bg); border:1px solid var(--card-border);
    font-size:0.8rem; min-width:0;
}
.logs-item[data-clickable="1"] { cursor:pointer; transition:background 0.15s; }
.logs-item[data-clickable="1"]:hover {
    background:var(--filter-btn-active-bg);
    border-color:var(--filter-btn-active-color);
}

.logs-item-ts {
    color:var(--meta-color); font-size:0.7rem;
    white-space:nowrap; font-family:monospace;
}
.logs-item-action {
    display:inline-flex; align-items:center;
    padding:2px 8px; border-radius:12px;
    font-size:0.68rem; font-weight:700;
    white-space:nowrap; border:1px solid transparent;
}
.logs-item-id {
    color:var(--meta-color); font-size:0.7rem;
    font-family:monospace; white-space:nowrap;
}
.logs-item-name {
    color:var(--text-color); font-weight:600;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    flex:0 1 auto; max-width:200px;
}
.logs-item-summary {
    color:var(--desc-color); font-size:0.72rem;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
    flex:1; min-width:0;
}
.logs-item-chevron {
    color:var(--meta-color); font-size:0.7rem;
    flex-shrink:0;
}

.logs-detail-row {
    display:flex; gap:10px; padding:4px 0;
    align-items:flex-start;
}
.logs-detail-key {
    flex:0 0 130px; color:var(--meta-color);
    font-size:0.78rem; font-weight:700;
}
.logs-detail-row > span:nth-child(2) {
    flex:1; min-width:0; word-break:break-word;
}

.logs-diff-row {
    display:grid; grid-template-columns: 120px 1fr auto 1fr;
    gap:8px; padding:6px 0; align-items:center;
    font-size:0.8rem;
    border-bottom:1px dashed var(--card-border);
}
.logs-diff-row:last-child { border-bottom:none; }
.logs-diff-field {
    color:var(--meta-color); font-weight:700; font-size:0.75rem;
}
.logs-diff-from {
    color:#e74c3c; background:rgba(231,76,60,0.1);
    padding:3px 8px; border-radius:6px;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.logs-diff-to {
    color:#2ecc71; background:rgba(46,204,113,0.1);
    padding:3px 8px; border-radius:6px;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.logs-diff-arrow {
    color:var(--meta-color); font-size:0.9rem;
}

@media (max-width: 700px) {
    #pluginLogsModal .modal-content { padding: 16px; }
    #pluginLogsModal > .modal-content > div:first-child { flex-direction: column; }
    #pluginLogsModal .logs-list { max-height: 40vh; }
    .logs-diff-row { grid-template-columns: 1fr; gap:4px; }
    .logs-diff-arrow { display:none; }
}
</style>'''})