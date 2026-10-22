/* ============================================================
   PLUGIN RUNTIME
   1. Глобальный патч window.fetch: авто-CSRF + retry при 403.
   2. openPluginModal / closePluginModal.
   3. Обработка кликов по data-plugin-action.
   4. pluginFetch как явный алиас.
   ============================================================ */

(function () {
    if (window.__reestrFetchPatched) return;
    window.__reestrFetchPatched = true;

    var origFetch = window.fetch.bind(window);
    var refreshing = null;

    function getToken() {
        var tok = window.REESTR_CSRF || '';
        if (!tok) {
            var m = document.querySelector('meta[name="csrf-token"]');
            if (m) tok = m.getAttribute('content') || '';
        }
        return tok;
    }

    function refreshToken() {
        if (refreshing) return refreshing;
        refreshing = origFetch('/api/csrf-token', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d && d.token) {
                    window.REESTR_CSRF = d.token;
                    var meta = document.querySelector('meta[name="csrf-token"]');
                    if (meta) meta.setAttribute('content', d.token);
                    return d.token;
                }
                return null;
            })
            .catch(function () { return null; })
            .finally(function () { refreshing = null; });
        return refreshing;
    }

    function isMutating(method) {
        method = (method || 'GET').toUpperCase();
        return method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS';
    }

    function isCsrfEndpoint(url) {
        try {
            return String(url).indexOf('/api/csrf-token') !== -1;
        } catch (e) { return false; }
    }

    function patchOptions(url, options) {
        options = options || {};
        var method = (options.method || 'GET').toUpperCase();
        if (isMutating(method) && !isCsrfEndpoint(url)) {
            options.headers = Object.assign({}, options.headers || {});
            var hasHeader =
                options.headers['X-CSRF-Token'] ||
                options.headers['x-csrf-token'];
            if (!hasHeader) {
                var tok = getToken();
                if (tok) options.headers['X-CSRF-Token'] = tok;
            }
            if (!options.credentials) options.credentials = 'same-origin';
        }
        return options;
    }

    window.fetch = function reestrFetch(url, options, _retried) {
        options = patchOptions(url, options);
        return origFetch(url, options).then(function (resp) {
            if (resp.status !== 403 || _retried) return resp;
            return resp.clone().json().then(function (j) {
                if (!j || j.code !== 'CSRF') return resp;
                return refreshToken().then(function (newTok) {
                    if (!newTok) return resp;
                    var opts2 = Object.assign({}, options);
                    opts2.headers = Object.assign({}, options.headers || {});
                    opts2.headers['X-CSRF-Token'] = newTok;
                    if (!opts2.credentials) opts2.credentials = 'same-origin';
                    return window.fetch(url, opts2, true);
                });
            }).catch(function () { return resp; });
        });
    };

    window.pluginFetch = function (url, options) {
        return window.fetch(url, options);
    };
})();

/* ---------- Модалки плагинов ---------- */
function openPluginModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.add('active');
}

function closePluginModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove('active');
}

window.openPluginModal = openPluginModal;
window.closePluginModal = closePluginModal;

/* ---------- Клики по кнопкам плагинов ---------- */
document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(e) {
        const btn = e.target.closest('[data-plugin-action]');
        if (!btn) return;
        const action = btn.getAttribute('data-plugin-action');
        const modalId = btn.getAttribute('data-plugin-modal') || '';
        const url = btn.getAttribute('data-plugin-url') || '';
        const jsCode = btn.getAttribute('data-plugin-js') || '';

        if (action === 'openModal' && modalId) {
            openPluginModal(modalId);
        } else if (action === 'link' && url) {
            window.location.href = url;
        } else if (action === 'download' && url) {
            window.open(url, '_blank', 'noopener,noreferrer');
        } else if (action === 'js' && jsCode) {
            try {
                (new Function(jsCode))();
            } catch (err) {
                console.error('[PLUGIN] JS error:', err);
            }
        }
    });

    document.querySelectorAll('.modal[data-plugin-modal="1"]').forEach(function(m) {
        m.addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('active');
        });
    });
});
