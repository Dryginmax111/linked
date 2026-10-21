"""Авто-теги по домену. Настраиваемые правила."""
import re
from urllib.parse import urlparse

__version__ = "1.0"
__description__ = "Авто-теги по домену ссылки"

DEFAULT_RULES = {
    'github.com': ['github', 'code'],
    'gitlab.com': ['gitlab', 'code'],
    'bitbucket.org': ['bitbucket', 'code'],
    'stackoverflow.com': ['stackoverflow', 'qa'],
    'stackexchange.com': ['stackexchange', 'qa'],
    'docs.google.com': ['google', 'docs'],
    'drive.google.com': ['google', 'drive'],
    'mail.google.com': ['google', 'mail'],
    'youtube.com': ['youtube', 'video'],
    'youtu.be': ['youtube', 'video'],
    'reddit.com': ['reddit', 'social'],
    'twitter.com': ['twitter', 'social'],
    'x.com': ['twitter', 'social'],
    'habr.com': ['habr', 'article'],
    'medium.com': ['medium', 'article'],
    'wikipedia.org': ['wiki'],
    'notion.so': ['notion', 'docs'],
    'figma.com': ['figma', 'design'],
    'trello.com': ['trello', 'tasks'],
    'jira.atlassian.com': ['jira', 'tasks'],
    'confluence.atlassian.com': ['confluence', 'docs'],
    'atlassian.net': ['atlassian'],
    'pypi.org': ['pypi', 'python'],
    'npmjs.com': ['npm', 'js'],
    'docker.com': ['docker'],
    'hub.docker.com': ['docker'],
    'localhost': ['local'],
    '127.0.0.1': ['local'],
}

_TAG_CLEAN_RE = re.compile(r'[^a-zA-Z0-9_\-]+')


def _sanitize_rules(rules):
    if not isinstance(rules, dict):
        return {}
    out = {}
    for dom, tags in list(rules.items())[:200]:
        dom = str(dom).strip().lower()
        if not dom or len(dom) > 200:
            continue
        if not isinstance(tags, list):
            continue
        clean_tags = []
        for t in tags[:20]:
            t = _TAG_CLEAN_RE.sub('', str(t).strip())
            if t and len(t) <= 40 and t not in clean_tags:
                clean_tags.append(t)
        if clean_tags:
            out[dom] = clean_tags
    return out


def _extract_host(url):
    if not url:
        return ''
    url = url.strip()
    if url.startswith('\\\\') or url.startswith('//'):
        # сетевая шара
        return ''
    try:
        p = urlparse(url if '://' in url else 'http://' + url)
        host = (p.netloc or '').split(':')[0].lower()
        if host.startswith('www.'):
            host = host[4:]
        return host
    except Exception:
        return ''


