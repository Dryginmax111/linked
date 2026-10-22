/* ============================================================
   РЕЕСТР ССЫЛОК — JavaScript
   Версия: 4.3 (устойчивая, с оффлайн-подсветкой, без внешних CDN)
   ============================================================ */

(function () {
    'use strict';

    /* ---------- Логирование ошибок ---------- */
    window.addEventListener('error', function (e) {
        var msg = e.message || '?';
        var loc = (e.filename || '') + ':' + (e.lineno || 0) + ':' + (e.colno || 0);
        if (window.__reestrLog) window.__reestrLog('error', '[REESTR-ERROR] ' + msg + ' @ ' + loc, (e.error && e.error.stack) || '');
        try { console.error('[REESTR-ERROR]', msg, '@', loc); } catch (_) {}
    });
    window.addEventListener('unhandledrejection', function (e) {
        var msg = (e.reason && e.reason.message) || String(e.reason) || '?';
        var stack = (e.reason && e.reason.stack) || '';
        if (window.__reestrLog) window.__reestrLog('error', '[REESTR-REJECT] ' + msg, stack);
        try { console.error('[REESTR-REJECT]', e.reason); } catch (_) {}
    });

    /* ============================================================
       КОНСТАНТЫ
       ============================================================ */
    const LS_KEYS = {
        theme: 'reestr_theme', fontSize: 'reestr_fontSize', cols: 'reestr_cols',
        sortField: 'reestr_sortField', sortAsc: 'reestr_sortAsc',
        activeCategory: 'reestr_activeCategory', showFavorites: 'reestr_showFavorites',
        sidebarCollapsed: 'reestr_sidebarCollapsed', searchQuery: 'reestr_searchQuery',
        collapsedCards: 'reestr_collapsedCards', catSort: 'reestr_catSortMode',
        headerAnim: 'reestr_headerAnim', radius: 'reestr_radius',
        sidebarWidth: 'reestr_sidebarWidth', wallpaper: 'reestr_wallpaper',
        meshBg: 'reestr_meshBg', presentation: 'reestr_presentation',
        compact: 'reestr_compact', searchHistory: 'reestr_searchHistory',
        activeTags: 'reestr_activeTags', allCollapsed: 'reestr_allCollapsed',
        settingsTab: 'reestr_settingsTab', cardStrip: 'reestr_cardStrip'
    };

    const DEFAULT_THEME = 'light';   // NEW: дефолт — «Светлая»

    const THEMES = [
        'dark', 'light', 'black', 'cinema', 'neon', 'material',
        'material-glass', 'neumorphism-dark', 'material-you',
        'ios-glass', 'midnight', 'ocean', 'nord',
        'solarized', 'dracula', 'gruvbox'
    ];
    const SECTION_IDS = ['categoriesSection'];

    const DATA = window.REESTR_DATA || {};
    const categoryManualOrder = DATA.category_manual_order || [];
    const categoryColors = DATA.category_colors || {};
    let allTagsFromServer = DATA.all_tags || {};

    const DEFAULT_SHIMMER_1 = '#f5d76e';
    const DEFAULT_SHIMMER_2 = '#f39c12';
    const HEADER_SHIMMER_VARIANTS = ['sweep', 'shine', 'breath', 'wave', 'aurora', 'off'];
    const MESH_STYLES = ['float', 'pulse', 'rotate', 'wave', 'orbit', 'flash', 'aurora'];
    const STRIP_VARIANTS = ['left', 'hover-fill', 'gradient-full', 'gradient-center',
                            'top', 'bottom', 'frame', 'off'];

    let _filterIndex = [];
    let _filterIndexDirty = true;
    let _hideLinkTooltipGlobal = function() {};
    let _scrollRaf = null;
    let _selectedIds = new Set();
    let _lastBulkSnapshot = null;
    let _lastBulkOp = null;

    /* ============================================================
       CSRF
       ============================================================ */
    function getCsrfToken() {
        if (window.REESTR_CSRF) return window.REESTR_CSRF;
        var m = document.querySelector('meta[name="csrf-token"]');
        return m ? m.getAttribute('content') : '';
    }

    function _withCsrf(method, headers, body) {
        var h = Object.assign({}, headers || {});
        var m = (method || 'GET').toUpperCase();
        if (m !== 'GET' && m !== 'HEAD' && m !== 'OPTIONS') {
            h['X-CSRF-Token'] = getCsrfToken();
        }
        return { headers: h, body: body };
    }

    let _csrfRefreshInFlight = null;
    function refreshCsrfToken() {
        if (_csrfRefreshInFlight) return _csrfRefreshInFlight;
        _csrfRefreshInFlight = fetch('/api/csrf-token', { credentials: 'same-origin' })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d && d.token) {
                    window.REESTR_CSRF = d.token;
                    var meta = document.querySelector('meta[name="csrf-token"]');
                    if (meta) meta.setAttribute('content', d.token);
                    return d.token;
                }
                return null;
            })
            .catch(function() { return null; })
            .finally(function() { _csrfRefreshInFlight = null; });
        return _csrfRefreshInFlight;
    }

    function apiFetch(url, options, _retried) {
        options = options || {};
        var method = (options.method || 'GET').toUpperCase();
        var patched = _withCsrf(method, options.headers, options.body);
        options.headers = patched.headers;
        if (patched.body !== undefined) options.body = patched.body;
        if (!options.credentials) options.credentials = 'same-origin';

        return fetch(url, options).then(function(response) {
            if (response.status !== 403 || _retried) return response;
            return response.clone().json().then(function(data) {
                if (!data || data.code !== 'CSRF') return response;
                return refreshCsrfToken().then(function(newToken) {
                    if (!newToken) return response;
                    var retryOptions = Object.assign({}, options);
                    retryOptions.headers = Object.assign({}, options.headers);
                    retryOptions.headers['X-CSRF-Token'] = newToken;
                    return apiFetch(url, retryOptions, true);
                });
            }).catch(function() { return response; });
        });
    }

    /* ============================================================
       Утилиты
       ============================================================ */
    function lsGet(key, def) {
        if (def === undefined) def = null;
        try { var v = localStorage.getItem(key); return v === null ? def : v; } catch (e) { return def; }
    }
    function lsSet(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
    function lsGetJSON(key, def) {
        if (def === undefined) def = null;
        try { var v = localStorage.getItem(key); return v === null ? def : JSON.parse(v); } catch (e) { return def; }
    }
    function lsSetJSON(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {} }
    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function(c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function $(id) { return document.getElementById(id); }

    function copyTextToClipboard(text) {
        return new Promise(function(resolve, reject) {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(resolve).catch(function() {
                    try {
                        var ta = document.createElement('textarea');
                        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                        document.body.appendChild(ta); ta.select();
                        document.execCommand('copy');
                        document.body.removeChild(ta);
                        resolve();
                    } catch (e) { reject(e); }
                });
            } else {
                try {
                    var ta = document.createElement('textarea');
                    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                    document.body.appendChild(ta); ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    resolve();
                } catch (e) { reject(e); }
            }
        });
    }

    /* ---------- Loading / notification ---------- */
    var _loadingCount = 0;
    function showLoading() {
        _loadingCount++;
        var bar = $('loadingBar'), spinner = $('loadingSpinner');
        if (bar) { bar.classList.remove('done'); bar.style.width = '30%'; setTimeout(function() { if (_loadingCount > 0) bar.style.width = '70%'; }, 150); }
        if (spinner) spinner.classList.add('visible');
    }
    function hideLoading() {
        _loadingCount = Math.max(0, _loadingCount - 1);
        if (_loadingCount === 0) {
            var bar = $('loadingBar'), spinner = $('loadingSpinner');
            if (bar) { bar.classList.add('done'); setTimeout(function() { bar.classList.remove('done'); bar.style.width = '0'; }, 350); }
            if (spinner) spinner.classList.remove('visible');
        }
    }
    function api(url, options) {
        options = options || {};
        showLoading();
        return apiFetch(url, options).finally(function() { hideLoading(); });
    }
    function showNotification(message, type) {
        var n = $('notification');
        if (!n) return;
        n.textContent = message;
        n.className = 'notification show ' + (type === 'error' ? 'error' : '');
        setTimeout(function() { n.classList.remove('show'); }, 3000);
    }
    window.showNotification = showNotification;

    var _confirmHandler = null;
    function showConfirm(title, messageHtml, okLabel, onConfirm) {
        var modal = $('confirmModal');
        if (!modal) { if (onConfirm) onConfirm(); return; }
        $('confirmTitle').innerHTML = title;
        $('confirmMessage').innerHTML = messageHtml;
        $('confirmOkBtn').textContent = okLabel || 'Подтвердить';
        _confirmHandler = onConfirm;
        modal.classList.add('active');
    }
    window.showConfirm = showConfirm;

    var _undoTimer = null, _undoCallback = null, _undoActionActive = false;
    function showUndoToast(message, undoCallback, duration) {
        duration = duration || 8000;
        var toast = $('undoToast');
        if (!toast) return;
        $('undoToastText').textContent = message;
        _undoCallback = undoCallback;
        _undoActionActive = true;
        toast.classList.add('show');
        if (_undoTimer) clearTimeout(_undoTimer);
        _undoTimer = setTimeout(function() {
            toast.classList.remove('show');
            _undoCallback = null;
            _undoActionActive = false;
        }, duration);
    }
    function triggerUndo() {
        if (!_undoActionActive) return false;
        var btn = $('undoToastBtn');
        if (btn) { btn.click(); return true; }
        return false;
    }

    /* ---------- Excel lock ---------- */
    function showExcelLockModal() {
        var id = 'excelLockModal';
        var old = document.getElementById(id);
        if (old) old.remove();
        var modal = document.createElement('div');
        modal.className = 'modal active';
        modal.id = id;
        modal.style.zIndex = '4000';
        modal.innerHTML =
            '<div class="modal-content" style="max-width:460px;">' +
            '<h2>⚠️ Файл занят</h2>' +
            '<p style="color:var(--desc-color); line-height:1.6; margin-bottom:16px;">' +
            'Файл <b>реестр.xlsx</b> сейчас открыт в Excel. Сохранение невозможно. ' +
            'Закройте его в Excel и повторите действие.</p>' +
            '<div class="modal-actions">' +
            '<button type="button" class="btn" onclick="document.getElementById(\'' + id + '\').remove()">Понятно</button>' +
            '</div></div>';
        document.body.appendChild(modal);
        modal.addEventListener('click', function(e) { if (e.target === modal) modal.remove(); });
    }
    function apiWithLockGuard(url, options) {
        return api(url, options).then(function(r) {
            if (r.status === 500) {
                return r.text().then(function(text) {
                    if (text && text.indexOf('открыт в Excel') !== -1) {
                        showExcelLockModal();
                        throw new Error('ExcelLock');
                    }
                    throw new Error('ServerError');
                });
            }
            return r;
        });
    }

    /* ============================================================
       ОФФЛАЙН-ПОДСВЕТКА КОДА
       Мини-парсер: строки, комментарии, числа, ключевые слова.
       Без CDN, без зависимостей. Экспортирует window.hljs.
       ============================================================ */
    (function setupHighlight() {
        if (window.hljs && window.hljs.__reestr) return;

        var KEYWORDS = {
            python: new Set(('and as assert async await break class continue def del elif else ' +
                'except False finally for from global if import in is lambda None nonlocal not ' +
                'or pass raise return True try while with yield print self __init__ __name__').split(/\s+/)),
            sql: new Set(('select from where insert update delete into values set create table ' +
                'alter drop index join left right inner outer full cross on as and or not null ' +
                'is in like between group by order having limit offset distinct union all case ' +
                'when then else end primary key foreign references default constraint unique ' +
                'check if exists count sum avg min max with returning top begin commit rollback ' +
                'grant revoke').split(/\s+/)),
            javascript: new Set(('break case catch class const continue debugger default delete ' +
                'do else export extends finally for function if import in instanceof new return ' +
                'super switch this throw try typeof var void while with yield let async await ' +
                'of from as true false null undefined NaN Infinity').split(/\s+/)),
            typescript: new Set(('interface type enum implements extends public private protected ' +
                'readonly abstract any unknown never string number boolean void null undefined ' +
                'true false as is keyof infer asserts import from export default class function ' +
                'if else for while do switch case break continue return try catch finally throw ' +
                'new this super const let var async await of yield').split(/\s+/)),
            bash: new Set(('if then else elif fi for while until do done case esac function ' +
                'return in exit export local readonly declare echo cd pwd ls mkdir rmdir rm cp ' +
                'mv cat grep sed awk find sort uniq head tail wc chmod chown sudo apt yum dnf ' +
                'pip git docker ps kill top curl wget tar zip unzip').split(/\s+/)),
            json: new Set(['true', 'false', 'null']),
            yaml: new Set(['true', 'false', 'null', 'yes', 'no', 'on', 'off']),
            php: new Set(('function class interface extends implements public private protected ' +
                'static const return if else elseif for foreach while do switch case break ' +
                'continue try catch finally throw new clone instanceof echo print var global ' +
                'isset unset empty array list true false null include require namespace use as').split(/\s+/)),
            ruby: new Set(('def end class module if elsif else unless while until for do then ' +
                'begin rescue ensure raise return yield self nil true false and or not require ' +
                'include attr_accessor puts').split(/\s+/)),
            go: new Set(('package import func var const type struct interface map chan go defer ' +
                'if else for range switch case default break continue return nil true false ' +
                'make new len cap append copy delete panic recover').split(/\s+/)),
            rust: new Set(('fn let mut const static struct enum impl trait for while loop if else ' +
                'match return break continue pub use mod crate self super as where type unsafe ' +
                'true false Some None Ok Err Result Option Vec String').split(/\s+/)),
            java: new Set(('abstract assert boolean break byte case catch char class const continue ' +
                'default do double else enum extends final finally float for goto if implements ' +
                'import instanceof int interface long native new package private protected public ' +
                'return short static strictfp super switch synchronized this throw throws transient ' +
                'try void volatile while true false null').split(/\s+/)),
            c: new Set(('auto break case char const continue default do double else enum extern ' +
                'float for goto if inline int long register restrict return short signed sizeof ' +
                'static struct switch typedef union unsigned void volatile while NULL true false').split(/\s+/)),
            cpp: new Set(('alignas alignof and and_eq asm auto bitand bitor bool break case catch ' +
                'char class const constexpr continue decltype default delete do double else enum ' +
                'explicit export extern false float for friend goto if inline int long mutable ' +
                'namespace new noexcept not nullptr operator or private protected public register ' +
                'return short signed sizeof static struct switch template this throw true try ' +
                'typedef typeid typename union unsigned using virtual void volatile while').split(/\s+/)),
            csharp: new Set(('abstract as base bool break byte case catch char checked class const ' +
                'continue decimal default delegate do double else enum event explicit extern false ' +
                'finally fixed float for foreach goto if implicit in int interface internal is lock ' +
                'long namespace new null object operator out override params private protected public ' +
                'readonly ref return sbyte sealed short sizeof stackalloc static string struct switch ' +
                'this throw true try typeof uint ulong unchecked unsafe ushort using virtual void ' +
                'volatile while async await var get set').split(/\s+/)),
            css: new Set(('important media supports keyframes import charset font-face and not ' +
                'only or from to').split(/\s+/))
        };

        var LANG_ALIASES = {
            py: 'python', js: 'javascript', ts: 'typescript',
            sh: 'bash', shell: 'bash', zsh: 'bash',
            yml: 'yaml', 'c++': 'cpp', 'c#': 'csharp', cs: 'csharp',
            golang: 'go'
        };

        function normLang(l) {
            if (!l) return '';
            l = String(l).toLowerCase();
            if (LANG_ALIASES[l]) return LANG_ALIASES[l];
            if (l === 'plaintext' || l === 'text' || l === 'txt') return '';
            return l;
        }

        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
            });
        }

        var RE_STRING = /(?:"""[\s\S]*?"""|'''[\s\S]*?'''|`(?:\\[\s\S]|[^`\\])*`|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/y;
        var RE_NUMBER = /\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
        var RE_WORD = /[A-Za-z_$@][\w$]*/y;
        var RE_SPACE = /\s+/y;
        var RE_COMMENT_HASH = /#[^\n]*/y;
        var RE_COMMENT_SLASH = /(?:\/\/[^\n]*|\/\*[\s\S]*?\*\/)/y;
        var RE_COMMENT_SQL = /(?:--[^\n]*|\/\*[\s\S]*?\*\/)/y;

        function getCommentRe(lang) {
            if (lang === 'sql') return RE_COMMENT_SQL;
            if (lang === 'python' || lang === 'bash' || lang === 'yaml' || lang === 'ruby') return RE_COMMENT_HASH;
            return RE_COMMENT_SLASH;
        }

        function classifyWord(text, kw) {
            var lower = text.toLowerCase();
            if (kw && kw.has(lower)) return 'keyword';
            if (lower === 'true' || lower === 'false' || lower === 'null' ||
                lower === 'undefined' || lower === 'none' || lower === 'nil') {
                return 'literal';
            }
            return 'ident';
        }

        function highlightToHtml(code, lang) {
            var n = normLang(lang);
            var kw = KEYWORDS[n] || null;
            var reComment = getCommentRe(n);
            var out = [];
            var i = 0;
            var L = code.length;
            while (i < L) {
                var m;
                reComment.lastIndex = i;
                if ((m = reComment.exec(code)) !== null && m.index === i) {
                    out.push('<span class="hljs-comment">' + escapeHtml(m[0]) + '</span>');
                    i = reComment.lastIndex;
                    continue;
                }
                RE_STRING.lastIndex = i;
                if ((m = RE_STRING.exec(code)) !== null && m.index === i) {
                    out.push('<span class="hljs-string">' + escapeHtml(m[0]) + '</span>');
                    i = RE_STRING.lastIndex;
                    continue;
                }
                RE_NUMBER.lastIndex = i;
                if ((m = RE_NUMBER.exec(code)) !== null && m.index === i) {
                    out.push('<span class="hljs-number">' + escapeHtml(m[0]) + '</span>');
                    i = RE_NUMBER.lastIndex;
                    continue;
                }
                RE_WORD.lastIndex = i;
                if ((m = RE_WORD.exec(code)) !== null && m.index === i) {
                    var cls = classifyWord(m[0], kw);
                    out.push('<span class="hljs-' + cls + '">' + escapeHtml(m[0]) + '</span>');
                    i = RE_WORD.lastIndex;
                    continue;
                }
                RE_SPACE.lastIndex = i;
                if ((m = RE_SPACE.exec(code)) !== null && m.index === i) {
                    out.push(escapeHtml(m[0]));
                    i = RE_SPACE.lastIndex;
                    continue;
                }
                out.push('<span class="hljs-punct">' + escapeHtml(code[i]) + '</span>');
                i++;
            }
            return out.join('');
        }

        window.hljs = {
            __reestr: true,
            highlightElement: function (el) {
                if (!el) return;
                if (el.dataset && el.dataset.highlighted === '1') return;
                var cls = el.className || '';
                var match = cls.match(/language-([a-zA-Z0-9_+#-]+)/);
                var lang = match ? match[1] : '';
                var code = el.textContent || '';
                try {
                    el.innerHTML = highlightToHtml(code, lang);
                } catch (e) {
                    /* оставить как есть */
                }
                el.classList.add('hljs');
                if (el.dataset) el.dataset.highlighted = '1';
            },
            highlightAuto: function (el) {
                window.hljs.highlightElement(el);
            }
        };
    })();

    function highlightAllCodeBlocks() {
        if (!window.hljs) return;
        document.querySelectorAll('.link-code pre code').forEach(function(el) {
            try { window.hljs.highlightElement(el); } catch (e) {}
        });
    }
    window.__highlightAllCodeBlocks = highlightAllCodeBlocks;

    /* ============================================================
       ТЕМА / SHIMMER / MESH / STRIP
       ============================================================ */

    // NEW: загрузка inline-CSS кастомной темы из localStorage.
    // Вызывается ДО первой отрисовки body, чтобы избежать мигания
    // дефолтной темой при загрузке кастомной.
    function applyCustomThemeCSS(themeId) {
        if (!themeId) return;
        var key = 'reestr_theme_css_' + themeId;
        var css = null;
        try { css = localStorage.getItem(key); } catch (e) {}
        var elId = 'reestr-custom-theme-css';
        var el = document.getElementById(elId);
        if (!css) {
            if (el) el.remove();
            return;
        }
        if (!el) {
            el = document.createElement('style');
            el.id = elId;
            var head = document.head || document.getElementsByTagName('head')[0];
            if (head) head.insertBefore(el, head.firstChild);
            else document.documentElement.appendChild(el);
        }
        el.textContent = css;
    }
    window.__reestrApplyCustomThemeCSS = applyCustomThemeCSS;

    // NEW: хелпер для плагина themes_user.py — сохранить CSS кастомной темы
    // в localStorage, чтобы при следующей загрузке страницы он применился
    // синхронно, до первой отрисовки.
    window.__reestrStoreCustomThemeCSS = function(themeId, css) {
        if (!themeId) return;
        try { localStorage.setItem('reestr_theme_css_' + themeId, css || ''); } catch (e) {}
    };

    // ИЗМЕНЕНО: дефолт — light, ВСЕГДА навешиваем класс темы (включая light),
    // и снимаем все остальные theme-* классы.
    function applyTheme(theme) {
        if (!theme) theme = DEFAULT_THEME;
        // Удаляем ВСЕ theme-* классы с body
        var cls = document.body.classList;
        var toRemove = [];
        for (var i = 0; i < cls.length; i++) {
            if (cls[i].indexOf('theme-') === 0) toRemove.push(cls[i]);
        }
        toRemove.forEach(function(c) { cls.remove(c); });
        // Навешиваем целевой ВСЕГДА (в т.ч. light), т.к. :root остаётся dark-fallback
        cls.add('theme-' + theme);
        // Подсвечиваем активный .theme-dot
        document.querySelectorAll('.theme-dot').forEach(function(d) {
            d.classList.toggle('active', d.getAttribute('data-theme') === theme);
        });
        lsSet(LS_KEYS.theme, theme);
        // NEW: подгружаем inline-CSS кастомной темы (если это кастомная)
        applyCustomThemeCSS(theme);
    }
    window.applyTheme = applyTheme;

    function applyShimmerColors(c1, c2) {
        var use1 = c1 || DEFAULT_SHIMMER_1, use2 = c2 || DEFAULT_SHIMMER_2;
        document.documentElement.style.setProperty('--shimmer-1', use1);
        document.documentElement.style.setProperty('--shimmer-2', use2);
        var inp1 = $('shimmerColor1'), inp2 = $('shimmerColor2');
        if (inp1) inp1.value = use1;
        if (inp2) inp2.value = use2;
    }
    function applyHeaderShimmer(variant, speed, intensity) {
        HEADER_SHIMMER_VARIANTS.forEach(function(v) { document.body.classList.remove('header-shimmer-' + v); });
        var useVariant = (HEADER_SHIMMER_VARIANTS.indexOf(variant) !== -1) ? variant : 'sweep';
        document.body.classList.add('header-shimmer-' + useVariant);
        var speedMap = { slow: 0.65, normal: 1, fast: 1.5 };
        document.documentElement.style.setProperty('--shimmer-speed', speedMap[speed] || 1);
        var inten = (typeof intensity === 'number' && intensity > 0) ? intensity : 1;
        document.documentElement.style.setProperty('--shimmer-intensity', inten);
        document.body.classList.toggle('has-header-shimmer', useVariant !== 'off');
    }
    function applyCardShimmer(enabled) {
        document.body.classList.toggle('card-shimmer-off', !enabled);
    }
    function applyCardStrip(style) {
        if (style === 'gradient-half') style = 'hover-fill';
        if (STRIP_VARIANTS.indexOf(style) === -1) style = 'left';
        ['left', 'hover-fill', 'gradient-half', 'gradient-full', 'gradient-center',
         'top', 'bottom', 'frame', 'off'].forEach(function(v) {
            document.body.classList.remove('strip-style-' + v);
        });
        if (style !== 'left') {
            document.body.classList.add('strip-style-' + style);
        }
    }
    function applyMeshStyle(style) {
        MESH_STYLES.forEach(function(s) { document.body.classList.remove('mesh-style-' + s); });
        document.body.classList.remove('mesh-bg-on');
        if (style && style !== 'off' && MESH_STYLES.indexOf(style) !== -1) {
            document.body.classList.add('mesh-bg-on');
            document.body.classList.add('mesh-style-' + style);
        }
    }

    /* ============================================================
       FILTER INDEX
       ============================================================ */
    function buildFilterIndex() {
        _filterIndex = [];
        document.querySelectorAll('.card').forEach(function(card) {
            var group = String(card.getAttribute('data-group') || '').toLowerCase();
            var cardCats = [];
            try {
                var raw = card.getAttribute('data-categories') || '[]';
                cardCats = JSON.parse(raw);
                if (!Array.isArray(cardCats)) cardCats = [];
            } catch (e) {
                cardCats = String(card.getAttribute('data-categories') || '').split('|').filter(Boolean);
            }
            cardCats = cardCats.map(function(c) { return String(c || '').toLowerCase(); });
            card.querySelectorAll('.link-item').forEach(function(li) {
                var linkDisplay = li.querySelector('.link-display');
                var smartLink = li.querySelector('.smart-link');
                var descEl = li.querySelector('.desc');
                var favBtn = li.querySelector('.favorite-btn');
                var codeEl = li.querySelector('.link-code pre code');
                _filterIndex.push({
                    el: li, card: card, id: li.getAttribute('data-id'),
                    group: group, cardCats: cardCats,
                    link: String(linkDisplay ? (linkDisplay.textContent || '') : '').toLowerCase(),
                    fullLink: String(smartLink ? (smartLink.getAttribute('data-full-link') || '') : '').toLowerCase(),
                    desc: String(descEl ? (descEl.getAttribute('data-original') || '') : '').toLowerCase(),
                    code: String(codeEl ? (codeEl.textContent || '') : '').toLowerCase().slice(0, 1000),
                    cat: String(li.getAttribute('data-category') || '').toLowerCase(),
                    tags: String(li.getAttribute('data-tags') || '').toLowerCase().split(',').filter(Boolean),
                    updated: li.getAttribute('data-updated') || '',
                    fav: favBtn ? favBtn.classList.contains('fav-on') : false
                });
            });
        });
        _filterIndexDirty = false;
    }

    /* ============================================================
       FOCUS TRAP
       ============================================================ */
    function trapFocus(modal) {
        var focusable = modal.querySelectorAll(
            'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable.length) return function() {};
        var first = focusable[0], last = focusable[focusable.length - 1];
        var previousActive = document.activeElement;
        function onKeydown(e) {
            if (e.key !== 'Tab') return;
            if (e.shiftKey) { if (document.activeElement === first) { e.preventDefault(); last.focus(); } }
            else { if (document.activeElement === last) { e.preventDefault(); first.focus(); } }
        }
        modal.addEventListener('keydown', onKeydown);
        setTimeout(function() { try { if (!modal.contains(document.activeElement)) first.focus(); } catch (err) {} }, 50);
        return function cleanup() {
            modal.removeEventListener('keydown', onKeydown);
            if (previousActive && previousActive.focus) { try { previousActive.focus(); } catch (err) {} }
        };
    }
    function setupFocusTraps() {
        document.querySelectorAll('.modal').forEach(function(modal) {
            var cleanup = null;
            var obs = new MutationObserver(function(mutations) {
                for (var i = 0; i < mutations.length; i++) {
                    if (mutations[i].attributeName === 'class') {
                        var isActive = modal.classList.contains('active');
                        if (isActive && !cleanup) cleanup = trapFocus(modal);
                        else if (!isActive && cleanup) { cleanup(); cleanup = null; }
                    }
                }
            });
            obs.observe(modal, { attributes: true, attributeFilter: ['class'] });
        });
    }

    /* ============================================================
       DRAG-AND-DROP (sortable)
       ============================================================ */
    function makeSortable(container, itemSelector, handleSelector, onEnd, isEnabled) {
        if (!container) return;
        var enabled = isEnabled || function() { return true; };
        function getItems() {
            return Array.from(container.children).filter(function(c) { return c.matches(itemSelector); });
        }
        container.addEventListener('pointerdown', function(e) {
            if (e.button !== 0 || !enabled()) return;
            var item = e.target.closest(itemSelector);
            if (!item || item.parentElement !== container) return;
            if (e.target.closest('button, .edit-btn, .delete-btn, .favorite-btn, .rename-group-btn, .cat-sort-btn, .card-sort-btn, .card-sort-dropdown, .bulk-checkbox, .bulk-checkbox-card, .card-icon, input[type="checkbox"], .desc, .link-status, .category-tag, .tag-chip, .link-code')) return;
            if (handleSelector && !e.target.closest(handleSelector)) return;
            var startX = e.clientX, startY = e.clientY;
            var isDragging = false, dragged = null;
            var origUserSelect = document.body.style.userSelect;
            function onMove(ev) {
                if (!isDragging) {
                    if (Math.abs(ev.clientY - startY) < 8 && Math.abs(ev.clientX - startX) < 8) return;
                    isDragging = true; dragged = item;
                    dragged.classList.add('dragging');
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'grabbing';
                }
                ev.preventDefault();
                if (ev.stopPropagation) ev.stopPropagation();
                var elem = document.elementFromPoint(ev.clientX, ev.clientY);
                if (!elem) return;
                var target = elem.closest(itemSelector);
                if (!target || target === dragged || target.parentElement !== container) {
                    getItems().forEach(function(i) { i.classList.remove('drag-over-top', 'drag-over-bottom'); });
                    return;
                }
                getItems().forEach(function(i) { i.classList.remove('drag-over-top', 'drag-over-bottom'); });
                var r = target.getBoundingClientRect();
                var mid = r.top + r.height / 2;
                if (ev.clientY < mid) {
                    target.classList.add('drag-over-top');
                    if (dragged.nextElementSibling !== target) container.insertBefore(dragged, target);
                } else {
                    target.classList.add('drag-over-bottom');
                    if (target.nextElementSibling !== dragged) container.insertBefore(dragged, target.nextSibling);
                }
            }
            function onUp() {
                document.removeEventListener('pointermove', onMove);
                document.removeEventListener('pointerup', onUp);
                document.removeEventListener('pointercancel', onUp);
                document.body.style.userSelect = origUserSelect;
                document.body.style.cursor = '';
                if (isDragging && dragged) {
                    dragged.classList.remove('dragging');
                    getItems().forEach(function(i) { i.classList.remove('drag-over-top', 'drag-over-bottom'); });
                    if (onEnd) onEnd();
                }
                dragged = null; isDragging = false;
            }
            document.addEventListener('pointermove', onMove);
            document.addEventListener('pointerup', onUp);
            document.addEventListener('pointercancel', onUp);
        });
    }

    /* ============================================================
       DRAG ссылок
       ============================================================ */
    function setupLinkDrag() {
        var dragging = null, sourceContainer = null, sourceCard = null;
        var groupDragIds = null, groupDragElements = null;

        function clearMarkers() {
            document.querySelectorAll('.link-item.drag-over-top, .link-item.drag-over-bottom').forEach(function(x) {
                x.classList.remove('drag-over-top', 'drag-over-bottom');
            });
            document.querySelectorAll('.card.drag-over-card').forEach(function(x) { x.classList.remove('drag-over-card'); });
        }

        function collectGroupForDrag(li) {
            var id = li.getAttribute('data-id');
            var selected = getSelectedIds();
            if (!selected.has(id)) return null;
            if (selected.size < 2) return null;
            var els = [];
            document.querySelectorAll('.link-item.bulk-selected').forEach(function(el) { els.push(el); });
            return els.length > 1 ? els : null;
        }

        document.querySelectorAll('.card .links').forEach(function(container) {
            container.addEventListener('pointerdown', function(e) {
                if (e.button !== 0) return;
                var li = e.target.closest('.link-item');
                if (!li || li.parentElement !== container) return;
                if (e.target.closest('button, .edit-btn, .delete-btn, .favorite-btn, .bulk-checkbox, input, a, .desc, .link-status, .meta-created, .tag-chip, .category-tag, .link-code')) return;

                var startX = e.clientX, startY = e.clientY;
                var started = false;

                function onMove(ev) {
                    if (!started) {
                        if (Math.abs(ev.clientX - startX) < 8 && Math.abs(ev.clientY - startY) < 8) return;
                        started = true;
                        dragging = li;
                        sourceContainer = container;
                        sourceCard = li.closest('.card');

                        groupDragElements = collectGroupForDrag(li);
                        if (groupDragElements) {
                            groupDragIds = groupDragElements.map(function(el) { return el.getAttribute('data-id'); });
                            groupDragElements.forEach(function(el) { el.classList.add('dragging'); });
                            showDragCounter(groupDragElements.length);
                        } else {
                            li.classList.add('dragging');
                        }

                        document.body.style.userSelect = 'none';
                        document.body.style.cursor = 'grabbing';
                    }
                    ev.preventDefault();
                    var elem = document.elementFromPoint(ev.clientX, ev.clientY);
                    if (!elem) return;
                    var targetLi = elem.closest('.link-item');
                    var targetCard = elem.closest('.card');
                    clearMarkers();
                    if (targetLi && targetLi !== dragging && targetLi.parentElement === sourceContainer) {
                        var r = targetLi.getBoundingClientRect();
                        if (ev.clientY < r.top + r.height / 2) targetLi.classList.add('drag-over-top');
                        else targetLi.classList.add('drag-over-bottom');
                    } else if (targetCard && targetCard !== sourceCard) {
                        targetCard.classList.add('drag-over-card');
                    }
                }

                function onUp(ev) {
                    document.removeEventListener('pointermove', onMove);
                    document.removeEventListener('pointerup', onUp);
                    document.removeEventListener('pointercancel', onUp);
                    document.body.style.userSelect = '';
                    document.body.style.cursor = '';
                    clearMarkers();
                    hideDragCounter();

                    if (started && dragging) {
                        var elem = document.elementFromPoint(ev.clientX, ev.clientY);
                        var targetLi = elem ? elem.closest('.link-item') : null;
                        var targetCard = elem ? elem.closest('.card') : null;

                        if (groupDragIds && targetCard && targetCard !== sourceCard) {
                            var targetGroupG = targetCard.getAttribute('data-group');
                            var sourceGroupG = sourceCard ? sourceCard.getAttribute('data-group') : '';
                            groupDragElements.forEach(function(el) { el.classList.remove('dragging'); });
                            if (targetGroupG && sourceGroupG && targetGroupG !== sourceGroupG) {
                                moveGroupToGroup(groupDragIds, targetGroupG, sourceGroupG);
                            }
                            dragging = null; sourceContainer = null; sourceCard = null; started = false;
                            groupDragIds = null; groupDragElements = null;
                            return;
                        }

                        if (groupDragElements) {
                            groupDragElements.forEach(function(el) { el.classList.remove('dragging'); });
                        } else {
                            dragging.classList.remove('dragging');
                        }

                        if (targetCard && targetCard !== sourceCard && !groupDragIds) {
                            var targetGroup = targetCard.getAttribute('data-group');
                            var recordId = dragging.getAttribute('data-id');
                            if (targetGroup && recordId && sourceCard) {
                                var sourceGroup = sourceCard.getAttribute('data-group');
                                apiWithLockGuard('/move_to_group', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ id: parseInt(recordId), group_name: targetGroup })
                                }).then(function(r) { return r.json(); }).then(function(data) {
                                    if (data.success) {
                                        showNotification('✅ Перемещено: «' + sourceGroup + '» → «' + targetGroup + '»', 'success');
                                        setTimeout(function() { location.reload(); }, 700);
                                    } else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
                                }).catch(function(err) {
                                    if (err && err.message === 'ExcelLock') return;
                                    showNotification('❌ Ошибка сети', 'error');
                                });
                            }
                        } else if (targetLi && targetLi !== dragging && targetLi.parentElement === sourceContainer && sourceCard && !groupDragIds) {
                            var r2 = targetLi.getBoundingClientRect();
                            if (ev.clientY < r2.top + r2.height / 2) sourceContainer.insertBefore(dragging, targetLi);
                            else sourceContainer.insertBefore(dragging, targetLi.nextSibling);
                            var orderedIds = [];
                            sourceContainer.querySelectorAll('.link-item').forEach(function(x) {
                                orderedIds.push(parseInt(x.getAttribute('data-id')));
                            });
                            var groupName = sourceCard.getAttribute('data-group');
                            if (orderedIds.length > 0 && groupName) {
                                api('/update_order', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({ group_name: groupName, ordered_ids: orderedIds })
                                }).then(function(r) {
                                    if (r.ok) showNotification('💾 Порядок сохранён', 'success');
                                }).catch(function() {});
                            }
                        }
                    }
                    dragging = null; sourceContainer = null; sourceCard = null; started = false;
                    groupDragIds = null; groupDragElements = null;
                }

                document.addEventListener('pointermove', onMove);
                document.addEventListener('pointerup', onUp);
                document.addEventListener('pointercancel', onUp);
            });
        });
    }

    var _dragCounterEl = null;
    function showDragCounter(n) {
        if (!_dragCounterEl) {
            _dragCounterEl = document.createElement('div');
            _dragCounterEl.style.cssText = 'position:fixed; z-index:5000; padding:8px 16px; background:var(--accent); color:var(--btn-text); border-radius:20px; font-weight:700; pointer-events:none; box-shadow:0 8px 24px rgba(0,0,0,0.4); font-size:0.9rem;';
            document.body.appendChild(_dragCounterEl);
        }
        _dragCounterEl.textContent = '📦 ' + n + ' ссылок';
        _dragCounterEl.style.display = 'block';
    }
    function hideDragCounter() {
        if (_dragCounterEl) _dragCounterEl.style.display = 'none';
    }

    document.addEventListener('mousemove', function(e) {
        if (_dragCounterEl && _dragCounterEl.style.display === 'block') {
            _dragCounterEl.style.left = (e.clientX + 16) + 'px';
            _dragCounterEl.style.top = (e.clientY + 16) + 'px';
        }
    });

    function moveGroupToGroup(ids, targetGroup, sourceGroup) {
        var done = 0, failed = 0, firstError = '';
        ids.forEach(function(id) {
            apiWithLockGuard('/move_to_group', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: parseInt(id), group_name: targetGroup })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) done++; else { failed++; firstError = data.error || ''; }
            }).catch(function(err) {
                failed++;
                if (err && err.message === 'ExcelLock') firstError = 'Файл открыт в Excel';
            }).finally(function() {
                if (done + failed === ids.length) {
                    if (failed === 0) {
                        showNotification('✅ Перемещено ' + done + ' ссылок в «' + targetGroup + '»', 'success');
                        setTimeout(function() { location.reload(); }, 700);
                    } else {
                        showNotification('⚠️ Перемещено ' + done + ', ошибок: ' + failed + (firstError ? ' (' + firstError + ')' : ''), 'error');
                    }
                }
            });
        });
    }

    /* ============================================================
       TOOLTIPS
       ============================================================ */
    function setupLinkTooltips() {
        var tooltip = $('linkTooltip');
        if (!tooltip) return;
        function hideTooltip() { tooltip.classList.remove('visible'); }
        _hideLinkTooltipGlobal = hideTooltip;
        document.querySelectorAll('.smart-link').forEach(function(link) {
            link.addEventListener('mouseenter', function() {
                var display = this.querySelector('.link-display');
                if (!display || display.scrollWidth <= display.clientWidth + 1) return;
                var fullText = this.getAttribute('data-full-link');
                if (!fullText) return;
                tooltip.textContent = fullText;
                tooltip.classList.add('visible');
                var rect = this.getBoundingClientRect();
                var top = rect.bottom + 6, left = rect.left;
                tooltip.style.left = '-9999px'; tooltip.style.top = '-9999px';
                var tw = tooltip.offsetWidth, th = tooltip.offsetHeight;
                if (left + tw > window.innerWidth - 10) left = Math.max(10, window.innerWidth - tw - 10);
                if (top + th > window.innerHeight - 10) top = Math.max(10, rect.top - th - 6);
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
            });
            link.addEventListener('mouseleave', hideTooltip);
            link.addEventListener('click', hideTooltip);
        });
    }

    /* ============================================================
       SORT DROPDOWN
       ============================================================ */
    var _activeSortDropdown = null, _activeSortBtn = null;
    function buildSortDropdown(group) {
        var dd = document.createElement('div');
        dd.className = 'card-sort-dropdown';
        dd.innerHTML =
            '<button data-sort-by="name" data-asc="1">🔤 А→Я</button>' +
            '<button data-sort-by="name" data-asc="0">🔤 Я→А</button>' +
            '<button data-sort-by="date" data-asc="0">📅 Сначала новые</button>' +
            '<button data-sort-by="date" data-asc="1">📅 Сначала старые</button>' +
            '<button data-sort-by="type" data-asc="1">🏷️ По типу</button>';
        dd.querySelectorAll('button').forEach(function(b) {
            b.addEventListener('click', function(e) {
                e.stopPropagation();
                var sortBy = this.getAttribute('data-sort-by');
                var asc = this.getAttribute('data-asc') === '1';
                hideSortDropdown();
                api('/sort_group', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ group_name: group, sort_by: sortBy, asc: asc })
                }).then(function(r) { return r.json(); }).then(function(data) {
                    if (data.success) {
                        showNotification('✅ Ссылки отсортированы', 'success');
                        setTimeout(function() { location.reload(); }, 500);
                    } else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
                }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
            });
        });
        return dd;
    }
    function hideSortDropdown() {
        if (_activeSortDropdown && _activeSortDropdown.parentNode) _activeSortDropdown.parentNode.removeChild(_activeSortDropdown);
        if (_activeSortBtn) _activeSortBtn.classList.remove('active');
        _activeSortDropdown = null; _activeSortBtn = null;
    }
    function showSortDropdown(btn, group) {
        hideSortDropdown();
        var dd = buildSortDropdown(group);
        document.body.appendChild(dd);
        var rect = btn.getBoundingClientRect();
        var ddRectWidth = 200;
        var left = rect.right - ddRectWidth;
        if (left < 8) left = 8;
        if (left + ddRectWidth > window.innerWidth - 8) left = window.innerWidth - ddRectWidth - 8;
        var top = rect.bottom + 4;
        var estimatedHeight = 180;
        if (top + estimatedHeight > window.innerHeight - 8) { top = rect.top - estimatedHeight - 4; if (top < 8) top = 8; }
        dd.style.left = left + 'px'; dd.style.top = top + 'px';
        dd.classList.add('show');
        btn.classList.add('active');
        _activeSortDropdown = dd; _activeSortBtn = btn;
    }

    /* ============================================================
       SELECTION
       ============================================================ */
    function getSelectedIds() { return _selectedIds; }
    function resetBulkSelection() {
        _selectedIds.clear();
        document.querySelectorAll('.link-item').forEach(function(li) { li.classList.remove('bulk-selected'); });
        document.querySelectorAll('.bulk-checkbox-card').forEach(function(cb) { cb.checked = false; });
        document.querySelectorAll('.bulk-checkbox').forEach(function(cb) { cb.checked = false; });
    }
    window.getSelectedIds = getSelectedIds;

    /* ============================================================
       Cross-tab sync
       ============================================================ */
    function setupStorageSync() {
        window.addEventListener('storage', function(e) {
            if (!e.key) return;
            var k = e.key, v = e.newValue;
            // ИЗМЕНЕНО: дефолт light + применение CSS кастомной темы
            if (k === LS_KEYS.theme) {
                applyTheme(v || DEFAULT_THEME);
                applyCustomThemeCSS(v || DEFAULT_THEME);
            }
            else if (k === LS_KEYS.cols) {
                if (typeof window.__applyColumns === 'function') window.__applyColumns(v || '2');
            } else if (k === LS_KEYS.meshBg) {
                var m = v || 'off';
                if (m === 'true') m = 'float';
                if (m === 'false') m = 'off';
                applyMeshStyle(m);
                var sel = $('meshBgSelect'); if (sel) sel.value = m;
            } else if (k === LS_KEYS.cardStrip) {
                var s = v || 'left';
                if (s === 'gradient-half') s = 'hover-fill';
                applyCardStrip(s);
                var sel2 = $('cardStripSelect'); if (sel2) sel2.value = s;
            } else if (k === LS_KEYS.fontSize) {
                document.documentElement.style.fontSize = (v || '14') + 'px';
            } else if (k === LS_KEYS.radius) {
                document.documentElement.style.setProperty('--radius-card', (v || '16') + 'px');
            } else if (k === LS_KEYS.sidebarWidth) {
                document.documentElement.style.setProperty('--sidebar-width', (v || '260') + 'px');
            } else if (k === LS_KEYS.compact) {
                document.body.classList.toggle('compact-mode', v === 'true');
            } else if (k === LS_KEYS.headerAnim) {
                document.body.classList.toggle('header-anim-off', v === 'false');
            }
        });
    }

    function saveServerSettings(partial) {
        return api('/save_settings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(partial)
        }).then(function(r) { return r.json(); }).catch(function() { return {success: false}; });
    }

    function schedulePageReady() {
        setTimeout(function() { document.body.classList.add('page-ready'); }, 200);
    }

/* ============================================================
   ============================================================
   INIT MAIN
   ============================================================
   ============================================================ */
function initMain() {
    var sidebar = $('sidebar');
    var sidebarOverlay = $('sidebarOverlay');
    var sidebarFloatToggle = $('sidebarFloatToggle');
    var searchInput = $('searchInput');
    var cardsGrid = $('cardsGrid');
    var manualHint = $('manualHint');
    var filterFavBtn = $('filterFavBtn');

    setupFocusTraps();

    function resetCategoryToAll() {
        document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
        if (filterFavBtn) filterFavBtn.classList.remove('active');
        var allBtn = document.querySelector('.cat-btn[data-filter="all"]');
        if (allBtn) allBtn.classList.add('active');
        lsSet(LS_KEYS.activeCategory, 'all');
        lsSet(LS_KEYS.showFavorites, 'false');
    }
    function closeAppearanceModal() {
        var m = $('appearanceModal'); if (m) m.classList.remove('active');
    }

    var _namesDatalistAbort = null;
    function updateNamesDatalist(category) {
        var datalist = $('names-datalist'); if (!datalist) return;
        if (_namesDatalistAbort) try { _namesDatalistAbort.abort(); } catch (e) {}
        _namesDatalistAbort = new AbortController();
        var url = category ? '/get_names_for_category?category=' + encodeURIComponent(category) : '/get_all_names';
        fetch(url, { signal: _namesDatalistAbort.signal })
            .then(function(r) { return r.json(); })
            .then(function(names) {
                datalist.innerHTML = (names || []).map(function(n) {
                    return '<option value="' + escapeHtml(n) + '">';
                }).join('');
            })
            .catch(function(err) { if (err && err.name === 'AbortError') return; });
    }

    /* ---------- Валидация: имя + (ссылка ИЛИ код) ---------- */
    // ИЗМЕНЕНО: чекбокс «Только код» убран, поле «Ссылка» необязательно
    // на уровне HTML — валидация только по JS.

    function updateLinkPlaceholder() {
        var linkInput = $('link');
        var codeInput = $('code_add');
        if (!linkInput || !codeInput) return;
        var hasCode = codeInput.value.trim().length > 0;
        linkInput.placeholder = hasCode
            ? 'ссылка необязательна — есть код'
            : 'https://... или \\\\server\\share';
    }
    var codeInputAdd = $('code_add');
    if (codeInputAdd) codeInputAdd.addEventListener('input', updateLinkPlaceholder);
    updateLinkPlaceholder();

    function prepareAddModal() {
        var catSelect = $('category_add');
        var catCustom = $('category_custom');
        var catHidden = $('category_hidden');
        var activeCat = '';
        var favActive = filterFavBtn && filterFavBtn.classList.contains('active');
        var activeBtn = document.querySelector('.cat-btn.active');
        if (!favActive && activeBtn) {
            var f = activeBtn.getAttribute('data-filter');
            if (f && f !== 'all' && f !== '__none__') activeCat = f;
        }
        if (catSelect) {
            if (activeCat) {
                var found = false;
                for (var i = 0; i < catSelect.options.length; i++) {
                    if (catSelect.options[i].value === activeCat) { catSelect.selectedIndex = i; found = true; break; }
                }
                if (!found) {
                    catSelect.value = '__other__';
                    if (catCustom) { catCustom.classList.add('visible'); catCustom.value = activeCat; }
                } else if (catCustom) { catCustom.classList.remove('visible'); catCustom.value = ''; }
            } else {
                catSelect.value = '';
                if (catCustom) { catCustom.classList.remove('visible'); catCustom.value = ''; }
            }
            if (catHidden) {
                catHidden.value = (catSelect.value === '__other__')
                    ? (catCustom ? catCustom.value.trim() : '')
                    : (catSelect.value || '');
            }
        }
        updateNamesDatalist(activeCat);
        var iconBtn = $('addIconPickerBtn'), iconHidden = $('add_group_icon');
        if (iconBtn) iconBtn.textContent = '📌';
        if (iconHidden) iconHidden.value = '';
        // Снять браузерную валидацию с поля «Ссылка» — проверяем сами
        var linkInput = $('link');
        if (linkInput) linkInput.removeAttribute('required');
        var codeEl = $('code_add');
        if (codeEl) codeEl.value = '';
        var langEl = $('code_lang_add');
        if (langEl) langEl.value = '';
        // NEW: закрываем спойлер кода при открытии модалки
        var codeDetails = $('addCodeDetails');
        if (codeDetails) codeDetails.open = false;
        updateLinkPlaceholder();
    }
    window.__prepareAddModal = prepareAddModal;

    SECTION_IDS.forEach(function(id) {
        var el = $(id); if (!el) return;
        if (lsGet('reestr_sectionCollapsed_' + id, 'false') === 'true') el.classList.add('collapsed');
    });
    document.querySelectorAll('.section-toggle').forEach(function(label) {
        label.addEventListener('click', function(e) {
            if (e.target.closest('.cat-sort-btn')) return;
            if (e.target.closest('.cat-manage-btn')) return;
            var targetId = this.getAttribute('data-target');
            if (!targetId) return;
            var section = $(targetId); if (!section) return;
            var isCollapsed = section.classList.toggle('collapsed');
            lsSet('reestr_sectionCollapsed_' + targetId, isCollapsed ? 'true' : 'false');
        });
    });

    /* ---------- Appearance modal ---------- */
    (function setupAppearanceModal() {
        var modal = $('appearanceModal');
        var openBtn = $('openAppearanceModal');
        var closeBtn = $('closeAppearanceModalBtn');
        var tabs = document.querySelectorAll('.settings-tab');
        var panels = document.querySelectorAll('.settings-panel');
        function switchTab(tabId) {
            tabs.forEach(function(t) { t.classList.toggle('active', t.getAttribute('data-tab') === tabId); });
            panels.forEach(function(p) { p.classList.toggle('active', p.id === tabId); });
            lsSet(LS_KEYS.settingsTab, tabId);
        }
        var savedTab = lsGet(LS_KEYS.settingsTab, 'tab-appearance');
        if (savedTab) switchTab(savedTab);
        tabs.forEach(function(t) {
            t.addEventListener('click', function() { switchTab(this.getAttribute('data-tab')); });
        });
        if (openBtn && modal) openBtn.addEventListener('click', function() { modal.classList.add('active'); });
        if (closeBtn && modal) closeBtn.addEventListener('click', function() { modal.classList.remove('active'); });
        if (modal) modal.addEventListener('click', function(e) { if (e.target === modal) modal.classList.remove('active'); });
    })();

    /* ---------- Header animation ---------- */
    function applyHeaderAnim(enabled) {
        document.body.classList.toggle('header-anim-off', !enabled);
        var cb = $('headerAnimToggle'); if (cb) cb.checked = enabled;
    }
    applyHeaderAnim(lsGet(LS_KEYS.headerAnim, 'true') === 'true');
    var headerAnimToggle = $('headerAnimToggle');
    if (headerAnimToggle) headerAnimToggle.addEventListener('change', function() {
        applyHeaderAnim(this.checked);
        lsSet(LS_KEYS.headerAnim, this.checked ? 'true' : 'false');
    });

    /* ---------- Mesh ---------- */
    var meshBgSelect = $('meshBgSelect');
    var savedMesh = lsGet(LS_KEYS.meshBg, 'off');
    if (savedMesh === 'true') savedMesh = 'float';
    if (savedMesh === 'false') savedMesh = 'off';
    if (savedMesh !== 'off' && MESH_STYLES.indexOf(savedMesh) === -1) savedMesh = 'off';
    applyMeshStyle(savedMesh);
    if (meshBgSelect) {
        meshBgSelect.value = savedMesh;
        meshBgSelect.addEventListener('change', function() {
            var val = this.value;
            applyMeshStyle(val);
            lsSet(LS_KEYS.meshBg, val);
            saveServerSettings({ mesh_style: val });
        });
    }

    /* ---------- Compact ---------- */
    function applyCompact(on) {
        document.body.classList.toggle('compact-mode', on);
        var cb = $('compactModeToggle'); if (cb) cb.checked = on;
    }
    applyCompact(lsGet(LS_KEYS.compact, 'false') === 'true');
    var compactToggle = $('compactModeToggle');
    if (compactToggle) compactToggle.addEventListener('change', function() {
        applyCompact(this.checked);
        lsSet(LS_KEYS.compact, this.checked ? 'true' : 'false');
    });

    /* ---------- Wallpaper ---------- */
    function applyWallpaper(dataUrl) {
        if (dataUrl) {
            document.body.style.backgroundImage = 'linear-gradient(rgba(0,0,0,0.35), rgba(0,0,0,0.35)), url(' + dataUrl + ')';
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundAttachment = 'fixed';
            document.body.style.backgroundPosition = 'center';
        } else {
            document.body.style.backgroundImage = '';
            document.body.style.backgroundSize = '';
            document.body.style.backgroundAttachment = '';
            document.body.style.backgroundPosition = '';
        }
    }
    var savedWallpaper = lsGet(LS_KEYS.wallpaper, '');
    if (savedWallpaper) applyWallpaper(savedWallpaper);
    var wallpaperInput = $('wallpaperInput');
    if (wallpaperInput) wallpaperInput.addEventListener('change', function() {
        var file = this.files[0]; if (!file) return;
        if (file.size > 2 * 1024 * 1024) { showNotification('❌ Картинка больше 2 МБ', 'error'); this.value = ''; return; }
        var reader = new FileReader();
        reader.onload = function(ev) {
            var dataUrl = ev.target.result;
            lsSet(LS_KEYS.wallpaper, dataUrl);
            applyWallpaper(dataUrl);
            showNotification('✅ Обои применены', 'success');
        };
        reader.readAsDataURL(file);
        this.value = '';
    });
    var wallpaperClearBtn = $('wallpaperClearBtn');
    if (wallpaperClearBtn) wallpaperClearBtn.addEventListener('click', function() {
        lsSet(LS_KEYS.wallpaper, ''); applyWallpaper('');
        showNotification('✅ Обои убраны', 'success');
    });

    /* ---------- Shimmer colors ---------- */
    (function() {
        var settings = DATA.settings || {};
        applyShimmerColors(settings.shimmer_color_1 || '', settings.shimmer_color_2 || '');
        var inp1 = $('shimmerColor1'), inp2 = $('shimmerColor2'), resetBtn = $('shimmerResetBtn');
        function saveColors(v1, v2) {
            saveServerSettings({ shimmer_color_1: v1, shimmer_color_2: v2 })
                .then(function(data) {
                    if (data.success) showNotification('✅ Цвета сохранены', 'success');
                });
        }
        if (inp1) {
            inp1.addEventListener('input', function() { document.documentElement.style.setProperty('--shimmer-1', this.value); });
            inp1.addEventListener('change', function() { saveColors(this.value, inp2 ? inp2.value : ''); });
        }
        if (inp2) {
            inp2.addEventListener('input', function() { document.documentElement.style.setProperty('--shimmer-2', this.value); });
            inp2.addEventListener('change', function() { saveColors(inp1 ? inp1.value : '', this.value); });
        }
        if (resetBtn) resetBtn.addEventListener('click', function() {
            if (inp1) inp1.value = DEFAULT_SHIMMER_1;
            if (inp2) inp2.value = DEFAULT_SHIMMER_2;
            applyShimmerColors('', ''); saveColors('', '');
        });
    })();

    /* ---------- Shimmer / card shimmer / strip ---------- */
    (function() {
        var settings = DATA.settings || {};
        var headerShimmer = settings.header_shimmer || 'sweep';
        var cardShimmer = settings.card_shimmer !== false;
        var speed = settings.shimmer_speed || 'normal';
        var intensity = (typeof settings.shimmer_intensity === 'number') ? settings.shimmer_intensity : 1;
        applyHeaderShimmer(headerShimmer, speed, intensity);
        applyCardShimmer(cardShimmer);

        var select = $('headerShimmerSelect');
        if (select) {
            select.value = headerShimmer;
            select.addEventListener('change', function() {
                var val = this.value;
                applyHeaderShimmer(val, speed, intensity);
                saveServerSettings({ header_shimmer: val })
                    .then(function(data) { if (data.success) showNotification('✅ Перелив: ' + val, 'success'); });
            });
        }
        var cardToggle = $('cardShimmerToggle');
        if (cardToggle) {
            cardToggle.checked = cardShimmer;
            cardToggle.addEventListener('change', function() {
                var on = this.checked; applyCardShimmer(on);
                saveServerSettings({ card_shimmer: on })
                    .then(function(data) {
                        if (data.success) showNotification(on ? '✅ Перелив карточек включён' : 'Перелив карточек выключен', 'success');
                    });
            });
        }
        var savedStrip = lsGet(LS_KEYS.cardStrip, settings.card_strip || 'left');
        if (savedStrip === 'gradient-half') savedStrip = 'hover-fill';
        if (STRIP_VARIANTS.indexOf(savedStrip) === -1) savedStrip = 'left';
        applyCardStrip(savedStrip);
        var cardStripSelect = $('cardStripSelect');
        if (cardStripSelect) {
            cardStripSelect.value = savedStrip;
            cardStripSelect.addEventListener('change', function() {
                var val = this.value;
                if (STRIP_VARIANTS.indexOf(val) === -1) val = 'left';
                applyCardStrip(val);
                lsSet(LS_KEYS.cardStrip, val);
                saveServerSettings({ card_strip: val });
            });
        }
        var speedGroup = $('shimmerSpeedGroup');
        if (speedGroup) {
            speedGroup.querySelectorAll('.col-btn').forEach(function(btn) {
                btn.classList.toggle('active', btn.getAttribute('data-speed') === speed);
                btn.addEventListener('click', function() {
                    var sp = this.getAttribute('data-speed');
                    speedGroup.querySelectorAll('.col-btn').forEach(function(b) { b.classList.remove('active'); });
                    this.classList.add('active');
                    var cv = document.body.className.match(/header-shimmer-(\w+)/);
                    var v = cv ? cv[1] : 'sweep';
                    var curInt = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--shimmer-intensity')) || 1;
                    applyHeaderShimmer(v, sp, curInt);
                    saveServerSettings({ shimmer_speed: sp })
                        .then(function(data) { if (data.success) showNotification('✅ Скорость: ' + sp, 'success'); });
                });
            });
        }
        var intGroup = $('shimmerIntensityGroup');
        if (intGroup) {
            intGroup.querySelectorAll('.col-btn').forEach(function(btn) {
                var val = parseFloat(btn.getAttribute('data-intensity'));
                btn.classList.toggle('active', Math.abs(val - intensity) < 0.01);
                btn.addEventListener('click', function() {
                    var v = parseFloat(this.getAttribute('data-intensity'));
                    intGroup.querySelectorAll('.col-btn').forEach(function(b) { b.classList.remove('active'); });
                    this.classList.add('active');
                    var cv = document.body.className.match(/header-shimmer-(\w+)/);
                    var variant = cv ? cv[1] : 'sweep';
                    var curSp = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--shimmer-speed')) || 1;
                    var spLabel = 'normal';
                    if (curSp < 0.9) spLabel = 'slow';
                    else if (curSp > 1.2) spLabel = 'fast';
                    applyHeaderShimmer(variant, spLabel, v);
                    saveServerSettings({ shimmer_intensity: v })
                        .then(function(data) { if (data.success) showNotification('✅ Интенсивность: ' + v + '×', 'success'); });
                });
            });
        }
    })();

    /* ---------- Presentation ---------- */
    function togglePresentation() {
        document.body.classList.toggle('presentation-mode');
        var on = document.body.classList.contains('presentation-mode');
        lsSet(LS_KEYS.presentation, on ? 'true' : 'false');
        showNotification(on ? '🎬 Режим презентации' : 'Режим презентации выключен', 'success');
    }
    if (lsGet(LS_KEYS.presentation, 'false') === 'true') document.body.classList.add('presentation-mode');
    var presentationBtn = $('presentationBtn');
    if (presentationBtn) presentationBtn.addEventListener('click', function() { closeAppearanceModal(); togglePresentation(); });

    /* ---------- Category sort ---------- */
    var categorySortMode = lsGet(LS_KEYS.catSort, 'name');
    if (['name', 'count', 'manual'].indexOf(categorySortMode) === -1) categorySortMode = 'name';
    function applyCategorySort() {
        var userWrapper = $('userCategoriesList'); if (!userWrapper) return;
        var buttons = Array.from(userWrapper.querySelectorAll('.cat-btn[data-cat-name]'));
        if (categorySortMode === 'name') {
            buttons.sort(function(a, b) {
                var an = a.getAttribute('data-cat-name') || '';
                var bn = b.getAttribute('data-cat-name') || '';
                return an.toLowerCase().localeCompare(bn.toLowerCase(), 'ru');
            });
        } else if (categorySortMode === 'count') {
            buttons.sort(function(a, b) {
                var ac = parseInt(a.getAttribute('data-cat-count')) || 0;
                var bc = parseInt(b.getAttribute('data-cat-count')) || 0;
                if (ac !== bc) return bc - ac;
                var an = a.getAttribute('data-cat-name') || '';
                var bn = b.getAttribute('data-cat-name') || '';
                return an.localeCompare(bn, 'ru');
            });
        } else {
            var idx = new Map(categoryManualOrder.map(function(n, i) { return [n, i]; }));
            buttons.sort(function(a, b) {
                var an = a.getAttribute('data-cat-name') || '';
                var bn = b.getAttribute('data-cat-name') || '';
                var ia = idx.has(an) ? idx.get(an) : 999999;
                var ib = idx.has(bn) ? idx.get(bn) : 999999;
                if (ia !== ib) return ia - ib;
                return an.localeCompare(bn, 'ru');
            });
        }
        buttons.forEach(function(b) { userWrapper.appendChild(b); });
        document.querySelectorAll('.cat-sort-btn').forEach(function(b) {
            b.classList.toggle('active', b.getAttribute('data-sort') === categorySortMode);
        });
    }
    document.querySelectorAll('.cat-sort-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            categorySortMode = this.getAttribute('data-sort');
            lsSet(LS_KEYS.catSort, categorySortMode);
            applyCategorySort();
        });
    });
    applyCategorySort();

    /* ---------- Drag категорий ---------- */
    var _catDragJustEnded = false;
    var catWrapperForDrag = $('userCategoriesList');
    if (catWrapperForDrag) {
        catWrapperForDrag.addEventListener('click', function(e) {
            if (_catDragJustEnded) {
                e.stopPropagation(); e.preventDefault();
                _catDragJustEnded = false;
            }
        }, true);
        catWrapperForDrag.addEventListener('pointerdown', function(e) {
            if (e.button !== 0) return;
            var btn = e.target.closest('.cat-btn[data-cat-name]');
            if (!btn || btn.parentElement !== catWrapperForDrag) return;
            var startX = e.clientX, startY = e.clientY;
            var started = false, dragged = null;
            var origUserSelect = document.body.style.userSelect;
            function clearMarkers() {
                catWrapperForDrag.querySelectorAll('.cat-btn').forEach(function(b) {
                    b.classList.remove('drag-over-top', 'drag-over-bottom');
                });
            }
            function switchToManual() {
                categorySortMode = 'manual';
                lsSet(LS_KEYS.catSort, 'manual');
                document.querySelectorAll('.cat-sort-btn').forEach(function(b) {
                    b.classList.toggle('active', b.getAttribute('data-sort') === 'manual');
                });
            }
            function onMove(ev) {
                if (!started) {
                    if (Math.abs(ev.clientX - startX) < 6 && Math.abs(ev.clientY - startY) < 6) return;
                    started = true; dragged = btn;
                    dragged.classList.add('dragging');
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'grabbing';
                    switchToManual();
                }
                ev.preventDefault();
                var elem = document.elementFromPoint(ev.clientX, ev.clientY);
                if (!elem) return;
                var target = elem.closest('.cat-btn[data-cat-name]');
                clearMarkers();
                if (!target || target === dragged || target.parentElement !== catWrapperForDrag) return;
                var r = target.getBoundingClientRect();
                var mid = r.top + r.height / 2;
                if (ev.clientY < mid) {
                    target.classList.add('drag-over-top');
                    if (dragged.nextElementSibling !== target) catWrapperForDrag.insertBefore(dragged, target);
                } else {
                    target.classList.add('drag-over-bottom');
                    if (target.nextElementSibling !== dragged) catWrapperForDrag.insertBefore(dragged, target.nextSibling);
                }
            }
            function onUp() {
                document.removeEventListener('pointermove', onMove);
                document.removeEventListener('pointerup', onUp);
                document.removeEventListener('pointercancel', onUp);
                document.body.style.userSelect = origUserSelect;
                document.body.style.cursor = '';
                clearMarkers();
                if (dragged) dragged.classList.remove('dragging');
                if (started) {
                    saveCurrentCategoryOrder();
                    _catDragJustEnded = true;
                    setTimeout(function() { _catDragJustEnded = false; }, 300);
                }
                dragged = null; started = false;
            }
            document.addEventListener('pointermove', onMove);
            document.addEventListener('pointerup', onUp);
            document.addEventListener('pointercancel', onUp);
        });
    }
    function saveCurrentCategoryOrder() {
        var userWrapper = $('userCategoriesList');
        if (!userWrapper) return;
        var names = Array.from(userWrapper.querySelectorAll('.cat-btn[data-cat-name]'))
            .map(function(b) { return b.getAttribute('data-cat-name'); });
        api('/save_category_order', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: names })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) showNotification('💾 Порядок категорий сохранён', 'success');
            else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    }

    /* ---------- Tag cloud ---------- */
    function buildTagCloud() {
        var cloud = $('tagsBar'); if (!cloud) return;
        cloud.innerHTML = '';
        var tags = Object.entries(allTagsFromServer || {}).sort(function(a, b) { return b[1] - a[1]; });
        var activeTags = lsGetJSON(LS_KEYS.activeTags, []);
        if (!tags.length) { cloud.style.display = 'none'; return; }
        cloud.style.display = '';
        tags.forEach(function(pair) {
            var name = pair[0], count = pair[1];
            var el = document.createElement('button');
            el.className = 'tag-cloud-item' + (activeTags.indexOf(name) !== -1 ? ' active' : '');
            el.type = 'button';
            el.innerHTML = '#' + escapeHtml(name) + '<span class="tag-count">' + count + '</span>';
            el.addEventListener('click', function() {
                var act = lsGetJSON(LS_KEYS.activeTags, []);
                if (act.indexOf(name) !== -1) act = act.filter(function(t) { return t !== name; });
                else act.push(name);
                lsSetJSON(LS_KEYS.activeTags, act);
                this.classList.toggle('active');
                resetCategoryToAll();
                applyFilters();
            });
            cloud.appendChild(el);
        });
    }
    buildTagCloud();

    /* ---------- Manual sort cards ---------- */
    var manualModeEnabled = false;
    function updateManualHint() { if (manualHint) manualHint.classList.toggle('visible', manualModeEnabled); }
    function enableManualCardSort(enable) {
        manualModeEnabled = enable;
        if (cardsGrid) cardsGrid.classList.toggle('manual-sort', enable);
        updateManualHint();
    }
    if (cardsGrid) {
        makeSortable(cardsGrid, '.card', '.card-header', function() {
            var order = [];
            cardsGrid.querySelectorAll('.card').forEach(function(c) {
                var g = c.getAttribute('data-group'); if (g) order.push(g);
            });
            api('/save_card_order', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order: order })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) showNotification('💾 Порядок сохранён', 'success');
                else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
            }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
        }, function() { return manualModeEnabled; });
    }
    setupLinkDrag();

    /* ---------- Theme ---------- */
    // ИЗМЕНЕНО: дефолт — light
    applyTheme(lsGet(LS_KEYS.theme, DEFAULT_THEME));
    document.querySelectorAll('.theme-dot').forEach(function(dot) {
        dot.addEventListener('click', function() { applyTheme(this.getAttribute('data-theme')); });
    });

    /* ---------- Sidebar ---------- */
    function updateSidebarFloatToggle() {
        if (!sidebar || !sidebarFloatToggle) return;
        var isCollapsed = sidebar.classList.contains('collapsed');
        var isMobile = window.innerWidth <= 992;
        sidebarFloatToggle.classList.toggle('visible', isCollapsed && !isMobile);
    }
    if (lsGet(LS_KEYS.sidebarCollapsed, 'false') === 'true' && window.innerWidth > 992 && sidebar) sidebar.classList.add('collapsed');
    updateSidebarFloatToggle();
    var sidebarToggle = $('sidebarToggle');
    if (sidebarToggle) sidebarToggle.addEventListener('click', function() {
        sidebar.classList.add('collapsed'); lsSet(LS_KEYS.sidebarCollapsed, 'true'); updateSidebarFloatToggle();
    });
    if (sidebarFloatToggle) sidebarFloatToggle.addEventListener('click', function() {
        sidebar.classList.remove('collapsed'); lsSet(LS_KEYS.sidebarCollapsed, 'false'); updateSidebarFloatToggle();
    });
    var burgerBtn = $('burgerBtn');
    if (burgerBtn) burgerBtn.addEventListener('click', function() {
        sidebar.classList.toggle('open'); sidebarOverlay.classList.toggle('open');
    });
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', function() {
        sidebar.classList.remove('open'); sidebarOverlay.classList.remove('open');
    });
    window.addEventListener('resize', updateSidebarFloatToggle);
    function closeMobileSidebar() {
        if (window.innerWidth <= 992 && sidebar) {
            sidebar.classList.remove('open'); sidebarOverlay.classList.remove('open');
        }
    }

    /* ---------- Font / radius / sidebar width ---------- */
    var savedFontSize = lsGet(LS_KEYS.fontSize, '14');
    document.documentElement.style.fontSize = savedFontSize + 'px';
    var fsSlider = $('fontSizeSlider'), fsVal = $('fontSizeVal');
    if (fsSlider) {
        fsSlider.value = savedFontSize;
        if (fsVal) fsVal.textContent = savedFontSize;
        fsSlider.addEventListener('input', function() {
            document.documentElement.style.fontSize = this.value + 'px';
            if (fsVal) fsVal.textContent = this.value;
            lsSet(LS_KEYS.fontSize, this.value);
        });
    }
    var savedRadius = lsGet(LS_KEYS.radius, '16');
    document.documentElement.style.setProperty('--radius-card', savedRadius + 'px');
    var rSlider = $('radiusSlider'), rVal = $('radiusVal');
    if (rSlider) {
        rSlider.value = savedRadius;
        if (rVal) rVal.textContent = savedRadius;
        rSlider.addEventListener('input', function() {
            document.documentElement.style.setProperty('--radius-card', this.value + 'px');
            if (rVal) rVal.textContent = this.value;
            lsSet(LS_KEYS.radius, this.value);
        });
    }
    var savedSidebarWidth = lsGet(LS_KEYS.sidebarWidth, '260');
    document.documentElement.style.setProperty('--sidebar-width', savedSidebarWidth + 'px');
    var swSlider = $('sidebarWidthSlider'), swVal = $('sidebarWidthVal');
    if (swSlider) {
        swSlider.value = savedSidebarWidth;
        if (swVal) swVal.textContent = savedSidebarWidth;
        swSlider.addEventListener('input', function() {
            document.documentElement.style.setProperty('--sidebar-width', this.value + 'px');
            if (swVal) swVal.textContent = this.value;
            lsSet(LS_KEYS.sidebarWidth, this.value);
        });
    }

    /* ---------- Columns ---------- */
    var savedCols = lsGet(LS_KEYS.cols, '2');
    function applyColumns(cols) {
        if (!cardsGrid) return;
        cardsGrid.className = cardsGrid.className.replace(/cols-\d+/g, '').trim();
        cardsGrid.classList.add('cols-' + cols);
        document.documentElement.setAttribute('data-cols', cols);
    }
    window.__applyColumns = applyColumns;
    applyColumns(savedCols);
    document.querySelectorAll('.col-btn[data-cols]').forEach(function(btn) {
        btn.classList.toggle('active', btn.getAttribute('data-cols') === savedCols);
        btn.addEventListener('click', function() {
            var cols = this.getAttribute('data-cols');
            applyColumns(cols);
            document.querySelectorAll('.col-btn[data-cols]').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            lsSet(LS_KEYS.cols, cols);
        });
    });

    /* ---------- Active category from localStorage ---------- */
    var savedCategory = lsGet(LS_KEYS.activeCategory, 'all');
    var categoryFound = false;
    document.querySelectorAll('.cat-btn').forEach(function(btn) {
        if (btn.getAttribute('data-filter') === savedCategory) categoryFound = true;
    });
    var effectiveCategory = categoryFound ? savedCategory : 'all';
    document.querySelectorAll('.cat-btn').forEach(function(btn) {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === effectiveCategory);
    });
    if (!categoryFound) lsSet(LS_KEYS.activeCategory, 'all');

    if (filterFavBtn) {
        var savedShowFav = lsGet(LS_KEYS.showFavorites, 'false') === 'true';
        if (savedShowFav) {
            filterFavBtn.classList.add('active');
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
        }
        filterFavBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            var isActive = this.classList.contains('active');
            lsSet(LS_KEYS.showFavorites, isActive ? 'true' : 'false');
            if (isActive) document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            else {
                var activeCat = lsGet(LS_KEYS.activeCategory, 'all');
                document.querySelectorAll('.cat-btn').forEach(function(b) {
                    if (b.getAttribute('data-filter') === activeCat) b.classList.add('active');
                });
            }
            applyFilters(); closeMobileSidebar();
        });
    }
    document.querySelectorAll('.cat-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            if (filterFavBtn) filterFavBtn.classList.remove('active');
            lsSet(LS_KEYS.showFavorites, 'false');
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            lsSet(LS_KEYS.activeCategory, this.getAttribute('data-filter'));
            applyFilters(); closeMobileSidebar();
        });
    });

    /* ---------- Search ---------- */
    var savedSearch = lsGet(LS_KEYS.searchQuery, '');
    if (savedSearch && searchInput) searchInput.value = savedSearch;
    var _lastSearchWasEmpty = !savedSearch || savedSearch.trim() === '';
    var searchDebounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchDebounceTimer);
            var val = this.value;
            searchDebounceTimer = setTimeout(function() {
                lsSet(LS_KEYS.searchQuery, val);
                var isEmpty = (val.trim() === '');
                if (!isEmpty && _lastSearchWasEmpty) resetCategoryToAll();
                _lastSearchWasEmpty = isEmpty;
                applyFilters();
                highlightSearch(val);
            }, 150);
        });
        searchInput.addEventListener('focus', showSearchHistory);
        searchInput.addEventListener('blur', function() { setTimeout(hideSearchHistory, 200); });
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                var history = lsGetJSON(LS_KEYS.searchHistory, []);
                var q = this.value.trim();
                var filtered = history.filter(function(x) { return x !== q; });
                filtered.unshift(q);
                lsSetJSON(LS_KEYS.searchHistory, filtered.slice(0, 10));
            }
        });
    }
    function showSearchHistory() {
        var history = lsGetJSON(LS_KEYS.searchHistory, []);
        var histEl = $('searchHistory'), listEl = $('searchHistoryList');
        if (!histEl || !listEl) return;
        if (!history.length) { histEl.classList.remove('show'); return; }
        listEl.innerHTML = history.map(function(q) {
            return '<button class="history-item" data-q="' + escapeHtml(q) + '">' + escapeHtml(q) + '</button>';
        }).join('');
        listEl.querySelectorAll('.history-item').forEach(function(btn) {
            btn.addEventListener('mousedown', function(e) {
                e.preventDefault();
                searchInput.value = this.getAttribute('data-q');
                lsSet(LS_KEYS.searchQuery, searchInput.value);
                applyFilters(); highlightSearch(searchInput.value); hideSearchHistory();
            });
        });
        histEl.classList.add('show');
    }
    function hideSearchHistory() { var histEl = $('searchHistory'); if (histEl) histEl.classList.remove('show'); }
    var clearSearchHistoryBtn = $('clearSearchHistory');
    if (clearSearchHistoryBtn) clearSearchHistoryBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        lsSetJSON(LS_KEYS.searchHistory, []);
        hideSearchHistory();
    });

    /* ---------- Collapsed cards ---------- */
    var collapsedCards = lsGetJSON(LS_KEYS.collapsedCards, []);
    document.querySelectorAll('.card').forEach(function(card) {
        var groupName = card.getAttribute('data-group');
        if (collapsedCards.indexOf(groupName) !== -1) card.classList.add('collapsed');
    });
    document.querySelectorAll('.card-header').forEach(function(header) {
        header.addEventListener('click', function(e) {
            if (e.target.closest('.rename-group-btn')) return;
            if (e.target.closest('.card-sort-btn')) return;
            if (e.target.closest('.bulk-checkbox-card')) return;
            if (e.target.closest('.card-icon')) return;
            var card = this.closest('.card'); if (!card) return;
            card.classList.toggle('collapsed');
            var collapsed = [];
            document.querySelectorAll('.card.collapsed').forEach(function(c) { collapsed.push(c.getAttribute('data-group')); });
            lsSetJSON(LS_KEYS.collapsedCards, collapsed);
        });
    });

    var collapseAllBtn = $('collapseAllBtn');
    if (collapseAllBtn) {
        var allCollapsed = lsGet(LS_KEYS.allCollapsed, 'false') === 'true';
        var applyAllCollapsed = function(state) {
            document.querySelectorAll('.card').forEach(function(c) {
                if (state) c.classList.add('collapsed'); else c.classList.remove('collapsed');
            });
            var collapsed = [];
            if (state) document.querySelectorAll('.card').forEach(function(c) { collapsed.push(c.getAttribute('data-group')); });
            lsSetJSON(LS_KEYS.collapsedCards, collapsed);
            collapseAllBtn.title = state ? 'Развернуть все' : 'Свернуть все';
        };
        collapseAllBtn.addEventListener('click', function() {
            allCollapsed = !allCollapsed;
            lsSet(LS_KEYS.allCollapsed, allCollapsed ? 'true' : 'false');
            applyAllCollapsed(allCollapsed);
        });
    }

    /* ---------- Sort cards ---------- */
    var savedSortField = lsGet(LS_KEYS.sortField, '');
    var savedSortAsc = lsGet(LS_KEYS.sortAsc, 'true') === 'true';
    if (savedSortField === 'manual') {
        updateSortButtonsUI('manual', true); enableManualCardSort(true);
    } else if (savedSortField) {
        applySort(savedSortField, savedSortAsc);
        updateSortButtonsUI(savedSortField, savedSortAsc);
    }
    document.querySelectorAll('.sort-btn[data-sort]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var field = this.getAttribute('data-sort'); if (!field) return;
            if (field === 'manual') {
                lsSet(LS_KEYS.sortField, 'manual');
                updateSortButtonsUI('manual', true); enableManualCardSort(true);
                showNotification('🔀 Ручной режим включён', 'success');
                return;
            }
            enableManualCardSort(false);
            var currentField = lsGet(LS_KEYS.sortField, '');
            var currentAsc = lsGet(LS_KEYS.sortAsc, 'true') === 'true';
            var newAsc = (currentField === field) ? !currentAsc : true;
            lsSet(LS_KEYS.sortField, field);
            lsSet(LS_KEYS.sortAsc, newAsc ? 'true' : 'false');
            applySort(field, newAsc);
            updateSortButtonsUI(field, newAsc);
        });
    });
    function updateSortButtonsUI(field, asc) {
        document.querySelectorAll('.sort-btn[data-sort]').forEach(function(btn) {
            btn.classList.remove('active');
            var arrow = btn.querySelector('.sort-arrow');
            if (arrow) arrow.textContent = '';
        });
        if (field) {
            var activeBtn = document.querySelector('.sort-btn[data-sort="' + field + '"]');
            if (activeBtn) {
                activeBtn.classList.add('active');
                var arrow = activeBtn.querySelector('.sort-arrow');
                if (arrow && field !== 'manual') arrow.textContent = asc ? '▲' : '▼';
            }
        }
    }
    function applySort(field, asc) {
        if (!field || field === 'manual' || !cardsGrid) return;
        var cards = Array.from(cardsGrid.querySelectorAll('.card'));
        if (!cards.length) return;
        cards.sort(function(a, b) {
            var va, vb;
            if (field === 'name') {
                va = (a.getAttribute('data-group') || '').toLowerCase();
                vb = (b.getAttribute('data-group') || '').toLowerCase();
            } else if (field === 'category') {
                va = ((a.getAttribute('data-categories') || '').split('|')[0] || '').toLowerCase();
                vb = ((b.getAttribute('data-categories') || '').split('|')[0] || '').toLowerCase();
            } else if (field === 'date') {
                va = a.getAttribute('data-updated') || '';
                vb = b.getAttribute('data-updated') || '';
            }
            if (va < vb) return asc ? -1 : 1;
            if (va > vb) return asc ? 1 : -1;
            return 0;
        });
        cards.forEach(function(card) { cardsGrid.appendChild(card); });
    }

    /* ---------- Highlight search ---------- */
    function highlightSearch(query) {
        var q = (query || '').trim();
        document.querySelectorAll('[data-original]').forEach(function(el) {
            var orig = el.getAttribute('data-original');
            if (orig !== null) el.innerHTML = escapeHtml(orig);
        });
        if (!q) return;
        var cleaned = q.replace(/\b(cat|tag|fav|updated|status):\S+/gi, '').trim();
        if (!cleaned) return;
        var qLower = cleaned.toLowerCase();
        document.querySelectorAll('.card-title[data-original], .desc[data-original]').forEach(function(el) {
            var card = el.closest('.card');
            if (card && card.style.display === 'none') return;
            var orig = el.getAttribute('data-original') || '';
            var idx = orig.toLowerCase().indexOf(qLower);
            if (idx === -1) return;
            var before = orig.slice(0, idx);
            var match = orig.slice(idx, idx + cleaned.length);
            var after = orig.slice(idx + cleaned.length);
            el.innerHTML = escapeHtml(before) + '<mark>' + escapeHtml(match) + '</mark>' + escapeHtml(after);
        });
    }

    /* ---------- Filters ---------- */
    function parseSearchQuery(raw) {
        var result = { text: '', categories: [], tags: [], favorite: null, updatedAfter: null, updatedBefore: null, status: [] };
        if (!raw) return result;
        var tokens = raw.match(/(?:[^\s"]+|"[^"]*")+/g) || [];
        var textParts = [];
        tokens.forEach(function(tok) {
            var m = tok.match(/^(cat|tag|fav|updated|status):(.*)$/i);
            if (!m) { textParts.push(tok.replace(/^"|"$/g, '')); return; }
            var key = String(m[1] || '').toLowerCase();
            var value = String(m[2] || '').replace(/^"|"$/g, '');
            if (key === 'cat') { if (value) result.categories.push(value); }
            else if (key === 'tag') { if (value) result.tags.push(value); }
            else if (key === 'status') { if (value) result.status.push(value.toLowerCase()); }
            else if (key === 'fav') result.favorite = (value === '1' || value.toLowerCase() === 'true');
            else if (key === 'updated') {
                if (!value) return;
                if (value.charAt(0) === '>') result.updatedAfter = value.slice(1);
                else if (value.charAt(0) === '<') result.updatedBefore = value.slice(1);
            }
        });
        result.text = textParts.join(' ').toLowerCase().trim();
        return result;
    }
    function applyFilters() {
        if (_filterIndexDirty) buildFilterIndex();
        var rawQuery = searchInput ? searchInput.value : '';
        var q = parseSearchQuery(rawQuery);
        var activeCatBtn = document.querySelector('.cat-btn.active');
        var activeCat = activeCatBtn ? activeCatBtn.getAttribute('data-filter') : 'all';
        var showFav = filterFavBtn ? filterFavBtn.classList.contains('active') : false;
        var activeTags = lsGetJSON(LS_KEYS.activeTags, []);
        var statusCache = window.__statusCache || {};
        var activeCatLower = activeCat.toLowerCase();
        var cardState = new Map();
        document.querySelectorAll('.card').forEach(function(card) {
            cardState.set(card, { anyVisible: false, anyFav: false });
        });
        for (var i = 0; i < _filterIndex.length; i++) {
            var item = _filterIndex[i];
            var li = item.el, card = item.card;
            var cardCatOK = true;
            if (activeCat !== '__none__' && activeCat !== 'all') {
                if (item.cardCats.indexOf(activeCatLower) === -1) cardCatOK = false;
            }
            if (cardCatOK && q.categories.length) {
                cardCatOK = q.categories.some(function(c) { return item.cardCats.indexOf(String(c).toLowerCase()) !== -1; });
            }
            var visible = true;
            if (visible && q.text) {
                var base = item.group + ' ' + item.link + ' ' + item.fullLink + ' ' + item.desc + ' ' + item.cat + ' ' + item.code;
                if (base.indexOf(q.text) === -1) visible = false;
            }
            if (visible && activeCat === '__none__') { if (item.cat) visible = false; }
            if (visible && activeCat !== 'all' && activeCat !== '__none__') {
                if (!item.cat || item.cat !== activeCatLower) visible = false;
            }
            if (visible && q.categories.length) {
                if (!q.categories.some(function(c) { return item.cat === c.toLowerCase(); })) visible = false;
            }
            if (visible && q.tags.length) {
                if (!q.tags.every(function(t) { return item.tags.indexOf(t.toLowerCase()) !== -1; })) visible = false;
            }
            if (visible && activeTags.length) {
                if (!activeTags.some(function(t) { return item.tags.indexOf(t.toLowerCase()) !== -1; })) visible = false;
            }
            if (visible && showFav && !item.fav) visible = false;
            if (visible && q.favorite !== null) {
                if (q.favorite && !item.fav) visible = false;
                if (!q.favorite && item.fav) visible = false;
            }
            if (visible && (q.updatedAfter || q.updatedBefore)) {
                if (q.updatedAfter && item.updated < q.updatedAfter) visible = false;
                if (q.updatedBefore && item.updated > q.updatedBefore) visible = false;
            }
            if (visible && q.status.length) {
                var st = (statusCache[item.id] && statusCache[item.id].status) || 'unknown';
                if (q.status.indexOf(st) === -1) visible = false;
            }
            if (visible && cardCatOK) {
                li.classList.remove('hidden');
                var st2 = cardState.get(card);
                if (st2) { st2.anyVisible = true; if (item.fav) st2.anyFav = true; }
            } else li.classList.add('hidden');
        }
        var anyVisible = false, anyFavVisible = false;
        cardState.forEach(function(state, card) {
            if (state.anyVisible) {
                card.style.display = ''; anyVisible = true;
                if (state.anyFav) anyFavVisible = true;
            } else card.style.display = 'none';
        });
        var noFav = cardsGrid ? cardsGrid.querySelector('.no-fav-msg') : null;
        if (showFav && !anyFavVisible && anyVisible) {
            if (!noFav && cardsGrid) {
                var msg = document.createElement('div');
                msg.className = 'no-data no-fav-msg';
                msg.textContent = '⭐ Нет избранных записей';
                cardsGrid.appendChild(msg);
            }
        } else if (noFav) noFav.remove();
        var noResults = cardsGrid ? cardsGrid.querySelector('.no-results-msg') : null;
        if (!anyVisible && !showFav) {
            if (!noResults && cardsGrid) {
                var msg2 = document.createElement('div');
                msg2.className = 'no-data no-results-msg';
                msg2.textContent = '🔍 Ничего не найдено';
                cardsGrid.appendChild(msg2);
            }
        } else if (noResults) noResults.remove();
    }
    try {
        applyFilters();
    } catch (e) {
        console.error('[applyFilters initial] FAILED:', e);
    }
    try {
        if (savedSearch) highlightSearch(savedSearch);
    } catch (e) {
        console.error('[highlightSearch initial] FAILED:', e);
    }

    /* ---------- Favorite button ---------- */
    document.querySelectorAll('.favorite-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var id = this.getAttribute('data-id'); if (!id) return;
            // Сохраняем текущую тему перед reload
            var currentTheme = lsGet(LS_KEYS.theme, DEFAULT_THEME);
            api('/toggle_favorite/' + id, { method: 'POST' })
                .then(function(r) {
                    if (r.ok) {
                        lsSet(LS_KEYS.theme, currentTheme);
                        location.reload();
                    } else alert('Ошибка');
                })
                .catch(function() { alert('Ошибка сети'); });
        });
    });

    /* ---------- Delete button ---------- */
    document.querySelectorAll('.delete-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var id = this.getAttribute('data-id');
            var linkItem = this.closest('.link-item');
            if (!id || !linkItem) return;
            var linkText = linkItem.querySelector('.link-display') ? linkItem.querySelector('.link-display').textContent : '';
            var groupName = linkItem.closest('.card') ? linkItem.closest('.card').getAttribute('data-group') : '';
            var messageHtml = groupName
                ? 'Удалить запись <span class="confirm-highlight">' + escapeHtml(linkText) + '</span> из группы <span class="confirm-highlight">' + escapeHtml(groupName) + '</span>?'
                : 'Удалить запись <span class="confirm-highlight">' + escapeHtml(linkText) + '</span>?';
            showConfirm('🗑 Удаление записи', messageHtml, '🗑 Удалить', function() {
                apiWithLockGuard('/delete/' + id, { method: 'POST' })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!data.success) { alert(data.error || 'Ошибка'); return; }
                        linkItem.style.opacity = '0.35';
                        linkItem.style.pointerEvents = 'none';
                        var undoId = id, undoItem = linkItem;
                        var undone = false;
                        showUndoToast('Запись удалена. Ctrl+Z — вернуть', function() {
                            undone = true;
                            apiFetch('/restore_from_trash/' + undoId, { method: 'POST' })
                                .then(function() {
                                    undoItem.style.opacity = '';
                                    undoItem.style.pointerEvents = '';
                                    showNotification('↩ Восстановлено', 'success');
                                })
                                .catch(function() { showNotification('❌ Не удалось', 'error'); });
                        }, 8000);
                        setTimeout(function() {
                            if (undone) return;
                            if (undoItem.parentNode) {
                                var card = undoItem.closest('.card');
                                undoItem.remove();
                                if (card && card.querySelectorAll('.link-item').length === 0) card.remove();
                                _filterIndexDirty = true;
                            }
                        }, 8100);
                    })
                    .catch(function(err) {
                        if (err && err.message === 'ExcelLock') return;
                        alert('Ошибка сети');
                    });
            });
        });
    });

    /* ---------- Add modal ---------- */
    var openAddModalBtn = $('openAddModal');
    if (openAddModalBtn) openAddModalBtn.addEventListener('click', function() {
        if (window.__reestrLog) window.__reestrLog('log', 'Click: #openAddModal');
        var m = $('addModal');
        if (!m) {
            if (window.__reestrLog) window.__reestrLog('error', '#addModal не найден в DOM');
            return;
        }
        m.classList.add('active');
        try {
            if (typeof window.__prepareAddModal === 'function') {
                window.__prepareAddModal();
            }
        } catch (e) {
            if (window.__reestrLog) window.__reestrLog('error', 'prepareAddModal: ' + e.message, e.stack || '');
        }
        setTimeout(function() { var n = $('name'); if (n) n.focus(); }, 100);
    });
    var closeAddModalBtn = $('closeAddModalBtn');
    if (closeAddModalBtn) closeAddModalBtn.addEventListener('click', function() { var m = $('addModal'); if (m) m.classList.remove('active'); });
    var addModal = $('addModal');
    if (addModal) addModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    var closeEditModalBtn = $('closeEditModalBtn');
    if (closeEditModalBtn) closeEditModalBtn.addEventListener('click', function() { var m = $('editModal'); if (m) m.classList.remove('active'); });
    var editModal = $('editModal');
    if (editModal) editModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    var confirmCancelBtn = $('confirmCancelBtn');
    if (confirmCancelBtn) confirmCancelBtn.addEventListener('click', function() {
        var m = $('confirmModal'); if (m) m.classList.remove('active');
        _confirmHandler = null;
    });
    var confirmOkBtn = $('confirmOkBtn');
    if (confirmOkBtn) confirmOkBtn.addEventListener('click', function() {
        var cb = _confirmHandler;
        var m = $('confirmModal'); if (m) m.classList.remove('active');
        _confirmHandler = null;
        if (cb) cb();
    });
    var confirmModalEl = $('confirmModal');
    if (confirmModalEl) confirmModalEl.addEventListener('click', function(e) {
        if (e.target === this) { this.classList.remove('active'); _confirmHandler = null; }
    });
    var undoToastBtn = $('undoToastBtn');
    if (undoToastBtn) undoToastBtn.addEventListener('click', function() {
        if (_undoTimer) clearTimeout(_undoTimer);
        var cb = _undoCallback;
        _undoCallback = null; _undoActionActive = false;
        var t = $('undoToast'); if (t) t.classList.remove('show');
        if (cb) cb();
    });

    /* ---------- Card sort dropdown ---------- */
    document.querySelectorAll('.card-sort-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var group = this.getAttribute('data-group'); if (!group) return;
            if (_activeSortBtn === this && _activeSortDropdown) { hideSortDropdown(); return; }
            showSortDropdown(this, group);
        });
    });
    document.addEventListener('click', function(e) {
        if (_activeSortDropdown && !e.target.closest('.card-sort-dropdown') && !e.target.closest('.card-sort-btn')) hideSortDropdown();
    });

    /* ---------- Page title reset ---------- */
    (function() {
        var pageTitle = document.querySelector('.page-title');
        if (!pageTitle) return;
        pageTitle.addEventListener('click', function() {
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            var allBtn = document.querySelector('.cat-btn[data-filter="all"]');
            if (allBtn) allBtn.classList.add('active');
            lsSet(LS_KEYS.activeCategory, 'all');
            if (filterFavBtn) filterFavBtn.classList.remove('active');
            lsSet(LS_KEYS.showFavorites, 'false');
            lsSetJSON(LS_KEYS.activeTags, []);
            buildTagCloud();
            if (searchInput) searchInput.value = '';
            lsSet(LS_KEYS.searchQuery, '');
            _lastSearchWasEmpty = true;
            highlightSearch('');
            applyFilters();
            try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) { window.scrollTo(0, 0); }
            showNotification('✅ Фильтры сброшены', 'success');
        });
    })();

    window.__state = {
        categorySortMode: categorySortMode, applyFilters: applyFilters,
        highlightSearch: highlightSearch, closeMobileSidebar: closeMobileSidebar,
        resetCategoryToAll: resetCategoryToAll, closeAppearanceModal: closeAppearanceModal,
        filterFavBtn: filterFavBtn, searchInput: searchInput, cardsGrid: cardsGrid,
        categoryManualOrder: categoryManualOrder, categoryColors: categoryColors,
        allTagsFromServer: allTagsFromServer, buildTagCloud: buildTagCloud,
        prepareAddModal: prepareAddModal, updateNamesDatalist: updateNamesDatalist,
        markIndexDirty: function() { _filterIndexDirty = true; }
    };
}

/* ============================================================
   ============================================================
   INIT EXTENDED
   ============================================================
   ============================================================ */
function initExtended() {
    var cardsGrid = $('cardsGrid');
    var searchInput = $('searchInput');

    window.addEventListener('scroll', function() {
        if (_scrollRaf) return;
        _scrollRaf = requestAnimationFrame(function() {
            _hideLinkTooltipGlobal();
            hideSortDropdown();
            _scrollRaf = null;
        });
    }, { passive: true, capture: true });
    window.addEventListener('resize', function() {
        _hideLinkTooltipGlobal(); hideSortDropdown();
    });

    /* ---------- Bootstrap ---------- */
    (function loadBootstrap() {
        apiFetch('/api/bootstrap')
            .then(function(r) { return r.json(); })
            .then(function(boot) {
                if (boot.settings) {
                    if (boot.settings.profile) applyProfileLocal(boot.settings.profile);
                    if (Array.isArray(boot.settings.custom_toolbar_buttons))
                        applyCustomToolbarButtonsLocal(boot.settings.custom_toolbar_buttons);
                }
                if (boot.all_tags && typeof boot.all_tags === 'object') {
                    allTagsFromServer = boot.all_tags;
                    if (window.__state && window.__state.buildTagCloud) window.__state.buildTagCloud();
                }
                if (boot.plugins) renderPluginsList(boot.plugins);
            })
            .catch(function() {});
    })();

    // ИЗМЕНЕНО: рендер в виде компактных плиток (grid),
    // с обрезкой описания по line-clamp и полным текстом в title.
    function renderPluginsList(info) {
        var list = $('pluginsList'); if (!list) return;
        var loaded = (info && info.loaded) || [];
        var errors = (info && info.errors) || [];
        if (!loaded.length && !errors.length) {
            list.innerHTML = '<div class="plugins-brief-loading">Плагины не установлены</div>';
            return;
        }
        var html = '';
        loaded.forEach(function(p) {
            html += '<div class="plugin-brief">'
                + '<div class="plugin-brief-name">✓ ' + escapeHtml(p.name)
                + ' <span class="plugin-brief-version">v' + escapeHtml(p.version) + '</span></div>'
                + (p.description
                    ? '<div class="plugin-brief-desc" title="' + escapeHtml(p.description) + '">'
                      + escapeHtml(p.description) + '</div>'
                    : '')
                + '</div>';
        });
        errors.forEach(function(e) {
            html += '<div class="plugin-brief plugin-brief-err">'
                + '<div class="plugin-brief-name">✗ ' + escapeHtml(e.file) + '</div>'
                + '<div class="plugin-brief-desc" title="' + escapeHtml(e.error) + '">'
                + escapeHtml(e.error) + '</div>'
                + '</div>';
        });
        list.innerHTML = html;
    }

    /* ---------- Meta chips ---------- */
    document.querySelectorAll('.link-meta .tag-chip[data-tag]').forEach(function(chip) {
        chip.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var tag = this.getAttribute('data-tag'); if (!tag) return;
            var act = lsGetJSON(LS_KEYS.activeTags, []);
            var idx = act.indexOf(tag);
            if (idx === -1) act.push(tag); else act.splice(idx, 1);
            lsSetJSON(LS_KEYS.activeTags, act);
            if (window.__state && window.__state.resetCategoryToAll) window.__state.resetCategoryToAll();
            if (window.__state && window.__state.buildTagCloud) window.__state.buildTagCloud();
            if (window.__state && window.__state.applyFilters) window.__state.applyFilters();
        });
    });
    document.querySelectorAll('.link-meta .category-tag[data-category]').forEach(function(tag) {
        tag.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var cat = this.getAttribute('data-category'); if (!cat) return;
            var btn = Array.from(document.querySelectorAll('.cat-btn')).find(function(b) {
                return b.getAttribute('data-filter') === cat;
            });
            if (btn) btn.click();
            else showNotification('❌ Категория не найдена', 'error');
        });
    });

    /* ---------- meta-created → history ---------- */
    document.querySelectorAll('.meta-created[data-id]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var rid = this.getAttribute('data-id');
            var logsModal = document.getElementById('pluginLogsModal');
            if (logsModal && typeof openPluginModal === 'function') {
                if (typeof window.__logsOpen === 'function') {
                    window.__logsOpen({record_id: rid});
                } else {
                    openPluginModal('pluginLogsModal');
                }
            } else {
                showNotification('ℹ️ Плагин «Журнал» не установлен', 'error');
            }
        });
    });

    /* ---------- Categories modal ---------- */
    var categoriesModal = $('categoriesModal');
    var manageCategoriesBtn = $('manageCategoriesBtn');
    if (manageCategoriesBtn && categoriesModal) {
        manageCategoriesBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            loadCategories();
            categoriesModal.classList.add('active');
            if (window.__state && window.__state.closeMobileSidebar) window.__state.closeMobileSidebar();
        });
    }
    var closeCategoriesModalBtn = $('closeCategoriesModalBtn');
    if (closeCategoriesModalBtn && categoriesModal) closeCategoriesModalBtn.addEventListener('click', function() { categoriesModal.classList.remove('active'); });
    if (categoriesModal) categoriesModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });

    var categoryColorsLocal = {};
    for (var k1 in (DATA.category_colors || {})) categoryColorsLocal[k1] = DATA.category_colors[k1];
    var categoryManualOrderLocal = (DATA.category_manual_order || []).slice();

    window.addEventListener('reestr:category-order-changed', function(e) {
        if (e.detail && Array.isArray(e.detail.order)) {
            categoryManualOrderLocal = e.detail.order.slice();
        }
    });

    var categoryListEl = $('categoryList');
    if (categoryListEl) {
        categoryListEl.addEventListener('click', function(e) {
            var btn = e.target.closest('[data-action]');
            if (!btn || btn.tagName === 'INPUT') return;
            var action = btn.getAttribute('data-action');
            var item = btn.closest('.category-item');
            var cat = item ? item.getAttribute('data-category') : '';
            if (!cat) return;
            if (action === 'up') window.moveCategoryUp(cat);
            else if (action === 'down') window.moveCategoryDown(cat);
            else if (action === 'rename') window.startRename(cat);
            else if (action === 'delete') window.deleteCategory(cat);
            else if (action === 'save-rename') window.saveRename(cat, btn);
        });
        categoryListEl.addEventListener('change', function(e) {
            var inp = e.target.closest('input[type="color"][data-action="color"]');
            if (!inp) return;
            var item = inp.closest('.category-item');
            var cat = item ? item.getAttribute('data-category') : '';
            if (!cat) return;
            window.updateCategoryColor(cat, inp.value);
        });
        categoryListEl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.target && e.target.matches('input[type="text"]')) {
                e.preventDefault();
                var item = e.target.closest('.category-item');
                var cat = item ? item.getAttribute('data-category') : '';
                var saveBtn = item ? item.querySelector('[data-action="save-rename"]') : null;
                if (cat && saveBtn) window.saveRename(cat, saveBtn);
            }
        });
    }
    function loadCategories() {
        api('/get_categories').then(function(r) { return r.json(); }).then(function(data) {
            var list = $('categoryList'); if (!list) return;
            if (data.length === 0) {
                list.innerHTML = '<p style="color:var(--meta-color); text-align:center;">Нет категорий</p>';
                return;
            }
            var idx = new Map(categoryManualOrderLocal.map(function(n, i) { return [n, i]; }));
            data.sort(function(a, b) {
                var ia = idx.has(a) ? idx.get(a) : 999999;
                var ib = idx.has(b) ? idx.get(b) : 999999;
                if (ia !== ib) return ia - ib;
                return a.localeCompare(b, 'ru');
            });
            var html = '';
            data.forEach(function(cat, i) {
                var color = categoryColorsLocal[cat] || '#f5d76e';
                var isFirst = i === 0, isLast = i === data.length - 1;
                html += '<div class="category-item" data-category="' + escapeHtml(cat) + '">'
                    + '<div class="cat-order-buttons">'
                    + '<button type="button" class="cat-order-btn" ' + (isFirst ? 'disabled' : '') + ' data-action="up">▲</button>'
                    + '<button type="button" class="cat-order-btn" ' + (isLast ? 'disabled' : '') + ' data-action="down">▼</button>'
                    + '</div>'
                    + '<span class="cat-name">' + escapeHtml(cat) + '</span>'
                    + '<div class="cat-actions">'
                    + '<span class="color-picker"><input type="color" value="' + color + '" data-action="color"></span>'
                    + '<button type="button" class="rename-btn" data-action="rename" title="Переименовать">✏️</button>'
                    + '<button type="button" class="delete-cat-btn" data-action="delete" title="Удалить">🗑</button>'
                    + '</div></div>';
            });
            list.innerHTML = html;
        }).catch(function() {
            var list = $('categoryList');
            if (list) list.innerHTML = '<p style="color:#e74c3c; text-align:center;">Ошибка</p>';
        });
    }
    function saveCategoryOrderFromModal(order) {
        categoryManualOrderLocal = order;
        api('/save_category_order', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order: order })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) showNotification('💾 Порядок сохранён', 'success');
            else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    }
    function getFullCategoryOrderFromModal() {
        var modalCats = Array.from(document.querySelectorAll('#categoryList .category-item'))
            .map(function(el) { return el.getAttribute('data-category'); }).filter(Boolean);
        var order = modalCats.slice();
        categoryManualOrderLocal.forEach(function(c) { if (order.indexOf(c) === -1) order.push(c); });
        return order;
    }
    window.moveCategoryUp = function(catName) {
        var order = getFullCategoryOrderFromModal();
        var idx = order.indexOf(catName);
        if (idx <= 0) return;
        var tmp = order[idx - 1]; order[idx - 1] = order[idx]; order[idx] = tmp;
        saveCategoryOrderFromModal(order); loadCategories();
    };
    window.moveCategoryDown = function(catName) {
        var order = getFullCategoryOrderFromModal();
        var idx = order.indexOf(catName);
        if (idx === -1 || idx >= order.length - 1) return;
        var tmp = order[idx + 1]; order[idx + 1] = order[idx]; order[idx] = tmp;
        saveCategoryOrderFromModal(order); loadCategories();
    };
    window.startRename = function(oldName) {
        var item = document.querySelector('.category-item[data-category="' + oldName + '"]');
        if (!item) return;
        var nameSpan = item.querySelector('.cat-name');
        var actions = item.querySelector('.cat-actions');
        var input = document.createElement('input');
        input.type = 'text'; input.value = oldName;
        nameSpan.innerHTML = ''; nameSpan.appendChild(input); input.focus();
        actions.innerHTML = '<button type="button" class="save-btn" data-action="save-rename">💾</button>'
            + '<button type="button" class="cancel-btn" data-action="cancel-rename">✖</button>';
        var cancelBtn = actions.querySelector('[data-action="cancel-rename"]');
        if (cancelBtn) cancelBtn.addEventListener('click', function() { loadCategories(); });
    };
    window.saveRename = function(oldName, btn) {
        var item = btn.closest('.category-item'); if (!item) return;
        var input = item.querySelector('input[type="text"]'); if (!input) return;
        var newName = input.value.trim();
        if (!newName || newName === oldName) { loadCategories(); return; }
        apiWithLockGuard('/rename_category', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_name: oldName, new_name: newName })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) { showNotification('✅ Переименована', 'success'); location.reload(); }
            else showNotification('❌ ' + data.error, 'error');
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    };
    window.deleteCategory = function(catName) {
        showConfirm('🗑 Удаление категории',
            'Удалить категорию <span class="confirm-highlight">' + escapeHtml(catName) + '</span>?<br><br>Записи останутся.',
            '🗑 Удалить',
            function() {
                apiWithLockGuard('/delete_category', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category: catName })
                }).then(function(r) { return r.json(); }).then(function(data) {
                    if (data.success) { showNotification('✅ Удалена', 'success'); location.reload(); }
                    else showNotification('❌ ' + data.error, 'error');
                }).catch(function(err) {
                    if (err && err.message === 'ExcelLock') return;
                    showNotification('❌ Ошибка сети', 'error');
                });
            });
    };
    window.updateCategoryColor = function(catName, color) {
        api('/update_category_color', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category: catName, color: color })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) {
                categoryColorsLocal[catName] = color;
                showNotification('✅ Цвет обновлён', 'success');
                setTimeout(function() { location.reload(); }, 400);
            } else showNotification('❌ ' + data.error, 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    };
    window.renameGroup = function(oldName) {
        var newName = prompt('Новое название:', oldName);
        if (newName === null || newName.trim() === '' || newName.trim() === oldName) return;
        apiWithLockGuard('/rename_group', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_name: oldName, new_name: newName.trim() })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) { showNotification('✅ Переименована', 'success'); location.reload(); }
            else showNotification('❌ ' + data.error, 'error');
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    };

    /* ---------- Category selectors ---------- */
    // ИЗМЕНЕНО: вместо style.display — класс .visible
    function setupCategorySelector(selectId, customId, hiddenId) {
        var select = $(selectId), custom = $(customId), hidden = $(hiddenId);
        if (!select || !custom || !hidden) return;
        function update() {
            hidden.value = (select.value === '__other__') ? custom.value.trim() : select.value;
        }
        function syncCustom() {
            if (select.value === '__other__') {
                custom.classList.add('visible');
                try { custom.focus(); } catch (e) {}
            } else {
                custom.classList.remove('visible');
                custom.value = '';
            }
            update();
        }
        update();
        syncCustom();
        select.addEventListener('change', syncCustom);
        custom.addEventListener('input', update);
    }
    setupCategorySelector('category_add', 'category_custom', 'category_hidden');
    setupCategorySelector('edit_category', 'edit_category_custom', 'edit_category_hidden');

    var catAddSelect = $('category_add');
    if (catAddSelect) catAddSelect.addEventListener('change', function() {
        var val = this.value === '__other__'
            ? (($('category_custom') && $('category_custom').value.trim()) || '')
            : (this.value || '');
        if (window.__state && window.__state.updateNamesDatalist) window.__state.updateNamesDatalist(val);
    });
    var catAddCustom = $('category_custom');
    if (catAddCustom) catAddCustom.addEventListener('input', function() {
        if (window.__state && window.__state.updateNamesDatalist) window.__state.updateNamesDatalist(this.value.trim() || '');
    });

    /* ---------- Tags input ---------- */
    function setupTagsInput(wrapperId, inputId, hiddenId, suggestionsId) {
        var wrapper = $(wrapperId), input = $(inputId);
        var hidden = $(hiddenId), suggestions = $(suggestionsId);
        if (!wrapper || !input || !hidden) return null;
        var tags = [];
        function render() {
            wrapper.querySelectorAll('.tags-chip').forEach(function(c) { c.remove(); });
            tags.forEach(function(t) {
                var chip = document.createElement('span');
                chip.className = 'tags-chip';
                chip.innerHTML = '#' + escapeHtml(t) + '<span class="remove-tag" data-tag="' + escapeHtml(t) + '">×</span>';
                wrapper.insertBefore(chip, input);
            });
            hidden.value = tags.join(',');
        }
        wrapper.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-tag')) {
                var t = e.target.getAttribute('data-tag');
                tags = tags.filter(function(x) { return x !== t; });
                render();
            } else input.focus();
        });
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                var val = this.value.trim().replace(/^#/, '').replace(/,/g, '');
                if (val && tags.indexOf(val) === -1) { tags.push(val); render(); }
                this.value = ''; hideSuggestions();
            } else if (e.key === 'Backspace' && this.value === '' && tags.length > 0) {
                tags.pop(); render();
            }
        });
        input.addEventListener('input', function() {
            var val = this.value.trim().toLowerCase();
            if (!val || !suggestions) { hideSuggestions(); return; }
            var allTags = Object.keys(allTagsFromServer || {});
            var matches = allTags.filter(function(t) { return t.toLowerCase().indexOf(val) !== -1 && tags.indexOf(t) === -1; }).slice(0, 8);
            if (!matches.length) { hideSuggestions(); return; }
            suggestions.innerHTML = matches.map(function(t) {
                return '<button type="button" data-tag="' + escapeHtml(t) + '">#' + escapeHtml(t) + '</button>';
            }).join('');
            suggestions.querySelectorAll('button').forEach(function(b) {
                b.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    var t = this.getAttribute('data-tag');
                    if (tags.indexOf(t) === -1) { tags.push(t); render(); }
                    input.value = ''; hideSuggestions();
                });
            });
            suggestions.classList.add('show');
        });
        function hideSuggestions() { if (suggestions) suggestions.classList.remove('show'); }
        input.addEventListener('blur', function() { setTimeout(hideSuggestions, 150); });
        return { setTags: function(arr) { tags = arr.slice(); render(); }, getTags: function() { return tags; } };
    }
    var tagsEditCtl = setupTagsInput('tagsEditWrapper', 'tagsEditInput', 'tags_edit', 'tagsEditSuggestions');
    setupTagsInput('tagsAddWrapper', 'tagsAddInput', 'tags_add', 'tagsAddSuggestions');

    /* ---------- Duplicate check ---------- */
    var linkInput = $('link');
    var dupWarn = $('duplicateWarn');
    var dupTimer = null;
    var _dupAbort = null;
    if (linkInput && dupWarn) {
        linkInput.addEventListener('input', function() {
            clearTimeout(dupTimer);
            var val = this.value.trim();
            if (!val || val.length < 5) { dupWarn.classList.remove('show'); dupWarn.textContent = ''; return; }
            dupTimer = setTimeout(function() {
                if (_dupAbort) try { _dupAbort.abort(); } catch (e) {}
                _dupAbort = new AbortController();
                apiFetch('/check_duplicate?url=' + encodeURIComponent(val), { signal: _dupAbort.signal })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.found && data.matches.length) {
                            var m = data.matches[0];
                            dupWarn.innerHTML = '⚠️ Похожая ссылка: <b>' + escapeHtml(m.name) + '</b>' + (m.category ? ' (' + escapeHtml(m.category) + ')' : '');
                            dupWarn.classList.add('show');
                        } else { dupWarn.classList.remove('show'); dupWarn.textContent = ''; }
                    }).catch(function(err) { if (err && err.name === 'AbortError') return; });
            }, 400);
        });
    }

    /* ---------- Category picker ---------- */
    var categoryPickerModal = $('categoryPickerModal');
    var categoryPickerList = $('categoryPickerList');
    var categoryPickerNewInput = $('categoryPickerNewInput');
    var categoryPickerCreateBtn = $('categoryPickerCreateBtn');
    var categoryPickerCancelBtn = $('categoryPickerCancelBtn');
    var categoryPickerTitle = $('categoryPickerTitle');
    var _categoryPickerState = null;
    function openCategoryPicker(opts) {
        if (!categoryPickerModal) return;
        _categoryPickerState = opts;
        if (categoryPickerTitle) categoryPickerTitle.textContent = opts.title || '🏷️ Перенести';
        if (categoryPickerNewInput) categoryPickerNewInput.value = '';
        renderCategoryPickerList(opts.currentCategory || '');
        categoryPickerModal.classList.add('active');
    }
    function closeCategoryPicker() {
        if (categoryPickerModal) categoryPickerModal.classList.remove('active');
        _categoryPickerState = null;
    }
    function renderCategoryPickerList(currentCat) {
        if (!categoryPickerList) return;
        var cats = [];
        document.querySelectorAll('.cat-btn[data-cat-name]').forEach(function(b) {
            cats.push({
                name: b.getAttribute('data-cat-name'),
                count: parseInt(b.getAttribute('data-cat-count')) || 0,
                color: (window.getComputedStyle(b).getPropertyValue('--cat-color') || '').trim() || ''
            });
        });
        var html = '<button type="button" class="category-picker-item picker-none" data-cat="__none__">'
            + '<span class="picker-dot" style="--cat-color:#888888;"></span>'
            + '<span class="picker-name">— Без категории —</span></button>';
        cats.sort(function(a, b) { return a.name.localeCompare(b.name, 'ru'); });
        cats.forEach(function(c) {
            var isSel = currentCat && c.name === currentCat;
            var dotStyle = c.color ? '--cat-color: ' + c.color + ';' : '';
            html += '<button type="button" class="category-picker-item' + (isSel ? ' selected' : '') + '" data-cat="' + escapeHtml(c.name) + '">'
                + '<span class="picker-dot" style="' + dotStyle + '"></span>'
                + '<span class="picker-name">' + escapeHtml(c.name) + '</span>'
                + (c.count ? '<span class="picker-badge">' + c.count + '</span>' : '') + '</button>';
        });
        categoryPickerList.innerHTML = html;
        categoryPickerList.querySelectorAll('.category-picker-item').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var cat = this.getAttribute('data-cat');
                applyCategoryChange(cat === '__none__' ? '' : cat);
            });
        });
    }
    function applyCategoryChange(category) {
        if (!_categoryPickerState) return;
        var st = _categoryPickerState;
        closeCategoryPicker();
        if (st.mode === 'single' && st.id) {
            apiWithLockGuard('/edit_category/' + st.id, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category: category })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) { showNotification('✅ Категория изменена', 'success'); setTimeout(function() { location.reload(); }, 500); }
                else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
            }).catch(function(err) {
                if (err && err.message === 'ExcelLock') return;
                showNotification('❌ Ошибка сети', 'error');
            });
        } else if (st.mode === 'bulk' && st.ids && st.ids.length) {
            apiWithLockGuard('/bulk/move', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: st.ids, category: category })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) {
                    showNotification('✅ Перемещено: ' + data.count, 'success');
                    _lastBulkSnapshot = data.snapshot;
                    _lastBulkOp = 'bulk_move';
                    showBulkUndoToast('Перемещено ' + data.count + ' записей');
                    setTimeout(function() { location.reload(); }, 900);
                } else showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
            }).catch(function(err) {
                if (err && err.message === 'ExcelLock') return;
                showNotification('❌ Ошибка сети', 'error');
            });
        }
    }
    if (categoryPickerCancelBtn) categoryPickerCancelBtn.addEventListener('click', closeCategoryPicker);
    if (categoryPickerModal) categoryPickerModal.addEventListener('click', function(e) { if (e.target === this) closeCategoryPicker(); });
    if (categoryPickerCreateBtn) categoryPickerCreateBtn.addEventListener('click', function() {
        var val = (categoryPickerNewInput ? categoryPickerNewInput.value : '').trim();
        if (!val) { showNotification('❌ Введите категорию', 'error'); return; }
        applyCategoryChange(val);
    });
    if (categoryPickerNewInput) categoryPickerNewInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); if (categoryPickerCreateBtn) categoryPickerCreateBtn.click(); }
    });

    function showBulkUndoToast(msg) {
        showUndoToast(msg + '. Отменить?', function() {
            if (!_lastBulkSnapshot || !_lastBulkOp) return;
            apiWithLockGuard('/bulk/undo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ op: _lastBulkOp, snapshot: _lastBulkSnapshot })
            }).then(function(r) { return r.json(); }).then(function(data) {
                if (data.success) {
                    showNotification('↩ Отменено: ' + data.restored, 'success');
                    setTimeout(function() { location.reload(); }, 700);
                } else {
                    showNotification('❌ ' + (data.error || 'Ошибка'), 'error');
                }
            }).catch(function(err) {
                if (err && err.message === 'ExcelLock') return;
                showNotification('❌ Ошибка сети', 'error');
            });
        }, 8000);
    }

    document.querySelectorAll('.bulk-checkbox').forEach(function(cb) {
        cb.addEventListener('click', function(e) {
            e.stopPropagation();
            var id = this.getAttribute('data-id');
            var li = this.closest('.link-item');
            if (this.checked) { _selectedIds.add(id); if (li) li.classList.add('bulk-selected'); }
            else { _selectedIds.delete(id); if (li) li.classList.remove('bulk-selected'); }
            updateBulkPanel();
        });
    });

    /* ---------- Edit modal ---------- */
    document.querySelectorAll('.edit-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            var id = this.getAttribute('data-id'); if (!id) return;
            api('/get_record/' + id).then(function(r) { return r.json(); }).then(function(data) {
                if (data.error) { alert(data.error); return; }
                $('edit_id').value = data.id;
                $('edit_name').value = data.name_del;
                $('edit_link').value = data.link_del;
                $('edit_desc').value = data.description || '';
                var codeEl = $('code_edit');
                var langEl = $('code_lang_edit');
                if (codeEl) codeEl.value = data.code || '';
                if (langEl) {
                    var lang = data.code_lang || '';
                    var found = false;
                    for (var i = 0; i < langEl.options.length; i++) {
                        if (langEl.options[i].value === lang) { langEl.selectedIndex = i; found = true; break; }
                    }
                    if (!found) langEl.value = '';
                }
                // Снять браузерную валидацию с «Ссылка» в редакторе
                var editLinkEl = $('edit_link');
                if (editLinkEl) editLinkEl.removeAttribute('required');
                var tags = (data.tags || '').split(',').map(function(t) { return t.trim(); }).filter(Boolean);
                if (tagsEditCtl) tagsEditCtl.setTags(tags);
                var catSelect = $('edit_category');
                var catCustom = $('edit_category_custom');
                var category = data.category || '';
                var found2 = false;
                for (var j = 0; j < catSelect.options.length; j++) {
                    if (catSelect.options[j].value === category) { catSelect.selectedIndex = j; found2 = true; break; }
                }
                if (!found2) {
                    catSelect.value = '__other__';
                    catCustom.classList.add('visible');
                    catCustom.value = category;
                } else {
                    catCustom.classList.remove('visible');
                    catCustom.value = '';
                }
                $('edit_category_hidden').value = (catSelect.value === '__other__') ? catCustom.value.trim() : catSelect.value;
                // NEW: авто-раскрытие спойлера кода, если он есть
                var editCodeDetails = $('editCodeDetails');
                if (editCodeDetails) {
                    editCodeDetails.open = !!(data.code && String(data.code).trim());
                }
                $('editModal').classList.add('active');
            }).catch(function() { alert('Ошибка'); });
        });
    });

    /* ---------- Smart link click ---------- */
    document.querySelectorAll('.smart-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) return;
            var fullLink = this.getAttribute('data-full-link') || this.getAttribute('href') || '';
            if (!fullLink) return;
            var id = this.getAttribute('data-id');
            var isHttp = /^https?:\/\//i.test(fullLink);
            var preview = fullLink.length > 70 ? fullLink.substring(0, 70) + '…' : fullLink;
            if (!isHttp) e.preventDefault();
            copyTextToClipboard(fullLink).then(function() {
                if (isHttp) showNotification('📋 Скопировано и открыто: ' + preview, 'success');
                else showNotification('📋 Скопировано: ' + preview, 'success');
            }).catch(function() { showNotification('❌ Не удалось скопировать', 'error'); });
            if (id) {
                try { apiFetch('/click/' + id, { method: 'POST', keepalive: true }).catch(function() {}); } catch (err) {}
            }
        });
    });

    /* ---------- Edit form submit ---------- */
    var editForm = $('editForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var id = $('edit_id').value;
            var name = $('edit_name').value.trim();
            var link = $('edit_link').value.trim();
            var desc = $('edit_desc').value.trim();
            var category = $('edit_category_hidden').value.trim();
            var tags = $('tags_edit').value;
            var code = $('code_edit') ? $('code_edit').value : '';
            var code_lang = $('code_lang_edit') ? $('code_lang_edit').value : '';
            if (!name) { alert('Название обязательно.'); return; }
            if (!link.trim() && !code.trim()) {
                // NEW: при ошибке раскрываем спойлер кода
                var details = $('editCodeDetails');
                if (details) details.open = true;
                alert('Укажите ссылку или введите код.');
                return;
            }
            apiWithLockGuard('/edit/' + id, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name, link: link, desc: desc,
                    category: category, tags: tags,
                    code: code, code_lang: code_lang
                })
            }).then(function(r) {
                if (r.ok) location.reload();
                else return r.text().then(function(t) { alert('Ошибка: ' + t); });
            }).catch(function(err) {
                if (err && err.message === 'ExcelLock') return;
                alert('Ошибка сети');
            });
        });
        editForm.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
                this.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            }
        });
    }
    var codeEditClearBtn = $('codeEditClearBtn');
    if (codeEditClearBtn) codeEditClearBtn.addEventListener('click', function() {
        var codeEl = $('code_edit');
        var langEl = $('code_lang_edit');
        if (codeEl) codeEl.value = '';
        if (langEl) langEl.value = '';
    });

    /* ---------- Add form validation ---------- */
    var addForm = $('addForm');
    if (addForm) {
        addForm.addEventListener('submit', function(e) {
            var name = $('name') ? $('name').value.trim() : '';
            var link = $('link') ? $('link').value.trim() : '';
            var code = $('code_add') ? $('code_add').value : '';
            if (!name) {
                e.preventDefault();
                alert('Название обязательно.');
                return;
            }
            if (!link.trim() && !code.trim()) {
                e.preventDefault();
                // NEW: при ошибке раскрываем спойлер кода
                var details = $('addCodeDetails');
                if (details) details.open = true;
                alert('Укажите ссылку или введите код.');
                return;
            }
        });
    }

    /* ---------- Bulk panel ---------- */
    var bulkPanel = $('bulkPanel');
    var bulkCount = $('bulkCount');
    function updateBulkPanel() {
        if (!bulkPanel) return;
        if (_selectedIds.size > 0) {
            bulkPanel.classList.add('show');
            if (bulkCount) bulkCount.textContent = _selectedIds.size;
        } else bulkPanel.classList.remove('show');
    }
    document.querySelectorAll('.bulk-checkbox-card').forEach(function(cb) {
        cb.addEventListener('click', function(e) {
            e.stopPropagation();
            var card = this.closest('.card');
            var checked = this.checked;
            card.querySelectorAll('.bulk-checkbox').forEach(function(sub) {
                var id = sub.getAttribute('data-id');
                var li = sub.closest('.link-item');
                if (checked) { _selectedIds.add(id); if (li) li.classList.add('bulk-selected'); }
                else { _selectedIds.delete(id); if (li) li.classList.remove('bulk-selected'); }
            });
            updateBulkPanel();
        });
    });
    var bulkClearBtn = $('bulkClearBtn');
    if (bulkClearBtn) bulkClearBtn.addEventListener('click', function() {
        resetBulkSelection();
        updateBulkPanel();
    });
    function bulkCall(url, body) {
        var payload = { ids: Array.from(_selectedIds) };
        for (var k in body) payload[k] = body[k];
        return apiWithLockGuard(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(function(r) { return r.json(); });
    }
    var bulkFavoriteBtn = $('bulkFavoriteBtn');
    if (bulkFavoriteBtn) bulkFavoriteBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        bulkCall('/bulk/favorite', { value: 1 }).then(function(d) {
            showNotification('✅ В избранном: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot; _lastBulkOp = 'bulk_favorite';
            showBulkUndoToast('Добавлено в избранное: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    var bulkUnfavoriteBtn = $('bulkUnfavoriteBtn');
    if (bulkUnfavoriteBtn) bulkUnfavoriteBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        bulkCall('/bulk/favorite', { value: 0 }).then(function(d) {
            showNotification('✅ Убрано: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot; _lastBulkOp = 'bulk_favorite';
            showBulkUndoToast('Убрано из избранного: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    var bulkMoveBtn = $('bulkMoveBtn');
    if (bulkMoveBtn) bulkMoveBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        openCategoryPicker({
            mode: 'bulk', ids: Array.from(_selectedIds),
            title: '🏷️ Переместить ' + _selectedIds.size + ' записей'
        });
    });
    var bulkTagBtn = $('bulkTagBtn');
    if (bulkTagBtn) bulkTagBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        var tag = prompt('Тег для добавления:', '');
        if (!tag || !tag.trim()) return;
        bulkCall('/bulk/tags', { tag: tag.trim(), action: 'add' }).then(function(d) {
            showNotification('✅ Тег добавлен: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot; _lastBulkOp = 'bulk_tags';
            showBulkUndoToast('Тег добавлен: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    var bulkGroupIconBtn = $('bulkGroupIconBtn');
    if (bulkGroupIconBtn) bulkGroupIconBtn.addEventListener('click', function() {
        var groups = [];
        document.querySelectorAll('.bulk-checkbox-card:checked').forEach(function(cb) {
            var g = cb.getAttribute('data-group');
            if (g && groups.indexOf(g) === -1) groups.push(g);
        });
        if (!groups.length && _selectedIds.size) {
            document.querySelectorAll('.card').forEach(function(card) {
                var g = card.getAttribute('data-group');
                if (!g) return;
                var links = card.querySelectorAll('.link-item');
                for (var i = 0; i < links.length; i++) {
                    if (_selectedIds.has(links[i].getAttribute('data-id'))) {
                        if (groups.indexOf(g) === -1) groups.push(g);
                        break;
                    }
                }
            });
        }
        if (!groups.length) { showNotification('❌ Отметьте карточку', 'error'); return; }
        window.openEmojiPicker(groups);
    });
    var bulkDeleteBtn = $('bulkDeleteBtn');
    if (bulkDeleteBtn) bulkDeleteBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        showConfirm('🗑 Массовое удаление', 'Удалить <b>' + _selectedIds.size + '</b> записей?', '🗑 Удалить', function() {
            bulkCall('/bulk/delete', {}).then(function(d) {
                showNotification('✅ Удалено: ' + d.count, 'success');
                setTimeout(function() { location.reload(); }, 600);
            }).catch(function(err) {
                if (err && err.message === 'ExcelLock') return;
                showNotification('❌ Ошибка сети', 'error');
            });
        });
    });
    var bulkExportBtn = $('bulkExportBtn');
    if (bulkExportBtn) bulkExportBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        var lines = [];
        document.querySelectorAll('.link-item.bulk-selected').forEach(function(li) {
            var card = li.closest('.card');
            var name = card ? card.getAttribute('data-group') : '';
            var sl = li.querySelector('.smart-link');
            var link = sl ? sl.getAttribute('data-full-link') : '';
            var descEl = li.querySelector('.desc');
            var desc = descEl ? descEl.getAttribute('data-original') : '';
            lines.push('- [' + name + '](' + link + ')' + (desc ? ' — ' + desc : ''));
        });
        var text = lines.join('\n');
        copyTextToClipboard(text).then(function() {
            showNotification('✅ Скопировано: ' + lines.length, 'success');
        }).catch(function() { alert('Не удалось скопировать:\n\n' + text); });
    });

    /* ---------- Inline desc edit ---------- */
    document.querySelectorAll('.desc[data-id]').forEach(function(descEl) {
        descEl.addEventListener('dblclick', function(e) {
            e.stopPropagation(); e.preventDefault();
            if (this.classList.contains('desc-editing')) return;
            var id = this.getAttribute('data-id'); if (!id) return;
            var originalText = this.getAttribute('data-original') || '';
            this.classList.add('desc-editing');
            this.textContent = originalText;
            this.setAttribute('contenteditable', 'plaintext-only');
            if (this.contentEditable !== 'plaintext-only') this.setAttribute('contenteditable', 'true');
            this.focus();
            try {
                var range = document.createRange();
                range.selectNodeContents(this); range.collapse(false);
                var sel = window.getSelection();
                sel.removeAllRanges(); sel.addRange(range);
            } catch (err) {}
            var finished = false;
            function finish(save) {
                if (finished) return; finished = true;
                descEl.removeEventListener('keydown', onKey);
                descEl.removeEventListener('blur', onBlur);
                descEl.removeAttribute('contenteditable');
                descEl.classList.remove('desc-editing');
                if (!save) { descEl.textContent = originalText; return; }
                var newText = (descEl.textContent || '').trim();
                if (newText === originalText) { descEl.textContent = originalText; return; }
                descEl.classList.add('desc-saving');
                apiWithLockGuard('/edit_desc/' + id, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ desc: newText })
                }).then(function(r) { return r.json(); }).then(function(data) {
                    descEl.classList.remove('desc-saving');
                    if (data.success) {
                        descEl.setAttribute('data-original', data.desc);
                        descEl.textContent = data.desc;
                        if (window.__state && window.__state.markIndexDirty) window.__state.markIndexDirty();
                        showNotification('✅ Сохранено', 'success');
                    } else { descEl.textContent = originalText; showNotification('❌ ' + (data.error || 'Ошибка'), 'error'); }
                }).catch(function(err) {
                    descEl.classList.remove('desc-saving'); descEl.textContent = originalText;
                    if (err && err.message === 'ExcelLock') return;
                    showNotification('❌ Ошибка сети', 'error');
                });
            }
            function onKey(ev) {
                if (ev.key === 'Enter' && !ev.shiftKey) { ev.preventDefault(); finish(true); }
                else if (ev.key === 'Escape') { ev.preventDefault(); finish(false); }
            }
            function onBlur() { finish(true); }
            descEl.addEventListener('keydown', onKey);
            descEl.addEventListener('blur', onBlur);
        });
    });

    /* ============================================================
       КОД: копирование и разворачивание
       ============================================================ */
    document.body.addEventListener('click', function(e) {
        var copyBtn = e.target.closest('.link-code .code-copy-btn');
        if (copyBtn) {
            e.stopPropagation();
            e.preventDefault();
            var block = copyBtn.closest('.link-code');
            if (!block) return;
            var codeEl = block.querySelector('pre code');
            if (!codeEl) return;
            var text = codeEl.textContent || '';
            copyTextToClipboard(text).then(function() {
                copyBtn.textContent = '✅';
                copyBtn.classList.add('copied');
                showNotification('📋 Код скопирован (' + text.length + ' симв.)', 'success');
                setTimeout(function() {
                    copyBtn.textContent = '📋';
                    copyBtn.classList.remove('copied');
                }, 1500);
            }).catch(function() {
                showNotification('❌ Не удалось скопировать', 'error');
            });
            return;
        }
        var expandBtn = e.target.closest('.link-code .code-expand-btn');
        if (expandBtn) {
            e.stopPropagation();
            e.preventDefault();
            var block2 = expandBtn.closest('.link-code');
            if (!block2) return;
            var expanded = block2.classList.toggle('expanded');
            expandBtn.textContent = expanded ? '⤡' : '⤢';
            expandBtn.title = expanded ? 'Свернуть' : 'Развернуть';
            return;
        }
    }, true);

    document.body.addEventListener('dblclick', function(e) {
        var block = e.target.closest('.link-code');
        if (!block) return;
        if (e.target.closest('.code-btn')) return;
        e.stopPropagation();
        e.preventDefault();
        block.classList.toggle('expanded');
        var btn = block.querySelector('.code-expand-btn');
        if (btn) {
            var expanded = block.classList.contains('expanded');
            btn.textContent = expanded ? '⤡' : '⤢';
        }
    }, true);

    /* ---------- Emoji picker ---------- */
    var EMOJI_CATEGORIES = [
        { name: 'Часто', icon: '⭐', list: ['📌','⭐','🔥','❤️','✅','💡','📁','📂','🗂️','📊','🎯','🏆','💎','🌟','✨','⚡','🚀','🎨','🛠️','🔧'] },
        { name: 'Технологии', icon: '💻', list: ['💻','🖥️','🖨️','⌨️','🖱️','💾','💿','📀','🧮','🔌','🔋','📡','🛰️','☎️','📞','📟','📠','📺','📻','🎥','📷','📹','🎞️','📼','🎬','📽️'] },
        { name: 'Работа', icon: '💼', list: ['💼','📁','📂','🗂️','🗃️','🗄️','📋','📌','📍','📎','🖇️','📏','📐','✂️','🖊️','🖋️','✒️','🖌️','🖍️','📝','✏️','🔍','🔎','🔏','🔐','🔒','🔓','📅','📆','🗓️','📇'] },
        { name: 'Символы', icon: '🔣', list: ['⚙️','🔧','🔨','⚒️','🛠️','⛏️','🔩','⚗️','🧪','🧬','🔬','🔭','📡','💡','🔦','🕯️','🪔','🧯','🛢️','💸','💵','💰','💳','🧾','💹','📈','📉','📊','📋'] },
        { name: 'Природа', icon: '🌿', list: ['🌍','🌎','🌏','🌕','🌖','🌗','🌘','🌑','🌒','🌓','🌔','🌙','⭐','🌟','✨','⚡','☄️','💥','🔥','🌪️','🌈','☀️','🌤️','⛅','🌥️','☁️','🌦️','🌧️','⛈️','🌩️','🌨️','❄️','🌊','💧'] },
        { name: 'Объекты', icon: '📦', list: ['📦','📫','📪','📬','📭','📮','🗳️','✉️','📧','📨','📩','📤','📥','🏠','🏢','🏣','🏤','🏥','🏦','🏨','🏪','🏫','🏬','🏭','🏯','🏰','🗼','🗽','⛪','🕌','🕍','🛕'] },
        { name: 'Дом/Сеть', icon: '🏠', list: ['🏠','🏡','🏘️','🏚️','🔌','💡','🛋️','🛏️','🚪','🚿','🛁','🧴','🧷','🧹','🧺','🧻','🧼','🪒','🧽','🪣','🛒','🛍️','🎁','🎀','🎊','🎉','🌐','📶','🔗','🔀'] },
        { name: 'Развлечения', icon: '🎮', list: ['🎮','🕹️','🎯','🎲','🎰','🎳','🎪','🎭','🎨','🎬','🎤','🎧','🎼','🎵','🎶','🎷','🎸','🎹','🎺','🎻','🥁','🎊','🎉','🎈','🎁','🎀','🎂','🍰','🍕','🍔'] }
    ];
    var emojiModal = $('emojiPickerModal');
    var currentEmojiGroups = [];
    var _emojiPickerMode = 'group';
    function renderEmojiCategories() {
        var container = $('emojiCategories'); if (!container) return;
        container.innerHTML = EMOJI_CATEGORIES.map(function(c, i) {
            return '<button type="button" class="emoji-cat-btn' + (i === 0 ? ' active' : '') + '" data-idx="' + i + '">' + c.icon + ' ' + c.name + '</button>';
        }).join('');
        container.querySelectorAll('.emoji-cat-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                container.querySelectorAll('.emoji-cat-btn').forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');
                renderEmojiGrid(parseInt(this.getAttribute('data-idx')));
            });
        });
    }
    function renderEmojiGrid(catIdx) {
        var grid = $('emojiGrid'); if (!grid) return;
        var cat = EMOJI_CATEGORIES[catIdx]; if (!cat) return;
        grid.innerHTML = cat.list.map(function(e) {
            return '<button type="button" class="emoji-btn" data-emoji="' + e + '">' + e + '</button>';
        }).join('');
        grid.querySelectorAll('.emoji-btn').forEach(function(btn) {
            btn.addEventListener('click', function() { applyEmojiIcon(this.getAttribute('data-emoji')); });
        });
    }
    function applyEmojiIcon(emoji) {
        if (_emojiPickerMode === 'add-form') {
            var iconBtn = $('addIconPickerBtn'), iconHidden = $('add_group_icon');
            if (iconBtn) iconBtn.textContent = emoji;
            if (iconHidden) iconHidden.value = emoji;
            if (emojiModal) emojiModal.classList.remove('active');
            _emojiPickerMode = 'group';
            return;
        }
        if (!currentEmojiGroups.length) return;
        var groups = currentEmojiGroups.slice();
        Promise.all(groups.map(function(group) {
            return apiFetch('/update_group_icon', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ group: group, icon: emoji })
            }).then(function(r) { return r.json(); });
        })).then(function(results) {
            if (results.every(function(r) { return r && r.success; })) {
                document.querySelectorAll('.card-icon[data-group-name]').forEach(function(el) {
                    if (groups.indexOf(el.getAttribute('data-group-name')) !== -1) el.textContent = emoji;
                });
                var prev = $('emojiPreview'); if (prev) prev.textContent = emoji;
                showNotification(groups.length === 1 ? '✅ Иконка обновлена' : '✅ Иконка обновлена для ' + groups.length + ' групп', 'success');
                if (emojiModal) emojiModal.classList.remove('active');
                currentEmojiGroups = [];
            } else showNotification('❌ Ошибка обновления', 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    }
    window.openEmojiPicker = function(groupNames) {
        if (!emojiModal) return;
        _emojiPickerMode = 'group';
        var arr = Array.isArray(groupNames) ? groupNames.filter(Boolean) : [groupNames].filter(Boolean);
        if (!arr.length) return;
        currentEmojiGroups = arr;
        var nameEl = $('emojiGroupName');
        if (nameEl) {
            nameEl.textContent = arr.length === 1 ? arr[0] : arr.length + ' групп: ' + arr.slice(0, 3).join(', ') + (arr.length > 3 ? '…' : '');
        }
        var curIcon = '📌';
        document.querySelectorAll('.card-icon[data-group-name]').forEach(function(el) {
            if (el.getAttribute('data-group-name') === arr[0]) curIcon = (el.textContent || '').trim() || '📌';
        });
        var prev = $('emojiPreview'); if (prev) prev.textContent = curIcon;
        var customInput = $('emojiCustomInput'); if (customInput) customInput.value = '';
        renderEmojiCategories(); renderEmojiGrid(0);
        emojiModal.classList.add('active');
    };
    var addIconPickerBtn = $('addIconPickerBtn');
    if (addIconPickerBtn) addIconPickerBtn.addEventListener('click', function(e) {
        e.preventDefault(); e.stopPropagation();
        if (!emojiModal) return;
        _emojiPickerMode = 'add-form';
        currentEmojiGroups = [];
        var nameEl = $('emojiGroupName');
        if (nameEl) {
            var nameVal = ($('name') && $('name').value || '').trim();
            nameEl.textContent = nameVal || 'Новая группа';
        }
        var prev = $('emojiPreview'), iconHidden = $('add_group_icon');
        if (prev) prev.textContent = (iconHidden && iconHidden.value) || '📌';
        var customInput = $('emojiCustomInput'); if (customInput) customInput.value = '';
        renderEmojiCategories(); renderEmojiGrid(0);
        emojiModal.classList.add('active');
    });
    var closeEmojiPickerBtn = $('closeEmojiPickerBtn');
    if (closeEmojiPickerBtn && emojiModal) closeEmojiPickerBtn.addEventListener('click', function() {
        emojiModal.classList.remove('active');
        currentEmojiGroups = []; _emojiPickerMode = 'group';
    });
    if (emojiModal) emojiModal.addEventListener('click', function(e) {
        if (e.target === this) { this.classList.remove('active'); currentEmojiGroups = []; _emojiPickerMode = 'group'; }
    });
    var emojiApplyCustomBtn = $('emojiApplyCustomBtn');
    if (emojiApplyCustomBtn) emojiApplyCustomBtn.addEventListener('click', function() {
        var inp = $('emojiCustomInput'); if (!inp) return;
        var val = (inp.value || '').trim(); if (val) applyEmojiIcon(val);
    });
    var emojiCustomInput = $('emojiCustomInput');
    if (emojiCustomInput) emojiCustomInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); var val = (this.value || '').trim(); if (val) applyEmojiIcon(val); }
    });
    var emojiResetBtn = $('emojiResetBtn');
    if (emojiResetBtn) emojiResetBtn.addEventListener('click', function() { applyEmojiIcon('📌'); });
    document.querySelectorAll('.card-icon[data-group-name]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            var group = this.getAttribute('data-group-name'); if (!group) return;
            if (typeof window.openEmojiPicker === 'function') window.openEmojiPicker(group);
        });
    });
    document.querySelectorAll('.rename-group-btn[data-group-name]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            var group = this.getAttribute('data-group-name'); if (!group) return;
            if (typeof window.renameGroup === 'function') window.renameGroup(group);
        });
    });

    /* ---------- Profile settings ---------- */
    var settingsModal = $('settingsModal');
    var closeSettingsModalBtn = $('closeSettingsModalBtn');
    if (closeSettingsModalBtn && settingsModal) closeSettingsModalBtn.addEventListener('click', function() { settingsModal.classList.remove('active'); });
    if (settingsModal) settingsModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    var customButtonsDraft = [];
    function openSettings() {
        fetch('/get_settings').then(function(r) { return r.json(); }).then(function(s) {
            var pn = $('profileNameInput'); if (pn) pn.value = (s.profile && s.profile.name) || 'Admin';
            var pc = $('profileColorInput'); if (pc) pc.value = (s.profile && s.profile.color) || '#f5d76e';
            customButtonsDraft = Array.isArray(s.custom_toolbar_buttons) ? s.custom_toolbar_buttons.slice() : [];
            renderCustomButtons();
        });
    }
    function renderCustomButtons() {
        var list = $('customButtonsList'); if (!list) return;
        list.innerHTML = customButtonsDraft.map(function(b, i) {
            return '<div class="custom-btn-row">'
                + '<input type="text" placeholder="🔗" value="' + escapeHtml(b.icon || '🔗') + '" data-field="icon" data-idx="' + i + '" style="max-width:60px;">'
                + '<input type="text" placeholder="Подпись" value="' + escapeHtml(b.label || '') + '" data-field="label" data-idx="' + i + '">'
                + '<input type="text" placeholder="URL или #category:Имя" value="' + escapeHtml(b.url || '') + '" data-field="url" data-idx="' + i + '">'
                + '<button type="button" class="remove-btn" data-idx="' + i + '">✖</button>'
                + '</div>';
        }).join('');
        list.querySelectorAll('input').forEach(function(inp) {
            inp.addEventListener('input', function() {
                var i = parseInt(this.getAttribute('data-idx'));
                var f = this.getAttribute('data-field');
                if (customButtonsDraft[i]) customButtonsDraft[i][f] = this.value;
            });
        });
        list.querySelectorAll('.remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var i = parseInt(this.getAttribute('data-idx'));
                customButtonsDraft.splice(i, 1);
                renderCustomButtons();
            });
        });
    }
    var addCustomBtn = $('addCustomBtn');
    if (addCustomBtn) addCustomBtn.addEventListener('click', function() {
        if (customButtonsDraft.length >= 20) return;
        customButtonsDraft.push({ icon: '🔗', label: 'Ссылка', url: 'https://' });
        renderCustomButtons();
    });
    var saveSettingsBtn = $('saveSettingsBtn');
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', function() {
        var profile = {
            name: ($('profileNameInput').value || '').trim() || 'Admin',
            color: $('profileColorInput').value
        };
        var payload = { profile: profile, custom_toolbar_buttons: customButtonsDraft };
        api('/save_settings', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) {
                showNotification('✅ Сохранено', 'success');
                applyProfileLocal(profile);
                applyCustomToolbarButtonsLocal(customButtonsDraft);
                settingsModal.classList.remove('active');
            } else showNotification('❌ Ошибка', 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    });
    function applyProfileLocal(profile) {
        var avatar = $('profileAvatar');
        if (avatar) {
            avatar.textContent = (profile.name || 'A').charAt(0).toUpperCase();
            avatar.style.background = profile.color || '#f5d76e';
            avatar.style.boxShadow = '0 0 10px ' + (profile.color || '#f5d76e');
        }
    }
    function applyCustomToolbarButtonsLocal(btns) {
        var container = $('customToolbarBtns'); if (!container) return;
        container.innerHTML = '';
        btns.forEach(function(b) {
            var btn = document.createElement('button');
            btn.className = 'custom-toolbar-btn';
            btn.textContent = (b.icon || '') + ' ' + (b.label || '');
            btn.title = b.url || '';
            btn.addEventListener('click', function() {
                if (b.url && b.url.indexOf('#category:') === 0) {
                    var cat = b.url.slice(10).trim();
                    var target = document.querySelector('.cat-btn[data-filter="' + cat + '"]');
                    if (target) target.click();
                } else if (b.url && /^https?:\/\//i.test(b.url)) {
                    window.open(b.url, '_blank', 'noopener,noreferrer');
                }
            });
            container.appendChild(btn);
        });
    }
    var profileWidget = $('profileWidget');
    if (profileWidget && settingsModal) profileWidget.addEventListener('click', function() {
        openSettings(); settingsModal.classList.add('active');
    });

    /* ============================================================
       STORAGE UI — ПЕРЕРАБОТАНО
       Радио-карточки выбора типа, валидация пути, поддержка UNC.
       ============================================================ */
    (function setupStorageTab() {
        var radios = document.querySelectorAll('input[name="storageType"]');
        var sqliteSection = $('storageSqliteSection');
        var sqlitePathInput = $('storageSqlitePath');
        var checkPathBtn = $('storageCheckPathBtn');
        var pathStatus = $('storagePathStatus');
        var switchBtn = $('storageSwitchBtn');
        var reloadBtn = $('storageReloadInfoBtn');
        var infoEl = $('storageFilesInfo');
        var currentTypeEl = $('storageCurrentType');
        var recordsCountEl = $('storageRecordsCount');
        var trashCountEl = $('storageTrashCount');
        var importFile = $('storageImportXlsxFile');
        var importPathInput = $('storageImportPath');
        var importByPathBtn = $('storageImportByPathBtn');
        var importProgress = $('storageImportProgress');
        var exportBtn = $('storageExportXlsxBtn');
        var resetBtn = $('storageResetBtn');

        if (!radios.length) return;

        function formatBytes(n) {
            if (!n) return '0 Б';
            if (n < 1024) return n + ' Б';
            if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' КБ';
            if (n < 1024 * 1024 * 1024) return (n / 1024 / 1024).toFixed(2) + ' МБ';
            return (n / 1024 / 1024 / 1024).toFixed(2) + ' ГБ';
        }

        function getSelectedType() {
            for (var i = 0; i < radios.length; i++) {
                if (radios[i].checked) return radios[i].value;
            }
            return 'sqlite';
        }
        function setSelectedType(t) {
            radios.forEach(function(r) { r.checked = (r.value === t); });
            updateSqliteVisibility();
        }
        function updateSqliteVisibility() {
            if (sqliteSection) {
                sqliteSection.style.display = (getSelectedType() === 'sqlite') ? '' : 'none';
            }
        }
        radios.forEach(function(r) { r.addEventListener('change', updateSqliteVisibility); });

        function showPathStatus(kind, msg) {
            if (!pathStatus) return;
            pathStatus.className = 'storage-path-status show ' + kind;
            pathStatus.textContent = msg;
        }
        function hidePathStatus() {
            if (pathStatus) pathStatus.className = 'storage-path-status';
        }

        function checkPath(quiet) {
            var p = (sqlitePathInput ? sqlitePathInput.value.trim() : '');
            if (!p) { if (!quiet) showPathStatus('err', '❌ Пустой путь'); return; }
            if (!quiet) showPathStatus('warn', '⏳ Проверка...');
            api('/api/storage/validate_path', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ path: p })
            }).then(function(r) { return r.json(); }).then(function(d) {
                if (d.success) {
                    var msg = '✅ Путь доступен' + (d.resolved && d.resolved !== p ? ' → ' + d.resolved : '');
                    if (d.is_network) {
                        showPathStatus('warn', msg + ' (сетевой, WAL отключится)');
                    } else {
                        showPathStatus('ok', msg);
                    }
                } else {
                    showPathStatus('err', '❌ ' + (d.error || 'Ошибка'));
                }
            }).catch(function() { showPathStatus('err', '❌ Ошибка сети'); });
        }
        if (checkPathBtn) checkPathBtn.addEventListener('click', function() { checkPath(false); });
        if (sqlitePathInput) {
            var _t = null;
            sqlitePathInput.addEventListener('input', function() {
                hidePathStatus();
                clearTimeout(_t);
                _t = setTimeout(function() { checkPath(true); }, 600);
            });
        }

        function loadStorageInfo() {
            if (currentTypeEl) currentTypeEl.textContent = '…';
            if (infoEl) infoEl.textContent = 'Загрузка...';
            fetch('/api/storage/info')
                .then(function(r) { return r.json(); })
                .then(function(d) {
                    if (!d.success) { if (infoEl) infoEl.textContent = 'Ошибка: ' + (d.error || '?'); return; }
                    if (currentTypeEl) currentTypeEl.textContent = d.type === 'sqlite' ? '⚡ SQLite' : '📊 Excel';
                    if (recordsCountEl) recordsCountEl.textContent = d.total_records || 0;
                    if (trashCountEl) trashCountEl.textContent = d.total_in_trash || 0;
                    setSelectedType(d.type || 'sqlite');
                    if (sqlitePathInput && d.db_path) {
                        var cur = sqlitePathInput.value.trim();
                        if (!cur || cur === 'reestr.db') {
                            var rel = d.db_path.replace(/^.*[\\\/]/, '');
                            sqlitePathInput.value = rel || 'reestr.db';
                        }
                    }
                    var lines = [];
                    lines.push('<b>Excel:</b> ' + (d.excel_exists ? '✅ есть, ' + formatBytes(d.excel_size) : '❌ нет'));
                    lines.push('<b>SQLite:</b> ' + (d.sqlite_exists ? '✅ есть, ' + formatBytes(d.sqlite_size) : '❌ нет'));
                    if (d.db_path) {
                        lines.push('<span style="opacity:0.7; font-family:monospace; font-size:0.72rem;">' + escapeHtml(d.db_path) + '</span>');
                    }
                    if (infoEl) infoEl.innerHTML = lines.join('<br>');
                })
                .catch(function() { if (infoEl) infoEl.textContent = 'Ошибка загрузки'; });
        }

        if (reloadBtn) reloadBtn.addEventListener('click', function() {
            loadStorageInfo();
            if (getSelectedType() === 'sqlite') checkPath(true);
        });

        if (switchBtn) switchBtn.addEventListener('click', function() {
            var newType = getSelectedType();
            var sqlitePath = (sqlitePathInput ? sqlitePathInput.value.trim() : '') || 'reestr.db';
            var msg = 'Переключить хранилище на «' + newType + '»?\n\n' +
                '⚠️ Данные НЕ переносятся автоматически.\n\n' +
                (newType === 'sqlite'
                    ? 'Если reestr.db ещё нет и есть reestr.xlsx, данные импортируются автоматически.'
                    : 'Данные берутся из реестр.xlsx.')
                + '\n\nПродолжить?';
            if (!confirm(msg)) return;

            switchBtn.disabled = true;
            var original = switchBtn.innerHTML;
            switchBtn.innerHTML = '⏳ Переключение...';
            api('/api/storage/switch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ type: newType, sqlite_path: sqlitePath })
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                switchBtn.disabled = false;
                switchBtn.innerHTML = original;
                if (d.success) {
                    var m = '✅ Переключено на ' + newType + '. Перезагрузка...';
                    if (d.warning) m += ' ' + d.warning;
                    showNotification(m, 'success');
                    setTimeout(function() { location.reload(); }, 1200);
                } else {
                    showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            })
            .catch(function() {
                switchBtn.disabled = false;
                switchBtn.innerHTML = original;
                showNotification('❌ Ошибка сети', 'error');
            });
        });

        // Импорт файлом
        if (importFile) importFile.addEventListener('change', function() {
            var file = this.files[0]; if (!file) return;
            doImportViaForm(file); this.value = '';
        });
        function doImportViaForm(file) {
            if (importProgress) {
                importProgress.classList.add('show');
                importProgress.textContent = '⏳ Загрузка ' + file.name + '...';
            }
            var fd = new FormData();
            fd.append('file', file);
            fetch('/api/storage/import_xlsx', {
                method: 'POST',
                body: fd,
                credentials: 'same-origin',
                headers: {'X-CSRF-Token': getCsrfToken()}
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    if (importProgress) importProgress.textContent = '✅ Импортировано: ' + d.imported;
                    showNotification('✅ Импортировано ' + d.imported + ' записей', 'success');
                    loadStorageInfo();
                    setTimeout(function() { location.reload(); }, 1200);
                } else {
                    if (importProgress) importProgress.textContent = '❌ ' + (d.error || 'Ошибка');
                }
            })
            .catch(function() {
                if (importProgress) importProgress.textContent = '❌ Ошибка сети';
            });
        }

        // Импорт путём
        if (importByPathBtn) importByPathBtn.addEventListener('click', function() {
            var p = (importPathInput ? importPathInput.value.trim() : '');
            if (!p) { showNotification('❌ Введите путь', 'error'); return; }
            if (importProgress) {
                importProgress.classList.add('show');
                importProgress.textContent = '⏳ Импорт из ' + p + '...';
            }
            api('/api/storage/import_xlsx', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ path: p })
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    if (importProgress) importProgress.textContent = '✅ Импортировано: ' + d.imported;
                    showNotification('✅ Импортировано ' + d.imported + ' записей', 'success');
                    loadStorageInfo();
                    setTimeout(function() { location.reload(); }, 1200);
                } else {
                    if (importProgress) importProgress.textContent = '❌ ' + (d.error || 'Ошибка');
                }
            })
            .catch(function() {
                if (importProgress) importProgress.textContent = '❌ Ошибка сети';
            });
        });

        // Экспорт
        if (exportBtn) exportBtn.addEventListener('click', function() {
            exportBtn.disabled = true;
            var original = exportBtn.innerHTML;
            exportBtn.innerHTML = '⏳ Готовим файл...';
            fetch('/api/storage/export_xlsx', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'X-CSRF-Token': getCsrfToken()}
            })
            .then(function(r) {
                if (!r.ok) throw new Error('Ошибка сервера');
                return r.blob();
            })
            .then(function(blob) {
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'реестр_' + new Date().toISOString().slice(0,10).replace(/-/g, '') + '.xlsx';
                document.body.appendChild(a);
                a.click();
                setTimeout(function() {
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }, 500);
                showNotification('✅ Файл скачан', 'success');
            })
            .catch(function() {
                showNotification('❌ Ошибка экспорта', 'error');
            })
            .finally(function() {
                exportBtn.disabled = false;
                exportBtn.innerHTML = original;
            });
        });

        // Reset
        if (resetBtn) resetBtn.addEventListener('click', function() {
            var confirmText = prompt(
                'Это удалит ВСЕ записи из SQLite-БД.\n' +
                'Файл reestr.xlsx не тронут.\n\n' +
                'Для подтверждения введите: YES_DELETE_ALL'
            );
            if (confirmText !== 'YES_DELETE_ALL') {
                showNotification('Отменено', 'success');
                return;
            }
            api('/api/storage/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ confirm: 'YES_DELETE_ALL' })
            })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    showNotification('✅ БД очищена', 'success');
                    setTimeout(function() { location.reload(); }, 800);
                } else {
                    showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            })
            .catch(function() { showNotification('❌ Ошибка сети', 'error'); });
        });

        // Загрузка при открытии вкладки
        document.querySelectorAll('.settings-tab[data-tab="tab-storage"]').forEach(function(t) {
            t.addEventListener('click', function() { setTimeout(loadStorageInfo, 50); });
        });
        if (document.querySelector('.settings-tab[data-tab="tab-storage"].active')) {
            loadStorageInfo();
        }
    })();

    /* ============================================================
       PLUGINS MANAGER
       ============================================================ */
    var pluginsManagerList = $('pluginsManagerList');
    var pluginEditorModal = $('pluginEditorModal');
    var pluginEditorName = $('pluginEditorName');
    var pluginEditorCode = $('pluginEditorCode');
    var pluginEditorStatus = $('pluginEditorStatus');
    var _pluginEditorIsNew = false;
    window.loadPluginsList = function() {
        if (!pluginsManagerList) return;
        pluginsManagerList.innerHTML = '<div style="color:var(--meta-color); text-align:center; padding:14px 0;">Загрузка...</div>';
        fetch('/api/plugins/list').then(function(r) { return r.json(); })
            .then(function(data) { renderPluginsManager(data); })
            .catch(function() { pluginsManagerList.innerHTML = '<div style="color:#e74c3c; padding:10px 0;">Ошибка</div>'; });
    };
    function renderPluginsManager(data) {
        if (!pluginsManagerList) return;
        var plugins = (data && data.plugins) || [];
        var hooksActive = (data && data.hooks_active) || {};
        if (!plugins.length) {
            pluginsManagerList.innerHTML = '<div style="color:var(--meta-color); text-align:center; padding:14px 0; font-style:italic;">Плагины не установлены.</div>';
            return;
        }
        var html = '';
        plugins.forEach(function(p) {
            var dotColor = p.status_color || '#7a9ab5';
            var statusLabel = p.status_label || '—';
            var toggleLabel = p.enabled ? '⏸ Отключить' : '▶ Включить';
            var toggleClass = p.enabled ? 'plugin-toggle on' : 'plugin-toggle off';
            html += '<div class="plugin-row" data-name="' + escapeHtml(p.name) + '">'
                + '<div class="plugin-row-main">'
                + '<span class="plugin-status-dot" style="background:' + dotColor + '; box-shadow: 0 0 8px ' + dotColor + ';" title="' + escapeHtml(statusLabel) + '"></span>'
                + '<div class="plugin-row-info">'
                + '<div class="plugin-row-name">' + escapeHtml(p.name) + '<span class="plugin-version">v' + escapeHtml(p.version) + '</span></div>'
                + (p.description ? '<div class="plugin-row-desc">' + escapeHtml(p.description) + '</div>' : '')
                + '<div class="plugin-row-meta"><span>' + escapeHtml(statusLabel) + '</span><span>·</span><span>' + p.size + ' Б</span></div>'
                + '</div></div>'
                + '<div class="plugin-row-actions">'
                + '<button class="' + toggleClass + '" data-action="toggle">' + toggleLabel + '</button>'
                + '<button class="plugin-action-btn" data-action="edit" title="Редактировать">✏️</button>'
                + '<button class="plugin-action-btn danger" data-action="delete" title="Удалить">🗑</button>'
                + '</div></div>';
        });
        if (Object.keys(hooksActive).length) {
            html += '<div class="plugin-hooks-info">Хуков: ' + Object.keys(hooksActive).map(function(k) { return '<code>' + escapeHtml(k) + '×' + hooksActive[k] + '</code>'; }).join(' ') + '</div>';
        }
        pluginsManagerList.innerHTML = html;
        pluginsManagerList.querySelectorAll('.plugin-action-btn, .plugin-toggle').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var row = this.closest('.plugin-row');
                var name = row ? row.getAttribute('data-name') : '';
                var action = this.getAttribute('data-action');
                if (!name) return;
                if (action === 'edit') openPluginEditor(name, false);
                else if (action === 'toggle') togglePlugin(name);
                else if (action === 'delete') deletePluginConfirm(name);
            });
        });
    }
    function openPluginEditor(name, isNew) {
        if (!pluginEditorModal) return;
        _pluginEditorIsNew = !!isNew;
        if (pluginEditorName) { pluginEditorName.value = name || ''; pluginEditorName.readOnly = !isNew; }
        if (pluginEditorStatus) { pluginEditorStatus.textContent = ''; pluginEditorStatus.style.color = ''; }
        if (pluginEditorCode) pluginEditorCode.value = '';
        pluginEditorModal.classList.add('active');
        if (!isNew && name) {
            if (pluginEditorCode) pluginEditorCode.value = 'Загрузка...';
            fetch('/api/plugins/read?name=' + encodeURIComponent(name))
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) { if (pluginEditorCode) pluginEditorCode.value = data.code; }
                    else {
                        if (pluginEditorCode) pluginEditorCode.value = '';
                        if (pluginEditorStatus) { pluginEditorStatus.textContent = data.error || 'Ошибка'; pluginEditorStatus.style.color = '#e74c3c'; }
                    }
                }).catch(function() { if (pluginEditorStatus) pluginEditorStatus.textContent = 'Ошибка загрузки'; });
        } else {
            if (pluginEditorCode) {
                pluginEditorCode.value = '"""\n' + (name || 'new_plugin') + '\n"""\n\n__version__ = "1.0"\n__description__ = ""\n\n\ndef register(hooks, app, config, core):\n    pass\n';
            }
        }
    }
    function closePluginEditor() { if (pluginEditorModal) pluginEditorModal.classList.remove('active'); }
    function togglePlugin(name) {
        fetch('/api/plugins/list').then(function(r) { return r.json(); }).then(function(data) {
            var p = (data.plugins || []).find(function(x) { return x.name === name; });
            if (!p) { showNotification('❌ Не найден', 'error'); return; }
            var newState = !p.enabled;
            api('/api/plugins/toggle', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, enabled: newState })
            }).then(function(r) { return r.json(); }).then(function(res) {
                if (res.success) {
                    showNotification((newState ? '▶ Включён' : '⏸ Отключён') + '. Перезагрузите плагины.', 'success');
                    window.loadPluginsList();
                } else showNotification('❌ ' + (res.error || 'Ошибка'), 'error');
            });
        });
    }
    function deletePluginConfirm(name) {
        showConfirm('🗑 Удаление плагина',
            'Удалить <span class="confirm-highlight">' + escapeHtml(name) + '</span>? Файл переместится в plugins/.trash/.',
            '🗑 Удалить',
            function() {
                api('/api/plugins/delete', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                }).then(function(r) { return r.json(); }).then(function(res) {
                    if (res.success) { showNotification('✅ Удалено. Перезагрузите плагины.', 'success'); window.loadPluginsList(); }
                    else showNotification('❌ ' + (res.error || 'Не удалось'), 'error');
                }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
            });
    }
    var pluginsRefreshBtn = $('pluginsRefreshBtn');
    if (pluginsRefreshBtn) pluginsRefreshBtn.addEventListener('click', window.loadPluginsList);
    var pluginsCreateBtn = $('pluginsCreateBtn');
    if (pluginsCreateBtn) pluginsCreateBtn.addEventListener('click', function() { openPluginEditor('', true); });
    var pluginEditorCloseBtn = $('pluginEditorCloseBtn');
    if (pluginEditorCloseBtn) pluginEditorCloseBtn.addEventListener('click', closePluginEditor);
    if (pluginEditorModal) pluginEditorModal.addEventListener('click', function(e) { if (e.target === this) closePluginEditor(); });
    var pluginEditorCheckBtn = $('pluginEditorCheckBtn');
    if (pluginEditorCheckBtn) pluginEditorCheckBtn.addEventListener('click', function() {
        var code = pluginEditorCode ? pluginEditorCode.value : '';
        var name = pluginEditorName ? pluginEditorName.value.trim() : 'plugin';
        api('/api/plugins/check', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, code: code })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (pluginEditorStatus) {
                pluginEditorStatus.textContent = data.success ? '✅ ' + (data.message || 'OK') : '❌ ' + (data.error || 'Ошибка');
                pluginEditorStatus.style.color = data.success ? '#2ecc71' : '#e74c3c';
            }
        });
    });
    var pluginEditorSaveBtn = $('pluginEditorSaveBtn');
    if (pluginEditorSaveBtn) pluginEditorSaveBtn.addEventListener('click', function() {
        var code = pluginEditorCode ? pluginEditorCode.value : '';
        var name = pluginEditorName ? pluginEditorName.value.trim() : '';
        if (!name) { showNotification('❌ Введите имя плагина', 'error'); return; }
        var url = _pluginEditorIsNew ? '/api/plugins/create' : '/api/plugins/save';
        api(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, code: code })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) {
                showNotification('✅ Сохранено. Нажмите «Перезагрузить плагины».', 'success');
                closePluginEditor(); window.loadPluginsList();
            } else if (pluginEditorStatus) {
                pluginEditorStatus.textContent = '❌ ' + (data.error || 'Ошибка');
                pluginEditorStatus.style.color = '#e74c3c';
            }
        });
    });
    document.querySelectorAll('.settings-tab[data-tab="tab-plugins"]').forEach(function(t) {
        t.addEventListener('click', function() { setTimeout(window.loadPluginsList, 50); });
    });

    /* ============================================================
       KEYBOARD
       ============================================================ */
    document.addEventListener('keydown', function(e) {
        var tag = (e.target && e.target.tagName) || '';
        var isEditable = (e.target && e.target.isContentEditable) || tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (searchInput) { searchInput.focus(); searchInput.select(); }
            return;
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'm') {
            e.preventDefault();
            var m = $('addModal'); if (m) m.classList.add('active');
            if (window.__prepareAddModal) window.__prepareAddModal();
            setTimeout(function() { var n = $('name'); if (n) n.focus(); }, 100);
            return;
        }
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
            if (isEditable) return;
            if (triggerUndo()) { e.preventDefault(); return; }
        }
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'p') {
            e.preventDefault();
            document.body.classList.toggle('presentation-mode');
            var on = document.body.classList.contains('presentation-mode');
            lsSet(LS_KEYS.presentation, on ? 'true' : 'false');
            showNotification(on ? '🎬 Режим презентации' : 'Режим презентации выключен', 'success');
            return;
        }
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'a') {
            if (isEditable) return;
            e.preventDefault();
            resetBulkSelection();
            document.querySelectorAll('.card').forEach(function(card) {
                if (card.style.display === 'none') return;
                card.querySelectorAll('.link-item:not(.hidden)').forEach(function(li) {
                    var id = li.getAttribute('data-id');
                    if (id) { _selectedIds.add(id); li.classList.add('bulk-selected'); }
                });
            });
            updateBulkPanel();
            return;
        }
        if (e.key === 'Escape') {
            if (isEditable) return;
            hideSortDropdown();
            var openModals = document.querySelectorAll('.modal.active');
            if (openModals.length > 0) {
                openModals.forEach(function(m) { m.classList.remove('active'); });
                _confirmHandler = null;
                if (emojiModal) { emojiModal.classList.remove('active'); currentEmojiGroups = []; _emojiPickerMode = 'group'; }
                _categoryPickerState = null;
            } else if (document.body.classList.contains('presentation-mode')) {
                document.body.classList.remove('presentation-mode');
                lsSet(LS_KEYS.presentation, 'false');
            } else if (_selectedIds.size > 0) {
                resetBulkSelection();
                updateBulkPanel();
            } else if (document.activeElement === searchInput && searchInput.value) {
                searchInput.value = '';
                lsSet(LS_KEYS.searchQuery, '');
                if (window.__state && window.__state.applyFilters) window.__state.applyFilters();
                if (window.__state && window.__state.highlightSearch) window.__state.highlightSearch('');
            }
        }
    });

    try { setupLinkTooltips(); } catch (e) { console.error('[setupLinkTooltips]', e); }
}

/* ============================================================
   ============================================================
   BOOT
   ============================================================
   ============================================================ */
    window.__reestrInitMain = initMain;
    window.__reestrInitExtended = initExtended;

    function _logErr(tag, e) {
        var msg = (e && e.message) || String(e);
        var stack = (e && e.stack) || '';
        if (window.__reestrLog) window.__reestrLog('error', tag + ': ' + msg, stack);
        try { console.error(tag, e); } catch (_) {}
    }

    function bootReestr() {
        // NEW: сначала применяем CSS кастомной темы ДО инициализации UI,
        // чтобы избежать мигания дефолтной темой.
        try {
            var _t0 = lsGet(LS_KEYS.theme, DEFAULT_THEME);
            try { applyCustomThemeCSS(_t0); } catch (e) { _logErr('[applyCustomThemeCSS]', e); }
        } catch (e) { _logErr('[theme-boot]', e); }

        try { initMain(); } catch (e) { _logErr('[initMain] FAILED', e); }
        try { initExtended(); } catch (e) { _logErr('[initExtended] FAILED', e); }
        try { schedulePageReady(); } catch (e) { _logErr('[schedulePageReady]', e); }
        try { setupStorageSync(); } catch (e) { _logErr('[setupStorageSync]', e); }

        // Подсветка кода — сразу и с задержкой (на случай, если DOM/плагин добавят блоки позже)
        highlightAllCodeBlocks();
        setTimeout(highlightAllCodeBlocks, 300);
        setTimeout(highlightAllCodeBlocks, 800);
        setTimeout(highlightAllCodeBlocks, 1500);

        // ИЗМЕНЕНО: переприменение темы с дефолтом light + очистка старых классов
        setTimeout(function() {
            var t = lsGet(LS_KEYS.theme, DEFAULT_THEME) || DEFAULT_THEME;
            // Убираем все theme-* кроме нужного
            var cls = document.body.classList;
            var toRemove = [];
            for (var i = 0; i < cls.length; i++) {
                if (cls[i].indexOf('theme-') === 0 && cls[i] !== 'theme-' + t) toRemove.push(cls[i]);
            }
            toRemove.forEach(function(c) { cls.remove(c); });
            if (!document.body.classList.contains('theme-' + t)) {
                document.body.classList.add('theme-' + t);
            }
            document.querySelectorAll('.theme-dot').forEach(function(d) {
                d.classList.toggle('active', d.getAttribute('data-theme') === t);
            });
        }, 800);

        console.log('[REESTR] app.js loaded, boot complete');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootReestr);
    } else {
        bootReestr();
    }
// Маркер успешной загрузки — его проверяет диагностика в index.html
    window.__reestrAppLoaded = true;
})();

