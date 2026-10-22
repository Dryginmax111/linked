"""
Корзина: мягкое удаление, восстановление, автоочистка.

UI:
  - Кнопка «Корзина» в сайдбаре (со счётчиком)
  - Модалка со списком удалённых
  - Кнопки «Восстановить» и «Удалить навсегда»
  - Автоочистка записей старше 30 дней
"""
from datetime import datetime, timedelta

__version__ = "2.0"
__description__ = "Корзина с восстановлением и автоочисткой (30 дней)"

TRASH_KEEP_DAYS = 30
_last_purge = [0.0]
PURGE_INTERVAL = 3600


def register(hooks, app, config, core):
    from flask import jsonify

    # ============================================================
    # API
    # ============================================================

    @app.route('/get_trash')
    def get_trash():
        wb = core.read_workbook(); ws = wb.active
        trash = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            d = core.safe_str(row[10]) if len(row) > 10 else ''
            if not d:
                continue
            trash.append({
                'id': row[0],
                'name': core.safe_str(row[1]),
                'link': core.safe_str(row[2]),
                'category': core.safe_str(row[4]),
                'deleted_at': core.format_datetime(d),
                'deleted_at_iso': d
            })
        trash.sort(key=lambda x: x['deleted_at_iso'], reverse=True)
        return jsonify(trash)

    @app.route('/restore_from_trash/<int:rid>', methods=['POST'])
    def restore_from_trash_route(rid):
        if not core.restore_from_trash(rid):
            return jsonify({'success': False, 'error': 'Не в корзине'}), 404
        rec = core.get_record_by_id(rid)
        name = rec['name_del'] if rec else ''
        core.log_action('restore_from_trash', rid, name)
        core.run_hook('on_restore', record_id=rid, name=name)
        return jsonify({'success': True})

    @app.route('/purge_trash', methods=['POST'])
    def purge_trash():
        wb = core.read_workbook(); ws = wb.active
        to_delete = []
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            d = core.safe_str(row[10]) if len(row) > 10 else ''
            if d and core.is_valid_datetime_str(d):
                to_delete.append(idx)
        for idx in reversed(to_delete):
            ws.delete_rows(idx)
        if to_delete:
            core.atomic_save_workbook(wb)
            core.invalidate_cache()
            core.log_action('purge_trash', None, '', {'count': len(to_delete)})
        return jsonify({'success': True, 'count': len(to_delete)})

    @app.route('/empty_record/<int:rid>', methods=['POST'])
    def empty_record(rid):
        core.hard_delete_record(rid)
        core.log_action('empty_record', rid)
        return jsonify({'success': True})

    @app.route('/trash_auto_purge', methods=['POST'])
    def auto_purge():
        import time
        now = time.time()
        if now - _last_purge[0] < PURGE_INTERVAL:
            return jsonify({'success': True, 'skipped': True})
        _last_purge[0] = now
        wb = core.read_workbook(); ws = wb.active
        cutoff = datetime.now() - timedelta(days=TRASH_KEEP_DAYS)
        to_delete = []
        for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            d = core.safe_str(row[10]) if len(row) > 10 else ''
            if d and core.is_valid_datetime_str(d):
                try:
                    if datetime.strptime(d, '%Y-%m-%d %H:%M:%S') < cutoff:
                        to_delete.append(idx)
                except Exception:
                    pass
        for idx in reversed(to_delete):
            ws.delete_rows(idx)
        if to_delete:
            core.atomic_save_workbook(wb)
            core.invalidate_cache()
            core.log_action('trash_auto_purge', None, '', {'count': len(to_delete)})
        return jsonify({'success': True, 'count': len(to_delete)})

    # ============================================================
    # UI: кнопка в сайдбаре
    # ============================================================
    hooks['ui_sidebar'].append({
        'id': 'showTrashBtn',
        'icon': '🗑',
        'label': 'Корзина',
        'action': 'openModal',
        'modal_id': 'pluginTrashModal',
    })

    # ============================================================
    # UI: модалка корзины
    # ============================================================
    hooks['ui_modals'].append({
        'id': 'pluginTrashModal',
        'title': '🗑 Корзина',
        'width': 'wide',
        'html': '''
<p style="color:var(--meta-color); font-size:0.85rem; margin-bottom:12px;">
    Удалённые записи хранятся 30 дней. После этого они удаляются навсегда.
</p>
<div class="trash-list" id="pluginTrashList">
    <p style="color:var(--meta-color); text-align:center; padding:20px 0;">Загрузка...</p>
</div>
<div class="modal-actions">
    <button type="button" class="btn btn-secondary" id="pluginPurgeTrashBtn" style="color:#e74c3c;">Очистить всё</button>
    <button type="button" class="btn btn-secondary" onclick="closePluginModal('pluginTrashModal')">Закрыть</button>
</div>
'''
    })

    # ============================================================
    # UI: скрипт
    # ============================================================
    hooks['ui_scripts'].append({'html': '''<script>
(function() {
    function escHtml(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    /* Загрузка и отрисовка списка корзины */
    function loadTrashList() {
        const list = document.getElementById('pluginTrashList');
        if (!list) return;
        list.innerHTML = '<p style="color:var(--meta-color); text-align:center; padding:20px 0;">Загрузка...</p>';
        fetch('/get_trash')
            .then(function(r) { return r.json(); })
            .then(function(items) {
                if (!items.length) {
                    list.innerHTML = '<p style="color:var(--meta-color); text-align:center; padding:20px 0;">Корзина пуста</p>';
                    updateTrashBadgeCount(0);
                    return;
                }
                let html = '';
                items.forEach(function(it) {
                    html += '<div class="trash-item" data-id="' + it.id + '">'
                        + '<div class="trash-item-info">'
                        +   '<div class="trash-item-name">' + escHtml(it.name) + '</div>'
                        +   '<div class="trash-item-link">' + escHtml(it.link) + '</div>'
                        +   '<div class="trash-item-date">Удалено: ' + escHtml(it.deleted_at) + '</div>'
                        + '</div>'
                        + '<div class="trash-item-actions">'
                        +   '<button type="button" class="restore-btn" data-id="' + it.id + '">↩ Восстановить</button>'
                        +   '<button type="button" class="purge-btn" data-id="' + it.id + '">✖ Удалить навсегда</button>'
                        + '</div>'
                        + '</div>';
                });
                list.innerHTML = html;

                list.querySelectorAll('.restore-btn').forEach(function(b) {
                    b.addEventListener('click', function() {
                        const id = this.getAttribute('data-id');
                        fetch('/restore_from_trash/' + id, { method: 'POST' })
                            .then(function(r) { return r.json(); })
                            .then(function(d) {
                                if (d.success) {
                                    if (typeof showNotification === 'function')
                                        showNotification('✅ Восстановлено', 'success');
                                    loadTrashList();
                                    setTimeout(function() { location.reload(); }, 700);
                                } else {
                                    if (typeof showNotification === 'function')
                                        showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                                }
                            })
                            .catch(function() {
                                if (typeof showNotification === 'function')
                                    showNotification('❌ Ошибка сети', 'error');
                            });
                    });
                });

                list.querySelectorAll('.purge-btn').forEach(function(b) {
                    b.addEventListener('click', function() {
                        const id = this.getAttribute('data-id');
                        if (typeof showConfirm !== 'function') {
                            if (!confirm('Удалить навсегда?')) return;
                            fetch('/empty_record/' + id, { method: 'POST' }).then(function() {
                                loadTrashList();
                            });
                            return;
                        }
                        showConfirm('🗑 Удалить навсегда',
                            'Запись будет удалена безвозвратно.',
                            'Удалить',
                            function() {
                                fetch('/empty_record/' + id, { method: 'POST' })
                                    .then(function() {
                                        if (typeof showNotification === 'function')
                                            showNotification('✅ Удалено', 'success');
                                        loadTrashList();
                                    });
                            });
                    });
                });

                updateTrashBadgeCount(items.length);
            })
            .catch(function() {
                list.innerHTML = '<p style="color:#e74c3c; text-align:center;">Ошибка загрузки</p>';
            });
    }

    /* Очистить всё */
    document.addEventListener('DOMContentLoaded', function() {
        const purgeBtn = document.getElementById('pluginPurgeTrashBtn');
        if (purgeBtn) {
            purgeBtn.addEventListener('click', function() {
                if (typeof showConfirm !== 'function') {
                    if (!confirm('Очистить корзину? Все записи будут удалены навсегда.')) return;
                    fetch('/purge_trash', { method: 'POST' }).then(function(r) { return r.json(); })
                        .then(function() { loadTrashList(); });
                    return;
                }
                showConfirm('🗑 Очистить корзину',
                    'Все записи из корзины будут удалены навсегда.',
                    'Очистить',
                    function() {
                        fetch('/purge_trash', { method: 'POST' })
                            .then(function(r) { return r.json(); })
                            .then(function(d) {
                                if (typeof showNotification === 'function')
                                    showNotification('✅ Удалено: ' + d.count, 'success');
                                loadTrashList();
                            });
                    });
            });
        }

        /* Открытие модалки — подгружаем список */
        const trashBtn = document.querySelector('[data-plugin-modal="pluginTrashModal"]');
        if (trashBtn) {
            trashBtn.addEventListener('click', function() {
                setTimeout(loadTrashList, 30);
            });
        }

        /* Инициализация бейджа при загрузке страницы */
        updateTrashBadgeCount(null);

        /* Обновляем бейдж после удаления (клик по кнопке удаления на ссылке) */
        document.body.addEventListener('click', function(e) {
            const delBtn = e.target.closest('.delete-btn');
            if (delBtn) {
                setTimeout(function() { updateTrashBadgeCount(null); }, 800);
                return;
            }
            const undoBtn = e.target.closest('#undoToastBtn');
            if (undoBtn) {
                setTimeout(function() { updateTrashBadgeCount(null); }, 500);
            }
        }, true);

        /* Ctrl+Z — отмена удаления — обновит бейдж через 500 мс */
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
                setTimeout(function() { updateTrashBadgeCount(null); }, 700);
            }
        });
    });

    /* Счётчик на кнопке корзины */
    function updateTrashBadgeCount(count) {
        const btn = document.querySelector('[data-plugin-modal="pluginTrashModal"]');
        if (!btn) return;
        if (count === null) {
            fetch('/get_trash').then(function(r) { return r.json(); })
                .then(function(items) { setBadge(btn, items.length); })
                .catch(function() {});
        } else {
            setBadge(btn, count);
        }
    }
    function setBadge(btn, n) {
        let badge = btn.querySelector('.sidebar-badge');
        if (n > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'sidebar-badge';
                btn.appendChild(badge);
            }
            badge.textContent = n;
        } else if (badge) {
            badge.remove();
        }
    }

    /* Автоочистка при старте (раз в час на сервере) */
    setTimeout(function() {
        var csrf = '';
        var meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) csrf = meta.getAttribute('content') || '';
        if (!csrf && window.REESTR_CSRF) csrf = window.REESTR_CSRF;
        fetch('/trash_auto_purge', { method: 'POST' }).catch(function() {});
    }, 5000);
})();
</script>'''})
