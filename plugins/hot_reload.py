"""UI-кнопка «Перезагрузить плагины» для /api/plugins/reload из ядра."""
__version__ = "2.0"
__description__ = "Кнопка горячей перезагрузки плагинов"


def register(hooks, app, config, core):
    # Роут /api/plugins/reload уже зарегистрирован в app.py.
    # Плагин только добавляет кнопку в UI.

    hooks['ui_scripts'].append({'html': '''<script>
(function() {

    function injectReloadButton() {
        if (document.getElementById('pluginsReloadBtn')) return;
        var container = document.querySelector('#tab-plugins .plugins-manager-list');
        if (!container) return;
        var parent = container.parentElement;
        if (!parent) return;
        var toolbar = parent.querySelector('.plugins-toolbar');
        if (!toolbar) {
            toolbar = document.createElement('div');
            toolbar.className = 'plugins-toolbar';
            toolbar.style.cssText = 'display:flex; gap:8px; margin-bottom:10px;';
            parent.insertBefore(toolbar, container);
        }
        var btn = document.createElement('button');
        btn.className = 'data-btn';
        btn.id = 'pluginsReloadBtn';
        btn.style.cssText = 'flex:1; justify-content:center;';
        btn.innerHTML = '<span class="data-icon">🔁</span><span>Перезагрузить плагины</span>';
        toolbar.appendChild(btn);
    }

    function setupReloadBtn() {
        var btn = document.getElementById('pluginsReloadBtn');
        if (!btn || btn.dataset.hotReloadBound === '1') return;
        btn.dataset.hotReloadBound = '1';
        btn.addEventListener('click', function() {
            if (!confirm('Перезагрузить все плагины? Открытые модалки плагинов будут закрыты.')) return;
            btn.disabled = true;
            var original = btn.innerHTML;
            btn.innerHTML = '<span class="data-icon">⏳</span><span>Загрузка...</span>';

            fetch('/api/plugins/reload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: '{}'
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                btn.disabled = false;
                btn.innerHTML = original;
                if (d.success) {
                    if (typeof showNotification === 'function') {
                        showNotification('✅ Плагинов: ' + d.loaded +
                            (d.errors ? ', ошибок: ' + d.errors : ''), 'success');
                    }
                    if (typeof window.loadPluginsList === 'function') {
                        window.loadPluginsList();
                    }
                    // Если были ошибки — покажем их
                    if (d.error_list && d.error_list.length) {
                        var msg = d.error_list.map(function(e) {
                            return '• ' + e.file + ': ' + e.error;
                        }).join('\\n');
                        alert('Ошибки загрузки плагинов:\\n\\n' + msg);
                    }
                } else {
                    if (typeof showNotification === 'function') {
                        showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                    }
                }
            })
            .catch(function() {
                btn.disabled = false;
                btn.innerHTML = original;
                if (typeof showNotification === 'function') {
                    showNotification('❌ Ошибка сети', 'error');
                }
            });
        });
    }

    // Ищем кнопку при загрузке и при переключении на вкладку
    function trySetup() {
        injectReloadButton();
        setupReloadBtn();
    }

    document.addEventListener('DOMContentLoaded', function() {
        var tries = 0;
        var iv = setInterval(function() {
            tries++;
            trySetup();
            if (document.getElementById('pluginsReloadBtn') || tries > 40) {
                clearInterval(iv);
            }
        }, 250);
    });

    document.addEventListener('click', function(e) {
        var tab = e.target.closest('.settings-tab[data-tab="tab-plugins"]');
        if (tab) setTimeout(trySetup, 100);
    });
})();
</script>'''})
