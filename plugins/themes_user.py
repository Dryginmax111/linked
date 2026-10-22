"""Редактор пользовательских тем с загрузкой и применением."""
from pathlib import Path

__version__ = "3.0"
__description__ = "Редактор пользовательских тем с цветовой иконкой"

_THEMES_FILE = None


def register(hooks, app, config, core):
    global _THEMES_FILE
    _THEMES_FILE = str(Path(core.BASE_DIR) / 'custom_themes.json')

    hooks['ui_appearance_tab'].append({
        'id': 'themes_user_block',
        'html': '''
<div class="appearance-title" style="margin-top:10px;">
    <span>🎨</span><span>Кастомные темы</span>
</div>
<div id="customThemesList" class="custom-themes-list">
    <div style="color:var(--meta-color); font-size:0.72rem; font-style:italic;">
        Нет кастомных тем
    </div>
</div>
<button class="data-btn" id="addCustomThemeBtn"
        style="justify-content:center; margin-top:6px; font-size:0.75rem;">
    <span class="data-icon">➕</span><span>Добавить тему</span>
</button>
'''
    })

    hooks['ui_modals'].append({
        'id': 'pluginThemeEditorModal',
        'title': '🎨 Редактор темы',
        'width': 'wide',
        'html': '''
<div class="form-group">
    <label for="pluginThemeId">ID (латиница, без пробелов)</label>
    <input type="text" id="pluginThemeId" placeholder="my_theme" maxlength="32" style="font-family:monospace;">
</div>
<div class="form-group">
    <label for="pluginThemeName">Название</label>
    <input type="text" id="pluginThemeName" maxlength="60">
</div>

<div class="form-group">
    <label>Иконка-кружок</label>
    <div style="display:flex; align-items:flex-start; gap:14px; padding:12px 14px; background:var(--input-bg); border:1px solid var(--input-border); border-radius:10px;">
        <div id="pluginThemeDotPreview"
             style="width:44px; height:44px; border-radius:50%; flex-shrink:0;
                    border:2px solid var(--card-border);
                    background:linear-gradient(135deg, #1a1f35, #5b8def, #8b7de8);"></div>
        <div style="flex:1; min-width:0; display:flex; flex-direction:column; gap:8px;">

            <div style="display:flex; flex-wrap:wrap; gap:10px; align-items:center;">
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <label for="pluginThemeDotColor1" style="font-size:0.75rem; color:var(--meta-color);">Цвет 1</label>
                    <input type="color" id="pluginThemeDotColor1" value="#1a1f35"
                           style="width:38px; height:26px; padding:1px; border:1px solid var(--input-border); border-radius:6px; cursor:pointer; background:transparent;">
                </span>
                <span style="display:inline-flex; align-items:center; gap:6px;">
                    <label for="pluginThemeDotColor2" style="font-size:0.75rem; color:var(--meta-color);">Цвет 2</label>
                    <input type="color" id="pluginThemeDotColor2" value="#5b8def"
                           style="width:38px; height:26px; padding:1px; border:1px solid var(--input-border); border-radius:6px; cursor:pointer; background:transparent;">
                </span>
                <span id="pluginThemeDotColor3Wrap" style="display:inline-flex; align-items:center; gap:6px;">
                    <label for="pluginThemeDotColor3" style="font-size:0.75rem; color:var(--meta-color);">Цвет 3</label>
                    <input type="color" id="pluginThemeDotColor3" value="#8b7de8"
                           style="width:38px; height:26px; padding:1px; border:1px solid var(--input-border); border-radius:6px; cursor:pointer; background:transparent;">
                </span>
                <button type="button" id="pluginThemeDotToggleThirdBtn"
                        title="Добавить / убрать третий цвет"
                        style="background:transparent; border:1px solid var(--filter-btn-border); color:var(--filter-btn-color);
                               padding:3px 10px; border-radius:6px; cursor:pointer; font-size:0.78rem;">
                    − 3-й цвет
                </button>
            </div>

            <input type="text" id="pluginThemeDot"
                   placeholder="linear-gradient(135deg, #111, #333)"
                   style="font-family:monospace; font-size:0.78rem; padding:5px 8px;
                          border:1px solid var(--input-border); border-radius:6px;
                          background:var(--input-bg); color:var(--text-color);
                          outline:none; opacity:0.8;">

            <div style="color:var(--meta-color); font-size:0.7rem; font-style:italic; line-height:1.4;">
                Выберите 2 или 3 цвета — кружок соберётся автоматически.
                Поле ниже — для ручного CSS, оно обновляется само.
            </div>
        </div>
    </div>
</div>

<div class="form-group">
    <label for="pluginThemeVars">CSS-переменные (JSON)</label>
    <textarea id="pluginThemeVars" class="plugin-editor-code" style="min-height:220px;" spellcheck="false">{
  "--bg-start": "#000000",
  "--text-color": "#ffffff",
  "--accent": "#ff00aa"
}</textarea>
</div>
<div id="pluginThemeStatus" class="plugin-editor-status"></div>
<div class="modal-actions">
    <button type="button" class="btn btn-secondary" onclick="closePluginModal('pluginThemeEditorModal')">Закрыть</button>
    <button type="button" class="btn" id="pluginThemeSaveBtn">💾 Сохранить</button>
</div>
'''
    })

    hooks['ui_scripts'].append({'html': '''<script>
(function() {
    var THEME_ID_RE = /^[a-z][a-z0-9_]{0,31}$/;

    /* ============================================================
       Хелперы для иконки-кружка (color picker -> linear-gradient)
       ============================================================ */
    var DOT_DEFAULT = { c1: '#1a1f35', c2: '#5b8def', c3: '#8b7de8' };
    var dotThirdEnabled = true;

    function _dotNorm(hex) {
        hex = (hex || '').trim();
        if (/^#[0-9a-f]{3}$/i.test(hex)) {
            return '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
        }
        if (/^#[0-9a-f]{6}$/i.test(hex)) return hex.toLowerCase();
        return null;
    }

    function parseDotToColors(dot) {
        var fallback = { c1: DOT_DEFAULT.c1, c2: DOT_DEFAULT.c2, c3: DOT_DEFAULT.c3, hasThird: true };
        if (!dot || typeof dot !== 'string') return fallback;
        var m = dot.match(
            /linear-gradient\\s*\\(\\s*[^,]+,\\s*([^,)]+?)\\s*,\\s*([^,)]+?)(?:\\s*,\\s*([^,)]+?))?\\s*\\)/i
        );
        if (!m) return fallback;
        var c1 = _dotNorm(m[1]) || fallback.c1;
        var c2 = _dotNorm(m[2]) || fallback.c2;
        var c3 = m[3] ? (_dotNorm(m[3]) || fallback.c3) : fallback.c3;
        return { c1: c1, c2: c2, c3: c3, hasThird: !!m[3] };
    }

    function buildDotFromColors() {
        var c1El = document.getElementById('pluginThemeDotColor1');
        var c2El = document.getElementById('pluginThemeDotColor2');
        var c3El = document.getElementById('pluginThemeDotColor3');
        var c1 = (c1El && c1El.value) || DOT_DEFAULT.c1;
        var c2 = (c2El && c2El.value) || DOT_DEFAULT.c2;
        var c3 = (c3El && c3El.value) || DOT_DEFAULT.c3;
        var grad = dotThirdEnabled
            ? 'linear-gradient(135deg, ' + c1 + ', ' + c2 + ', ' + c3 + ')'
            : 'linear-gradient(135deg, ' + c1 + ', ' + c2 + ')';

        var dotInput = document.getElementById('pluginThemeDot');
        if (dotInput) dotInput.value = grad;
        var preview = document.getElementById('pluginThemeDotPreview');
        if (preview) preview.style.background = grad;
        return grad;
    }

    function applyDotToInputs(dotStr) {
        var parsed = parseDotToColors(dotStr);
        var c1El = document.getElementById('pluginThemeDotColor1');
        var c2El = document.getElementById('pluginThemeDotColor2');
        var c3El = document.getElementById('pluginThemeDotColor3');
        if (c1El) c1El.value = parsed.c1;
        if (c2El) c2El.value = parsed.c2;
        if (c3El) c3El.value = parsed.c3;
        dotThirdEnabled = parsed.hasThird;
        updateThirdColorVisibility();
        var preview = document.getElementById('pluginThemeDotPreview');
        if (preview) preview.style.background = dotStr;
    }

    function updateThirdColorVisibility() {
        var wrap = document.getElementById('pluginThemeDotColor3Wrap');
        var btn = document.getElementById('pluginThemeDotToggleThirdBtn');
        if (wrap) wrap.style.display = dotThirdEnabled ? 'inline-flex' : 'none';
        if (btn) btn.textContent = dotThirdEnabled ? '− 3-й цвет' : '+ 3-й цвет';
    }

    function setupDotColorPickers() {
        ['pluginThemeDotColor1', 'pluginThemeDotColor2', 'pluginThemeDotColor3'].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.addEventListener('input', buildDotFromColors);
        });
        var toggleBtn = document.getElementById('pluginThemeDotToggleThirdBtn');
        if (toggleBtn) toggleBtn.addEventListener('click', function() {
            dotThirdEnabled = !dotThirdEnabled;
            updateThirdColorVisibility();
            buildDotFromColors();
        });
        var dotInput = document.getElementById('pluginThemeDot');
        if (dotInput) dotInput.addEventListener('input', function() {
            var v = (this.value || '').trim();
            if (!v) return;
            applyDotToInputs(v);
        });
        updateThirdColorVisibility();
    }
    /* ============================================================ */

    function injectCustomThemes(themes) {
        var styleId = 'custom-themes-style';
        var styleEl = document.getElementById(styleId);
        if (styleEl) styleEl.remove();
        if (!themes || !themes.length) return;
        styleEl = document.createElement('style');
        styleEl.id = styleId;
        var css = '';
        themes.forEach(function(t) {
            var vars = t.vars || {};
            var lines = [];
            Object.keys(vars).forEach(function(k) {
                lines.push('  ' + k + ': ' + vars[k] + ';');
            });
            if (lines.length) {
                css += 'body.theme-' + t.id + ' {\\n' + lines.join('\\n') + '\\n}\\n';
            }
        });
        styleEl.textContent = css;
        document.head.appendChild(styleEl);
    }

    function escHtml(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function renderCustomThemes(themes) {
        var container = document.getElementById('customThemesList');
        if (!container) return;
        if (!themes || !themes.length) {
            container.innerHTML = '<div style="color:var(--meta-color); font-size:0.72rem; font-style:italic;">Нет кастомных тем</div>';
            return;
        }
        var html = '';
        themes.forEach(function(t) {
            var dotStyle = t.dot || 'linear-gradient(135deg, #444, #888)';
            html += '<div class="custom-theme-row" data-id="' + escHtml(t.id) + '">'
                + '<span class="custom-theme-dot" style="background:' + escHtml(dotStyle) + '"></span>'
                + '<span class="custom-theme-name">' + escHtml(t.name) + '</span>'
                + '<button class="plugin-action-btn" data-action="edit" title="Редактировать">✏️</button>'
                + '<button class="plugin-action-btn danger" data-action="delete" title="Удалить">🗑</button>'
                + '</div>';
        });
        container.innerHTML = html;
        container.querySelectorAll('.plugin-action-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var row = this.closest('.custom-theme-row');
                var id = row ? row.getAttribute('data-id') : '';
                var action = this.getAttribute('data-action');
                var theme = themes.find(function(t) { return t.id === id; });
                if (action === 'edit') openThemeEditor(theme, false);
                else if (action === 'delete') deleteTheme(id);
            });
        });
    }

    function updateThemeSelector(themes) {
        var selector = document.getElementById('themeSelector');
        if (!selector) return;
        selector.querySelectorAll('.theme-dot[data-custom="1"]').forEach(function(x) { x.remove(); });
        themes.forEach(function(t) {
            var dot = document.createElement('button');
            dot.className = 'theme-dot';
            dot.setAttribute('data-theme', t.id);
            dot.setAttribute('data-custom', '1');
            dot.title = t.name;
            dot.style.background = t.dot || 'linear-gradient(135deg, #444, #888)';
            dot.addEventListener('click', function() {
                if (typeof applyTheme === 'function') applyTheme(t.id);
            });
            selector.appendChild(dot);
        });
    }

    function loadCustomThemes() {
        fetch('/api/custom_themes')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var themes = (data && data.themes) || [];
                injectCustomThemes(themes);
                renderCustomThemes(themes);
                updateThemeSelector(themes);
                // Повторно применить активную тему, чтобы подсветилась иконка
                try {
                    var cur = localStorage.getItem('reestr_theme') || 'dark';
                    if (typeof applyTheme === 'function') applyTheme(cur);
                } catch (e) {}
            })
            .catch(function() {});
    }

    function openThemeEditor(theme, isNew) {
        var idEl = document.getElementById('pluginThemeId');
        var nameEl = document.getElementById('pluginThemeName');
        var dotEl = document.getElementById('pluginThemeDot');
        var varsEl = document.getElementById('pluginThemeVars');
        var stEl = document.getElementById('pluginThemeStatus');
        if (idEl) { idEl.value = (theme && theme.id) || ''; idEl.readOnly = !isNew; }
        if (nameEl) nameEl.value = (theme && theme.name) || '';

        var dotStr = (theme && theme.dot)
            ? theme.dot
            : 'linear-gradient(135deg, ' + DOT_DEFAULT.c1 + ', ' + DOT_DEFAULT.c2 + ', ' + DOT_DEFAULT.c3 + ')';
        if (dotEl) dotEl.value = dotStr;
        applyDotToInputs(dotStr);

        if (varsEl) {
            varsEl.value = theme && theme.vars
                ? JSON.stringify(theme.vars, null, 2)
                : '{\\n  "--bg-start": "#000000",\\n  "--text-color": "#ffffff",\\n  "--accent": "#ff00aa"\\n}';
        }
        if (stEl) { stEl.textContent = ''; stEl.style.color = ''; }
        if (typeof openPluginModal === 'function') openPluginModal('pluginThemeEditorModal');
    }

    function deleteTheme(id) {
        if (typeof showConfirm !== 'function') {
            if (!confirm('Удалить тему ' + id + '?')) return;
            csrfFetch('/api/custom_themes/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id})
            }).then(function() { loadCustomThemes(); });
            return;
        }
        showConfirm('🗑 Удаление темы',
            'Удалить тему <span class="confirm-highlight">' + escHtml(id) + '</span>?',
            '🗑 Удалить',
            function() {
                csrfFetch('/api/custom_themes/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: id})
                }).then(function(r) { return r.json(); }).then(function(res) {
                    if (res.success) {
                        if (typeof showNotification === 'function')
                            showNotification('✅ Тема удалена', 'success');
                        loadCustomThemes();
                    } else {
                        if (typeof showNotification === 'function')
                            showNotification('❌ ' + (res.error || 'Ошибка'), 'error');
                    }
                });
            });
    }

    document.addEventListener('DOMContentLoaded', function() {
        setupDotColorPickers();

        var addBtn = document.getElementById('addCustomThemeBtn');
        if (addBtn) addBtn.addEventListener('click', function() { openThemeEditor(null, true); });

        var saveBtn = document.getElementById('pluginThemeSaveBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', function() {
                var idEl = document.getElementById('pluginThemeId');
                var nameEl = document.getElementById('pluginThemeName');
                var dotEl = document.getElementById('pluginThemeDot');
                var varsEl = document.getElementById('pluginThemeVars');
                var stEl = document.getElementById('pluginThemeStatus');
                var id = ((idEl && idEl.value) || '').toLowerCase().trim();
                var name = ((nameEl && nameEl.value) || '').trim();
                var dot = ((dotEl && dotEl.value) || '').trim();
                var vars;
                try { vars = JSON.parse((varsEl && varsEl.value) || '{}'); }
                catch (e) {
                    if (stEl) { stEl.textContent = '❌ Некорректный JSON'; stEl.style.color = '#e74c3c'; }
                    return;
                }
                if (!name) {
                    if (stEl) { stEl.textContent = '❌ Укажите название'; stEl.style.color = '#e74c3c'; }
                    return;
                }
                if (id && !THEME_ID_RE.test(id)) {
                    if (stEl) { stEl.textContent = '❌ ID: строчная латиница, цифры, _, до 32 символов'; stEl.style.color = '#e74c3c'; }
                    return;
                }
                csrfFetch('/api/custom_themes/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        id: id || 'custom_' + Date.now().toString(36),
                        theme: { name: name, dot: dot, vars: vars }
                    })
                }).then(function(r) { return r.json(); }).then(function(res) {
                    if (res.success) {
                        if (typeof showNotification === 'function')
                            showNotification('✅ Тема сохранена', 'success');
                        if (typeof closePluginModal === 'function')
                            closePluginModal('pluginThemeEditorModal');
                        loadCustomThemes();
                    } else if (stEl) {
                        stEl.textContent = '❌ ' + (res.error || 'Ошибка');
                        stEl.style.color = '#e74c3c';
                    }
                });
            });
        }

        loadCustomThemes();
    });
})();
</script>'''})