def _suggest_for_host(host, rules):
    """Возвращает список тегов по хосту и его поддоменам."""
    if not host:
        return []
    tags = []
    # точное совпадение
    if host in rules:
        tags.extend(rules[host])
    # поддомены (например docs.google.com → google.com если есть правило)
    parts = host.split('.')
    for i in range(1, len(parts) - 1):
        parent = '.'.join(parts[i:])
        if parent in rules and parent != host:
            tags.extend(rules[parent])
    # убираем дубли с сохранением порядка
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def register(hooks, app, config, core):
    from flask import request, jsonify

    # Первая инициализация
    stored = config.get('rules')
    if not isinstance(stored, dict) or not stored:
        config.set('rules', dict(DEFAULT_RULES))

    @app.route('/api/autotag/suggest')
    def api_autotag_suggest():
        url = request.args.get('url', '').strip()
        if not url:
            return jsonify({'tags': []})
        rules = config.get('rules') or DEFAULT_RULES
        host = _extract_host(url)
        tags = _suggest_for_host(host, rules)
        return jsonify({'host': host, 'tags': tags})

    @app.route('/api/autotag/rules')
    def api_autotag_rules():
        rules = config.get('rules') or DEFAULT_RULES
        return jsonify({'rules': rules})

    @app.route('/api/autotag/save', methods=['POST'])
    def api_autotag_save():
        data = request.get_json() or {}
        rules = _sanitize_rules(data.get('rules') or {})
        if not rules:
            return jsonify({'success': False, 'error': 'Пустой список правил'}), 400
        config.set('rules', rules)
        return jsonify({'success': True, 'rules': rules})

    @app.route('/api/autotag/reset', methods=['POST'])
    def api_autotag_reset():
        config.set('rules', dict(DEFAULT_RULES))
        return jsonify({'success': True, 'rules': dict(DEFAULT_RULES)})

    # -------- UI --------

    hooks['ui_tools_tab'].append({
        'id': 'autotag_rules_btn', 'icon': '🏷️',
        'label': 'Правила авто-тегов', 'action': 'js',
        'js': 'window.__autotagOpenEditor && window.__autotagOpenEditor()',
    })

    hooks['ui_modals'].append({
        'id': 'autotagRulesModal',
        'title': '🏷️ Правила авто-тегов',
        'width': 'wide',
        'html': '''
<p style="color:var(--meta-color); font-size:0.85rem; margin-bottom:12px; line-height:1.5;">
    При вводе ссылки в модалке «Добавить» система предложит добавить теги,
    соответствующие домену. Например <code>github.com</code> → <code>github, code</code>.
    Правила применяются к домену и его поддоменам (для <code>docs.google.com</code>
    подойдёт правило от <code>google.com</code>).
</p>
<div id="autotagRulesList" style="display:flex; flex-direction:column; gap:6px; max-height:400px; overflow-y:auto; padding:6px; background:var(--input-bg); border:1px solid var(--card-border); border-radius:10px;"></div>
<div style="display:flex; gap:8px; flex-wrap:wrap; margin-top:10px;">
    <button type="button" class="data-btn" id="autotagAddRuleBtn" style="flex:1; justify-content:center;">
        <span class="data-icon">➕</span><span>Добавить правило</span>
    </button>
    <button type="button" class="data-btn" id="autotagResetRulesBtn" style="flex:0 0 auto;">
        <span class="data-icon">↺</span><span>Сбросить</span>
    </button>
</div>
<div class="modal-actions" style="margin-top:14px;">
    <button type="button" class="btn btn-secondary" onclick="closePluginModal('autotagRulesModal')">Закрыть</button>
    <button type="button" class="btn" id="autotagSaveRulesBtn">💾 Сохранить</button>
</div>
'''
    })

    hooks['ui_scripts'].append({'html': '''<script>
(function() {
    var _rules = {};

    function getCsrf() {
        var m = document.querySelector('meta[name="csrf-token"]');
        return m ? m.getAttribute('content') : '';
    }
    function esc(s) {
        return String(s || '').replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
        });
    }

    function renderRules() {
        var list = document.getElementById('autotagRulesList');
        if (!list) return;
        var entries = Object.keys(_rules).sort();
        if (!entries.length) {
            list.innerHTML = '<p style="color:var(--meta-color); text-align:center; padding:14px 0;">Нет правил</p>';
            return;
        }
        var html = '';
        entries.forEach(function(dom) {
            var tags = (_rules[dom] || []).join(', ');
            html += '<div class="autotag-row" data-domain="' + esc(dom) + '" style="display:grid; grid-template-columns:1fr 2fr auto; gap:6px; align-items:center; padding:6px; background:rgba(255,255,255,0.02); border:1px solid var(--card-border); border-radius:8px;">'
                + '<input type="text" class="autotag-domain" value="' + esc(dom) + '" style="font-family:monospace; font-size:0.85rem;">'
                + '<input type="text" class="autotag-tags" value="' + esc(tags) + '" placeholder="tag1, tag2">'
                + '<button type="button" class="autotag-remove" style="background:transparent; border:1px solid var(--filter-btn-border); color:#e74c3c; width:32px; height:32px; border-radius:8px; cursor:pointer;">✖</button>'
                + '</div>';
        });
        list.innerHTML = html;
        list.querySelectorAll('.autotag-row').forEach(function(row) {
            var dom = row.getAttribute('data-domain');
            var domInp = row.querySelector('.autotag-domain');
            var tagsInp = row.querySelector('.autotag-tags');
            var rmBtn = row.querySelector('.autotag-remove');
            domInp.addEventListener('input', function() {
                var newDom = this.value.trim().toLowerCase();
                if (!newDom || newDom === dom) return;
                if (_rules[newDom]) return; // не перезаписываем
                _rules[newDom] = _rules[dom];
                delete _rules[dom];
                dom = newDom;
                row.setAttribute('data-domain', newDom);
            });
            tagsInp.addEventListener('input', function() {
                _rules[dom] = this.value.split(',').map(function(x){return x.trim();}).filter(Boolean);
            });
            rmBtn.addEventListener('click', function() {
                delete _rules[dom];
                renderRules();
            });
        });
    }

    window.__autotagOpenEditor = function() {
        fetch('/api/autotag/rules').then(function(r) { return r.json(); }).then(function(d) {
            _rules = Object.assign({}, d.rules || {});
            renderRules();
            if (typeof openPluginModal === 'function') openPluginModal('autotagRulesModal');
        });
    };

    document.addEventListener('DOMContentLoaded', function() {
        var addBtn = document.getElementById('autotagAddRuleBtn');
        if (addBtn) addBtn.addEventListener('click', function() {
            var dom = 'example.com';
            var n = 1;
            while (_rules[dom]) { dom = 'example' + (++n) + '.com'; }
            _rules[dom] = ['tag'];
            renderRules();
        });
        var resetBtn = document.getElementById('autotagResetRulesBtn');
        if (resetBtn) resetBtn.addEventListener('click', function() {
            if (!confirm('Сбросить правила к стандартным?')) return;
            fetch('/api/autotag/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf()},
                body: '{}'
            }).then(function(r) { return r.json(); }).then(function(d) {
                _rules = Object.assign({}, d.rules || {});
                renderRules();
            });
        });
        var saveBtn = document.getElementById('autotagSaveRulesBtn');
        if (saveBtn) saveBtn.addEventListener('click', function() {
            fetch('/api/autotag/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCsrf()},
                body: JSON.stringify({rules: _rules})
            }).then(function(r) { return r.json(); }).then(function(d) {
                if (d.success) {
                    if (typeof showNotification === 'function') showNotification('✅ Правила сохранены', 'success');
                    if (typeof closePluginModal === 'function') closePluginModal('autotagRulesModal');
                } else {
                    if (typeof showNotification === 'function') showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            });
        });
    });

    // ---------- Автоподсказка тегов при вводе ссылки ----------
    var _suggestTimer = null;
    var _shownTags = {};

    function showSuggestPopup(tags, host) {
        var old = document.getElementById('autotagSuggest');
        if (old) old.remove();
        if (!tags || !tags.length) return;
        var linkInput = document.getElementById('link');
        if (!linkInput) return;
        var rect = linkInput.getBoundingClientRect();
        var popup = document.createElement('div');
        popup.id = 'autotagSuggest';
        popup.style.cssText = 'position:fixed; z-index:3000; background:var(--modal-bg); border:1px solid var(--modal-border); border-radius:10px; box-shadow:0 8px 24px rgba(0,0,0,0.4); padding:8px 10px; font-size:0.85rem; max-width:min(400px, 90vw);';
        popup.style.left = rect.left + 'px';
        popup.style.top = (rect.bottom + 6) + 'px';

        var html = '<div style="color:var(--meta-color); font-size:0.72rem; margin-bottom:6px;">'
            + '💡 Авто-теги для <b>' + esc(host) + '</b>:</div>'
            + '<div style="display:flex; gap:6px; flex-wrap:wrap; margin-bottom:6px;">';
        tags.forEach(function(t) {
            html += '<span data-tag="' + esc(t) + '" class="autotag-tag-chip" style="cursor:pointer; padding:3px 10px; border-radius:12px; background:var(--tag-bg); color:var(--tag-color); border:1px solid var(--tag-bg);">#' + esc(t) + '</span>';
        });
        html += '</div>';
        html += '<div style="display:flex; gap:6px; margin-top:6px;">'
            + '<button type="button" id="autotagAddAll" style="background:var(--btn-gradient); color:var(--btn-text); border:none; padding:4px 12px; border-radius:8px; cursor:pointer; font-size:0.78rem; font-weight:600;">Добавить все</button>'
            + '<button type="button" id="autotagClose" style="background:transparent; border:1px solid var(--filter-btn-border); color:var(--filter-btn-color); padding:4px 12px; border-radius:8px; cursor:pointer; font-size:0.78rem;">Скрыть</button>'
            + '</div>';
        popup.innerHTML = html;
        document.body.appendChild(popup);

        function addTag(tag) {
            var wrapper = document.getElementById('tagsAddWrapper');
            var hidden = document.getElementById('tags_add');
            if (!wrapper || !hidden) return;
            var cur = hidden.value ? hidden.value.split(',').map(function(x){return x.trim();}).filter(Boolean) : [];
            if (cur.indexOf(tag) !== -1) return;
            cur.push(tag);
            hidden.value = cur.join(',');
            // добавим чип
            var input = document.getElementById('tagsAddInput');
            var chip = document.createElement('span');
            chip.className = 'tags-chip';
            chip.innerHTML = '#' + esc(tag) + '<span class="remove-tag" data-tag="' + esc(tag) + '">×</span>';
            if (input) wrapper.insertBefore(chip, input);
            else wrapper.appendChild(chip);
        }

        popup.querySelectorAll('.autotag-tag-chip').forEach(function(chip) {
            chip.addEventListener('click', function() {
                var tag = this.getAttribute('data-tag');
                addTag(tag);
                this.style.opacity = '0.35';
                this.style.pointerEvents = 'none';
            });
        });
        var addAll = popup.querySelector('#autotagAddAll');
        if (addAll) addAll.addEventListener('click', function() {
            tags.forEach(addTag);
            popup.remove();
        });
        var closeBtn = popup.querySelector('#autotagClose');
        if (closeBtn) closeBtn.addEventListener('click', function() { popup.remove(); });
    }

    function hideSuggestPopup() {
        var el = document.getElementById('autotagSuggest');
        if (el) el.remove();
    }

    function attachAutotag() {
        var linkInput = document.getElementById('link');
        if (!linkInput || linkInput.dataset.autotagBound === '1') return;
        linkInput.dataset.autotagBound = '1';
        linkInput.addEventListener('input', function() {
            clearTimeout(_suggestTimer);
            var val = this.value.trim();
            if (val.length < 5) { hideSuggestPopup(); return; }
            _suggestTimer = setTimeout(function() {
                fetch('/api/autotag/suggest?url=' + encodeURIComponent(val))
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.tags && d.tags.length) showSuggestPopup(d.tags, d.host || '');
                        else hideSuggestPopup();
                    }).catch(function() { hideSuggestPopup(); });
            }, 500);
        });
        linkInput.addEventListener('blur', function() {
            setTimeout(hideSuggestPopup, 300);
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        var iv = setInterval(function() {
            if (document.getElementById('link')) {
                attachAutotag();
                clearInterval(iv);
            }
        }, 300);
        setTimeout(function() { clearInterval(iv); }, 10000);
    });

    document.addEventListener('click', function(e) {
        var btn = e.target.closest('#openAddModal');
        if (btn) setTimeout(attachAutotag, 50);
    });
})();
</script>'''})