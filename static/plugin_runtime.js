/* ============================================================
   CSRF-ХЕЛПЕРЫ ДЛЯ ПЛАГИНОВ
   Использование в плагинах:
     window.reestrFetch('/api/...', {method: 'POST', body: '...'})
     fetch('/api/...', {method: 'POST', headers: window.reestrCsrfHeader(), ...})
   ============================================================ */
window.reestrCsrf = function() {
    if (window.REESTR_CSRF) return window.REESTR_CSRF;
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.getAttribute('content') : '';
};

window.reestrCsrfHeader = function() {
    var t = window.reestrCsrf();
    return t ? { 'X-CSRF-Token': t } : {};
};

window.reestrFetch = function(url, options) {
    options = options || {};
    var method = (options.method || 'GET').toUpperCase();
    if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
        options.headers = Object.assign({}, options.headers || {}, window.reestrCsrfHeader());
    }
    return fetch(url, options);
};

/* ============================================================
   Модалки плагинов
   ============================================================ */
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