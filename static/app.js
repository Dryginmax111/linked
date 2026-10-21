/* ============================================================
   РЕЕСТР ССЫЛОК — JavaScript
   Версия: 4.0
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

var _csrfRefreshInFlight = null;

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
                return apiFetch(url, retryOptions, true).then(function(retriedResp) {
                    if (retriedResp.status === 403 && typeof showNotification === 'function') {
                        showNotification('⚠️ Сессия устарела. Обновите страницу (Ctrl+F5).', 'error');
                    }
                    return retriedResp;
                });
            });
        }).catch(function() {
            return response;
        });
    });
}

/* ============================================================
   LocalStorage helpers
   ============================================================ */
function lsGet(key, def = null) {
    try { const v = localStorage.getItem(key); return v === null ? def : v; } catch (e) { return def; }
}
function lsSet(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
function lsGetJSON(key, def = null) {
    try { const v = localStorage.getItem(key); return v === null ? def : JSON.parse(v); } catch (e) { return def; }
}
function lsSetJSON(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {} }
function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
}
function $(id) { return document.getElementById(id); }

/* ============================================================
   Clipboard
   ============================================================ */
function copyTextToClipboard(text) {
    return new Promise(function(resolve, reject) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(resolve).catch(function() {
                try {
                    const ta = document.createElement('textarea');
                    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                    document.body.appendChild(ta); ta.select();
                    document.execCommand('copy');
                    document.body.removeChild(ta);
                    resolve();
                } catch (e) { reject(e); }
            });
        } else {
            try {
                const ta = document.createElement('textarea');
                ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
                document.body.appendChild(ta); ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                resolve();
            } catch (e) { reject(e); }
        }
    });
}

/* ============================================================
   Loading / notification
   ============================================================ */
let _loadingCount = 0;
function showLoading() {
    _loadingCount++;
    const bar = $('loadingBar'), spinner = $('loadingSpinner');
    if (bar) { bar.classList.remove('done'); bar.style.width = '30%'; setTimeout(function() { if (_loadingCount > 0) bar.style.width = '70%'; }, 150); }
    if (spinner) spinner.classList.add('visible');
}
function hideLoading() {
    _loadingCount = Math.max(0, _loadingCount - 1);
    if (_loadingCount === 0) {
        const bar = $('loadingBar'), spinner = $('loadingSpinner');
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
    const n = $('notification');
    if (!n) return;
    n.textContent = message;
    n.className = 'notification show ' + (type === 'error' ? 'error' : '');
    setTimeout(function() { n.classList.remove('show'); }, 3000);
}

/* ============================================================
   Excel lock modal
   ============================================================ */
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
   Confirm / undo toast
   ============================================================ */
let _confirmHandler = null;
function showConfirm(title, messageHtml, okLabel, onConfirm) {
    const modal = $('confirmModal');
    if (!modal) { if (onConfirm) onConfirm(); return; }
    $('confirmTitle').innerHTML = title;
    $('confirmMessage').innerHTML = messageHtml;
    $('confirmOkBtn').textContent = okLabel || 'Подтвердить';
    _confirmHandler = onConfirm;
    modal.classList.add('active');
}
let _undoTimer = null, _undoCallback = null, _undoActionActive = false;
function showUndoToast(message, undoCallback, duration) {
    duration = duration || 8000;
    const toast = $('undoToast');
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
    const btn = $('undoToastBtn');
    if (btn) { btn.click(); return true; }
    return false;
}

/* ============================================================
   Theme / shimmer / mesh / strip
   ============================================================ */
function applyTheme(theme) {
    if (!theme || typeof theme !== 'string') theme = 'dark';
    if (!/^[a-z][a-z0-9_-]{0,63}$/i.test(theme)) theme = 'dark';

    // Убираем ВСЕ классы theme-*
    document.body.className = document.body.className
        .split(/\s+/)
        .filter(function(c) { return c && !c.startsWith('theme-'); })
        .join(' ');

    if (theme !== 'dark') {
        document.body.classList.add('theme-' + theme);
    }

    document.querySelectorAll('.theme-dot').forEach(function(d) {
        d.classList.toggle('active', d.getAttribute('data-theme') === theme);
    });
    lsSet(LS_KEYS.theme, theme);
}
function applyShimmerColors(c1, c2) {
    const use1 = c1 || DEFAULT_SHIMMER_1, use2 = c2 || DEFAULT_SHIMMER_2;
    document.documentElement.style.setProperty('--shimmer-1', use1);
    document.documentElement.style.setProperty('--shimmer-2', use2);
    const inp1 = $('shimmerColor1'), inp2 = $('shimmerColor2');
    if (inp1) inp1.value = use1;
    if (inp2) inp2.value = use2;
}
function applyHeaderShimmer(variant, speed, intensity) {
    HEADER_SHIMMER_VARIANTS.forEach(function(v) { document.body.classList.remove('header-shimmer-' + v); });
    const useVariant = (HEADER_SHIMMER_VARIANTS.indexOf(variant) !== -1) ? variant : 'sweep';
    document.body.classList.add('header-shimmer-' + useVariant);
    const speedMap = { slow: 0.65, normal: 1, fast: 1.5 };
    document.documentElement.style.setProperty('--shimmer-speed', speedMap[speed] || 1);
    const inten = (typeof intensity === 'number' && intensity > 0) ? intensity : 1;
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
   Filter index
   ============================================================ */
function buildFilterIndex() {
    _filterIndex = [];
    document.querySelectorAll('.card').forEach(function(card) {
        const group = (card.getAttribute('data-group') || '').toLowerCase();
        let cardCats = [];
        try {
            const raw = card.getAttribute('data-categories') || '[]';
            cardCats = JSON.parse(raw);
            if (!Array.isArray(cardCats)) cardCats = [];
        } catch (e) {
            cardCats = (card.getAttribute('data-categories') || '').split('|').filter(Boolean);
        }
        cardCats = cardCats.map(function(c) { return String(c).toLowerCase(); });
        card.querySelectorAll('.link-item').forEach(function(li) {
            const linkDisplay = li.querySelector('.link-display');
            const smartLink = li.querySelector('.smart-link');
            const descEl = li.querySelector('.desc');
            const favBtn = li.querySelector('.favorite-btn');
            _filterIndex.push({
                el: li, card: card, id: li.getAttribute('data-id'),
                group: group, cardCats: cardCats,
                link: (linkDisplay ? linkDisplay.textContent : '').toLowerCase(),
                fullLink: (smartLink ? smartLink.getAttribute('data-full-link') : '').toLowerCase(),
                desc: ((descEl && descEl.getAttribute('data-original')) || '').toLowerCase(),
                cat: (li.getAttribute('data-category') || '').toLowerCase(),
                tags: (li.getAttribute('data-tags') || '').toLowerCase().split(',').filter(Boolean),
                updated: li.getAttribute('data-updated') || '',
                fav: favBtn ? favBtn.classList.contains('fav-on') : false
            });
        });
    });
    _filterIndexDirty = false;
}

/* ============================================================
   Sortable
   ============================================================ */
function makeSortable(container, itemSelector, handleSelector, onEnd, isEnabled) {
    if (!container) return;
    const enabled = isEnabled || function() { return true; };
    function getItems() {
        return Array.from(container.children).filter(function(c) { return c.matches(itemSelector); });
    }
    container.addEventListener('pointerdown', function(e) {
        if (e.button !== 0 || !enabled()) return;
        const item = e.target.closest(itemSelector);
        if (!item || item.parentElement !== container) return;
        if (e.target.closest('button, .edit-btn, .delete-btn, .favorite-btn, .rename-group-btn, .cat-sort-btn, .card-sort-btn, .card-sort-dropdown, .bulk-checkbox, .bulk-checkbox-card, .card-icon, input[type="checkbox"], .desc, .link-status, .category-tag, .tag-chip, .link-code')) return;
        if (handleSelector && !e.target.closest(handleSelector)) return;
        const startX = e.clientX, startY = e.clientY;
        let isDragging = false, dragged = null;
        const origUserSelect = document.body.style.userSelect;
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
            const elem = document.elementFromPoint(ev.clientX, ev.clientY);
            if (!elem) return;
            const target = elem.closest(itemSelector);
            if (!target || target === dragged || target.parentElement !== container) {
                getItems().forEach(function(i) { i.classList.remove('drag-over-top', 'drag-over-bottom'); });
                return;
            }
            getItems().forEach(function(i) { i.classList.remove('drag-over-top', 'drag-over-bottom'); });
            const r = target.getBoundingClientRect();
            const mid = r.top + r.height / 2;
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
   Link drag: одна ссылка ИЛИ группа выделенных
   ============================================================ */
function setupLinkDrag() {
    let dragging = null, sourceContainer = null, sourceCard = null;
    let groupDragIds = null, groupDragElements = null;

    function clearMarkers() {
        document.querySelectorAll('.link-item.drag-over-top, .link-item.drag-over-bottom').forEach(function(x) {
            x.classList.remove('drag-over-top', 'drag-over-bottom');
        });
        document.querySelectorAll('.card.drag-over-card').forEach(function(x) { x.classList.remove('drag-over-card'); });
    }

    function collectGroupForDrag(li) {
        const id = li.getAttribute('data-id');
        const selected = getSelectedIds();
        if (!selected.has(id)) return null;
        if (selected.size < 2) return null;
        const els = [];
        document.querySelectorAll('.link-item.bulk-selected').forEach(function(el) { els.push(el); });
        return els.length > 1 ? els : null;
    }

    document.querySelectorAll('.card .links').forEach(function(container) {
        container.addEventListener('pointerdown', function(e) {
            if (e.button !== 0) return;
            const li = e.target.closest('.link-item');
            if (!li || li.parentElement !== container) return;
            if (e.target.closest('button, .edit-btn, .delete-btn, .favorite-btn, .bulk-checkbox, input, a, .desc, .link-status, .meta-created, .tag-chip, .category-tag, .link-code')) return;

            const startX = e.clientX, startY = e.clientY;
            let started = false;

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
                const elem = document.elementFromPoint(ev.clientX, ev.clientY);
                if (!elem) return;
                const targetLi = elem.closest('.link-item');
                const targetCard = elem.closest('.card');
                clearMarkers();
                if (targetLi && targetLi !== dragging && targetLi.parentElement === sourceContainer) {
                    const r = targetLi.getBoundingClientRect();
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
                    const elem = document.elementFromPoint(ev.clientX, ev.clientY);
                    const targetLi = elem ? elem.closest('.link-item') : null;
                    const targetCard = elem ? elem.closest('.card') : null;

                    if (groupDragIds && targetCard && targetCard !== sourceCard) {
                        const targetGroup = targetCard.getAttribute('data-group');
                        const sourceGroup = sourceCard ? sourceCard.getAttribute('data-group') : '';
                        groupDragElements.forEach(function(el) { el.classList.remove('dragging'); });
                        if (targetGroup && sourceGroup && targetGroup !== sourceGroup) {
                            moveGroupToGroup(groupDragIds, targetGroup, sourceGroup);
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
                        const targetGroup = targetCard.getAttribute('data-group');
                        const recordId = dragging.getAttribute('data-id');
                        if (targetGroup && recordId && sourceCard) {
                            const sourceGroup = sourceCard.getAttribute('data-group');
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
                        const r = targetLi.getBoundingClientRect();
                        if (ev.clientY < r.top + r.height / 2) sourceContainer.insertBefore(dragging, targetLi);
                        else sourceContainer.insertBefore(dragging, targetLi.nextSibling);
                        const orderedIds = [];
                        sourceContainer.querySelectorAll('.link-item').forEach(function(x) {
                            orderedIds.push(parseInt(x.getAttribute('data-id')));
                        });
                        const groupName = sourceCard.getAttribute('data-group');
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

let _dragCounterEl = null;
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
    let done = 0;
    let failed = 0;
    let firstError = '';
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
   Link tooltips
   ============================================================ */
function setupLinkTooltips() {
    const tooltip = $('linkTooltip');
    if (!tooltip) return;
    function hideTooltip() { tooltip.classList.remove('visible'); }
    _hideLinkTooltipGlobal = hideTooltip;
    document.querySelectorAll('.smart-link').forEach(function(link) {
        link.addEventListener('mouseenter', function() {
            const display = this.querySelector('.link-display');
            if (!display || display.scrollWidth <= display.clientWidth + 1) return;
            const fullText = this.getAttribute('data-full-link');
            if (!fullText) return;
            tooltip.textContent = fullText;
            tooltip.classList.add('visible');
            const rect = this.getBoundingClientRect();
            let top = rect.bottom + 6, left = rect.left;
            tooltip.style.left = '-9999px'; tooltip.style.top = '-9999px';
            const tw = tooltip.offsetWidth, th = tooltip.offsetHeight;
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
   Sort dropdown
   ============================================================ */
let _activeSortDropdown = null, _activeSortBtn = null;

function buildSortDropdown(group) {
    const dd = document.createElement('div');
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
            const sortBy = this.getAttribute('data-sort-by');
            const asc = this.getAttribute('data-asc') === '1';
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
    const dd = buildSortDropdown(group);
    document.body.appendChild(dd);
    const rect = btn.getBoundingClientRect();
    const ddRectWidth = 200;
    let left = rect.right - ddRectWidth;
    if (left < 8) left = 8;
    if (left + ddRectWidth > window.innerWidth - 8) left = window.innerWidth - ddRectWidth - 8;
    let top = rect.bottom + 4;
    const estimatedHeight = 180;
    if (top + estimatedHeight > window.innerHeight - 8) { top = rect.top - estimatedHeight - 4; if (top < 8) top = 8; }
    dd.style.left = left + 'px'; dd.style.top = top + 'px';
    dd.classList.add('show');
    btn.classList.add('active');
    _activeSortDropdown = dd; _activeSortBtn = btn;
}

/* ============================================================
   Focus trap
   ============================================================ */
function trapFocus(modal) {
    const focusable = modal.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable.length) return function() {};
    const first = focusable[0], last = focusable[focusable.length - 1];
    const previousActive = document.activeElement;
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
        let cleanup = null;
        const obs = new MutationObserver(function(mutations) {
            for (let i = 0; i < mutations.length; i++) {
                if (mutations[i].attributeName === 'class') {
                    const isActive = modal.classList.contains('active');
                    if (isActive && !cleanup) cleanup = trapFocus(modal);
                    else if (!isActive && cleanup) { cleanup(); cleanup = null; }
                }
            }
        });
        obs.observe(modal, { attributes: true, attributeFilter: ['class'] });
    });
}

/* ============================================================
   Selection helpers
   ============================================================ */
function getSelectedIds() {
    return _selectedIds;
}
function resetBulkSelection() {
    _selectedIds.clear();
    document.querySelectorAll('.link-item').forEach(function(li) { li.classList.remove('bulk-selected'); });
    document.querySelectorAll('.bulk-checkbox-card').forEach(function(cb) { cb.checked = false; });
    document.querySelectorAll('.bulk-checkbox').forEach(function(cb) { cb.checked = false; });
}

/* ============================================================
   Cross-tab sync
   ============================================================ */
function setupStorageSync() {
    window.addEventListener('storage', function(e) {
        if (!e.key) return;
        var k = e.key;
        var v = e.newValue;
        if (k === LS_KEYS.theme) {
            applyTheme(v || 'dark');
        } else if (k === LS_KEYS.cols) {
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
            var fs = $('fontSizeSlider'); if (fs) fs.value = v;
            var fsv = $('fontSizeVal'); if (fsv) fsv.textContent = v;
        } else if (k === LS_KEYS.radius) {
            document.documentElement.style.setProperty('--radius-card', (v || '16') + 'px');
            var rs = $('radiusSlider'); if (rs) rs.value = v;
            var rv = $('radiusVal'); if (rv) rv.textContent = v;
        } else if (k === LS_KEYS.sidebarWidth) {
            document.documentElement.style.setProperty('--sidebar-width', (v || '260') + 'px');
            var sw = $('sidebarWidthSlider'); if (sw) sw.value = v;
            var swv = $('sidebarWidthVal'); if (swv) swv.textContent = v;
        } else if (k === LS_KEYS.compact) {
            var on = v === 'true';
            document.body.classList.toggle('compact-mode', on);
            var ct = $('compactModeToggle'); if (ct) ct.checked = on;
        } else if (k === LS_KEYS.headerAnim) {
            var on2 = v !== 'false';
            document.body.classList.toggle('header-anim-off', !on2);
            var ha = $('headerAnimToggle'); if (ha) ha.checked = on2;
        }
    });
}

/* ============================================================
   Server-side settings auto-save
   ============================================================ */
function saveServerSettings(partial) {
    return api('/save_settings', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(partial)
    }).then(function(r) { return r.json(); }).catch(function() { return {success: false}; });
}

/* ============================================================
   Card animation trigger
   ============================================================ */
function schedulePageReady() {
    setTimeout(function() {
        document.body.classList.add('page-ready');
    }, 200);
}

/* ============================================================
   INIT MAIN
   ============================================================ */
document.addEventListener('DOMContentLoaded', function() {
    /* Критические кнопки — вешаем СРАЗУ, до initMain.
       Если initMain упадёт, «+», категории и теги всё равно работают. */
    try { bindCriticalUI(); } catch (e) { console.error('[bindCriticalUI]', e); }
    try { initMain(); } catch (e) { console.error('[initMain]', e); }
    try { initExtended(); } catch (e) { console.error('[initExtended]', e); }
    schedulePageReady();
    setupStorageSync();
});

/* ============================================================
   Критический UI (делегирование) — не зависит от initMain
   ============================================================ */
function bindCriticalUI() {
    if (window.__criticalUIBound) return;
    window.__criticalUIBound = true;

    // Сброс застрявшего режима презентации, если FAB скрыт
    try {
        if (document.body.classList.contains('presentation-mode')) {
            var fab = document.getElementById('openAddModal');
            if (fab) {
                var st = window.getComputedStyle(fab);
                if (st.display === 'none') {
                    document.body.classList.remove('presentation-mode');
                    try { localStorage.removeItem('reestr_presentation'); } catch (e) {}
                }
            }
        }
    } catch (e) {}

    document.addEventListener('click', function(e) {
        // FAB «+» — открыть модалку добавления
        var addBtn = e.target.closest('#openAddModal');
        if (addBtn) {
            e.preventDefault();
            var m = document.getElementById('addModal');
            if (m) m.classList.add('active');
            if (window.__prepareAddModal) window.__prepareAddModal();
            else if (window.__state && window.__state.prepareAddModal) window.__state.prepareAddModal();
            setTimeout(function() {
                var n = document.getElementById('name');
                if (n) n.focus();
            }, 80);
            return;
        }

        // Кнопка настроек (шестерёнка)
        var appBtn = e.target.closest('#openAppearanceModal');
        if (appBtn) {
            var am = document.getElementById('appearanceModal');
            if (am) am.classList.add('active');
            return;
        }

        // Категории в сайдбаре
        var catBtn = e.target.closest('.cat-btn[data-filter]');
        if (catBtn && !e.target.closest('.cat-move-btn, .cat-sort-btn')) {
            if (window.__catDragJustEnded) return;
            var favBtn = document.getElementById('filterFavBtn');
            if (favBtn) favBtn.classList.remove('active');
            try { localStorage.setItem('reestr_showFavorites', 'false'); } catch (err) {}
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            catBtn.classList.add('active');
            var filter = catBtn.getAttribute('data-filter') || 'all';
            try { localStorage.setItem('reestr_activeCategory', filter); } catch (err) {}
            var _af = (window.__state && window.__state.applyFilters) || window.__applyFilters;
            if (_af) _af();
            if (window.__state && window.__state.closeMobileSidebar) window.__state.closeMobileSidebar();
            return;
        }

        // Избранное
        var fav = e.target.closest('#filterFavBtn');
        if (fav) {
            fav.classList.toggle('active');
            var isActive = fav.classList.contains('active');
            try { localStorage.setItem('reestr_showFavorites', isActive ? 'true' : 'false'); } catch (err) {}
            if (isActive) {
                document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            } else {
                var activeCat = 'all';
                try { activeCat = localStorage.getItem('reestr_activeCategory') || 'all'; } catch (err) {}
                document.querySelectorAll('.cat-btn').forEach(function(b) {
                    if (b.getAttribute('data-filter') === activeCat) b.classList.add('active');
                });
            }
            var _af2 = (window.__state && window.__state.applyFilters) || window.__applyFilters;
            if (_af2) _af2();
            if (window.__state && window.__state.closeMobileSidebar) window.__state.closeMobileSidebar();
            return;
        }

        // Теги в облаке
        var tagItem = e.target.closest('.tag-cloud-item');
        if (tagItem) {
            var tagName = (tagItem.getAttribute('data-tag') || '').trim();
            if (!tagName) {
                var raw = (tagItem.textContent || '').replace(/\d+/g, '').replace(/#/g, '').trim();
                tagName = raw.split(/\s+/)[0] || '';
            }
            if (!tagName) return;
            var act = [];
            try {
                act = JSON.parse(localStorage.getItem('reestr_activeTags') || '[]');
                if (!Array.isArray(act)) act = [];
            } catch (err) { act = []; }
            if (act.indexOf(tagName) !== -1) act = act.filter(function(t) { return t !== tagName; });
            else act.push(tagName);
            try { localStorage.setItem('reestr_activeTags', JSON.stringify(act)); } catch (err) {}
            tagItem.classList.toggle('active');
            if (window.__state && window.__state.resetCategoryToAll) window.__state.resetCategoryToAll();
            var _af3 = (window.__state && window.__state.applyFilters) || window.__applyFilters;
            if (_af3) _af3();
            return;
        }

        // Закрытие модалок по кнопкам Отмена/Закрыть
        var closeAdd = e.target.closest('#closeAddModalBtn');
        if (closeAdd) {
            var addM = document.getElementById('addModal');
            if (addM) addM.classList.remove('active');
            return;
        }
        var closeApp = e.target.closest('#closeAppearanceModalBtn');
        if (closeApp) {
            var appM = document.getElementById('appearanceModal');
            if (appM) appM.classList.remove('active');
            return;
        }
    });

    // Закрытие модалки по клику на фон
    document.querySelectorAll('.modal').forEach(function(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) modal.classList.remove('active');
        });
    });
}

function initMain() {
    const sidebar = $('sidebar');
    const sidebarOverlay = $('sidebarOverlay');
    const sidebarFloatToggle = $('sidebarFloatToggle');
    const searchInput = $('searchInput');
    const cardsGrid = $('cardsGrid');
    const manualHint = $('manualHint');
    const filterFavBtn = $('filterFavBtn');

    setupFocusTraps();

    function resetCategoryToAll() {
        document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
        if (filterFavBtn) filterFavBtn.classList.remove('active');
        const allBtn = document.querySelector('.cat-btn[data-filter="all"]');
        if (allBtn) allBtn.classList.add('active');
        lsSet(LS_KEYS.activeCategory, 'all');
        lsSet(LS_KEYS.showFavorites, 'false');
    }
    function closeAppearanceModal() {
        const m = $('appearanceModal'); if (m) m.classList.remove('active');
    }

    let _namesDatalistAbort = null;
    function updateNamesDatalist(category) {
        const datalist = $('names-datalist'); if (!datalist) return;
        if (_namesDatalistAbort) try { _namesDatalistAbort.abort(); } catch (e) {}
        _namesDatalistAbort = new AbortController();
        const url = category ? '/get_names_for_category?category=' + encodeURIComponent(category) : '/get_all_names';
        fetch(url, { signal: _namesDatalistAbort.signal })
            .then(function(r) { return r.json(); })
            .then(function(names) {
                datalist.innerHTML = (names || []).map(function(n) {
                    return '<option value="' + escapeHtml(n) + '">';
                }).join('');
            })
            .catch(function(err) { if (err && err.name === 'AbortError') return; });
    }
    function prepareAddModal() {
        const catSelect = $('category_add');
        const catCustom = $('category_custom');
        const catHidden = $('category_hidden');
        let activeCat = '';
        const favActive = filterFavBtn && filterFavBtn.classList.contains('active');
        const activeBtn = document.querySelector('.cat-btn.active');
        if (!favActive && activeBtn) {
            const f = activeBtn.getAttribute('data-filter');
            if (f && f !== 'all' && f !== '__none__') activeCat = f;
        }
        if (catSelect) {
            if (activeCat) {
                let found = false;
                for (let i = 0; i < catSelect.options.length; i++) {
                    if (catSelect.options[i].value === activeCat) { catSelect.selectedIndex = i; found = true; break; }
                }
                if (!found) {
                    catSelect.value = '__other__';
                    if (catCustom) { catCustom.style.display = 'block'; catCustom.value = activeCat; }
                } else if (catCustom) { catCustom.style.display = 'none'; catCustom.value = ''; }
            } else {
                catSelect.value = '';
                if (catCustom) { catCustom.style.display = 'none'; catCustom.value = ''; }
            }
            if (catHidden) {
                catHidden.value = (catSelect.value === '__other__')
                    ? (catCustom ? catCustom.value.trim() : '')
                    : (catSelect.value || '');
            }
        }
        updateNamesDatalist(activeCat);
        const iconBtn = $('addIconPickerBtn'), iconHidden = $('add_group_icon');
        if (iconBtn) iconBtn.textContent = '📌';
        if (iconHidden) iconHidden.value = '';

        // Сброс редактора кода
        const codeAddEl = $('code_add');
        const langAddEl = $('code_lang_add');
        const codeBodyAdd = $('codeEditorBodyAdd');
        const codeBtnAdd = $('codeToggleBtnAdd');
        if (codeAddEl) codeAddEl.value = '';
        if (langAddEl) langAddEl.value = '';
        if (codeBodyAdd) codeBodyAdd.classList.remove('open');
        if (codeBtnAdd) codeBtnAdd.textContent = '▼ Раскрыть';
    }
    window.__prepareAddModal = prepareAddModal;

    SECTION_IDS.forEach(function(id) {
        const el = $(id); if (!el) return;
        if (lsGet('reestr_sectionCollapsed_' + id, 'false') === 'true') el.classList.add('collapsed');
    });
    document.querySelectorAll('.section-toggle').forEach(function(label) {
        label.addEventListener('click', function(e) {
            if (e.target.closest('.cat-sort-btn')) return;
            if (e.target.closest('.cat-manage-btn')) return;
            const targetId = this.getAttribute('data-target');
            if (!targetId) return;
            const section = $(targetId); if (!section) return;
            const isCollapsed = section.classList.toggle('collapsed');
            lsSet('reestr_sectionCollapsed_' + targetId, isCollapsed ? 'true' : 'false');
        });
    });

    /* ---------- Appearance modal ---------- */
    (function setupAppearanceModal() {
        const modal = $('appearanceModal');
        const openBtn = $('openAppearanceModal');
        const closeBtn = $('closeAppearanceModalBtn');
        const tabs = document.querySelectorAll('.settings-tab');
        const panels = document.querySelectorAll('.settings-panel');
        function switchTab(tabId) {
            tabs.forEach(function(t) { t.classList.toggle('active', t.getAttribute('data-tab') === tabId); });
            panels.forEach(function(p) { p.classList.toggle('active', p.id === tabId); });
            lsSet(LS_KEYS.settingsTab, tabId);
        }
        const savedTab = lsGet(LS_KEYS.settingsTab, 'tab-appearance');
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
        const cb = $('headerAnimToggle'); if (cb) cb.checked = enabled;
    }
    applyHeaderAnim(lsGet(LS_KEYS.headerAnim, 'true') === 'true');
    const headerAnimToggle = $('headerAnimToggle');
    if (headerAnimToggle) headerAnimToggle.addEventListener('change', function() {
        applyHeaderAnim(this.checked);
        lsSet(LS_KEYS.headerAnim, this.checked ? 'true' : 'false');
    });

    /* ---------- Mesh-фон ---------- */
    const meshBgSelect = $('meshBgSelect');
    let savedMesh = lsGet(LS_KEYS.meshBg, 'off');
    if (savedMesh === 'true') savedMesh = 'float';
    if (savedMesh === 'false') savedMesh = 'off';
    if (savedMesh !== 'off' && MESH_STYLES.indexOf(savedMesh) === -1) savedMesh = 'off';

    applyMeshStyle(savedMesh);
    if (meshBgSelect) {
        meshBgSelect.value = savedMesh;
        meshBgSelect.addEventListener('change', function() {
            const val = this.value;
            applyMeshStyle(val);
            lsSet(LS_KEYS.meshBg, val);
            saveServerSettings({ mesh_style: val });
        });
    }

    /* ---------- Compact mode ---------- */
    function applyCompact(on) {
        document.body.classList.toggle('compact-mode', on);
        const cb = $('compactModeToggle'); if (cb) cb.checked = on;
    }
    applyCompact(lsGet(LS_KEYS.compact, 'false') === 'true');
    const compactToggle = $('compactModeToggle');
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
    const savedWallpaper = lsGet(LS_KEYS.wallpaper, '');
    if (savedWallpaper) applyWallpaper(savedWallpaper);
    const wallpaperInput = $('wallpaperInput');
    if (wallpaperInput) wallpaperInput.addEventListener('change', function() {
        const file = this.files[0]; if (!file) return;
        if (file.size > 2 * 1024 * 1024) { showNotification('❌ Картинка больше 2 МБ', 'error'); this.value = ''; return; }
        const reader = new FileReader();
        reader.onload = function(ev) {
            const dataUrl = ev.target.result;
            lsSet(LS_KEYS.wallpaper, dataUrl);
            applyWallpaper(dataUrl);
            showNotification('✅ Обои применены', 'success');
        };
        reader.readAsDataURL(file);
        this.value = '';
    });
    const wallpaperClearBtn = $('wallpaperClearBtn');
    if (wallpaperClearBtn) wallpaperClearBtn.addEventListener('click', function() {
        lsSet(LS_KEYS.wallpaper, ''); applyWallpaper('');
        showNotification('✅ Обои убраны', 'success');
    });

    /* ---------- Shimmer colors ---------- */
    (function() {
        const settings = DATA.settings || {};
        applyShimmerColors(settings.shimmer_color_1 || '', settings.shimmer_color_2 || '');
        const inp1 = $('shimmerColor1'), inp2 = $('shimmerColor2'), resetBtn = $('shimmerResetBtn');
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
        const settings = DATA.settings || {};
        const headerShimmer = settings.header_shimmer || 'sweep';
        const cardShimmer = settings.card_shimmer !== false;
        const speed = settings.shimmer_speed || 'normal';
        const intensity = (typeof settings.shimmer_intensity === 'number') ? settings.shimmer_intensity : 1;
        applyHeaderShimmer(headerShimmer, speed, intensity);
        applyCardShimmer(cardShimmer);

        const select = $('headerShimmerSelect');
        if (select) {
            select.value = headerShimmer;
            select.addEventListener('change', function() {
                const val = this.value;
                applyHeaderShimmer(val, speed, intensity);
                saveServerSettings({ header_shimmer: val })
                    .then(function(data) { if (data.success) showNotification('✅ Перелив: ' + val, 'success'); });
            });
        }
        const cardToggle = $('cardShimmerToggle');
        if (cardToggle) {
            cardToggle.checked = cardShimmer;
            cardToggle.addEventListener('change', function() {
                const on = this.checked; applyCardShimmer(on);
                saveServerSettings({ card_shimmer: on })
                    .then(function(data) {
                        if (data.success) showNotification(on ? '✅ Перелив карточек включён' : 'Перелив карточек выключен', 'success');
                    });
            });
        }

        let savedStrip = lsGet(LS_KEYS.cardStrip, settings.card_strip || 'left');
        if (savedStrip === 'gradient-half') savedStrip = 'hover-fill';
        if (STRIP_VARIANTS.indexOf(savedStrip) === -1) savedStrip = 'left';
        applyCardStrip(savedStrip);
        const cardStripSelect = $('cardStripSelect');
        if (cardStripSelect) {
            cardStripSelect.value = savedStrip;
            cardStripSelect.addEventListener('change', function() {
                let val = this.value;
                if (STRIP_VARIANTS.indexOf(val) === -1) val = 'left';
                applyCardStrip(val);
                lsSet(LS_KEYS.cardStrip, val);
                saveServerSettings({ card_strip: val });
            });
        }

        const speedGroup = $('shimmerSpeedGroup');
        if (speedGroup) {
            speedGroup.querySelectorAll('.col-btn').forEach(function(btn) {
                btn.classList.toggle('active', btn.getAttribute('data-speed') === speed);
                btn.addEventListener('click', function() {
                    const sp = this.getAttribute('data-speed');
                    speedGroup.querySelectorAll('.col-btn').forEach(function(b) { b.classList.remove('active'); });
                    this.classList.add('active');
                    const cv = document.body.className.match(/header-shimmer-(\w+)/);
                    const v = cv ? cv[1] : 'sweep';
                    const curInt = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--shimmer-intensity')) || 1;
                    applyHeaderShimmer(v, sp, curInt);
                    saveServerSettings({ shimmer_speed: sp })
                        .then(function(data) { if (data.success) showNotification('✅ Скорость: ' + sp, 'success'); });
                });
            });
        }
        const intGroup = $('shimmerIntensityGroup');
        if (intGroup) {
            intGroup.querySelectorAll('.col-btn').forEach(function(btn) {
                const val = parseFloat(btn.getAttribute('data-intensity'));
                btn.classList.toggle('active', Math.abs(val - intensity) < 0.01);
                btn.addEventListener('click', function() {
                    const v = parseFloat(this.getAttribute('data-intensity'));
                    intGroup.querySelectorAll('.col-btn').forEach(function(b) { b.classList.remove('active'); });
                    this.classList.add('active');
                    const cv = document.body.className.match(/header-shimmer-(\w+)/);
                    const variant = cv ? cv[1] : 'sweep';
                    const curSp = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--shimmer-speed')) || 1;
                    let spLabel = 'normal';
                    if (curSp < 0.9) spLabel = 'slow';
                    else if (curSp > 1.2) spLabel = 'fast';
                    applyHeaderShimmer(variant, spLabel, v);
                    saveServerSettings({ shimmer_intensity: v })
                        .then(function(data) { if (data.success) showNotification('✅ Интенсивность: ' + v + '×', 'success'); });
                });
            });
        }
    })();

    /* ---------- Presentation mode ---------- */
    function togglePresentation() {
        document.body.classList.toggle('presentation-mode');
        const on = document.body.classList.contains('presentation-mode');
        lsSet(LS_KEYS.presentation, on ? 'true' : 'false');
        showNotification(on ? '🎬 Режим презентации' : 'Режим презентации выключен', 'success');
    }
    if (lsGet(LS_KEYS.presentation, 'false') === 'true') document.body.classList.add('presentation-mode');
    const presentationBtn = $('presentationBtn');
    if (presentationBtn) presentationBtn.addEventListener('click', function() { closeAppearanceModal(); togglePresentation(); });

    /* ---------- Category sort ---------- */
    let categorySortMode = lsGet(LS_KEYS.catSort, 'name');
    if (['name', 'count', 'manual'].indexOf(categorySortMode) === -1) categorySortMode = 'name';
    function applyCategorySort() {
        const userWrapper = $('userCategoriesList'); if (!userWrapper) return;
        const rows = Array.from(userWrapper.querySelectorAll('.cat-row'));
        function catName(row) {
            const btn = row.querySelector('.cat-btn');
            return btn ? (btn.getAttribute('data-cat-name') || '') : '';
        }
        function catCount(row) {
            const btn = row.querySelector('.cat-btn');
            return btn ? (parseInt(btn.getAttribute('data-cat-count')) || 0) : 0;
        }
        if (categorySortMode === 'name') {
            rows.sort(function(a, b) {
                return catName(a).toLowerCase().localeCompare(catName(b).toLowerCase(), 'ru');
            });
        } else if (categorySortMode === 'count') {
            rows.sort(function(a, b) {
                const ac = catCount(a), bc = catCount(b);
                if (ac !== bc) return bc - ac;
                return catName(a).localeCompare(catName(b), 'ru');
            });
        } else {
            const idx = new Map((categoryManualOrder || []).map(function(n, i) { return [n, i]; }));
            rows.sort(function(a, b) {
                const an = catName(a), bn = catName(b);
                const ia = idx.has(an) ? idx.get(an) : 999999;
                const ib = idx.has(bn) ? idx.get(bn) : 999999;
                if (ia !== ib) return ia - ib;
                return an.localeCompare(bn, 'ru');
            });
        }
        rows.forEach(function(r) { userWrapper.appendChild(r); });
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

    /* ---------- Drag категорий (фикс + drag-and-drop) ---------- */
    let _catDragJustEnded = false;
    window.__catDragJustEnded = false;
    const catWrapperForDrag = $('userCategoriesList');
    if (catWrapperForDrag) {
        catWrapperForDrag.addEventListener('click', function(e) {
            if (_catDragJustEnded) {
                e.stopPropagation(); e.preventDefault();
                _catDragJustEnded = false;
            }
        }, true);
		catWrapperForDrag.addEventListener('pointerdown', function(e) {
            if (e.button !== 0) return;
            const btn = e.target.closest('.cat-btn[data-cat-name]');
            if (!btn) return;
            const row = btn.closest('.cat-row');
            if (!row || row.parentElement !== catWrapperForDrag) return;
            const startX = e.clientX, startY = e.clientY;
            let started = false, dragged = null;
            const origUserSelect = document.body.style.userSelect;
            function clearMarkers() {
                catWrapperForDrag.querySelectorAll('.cat-row').forEach(function(b) {
                    b.classList.remove('drag-over-top', 'drag-over-bottom');
                });
            }
            function onMove(ev) {
                if (!started) {
                    if (Math.abs(ev.clientX - startX) < 6 && Math.abs(ev.clientY - startY) < 6) return;
                    started = true; dragged = row;
                    dragged.classList.add('dragging');
                    document.body.style.userSelect = 'none';
                    document.body.style.cursor = 'grabbing';
                    categorySortMode = 'manual';
                    lsSet(LS_KEYS.catSort, 'manual');
                    document.querySelectorAll('.cat-sort-btn').forEach(function(b) {
                        b.classList.toggle('active', b.getAttribute('data-sort') === 'manual');
                    });
                }
                ev.preventDefault();
                const elem = document.elementFromPoint(ev.clientX, ev.clientY);
                if (!elem) return;
                const targetRow = elem.closest('.cat-row');
                clearMarkers();
                if (!targetRow || targetRow === dragged || targetRow.parentElement !== catWrapperForDrag) return;
                const r = targetRow.getBoundingClientRect();
                const mid = r.top + r.height / 2;
                if (ev.clientY < mid) {
                    targetRow.classList.add('drag-over-top');
                    if (dragged.nextElementSibling !== targetRow) catWrapperForDrag.insertBefore(dragged, targetRow);
                } else {
                    targetRow.classList.add('drag-over-bottom');
                    if (targetRow.nextElementSibling !== dragged) catWrapperForDrag.insertBefore(dragged, targetRow.nextSibling);
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
                    const names = Array.from(catWrapperForDrag.querySelectorAll('.cat-row'))
                        .map(function(r) {
                            return r.querySelector('.cat-btn').getAttribute('data-cat-name');
                        });
                    api('/save_category_order', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ order: names })
                    }).then(function(r) { return r.json(); }).then(function(data) {
                        if (data.success) showNotification('💾 Порядок категорий сохранён', 'success');
                    }).catch(function() {});
                    _catDragJustEnded = true; window.__catDragJustEnded = true;
                    setTimeout(function() { _catDragJustEnded = false; window.__catDragJustEnded = false; }, 300);
                }
                dragged = null; started = false;
            }
            document.addEventListener('pointermove', onMove);
            document.addEventListener('pointerup', onUp);
            document.addEventListener('pointercancel', onUp);
        });
    }

    /* ---------- Tag cloud ---------- */
    function buildTagCloud() {
        const cloud = $('tagsBar'); if (!cloud) return;
        cloud.innerHTML = '';
        const tags = Object.entries(allTagsFromServer || {}).sort(function(a, b) { return b[1] - a[1]; });
        const activeTags = lsGetJSON(LS_KEYS.activeTags, []);
        if (!tags.length) { cloud.style.display = 'none'; return; }
        cloud.style.display = '';
        tags.forEach(function(pair) {
            const name = pair[0], count = pair[1];
            const el = document.createElement('button');
            el.className = 'tag-cloud-item' + (activeTags.indexOf(name) !== -1 ? ' active' : '');
            el.type = 'button';
            el.setAttribute('data-tag', name);
            el.innerHTML = '#' + escapeHtml(name) + '<span class="tag-count">' + count + '</span>';
            // клик обрабатывается в bindCriticalUI (делегирование)
            cloud.appendChild(el);
        });
    }
    buildTagCloud();

    /* ---------- Manual sort cards ---------- */
    let manualModeEnabled = false;
    function updateManualHint() { if (manualHint) manualHint.classList.toggle('visible', manualModeEnabled); }
    function enableManualCardSort(enable) {
        manualModeEnabled = enable;
        if (cardsGrid) cardsGrid.classList.toggle('manual-sort', enable);
        updateManualHint();
    }
    if (cardsGrid) {
        makeSortable(cardsGrid, '.card', '.card-header', function() {
            const order = [];
            cardsGrid.querySelectorAll('.card').forEach(function(c) {
                const g = c.getAttribute('data-group'); if (g) order.push(g);
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
    applyTheme(lsGet(LS_KEYS.theme, 'dark'));
    document.querySelectorAll('.theme-dot').forEach(function(dot) {
        dot.addEventListener('click', function() { applyTheme(this.getAttribute('data-theme')); });
    });

    /* ---------- Sidebar ---------- */
    function updateSidebarFloatToggle() {
        if (!sidebar || !sidebarFloatToggle) return;
        const isCollapsed = sidebar.classList.contains('collapsed');
        const isMobile = window.innerWidth <= 992;
        sidebarFloatToggle.classList.toggle('visible', isCollapsed && !isMobile);
    }
    if (lsGet(LS_KEYS.sidebarCollapsed, 'false') === 'true' && window.innerWidth > 992 && sidebar) sidebar.classList.add('collapsed');
    updateSidebarFloatToggle();
    const sidebarToggle = $('sidebarToggle');
    if (sidebarToggle) sidebarToggle.addEventListener('click', function() {
        sidebar.classList.add('collapsed'); lsSet(LS_KEYS.sidebarCollapsed, 'true'); updateSidebarFloatToggle();
    });
    if (sidebarFloatToggle) sidebarFloatToggle.addEventListener('click', function() {
        sidebar.classList.remove('collapsed'); lsSet(LS_KEYS.sidebarCollapsed, 'false'); updateSidebarFloatToggle();
    });
    const burgerBtn = $('burgerBtn');
    if (burgerBtn) burgerBtn.addEventListener('click', function() {
        if (sidebar) sidebar.classList.toggle('open');
        if (sidebarOverlay) sidebarOverlay.classList.toggle('open');
    });
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', function() {
        sidebar.classList.remove('open'); sidebarOverlay.classList.remove('open');
    });
    window.addEventListener('resize', updateSidebarFloatToggle);
    function closeMobileSidebar() {
        if (window.innerWidth <= 992 && sidebar) {
            sidebar.classList.remove('open');
            if (sidebarOverlay) sidebarOverlay.classList.remove('open');
        }
    }

    /* ---------- Font / radius / sidebar width ---------- */
    const savedFontSize = lsGet(LS_KEYS.fontSize, '14');
    document.documentElement.style.fontSize = savedFontSize + 'px';
    const fsSlider = $('fontSizeSlider'), fsVal = $('fontSizeVal');
    if (fsSlider) {
        fsSlider.value = savedFontSize;
        if (fsVal) fsVal.textContent = savedFontSize;
        fsSlider.addEventListener('input', function() {
            document.documentElement.style.fontSize = this.value + 'px';
            if (fsVal) fsVal.textContent = this.value;
            lsSet(LS_KEYS.fontSize, this.value);
        });
    }
    const savedRadius = lsGet(LS_KEYS.radius, '16');
    document.documentElement.style.setProperty('--radius-card', savedRadius + 'px');
    const rSlider = $('radiusSlider'), rVal = $('radiusVal');
    if (rSlider) {
        rSlider.value = savedRadius;
        if (rVal) rVal.textContent = savedRadius;
        rSlider.addEventListener('input', function() {
            document.documentElement.style.setProperty('--radius-card', this.value + 'px');
            if (rVal) rVal.textContent = this.value;
            lsSet(LS_KEYS.radius, this.value);
        });
    }
    const savedSidebarWidth = lsGet(LS_KEYS.sidebarWidth, '260');
    document.documentElement.style.setProperty('--sidebar-width', savedSidebarWidth + 'px');
    const swSlider = $('sidebarWidthSlider'), swVal = $('sidebarWidthVal');
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
    const savedCols = lsGet(LS_KEYS.cols, '2');
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
            const cols = this.getAttribute('data-cols');
            applyColumns(cols);
            document.querySelectorAll('.col-btn[data-cols]').forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            lsSet(LS_KEYS.cols, cols);
        });
    });

    /* ---------- Active category from localStorage ---------- */
    const savedCategory = lsGet(LS_KEYS.activeCategory, 'all');
    let categoryFound = false;
    document.querySelectorAll('.cat-btn').forEach(function(btn) {
        if (btn.getAttribute('data-filter') === savedCategory) categoryFound = true;
    });
    const effectiveCategory = categoryFound ? savedCategory : 'all';
    document.querySelectorAll('.cat-btn').forEach(function(btn) {
        btn.classList.toggle('active', btn.getAttribute('data-filter') === effectiveCategory);
    });
    if (!categoryFound) lsSet(LS_KEYS.activeCategory, 'all');

    /* ---------- Favorites ---------- */
    if (filterFavBtn) {
        const savedShowFav = lsGet(LS_KEYS.showFavorites, 'false') === 'true';
        if (savedShowFav) {
            filterFavBtn.classList.add('active');
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
        }
        filterFavBtn.addEventListener('click', function() {
            this.classList.toggle('active');
            const isActive = this.classList.contains('active');
            lsSet(LS_KEYS.showFavorites, isActive ? 'true' : 'false');
            if (isActive) document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            else {
                const activeCat = lsGet(LS_KEYS.activeCategory, 'all');
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
    const savedSearch = lsGet(LS_KEYS.searchQuery, '');
    if (savedSearch && searchInput) searchInput.value = savedSearch;
    let _lastSearchWasEmpty = !savedSearch || savedSearch.trim() === '';
    let searchDebounceTimer = null;
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            clearTimeout(searchDebounceTimer);
            const val = this.value;
            searchDebounceTimer = setTimeout(function() {
                lsSet(LS_KEYS.searchQuery, val);
                const isEmpty = (val.trim() === '');
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
                const history = lsGetJSON(LS_KEYS.searchHistory, []);
                const q = this.value.trim();
                const filtered = history.filter(function(x) { return x !== q; });
                filtered.unshift(q);
                lsSetJSON(LS_KEYS.searchHistory, filtered.slice(0, 10));
            }
        });
    }
    function showSearchHistory() {
        const history = lsGetJSON(LS_KEYS.searchHistory, []);
        const histEl = $('searchHistory'), listEl = $('searchHistoryList');
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
    function hideSearchHistory() { const histEl = $('searchHistory'); if (histEl) histEl.classList.remove('show'); }
    const clearSearchHistoryBtn = $('clearSearchHistory');
    if (clearSearchHistoryBtn) clearSearchHistoryBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        lsSetJSON(LS_KEYS.searchHistory, []);
        hideSearchHistory();
    });

    /* ---------- Collapsed cards ---------- */
    const collapsedCards = lsGetJSON(LS_KEYS.collapsedCards, []);
    document.querySelectorAll('.card').forEach(function(card) {
        const groupName = card.getAttribute('data-group');
        if (collapsedCards.indexOf(groupName) !== -1) card.classList.add('collapsed');
    });
    document.querySelectorAll('.card-header').forEach(function(header) {
        header.addEventListener('click', function(e) {
            if (e.target.closest('.rename-group-btn')) return;
            if (e.target.closest('.card-sort-btn')) return;
            if (e.target.closest('.bulk-checkbox-card')) return;
            if (e.target.closest('.card-icon')) return;
            const card = this.closest('.card'); if (!card) return;
            card.classList.toggle('collapsed');
            const collapsed = [];
            document.querySelectorAll('.card.collapsed').forEach(function(c) { collapsed.push(c.getAttribute('data-group')); });
            lsSetJSON(LS_KEYS.collapsedCards, collapsed);
        });
    });

    const collapseAllBtn = $('collapseAllBtn');
    if (collapseAllBtn) {
        let allCollapsed = lsGet(LS_KEYS.allCollapsed, 'false') === 'true';
        function applyAllCollapsed(state) {
            document.querySelectorAll('.card').forEach(function(c) {
                if (state) c.classList.add('collapsed'); else c.classList.remove('collapsed');
            });
            const collapsed = [];
            if (state) document.querySelectorAll('.card').forEach(function(c) { collapsed.push(c.getAttribute('data-group')); });
            lsSetJSON(LS_KEYS.collapsedCards, collapsed);
            collapseAllBtn.title = state ? 'Развернуть все' : 'Свернуть все';
        }
        collapseAllBtn.addEventListener('click', function() {
            allCollapsed = !allCollapsed;
            lsSet(LS_KEYS.allCollapsed, allCollapsed ? 'true' : 'false');
            applyAllCollapsed(allCollapsed);
        });
    }

    /* ---------- Sort cards ---------- */
    const savedSortField = lsGet(LS_KEYS.sortField, '');
    const savedSortAsc = lsGet(LS_KEYS.sortAsc, 'true') === 'true';
    if (savedSortField === 'manual') {
        updateSortButtonsUI('manual', true); enableManualCardSort(true);
    } else if (savedSortField) {
        applySort(savedSortField, savedSortAsc);
        updateSortButtonsUI(savedSortField, savedSortAsc);
    }
    document.querySelectorAll('.sort-btn[data-sort]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const field = this.getAttribute('data-sort'); if (!field) return;
            if (field === 'manual') {
                lsSet(LS_KEYS.sortField, 'manual');
                updateSortButtonsUI('manual', true); enableManualCardSort(true);
                showNotification('🔀 Ручной режим включён', 'success');
                return;
            }
            enableManualCardSort(false);
            const currentField = lsGet(LS_KEYS.sortField, '');
            const currentAsc = lsGet(LS_KEYS.sortAsc, 'true') === 'true';
            const newAsc = (currentField === field) ? !currentAsc : true;
            lsSet(LS_KEYS.sortField, field);
            lsSet(LS_KEYS.sortAsc, newAsc ? 'true' : 'false');
            applySort(field, newAsc);
            updateSortButtonsUI(field, newAsc);
        });
    });
    function updateSortButtonsUI(field, asc) {
        document.querySelectorAll('.sort-btn[data-sort]').forEach(function(btn) {
            btn.classList.remove('active');
            const arrow = btn.querySelector('.sort-arrow');
            if (arrow) arrow.textContent = '';
        });
        if (field) {
            const activeBtn = document.querySelector('.sort-btn[data-sort="' + field + '"]');
            if (activeBtn) {
                activeBtn.classList.add('active');
                const arrow = activeBtn.querySelector('.sort-arrow');
                if (arrow && field !== 'manual') arrow.textContent = asc ? '▲' : '▼';
            }
        }
    }
	
	function _firstCardCat(card) {
        try {
            const arr = JSON.parse(card.getAttribute('data-categories') || '[]');
            if (Array.isArray(arr) && arr.length) return String(arr[0]).toLowerCase();
        } catch (e) {}
        return '';
    }
	
    function applySort(field, asc) {
        if (!field || field === 'manual' || !cardsGrid) return;
        const cards = Array.from(cardsGrid.querySelectorAll('.card'));
        if (!cards.length) return;
        cards.sort(function(a, b) {
            let va, vb;
            if (field === 'name') {
                va = (a.getAttribute('data-group') || '').toLowerCase();
                vb = (b.getAttribute('data-group') || '').toLowerCase();
			} else if (field === 'category') {
                va = _firstCardCat(a);
                vb = _firstCardCat(b);
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

    /* ---------- Highlight ---------- */
    function highlightSearch(query) {
        const q = (query || '').trim();
        document.querySelectorAll('[data-original]').forEach(function(el) {
            const orig = el.getAttribute('data-original');
            if (orig !== null) el.innerHTML = escapeHtml(orig);
        });
        if (!q) return;
        const cleaned = q.replace(/\b(cat|tag|fav|updated|status):\S+/gi, '').trim();
        if (!cleaned) return;
        const qLower = cleaned.toLowerCase();
        document.querySelectorAll('.card-title[data-original], .desc[data-original]').forEach(function(el) {
            const card = el.closest('.card');
            if (card && card.style.display === 'none') return;
            const orig = el.getAttribute('data-original') || '';
            const idx = orig.toLowerCase().indexOf(qLower);
            if (idx === -1) return;
            const before = orig.slice(0, idx);
            const match = orig.slice(idx, idx + cleaned.length);
            const after = orig.slice(idx + cleaned.length);
            el.innerHTML = escapeHtml(before) + '<mark>' + escapeHtml(match) + '</mark>' + escapeHtml(after);
        });
    }

    /* ---------- Parse search / apply filters ---------- */
    function parseSearchQuery(raw) {
        const result = { text: '', categories: [], tags: [], favorite: null, updatedAfter: null, updatedBefore: null, status: [] };
        if (!raw) return result;
        const tokens = raw.match(/(?:[^\s"]+|"[^"]*")+/g) || [];
        const textParts = [];
        tokens.forEach(function(tok) {
            const m = tok.match(/^(cat|tag|fav|updated|status):(.*)$/i);
            if (!m) { textParts.push(tok.replace(/^"|"$/g, '')); return; }
            const key = m[1].toLowerCase();
            let value = m[2].replace(/^"|"$/g, '');
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
        const rawQuery = searchInput ? searchInput.value : '';
        const q = parseSearchQuery(rawQuery);
        const activeCatBtn = document.querySelector('.cat-btn.active');
        const activeCat = activeCatBtn ? activeCatBtn.getAttribute('data-filter') : 'all';
        const showFav = filterFavBtn ? filterFavBtn.classList.contains('active') : false;
        const activeTags = lsGetJSON(LS_KEYS.activeTags, []);
        const statusCache = window.__statusCache || {};
        const activeCatLower = activeCat.toLowerCase();
        const cardState = new Map();
        document.querySelectorAll('.card').forEach(function(card) {
            cardState.set(card, { anyVisible: false, anyFav: false });
        });
        for (let i = 0; i < _filterIndex.length; i++) {
            const item = _filterIndex[i];
            const li = item.el, card = item.card;
            let cardCatOK = true;
            if (activeCat !== '__none__' && activeCat !== 'all') {
                if (item.cardCats.indexOf(activeCatLower) === -1) cardCatOK = false;
            }
            if (cardCatOK && q.categories.length) {
                cardCatOK = q.categories.some(function(c) { return item.cardCats.indexOf(String(c).toLowerCase()) !== -1; });
            }
            let visible = true;
            if (visible && q.text) {
                const base = item.group + ' ' + item.link + ' ' + item.fullLink + ' ' + item.desc + ' ' + item.cat;
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
                const st = (statusCache[item.id] && statusCache[item.id].status) || 'unknown';
                if (q.status.indexOf(st) === -1) visible = false;
            }
            if (visible && cardCatOK) {
                li.classList.remove('hidden');
                const st = cardState.get(card);
                if (st) { st.anyVisible = true; if (item.fav) st.anyFav = true; }
            } else li.classList.add('hidden');
        }
        let anyVisible = false, anyFavVisible = false;
        cardState.forEach(function(state, card) {
            if (state.anyVisible) {
                card.style.display = ''; anyVisible = true;
                if (state.anyFav) anyFavVisible = true;
            } else card.style.display = 'none';
        });
        const noFav = cardsGrid ? cardsGrid.querySelector('.no-fav-msg') : null;
        if (showFav && !anyFavVisible && anyVisible) {
            if (!noFav && cardsGrid) {
                const msg = document.createElement('div');
                msg.className = 'no-data no-fav-msg';
                msg.textContent = '⭐ Нет избранных записей';
                cardsGrid.appendChild(msg);
            }
        } else if (noFav) noFav.remove();
        const noResults = cardsGrid ? cardsGrid.querySelector('.no-results-msg') : null;
        if (!anyVisible && !showFav) {
            if (!noResults && cardsGrid) {
                const msg = document.createElement('div');
                msg.className = 'no-data no-results-msg';
                msg.textContent = '🔍 Ничего не найдено';
                cardsGrid.appendChild(msg);
            }
        } else if (noResults) noResults.remove();
    }
    // Ранний доступ для bindCriticalUI
    window.__applyFilters = applyFilters;
    window.__state = window.__state || {};
    window.__state.applyFilters = applyFilters;
    window.__state.resetCategoryToAll = resetCategoryToAll;
    window.__state.closeMobileSidebar = closeMobileSidebar;
    window.__state.prepareAddModal = prepareAddModal;
    window.__prepareAddModal = prepareAddModal;

    applyFilters();
    if (savedSearch) highlightSearch(savedSearch);

    /* ---------- Favorite / delete ---------- */
    document.querySelectorAll('.favorite-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const id = this.getAttribute('data-id'); if (!id) return;
            api('/toggle_favorite/' + id, { method: 'POST' })
                .then(function(r) { if (r.ok) location.reload(); else alert('Ошибка'); })
                .catch(function() { alert('Ошибка сети'); });
        });
    });

    document.querySelectorAll('.delete-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const id = this.getAttribute('data-id');
            const linkItem = this.closest('.link-item');
            if (!id || !linkItem) return;
            const linkText = linkItem.querySelector('.link-display') ? linkItem.querySelector('.link-display').textContent : '';
            const groupName = linkItem.closest('.card') ? linkItem.closest('.card').getAttribute('data-group') : '';
            const messageHtml = groupName
                ? 'Удалить запись <span class="confirm-highlight">' + escapeHtml(linkText) + '</span> из группы <span class="confirm-highlight">' + escapeHtml(groupName) + '</span>?'
                : 'Удалить запись <span class="confirm-highlight">' + escapeHtml(linkText) + '</span>?';
            showConfirm('🗑 Удаление записи', messageHtml, '🗑 Удалить', function() {
                apiWithLockGuard('/delete/' + id, { method: 'POST' })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (!data.success) { alert(data.error || 'Ошибка'); return; }
                        linkItem.style.opacity = '0.35';
                        linkItem.style.pointerEvents = 'none';
                        const undoId = id, undoItem = linkItem;
                        let undone = false;
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
                                const card = undoItem.closest('.card');
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
    const openAddModalBtn = $('openAddModal');
    if (openAddModalBtn) openAddModalBtn.addEventListener('click', function() {
        const m = $('addModal'); if (m) m.classList.add('active');
        prepareAddModal();
        setTimeout(function() { const n = $('name'); if (n) n.focus(); }, 100);
    });
    const closeAddModalBtn = $('closeAddModalBtn');
    if (closeAddModalBtn) closeAddModalBtn.addEventListener('click', function() { const m = $('addModal'); if (m) m.classList.remove('active'); });
    const addModal = $('addModal');
    if (addModal) addModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    const closeEditModalBtn = $('closeEditModalBtn');
    if (closeEditModalBtn) closeEditModalBtn.addEventListener('click', function() { const m = $('editModal'); if (m) m.classList.remove('active'); });
    const editModal = $('editModal');
    if (editModal) editModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    const confirmCancelBtn = $('confirmCancelBtn');
    if (confirmCancelBtn) confirmCancelBtn.addEventListener('click', function() {
        const m = $('confirmModal'); if (m) m.classList.remove('active');
        _confirmHandler = null;
    });
    const confirmOkBtn = $('confirmOkBtn');
    if (confirmOkBtn) confirmOkBtn.addEventListener('click', function() {
        const cb = _confirmHandler;
        const m = $('confirmModal'); if (m) m.classList.remove('active');
        _confirmHandler = null;
        if (cb) cb();
    });
    const confirmModal = $('confirmModal');
    if (confirmModal) confirmModal.addEventListener('click', function(e) {
        if (e.target === this) { this.classList.remove('active'); _confirmHandler = null; }
    });
    const undoToastBtn = $('undoToastBtn');
    if (undoToastBtn) undoToastBtn.addEventListener('click', function() {
        if (_undoTimer) clearTimeout(_undoTimer);
        const cb = _undoCallback;
        _undoCallback = null; _undoActionActive = false;
        const t = $('undoToast'); if (t) t.classList.remove('show');
        if (cb) cb();
    });

    /* ---------- Card sort dropdown ---------- */
    document.querySelectorAll('.card-sort-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const group = this.getAttribute('data-group'); if (!group) return;
            if (_activeSortBtn === this && _activeSortDropdown) { hideSortDropdown(); return; }
            showSortDropdown(this, group);
        });
    });
    document.addEventListener('click', function(e) {
        if (_activeSortDropdown && !e.target.closest('.card-sort-dropdown') && !e.target.closest('.card-sort-btn')) hideSortDropdown();
    });

    /* ---------- Page title reset ---------- */
    (function setupPageTitleReset() {
        const pageTitle = document.querySelector('.page-title');
        if (!pageTitle) return;
        pageTitle.addEventListener('click', function() {
            document.querySelectorAll('.cat-btn').forEach(function(b) { b.classList.remove('active'); });
            const allBtn = document.querySelector('.cat-btn[data-filter="all"]');
            if (allBtn) allBtn.classList.add('active');
            lsSet(LS_KEYS.activeCategory, 'all');
            if (filterFavBtn) filterFavBtn.classList.remove('active');
            lsSet(LS_KEYS.showFavorites, 'false');
            lsSetJSON(LS_KEYS.activeTags, []);
            if (typeof buildTagCloud === 'function') buildTagCloud();
            if (searchInput) searchInput.value = '';
            lsSet(LS_KEYS.searchQuery, '');
            _lastSearchWasEmpty = true;
            if (typeof highlightSearch === 'function') highlightSearch('');
            applyFilters();
            try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (e) { window.scrollTo(0, 0); }
            showNotification('✅ Фильтры сброшены', 'success');
        });
    })();

    /* ---------- Expose state ---------- */
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
   ЛОКАЛЬНАЯ ПОДСВЕТКА КОДА (замена highlight.js)
   Работает офлайн. Классы .hljs-* — те же, что уже есть в CSS.
   ============================================================ */
const reestrHL_KEYWORDS = {
    python: 'and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield|True|False|None|self',
    sql: 'SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|VIEW|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|ORDER|BY|HAVING|LIMIT|OFFSET|AS|AND|OR|NOT|NULL|IS|IN|LIKE|BETWEEN|EXISTS|UNION|ALL|DISTINCT|CASE|WHEN|THEN|ELSE|END|VALUES|INTO|SET|PRIMARY|KEY|FOREIGN|REFERENCES|DEFAULT|CASCADE|CONSTRAINT|UNIQUE|CHECK|WITH|ASC|DESC|COUNT|SUM|AVG|MIN|MAX',
    javascript: 'var|let|const|function|return|if|else|for|while|do|switch|case|break|continue|new|this|typeof|instanceof|in|of|null|undefined|true|false|class|extends|super|import|export|from|as|default|async|await|try|catch|finally|throw|yield|delete|void',
    json: 'true|false|null',
    bash: 'if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|echo|cd|ls|pwd|cat|grep|awk|sed|export|source|alias|unalias|set|unset|read|local|readonly|declare|typeset|shift|test|printf',
    powershell: 'if|else|elseif|switch|foreach|while|do|function|return|param|begin|process|end|try|catch|finally|throw|break|continue|Write-Host|Write-Output|Get-Item|Set-Item|Get-ChildItem|Where-Object|ForEach-Object|Select-Object',
    yaml: 'true|false|null|yes|no|on|off',
    ini: 'true|false|yes|no',
    css: 'important|media|import|charset|keyframes|supports|and|or|not|only|from|to',
    html: '',
    xml: '',
    plaintext: 'if|else|for|while|function|return|class|def|import|from|var|let|const|true|false|null|None|True|False'
};

const reestrHL_COMMENT = {
    python: /#[^\n]*/g,
    bash: /#[^\n]*/g,
    powershell: /#[^\n]*/g,
    yaml: /#[^\n]*/g,
    ini: /[;#][^\n]*/g,
    javascript: /\/\/[^\n]*|\/\*[\s\S]*?\*\//g,
    sql: /--[^\n]*|\/\*[\s\S]*?\*\//g,
    css: /\/\*[\s\S]*?\*\//g,
    json: null,
    html: null,
    xml: null,
    plaintext: /#[^\n]*|\/\/[^\n]*/g
};

function reestrHighlightCode(source, lang) {
    if (!source) return '';
    lang = (lang || 'plaintext').toLowerCase();

    let html = source
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    const tokens = [];
    let tokenIdx = 0;
    function stash(cls, text) {
        const ch = String.fromCharCode(0xE000 + tokenIdx++);
        tokens.push('<span class="hljs-' + cls + '">' + text + '</span>');
        return ch;
    }

    const cmtRe = reestrHL_COMMENT[lang];
    if (cmtRe) {
        html = html.replace(cmtRe, function(m) { return stash('comment', m); });
    }

    if (lang === 'python') {
        html = html.replace(/("""[\s\S]*?"""|'''[\s\S]*?''')/g, function(m) { return stash('string', m); });
    }
    html = html.replace(/"(?:[^"\\]|\\.)*"/g, function(m) { return stash('string', m); });
    html = html.replace(/'(?:[^'\\]|\\.)*'/g, function(m) { return stash('string', m); });
    if (lang === 'javascript') {
        html = html.replace(/`(?:[^`\\]|\\.)*`/g, function(m) { return stash('string', m); });
    }

    html = html.replace(/\b(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b/g, function(m) { return stash('number', m); });

    const kw = reestrHL_KEYWORDS[lang];
    if (kw) {
        const re = new RegExp('\\b(' + kw + ')\\b', 'g');
        html = html.replace(re, function(m) { return stash('keyword', m); });
    }

    html = html.replace(/\b([A-Za-z_][A-Za-z0-9_]*)(?=\s*\()/g, function(m) { return stash('function', m); });

    html = html.replace(/[\uE000-\uF8FF]/g, function(ch) {
        const i = ch.charCodeAt(0) - 0xE000;
        return tokens[i] !== undefined ? tokens[i] : ch;
    });

    return html;
}

function reestrHighlightElement(el) {
    if (!el || el.dataset.reestrHighlighted === '1') return;
    const cls = el.className || '';
    const m = cls.match(/language-([a-z0-9+#_-]+)/i);
    const lang = m ? m[1].toLowerCase() : 'plaintext';
    const src = el.textContent || '';
    el.innerHTML = reestrHighlightCode(src, lang);
    el.dataset.reestrHighlighted = '1';
}

function reestrHighlightAll(root) {
    const ctx = root || document;
    ctx.querySelectorAll('.link-code-body code').forEach(reestrHighlightElement);
}

/* ============================================================
   INIT EXTENDED
   ============================================================ */
function initExtended() {
    const cardsGrid = $('cardsGrid');
    const searchInput = $('searchInput');

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

	function renderPluginsList(info) {
        const list = $('pluginsList'); if (!list) return;
        const loaded = (info && info.loaded) || [];
        const errors = (info && info.errors) || [];
        if (!loaded.length && !errors.length) {
            list.innerHTML = '<div class="tools-empty">Плагины не установлены</div>';
            return;
        }
        let html = '';
        loaded.forEach(function(p) {
            const enabled = p.enabled !== false;
            const dotColor = enabled ? '#2ecc71' : '#7a9ab5';
            const title = (p.description || p.name) + ' — v' + (p.version || '—');
            html += '<div class="plugin-mini" title="' + escapeHtml(title) + '">'
                + '<span class="plugin-mini-dot" style="background:' + dotColor + '; box-shadow: 0 0 6px ' + dotColor + ';"></span>'
                + '<span class="plugin-mini-name">' + escapeHtml(p.name) + '</span>'
                + '<span class="plugin-mini-ver">v' + escapeHtml(p.version || '—') + '</span>'
                + '</div>';
        });
        errors.forEach(function(e) {
            html += '<div class="plugin-mini" style="border-color:#e74c3c;">'
                + '<span class="plugin-mini-dot" style="background:#e74c3c; box-shadow: 0 0 6px #e74c3c;"></span>'
                + '<span class="plugin-mini-name" title="' + escapeHtml(e.error) + '">✗ ' + escapeHtml(e.file) + '</span>'
                + '</div>';
        });
        list.innerHTML = html;
    }

	/* ---------- Подсветка кода (локальная) ---------- */
    (function initCodeHighlight() {
        const settings = DATA.settings || {};
        if (settings.code_highlight === false) return;
        try { reestrHighlightAll(); } catch (e) { console.error('[highlight]', e); }
    })();

    /* ---------- Кнопки «развернуть/свернуть» и «копировать» ---------- */
    document.querySelectorAll('.link-code-toggle').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const wrap = this.closest('.link-code');
            if (!wrap) return;
            const collapsed = wrap.classList.toggle('code-collapsed');
            this.textContent = collapsed ? '▼ Развернуть' : '▲ Свернуть';
        });
    });

    document.querySelectorAll('.link-code-copy').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const wrap = this.closest('.link-code');
            if (!wrap) return;
            const codeEl = wrap.querySelector('.link-code-body code');
            if (!codeEl) return;
            const text = codeEl.textContent || '';
            copyTextToClipboard(text).then(function() {
                showNotification('📋 Код скопирован', 'success');
            }).catch(function() {
                showNotification('❌ Не удалось скопировать', 'error');
            });
        });
    });

    /* ---------- Редактор кода в модалках ---------- */
    function setupCodeEditor(toggleBtnId, bodyId) {
        const btn = $(toggleBtnId);
        const body = $(bodyId);
        if (!btn || !body) return;
        btn.addEventListener('click', function() {
            const opened = body.classList.toggle('open');
            this.textContent = opened ? '▲ Свернуть' : '▼ Раскрыть';
        });
    }
    setupCodeEditor('codeToggleBtnAdd', 'codeEditorBodyAdd');
    setupCodeEditor('codeToggleBtnEdit', 'codeEditorBodyEdit');

    /* ---------- Модалка «Источник данных» ---------- */
    (function setupStorageModal() {
        const modal = $('storageSettingsModal');
        const openBtn = $('openStorageSettingsBtn');
        if (!modal) return;

        function refreshInfo() {
            const box = $('storageInfoBox');
            if (box) box.innerHTML = '<div style="color:var(--meta-color); text-align:center;">Загрузка...</div>';
            apiFetch('/api/storage/info').then(function(r) { return r.json(); }).then(function(info) {
                if (!box) return;
                const rows = [];
                rows.push('<div><b>Backend:</b> <code>' + escapeHtml(info.backend) + '</code></div>');
                if (info.backend === 'sqlite') {
                    rows.push('<div><b>SQLite:</b> <code>' + escapeHtml(info.sqlite_file) + '</code> ' +
                              (info.sqlite_exists ? '✅' : '❌') + '</div>');
                    if (info.sqlite_info) {
                        rows.push('<div style="opacity:0.8;">Записей: <b>' +
                                  (info.sqlite_info.count || 0) + '</b>, ' +
                                  'WAL: ' + (info.sqlite_info.wal_mode ? 'да' : 'нет') + ', ' +
                                  'размер: ' + (info.sqlite_info.size_bytes || 0) + ' Б</div>');
                        if (info.sqlite_info.imported_from) {
                            rows.push('<div style="opacity:0.6; font-size:0.78rem;">Импортировано из: ' +
                                      escapeHtml(info.sqlite_info.imported_from) + '</div>');
                        }
                    }
                }
                rows.push('<div><b>XLSX (зеркало):</b> <code>' + escapeHtml(info.excel_file) + '</code> ' +
                          (info.excel_exists ? '✅' : '❌') +
                          (info.excel_locked ? ' 🔒 <span style="color:#f1c40f;">открыт в Excel</span>' : '') +
                          (info.is_network_path ? ' <span style="color:var(--accent);">🌐 сеть</span>' : '') +
                          '</div>');
                box.innerHTML = rows.join('');
            }).catch(function() {
                if (box) box.innerHTML = '<div style="color:#e74c3c;">Ошибка загрузки</div>';
            });
        }

        function fillForm() {
            apiFetch('/get_settings').then(function(r) { return r.json(); }).then(function(s) {
                const be = $('dataBackendSelect'); if (be) be.value = s.data_backend || 'xlsx';
                const ds = $('dataSourceInput'); if (ds) ds.value = s.data_source || '';
                const sp = $('sqlitePathInput'); if (sp) sp.value = s.sqlite_path || '';
                const cc = $('codeCollapsedInput'); if (cc) cc.value = s.code_collapsed_lines || 5;
                const ch = $('codeHighlightToggle'); if (ch) ch.checked = s.code_highlight !== false;
            });
        }

		if (openBtn) openBtn.addEventListener('click', function() {
            refreshInfo(); fillForm();
            modal.style.zIndex = '1300';
            modal.classList.add('active');
        });

        const saveBtn = $('saveStorageSettingsBtn');
        if (saveBtn) saveBtn.addEventListener('click', function() {
            const payload = {
                data_backend: ($('dataBackendSelect') || {}).value || 'xlsx',
                data_source: (($('dataSourceInput') || {}).value || '').trim(),
                sqlite_path: (($('sqlitePathInput') || {}).value || '').trim(),
                code_collapsed_lines: parseInt((($('codeCollapsedInput') || {}).value) || 5),
                code_highlight: ($('codeHighlightToggle') || {}).checked !== false,
            };
            api('/save_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(function(r) { return r.json(); }).then(function(d) {
                if (d.success) {
                    showNotification('✅ Сохранено. ' +
                        (d.needs_restart ? '⚠️ Перезапустите сервер для смены бэкенда.' : 'Обновите страницу (Ctrl+F5).'),
                        'success');
                    refreshInfo();
                } else {
                    showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
        });

        const m1 = $('migrateXlsxToSqliteBtn');
        if (m1) m1.addEventListener('click', function() {
            if (!confirm('Импортировать данные из XLSX в SQLite?\nТекущие записи в БД будут ПЕРЕЗАПИСАНЫ.')) return;
            apiFetch('/api/storage/migrate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
                body: JSON.stringify({ direction: 'xlsx_to_sqlite' })
            }).then(function(r) { return r.json(); }).then(function(d) {
                if (d.success) {
                    showNotification('✅ Импортировано: ' + d.rows + ' строк', 'success');
                    refreshInfo();
                    setTimeout(function() { location.reload(); }, 1200);
                } else {
                    showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
        });

        const m2 = $('migrateSqliteToXlsxBtn');
        if (m2) m2.addEventListener('click', function() {
            if (!confirm('Экспортировать данные из SQLite в XLSX? Файл будет перезаписан.')) return;
            apiFetch('/api/storage/migrate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
                body: JSON.stringify({ direction: 'sqlite_to_xlsx' })
            }).then(function(r) { return r.json(); }).then(function(d) {
                if (d.success) {
                    showNotification('✅ Экспортировано в ' + d.to, 'success');
                    refreshInfo();
                } else {
                    showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
                }
            }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
        });

        modal.addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('active');
        });
    })();

    /* ---------- Tags / categories click in meta ---------- */
    document.querySelectorAll('.link-meta .tag-chip[data-tag]').forEach(function(chip) {
        chip.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const tag = this.getAttribute('data-tag'); if (!tag) return;
            let act = lsGetJSON(LS_KEYS.activeTags, []);
            const idx = act.indexOf(tag);
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
            const cat = this.getAttribute('data-category'); if (!cat) return;
            const btn = Array.from(document.querySelectorAll('.cat-btn')).find(function(b) {
                return b.getAttribute('data-filter') === cat;
            });
            if (btn) btn.click();
            else showNotification('❌ Категория не найдена', 'error');
        });
    });

    /* ---------- History click ---------- */
    document.querySelectorAll('.meta-created[data-id]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const rid = this.getAttribute('data-id');
            const logsModal = document.getElementById('pluginLogsModal');
            if (logsModal && typeof openPluginModal === 'function') {
                openPluginModal('pluginLogsModal');
                const list = document.getElementById('pluginLogsList');
                if (list && rid) {
                    fetch('/get_record_history/' + rid)
                        .then(function(r) { return r.json(); })
                        .then(function(logs) {
                            if (!logs.length) {
                                list.innerHTML = '<p style="text-align:center;padding:20px 0;">Нет записей.</p>';
                                return;
                            }
                            const LABELS = {
                                add: '➕ Добавление', edit: '✏️ Изменение', soft_delete: '🗑 Удаление',
                                restore: '↩ Восстановление', restore_from_trash: '↩ Восстановление',
                                rename_category: '✏️ Категория', rename_group: '✏️ Группа',
                                delete_category: '🗑 Категория', sort_group: '⇅ Сортировка',
                                update_group_icon: '🎨 Иконка', edit_desc: '📝 Описание',
                                edit_category: '🏷️ Категория', move_to_group: '📁 Перемещение'
                            };
                            list.innerHTML = logs.map(function(l) {
                                const label = LABELS[l.action] || l.action;
                                let desc = l.name || '';
                                if (l.details && typeof l.details === 'object') {
                                    const parts = [];
                                    if (l.details.count !== undefined) parts.push('×' + l.details.count);
                                    if (l.details.category) parts.push('→ ' + l.details.category);
                                    if (parts.length) desc += (desc ? ' ' : '') + parts.join(' ');
                                }
                                return '<div class="log-item"><span class="log-ts">' + escapeHtml(l.ts) + '</span>'
                                    + '<span class="log-action">' + escapeHtml(label) + '</span>'
                                    + '<span class="log-desc">' + escapeHtml(desc) + '</span></div>';
                            }).join('');
                        }).catch(function() {});
                }
            } else {
                showNotification('ℹ️ Плагин «Журнал» не установлен', 'error');
            }
        });
    });

    /* ---------- Categories modal ---------- */
    const categoriesModal = $('categoriesModal');
    const manageCategoriesBtn = $('manageCategoriesBtn');
    if (manageCategoriesBtn && categoriesModal) {
        manageCategoriesBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            loadCategories();
            categoriesModal.classList.add('active');
            if (window.__state && window.__state.closeMobileSidebar) window.__state.closeMobileSidebar();
        });
    }
    const closeCategoriesModalBtn = $('closeCategoriesModalBtn');
    if (closeCategoriesModalBtn && categoriesModal) closeCategoriesModalBtn.addEventListener('click', function() { categoriesModal.classList.remove('active'); });
    if (categoriesModal) categoriesModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });

    let categoryColorsLocal = {};
    for (const k in (DATA.category_colors || {})) categoryColorsLocal[k] = DATA.category_colors[k];
    let categoryManualOrderLocal = (DATA.category_manual_order || []).slice();

    window.addEventListener('reestr:category-order-changed', function(e) {
        if (e.detail && Array.isArray(e.detail.order)) {
            categoryManualOrderLocal = e.detail.order.slice();
        }
    });

    const categoryListEl = $('categoryList');
    if (categoryListEl) {
        categoryListEl.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-action]');
            if (!btn || btn.tagName === 'INPUT') return;
            const action = btn.getAttribute('data-action');
            const item = btn.closest('.category-item');
            const cat = item ? item.getAttribute('data-category') : '';
            if (!cat) return;
            if (action === 'up') window.moveCategoryUp(cat);
            else if (action === 'down') window.moveCategoryDown(cat);
            else if (action === 'rename') window.startRename(cat);
            else if (action === 'delete') window.deleteCategory(cat);
            else if (action === 'save-rename') window.saveRename(cat, btn);
        });
        categoryListEl.addEventListener('change', function(e) {
            const inp = e.target.closest('input[type="color"][data-action="color"]');
            if (!inp) return;
            const item = inp.closest('.category-item');
            const cat = item ? item.getAttribute('data-category') : '';
            if (!cat) return;
            window.updateCategoryColor(cat, inp.value);
        });
        categoryListEl.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.target && e.target.matches('input[type="text"]')) {
                e.preventDefault();
                const item = e.target.closest('.category-item');
                const cat = item ? item.getAttribute('data-category') : '';
                const saveBtn = item ? item.querySelector('[data-action="save-rename"]') : null;
                if (cat && saveBtn) window.saveRename(cat, saveBtn);
            }
        });
    }
    function loadCategories() {
        api('/get_categories').then(function(r) { return r.json(); }).then(function(data) {
            const list = $('categoryList'); if (!list) return;
            if (data.length === 0) {
                list.innerHTML = '<p style="color:var(--meta-color); text-align:center;">Нет категорий</p>';
                return;
            }
            const idx = new Map(categoryManualOrderLocal.map(function(n, i) { return [n, i]; }));
            data.sort(function(a, b) {
                const ia = idx.has(a) ? idx.get(a) : 999999;
                const ib = idx.has(b) ? idx.get(b) : 999999;
                if (ia !== ib) return ia - ib;
                return a.localeCompare(b, 'ru');
            });
            let html = '';
            data.forEach(function(cat, i) {
                const color = categoryColorsLocal[cat] || '#f5d76e';
                const isFirst = i === 0, isLast = i === data.length - 1;
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
            const list = $('categoryList');
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
        const modalCats = Array.from(document.querySelectorAll('#categoryList .category-item'))
            .map(function(el) { return el.getAttribute('data-category'); }).filter(Boolean);
        const order = modalCats.slice();
        categoryManualOrderLocal.forEach(function(c) { if (order.indexOf(c) === -1) order.push(c); });
        return order;
    }
    window.moveCategoryUp = function(catName) {
        const order = getFullCategoryOrderFromModal();
        const idx = order.indexOf(catName);
        if (idx <= 0) return;
        const tmp = order[idx - 1]; order[idx - 1] = order[idx]; order[idx] = tmp;
        saveCategoryOrderFromModal(order); loadCategories();
    };
    window.moveCategoryDown = function(catName) {
        const order = getFullCategoryOrderFromModal();
        const idx = order.indexOf(catName);
        if (idx === -1 || idx >= order.length - 1) return;
        const tmp = order[idx + 1]; order[idx + 1] = order[idx]; order[idx] = tmp;
        saveCategoryOrderFromModal(order); loadCategories();
    };
    window.startRename = function(oldName) {
        const item = document.querySelector('.category-item[data-category="' + oldName + '"]');
        if (!item) return;
        const nameSpan = item.querySelector('.cat-name');
        const actions = item.querySelector('.cat-actions');
        const input = document.createElement('input');
        input.type = 'text'; input.value = oldName;
        nameSpan.innerHTML = ''; nameSpan.appendChild(input); input.focus();
        actions.innerHTML = '<button type="button" class="save-btn" data-action="save-rename">💾</button>'
            + '<button type="button" class="cancel-btn" data-action="cancel-rename">✖</button>';
        const cancelBtn = actions.querySelector('[data-action="cancel-rename"]');
        if (cancelBtn) cancelBtn.addEventListener('click', function() { loadCategories(); });
    };
    window.saveRename = function(oldName, btn) {
        const item = btn.closest('.category-item'); if (!item) return;
        const input = item.querySelector('input[type="text"]'); if (!input) return;
        const newName = input.value.trim();
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
        const newName = prompt('Новое название:', oldName);
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
    function setupCategorySelector(selectId, customId, hiddenId) {
        const select = $(selectId), custom = $(customId), hidden = $(hiddenId);
        if (!select || !custom || !hidden) return;
        function update() { hidden.value = (select.value === '__other__') ? custom.value.trim() : select.value; }
        update();
        select.addEventListener('change', function() {
            if (this.value === '__other__') { custom.style.display = 'block'; custom.focus(); }
            else { custom.style.display = 'none'; custom.value = ''; }
            update();
        });
        custom.addEventListener('input', update);
    }
    setupCategorySelector('category_add', 'category_custom', 'category_hidden');
    setupCategorySelector('edit_category', 'edit_category_custom', 'edit_category_hidden');

    const catAddSelect = $('category_add');
    if (catAddSelect) catAddSelect.addEventListener('change', function() {
        const val = this.value === '__other__'
            ? (($('category_custom') && $('category_custom').value.trim()) || '')
            : (this.value || '');
        if (window.__state && window.__state.updateNamesDatalist) window.__state.updateNamesDatalist(val);
    });
    const catAddCustom = $('category_custom');
    if (catAddCustom) catAddCustom.addEventListener('input', function() {
        if (window.__state && window.__state.updateNamesDatalist) window.__state.updateNamesDatalist(this.value.trim() || '');
    });

    /* ---------- Tags input ---------- */
    function setupTagsInput(wrapperId, inputId, hiddenId, suggestionsId) {
        const wrapper = $(wrapperId), input = $(inputId);
        const hidden = $(hiddenId), suggestions = $(suggestionsId);
        if (!wrapper || !input || !hidden) return null;
        let tags = [];
        function render() {
            wrapper.querySelectorAll('.tags-chip').forEach(function(c) { c.remove(); });
            tags.forEach(function(t) {
                const chip = document.createElement('span');
                chip.className = 'tags-chip';
                chip.innerHTML = '#' + escapeHtml(t) + '<span class="remove-tag" data-tag="' + escapeHtml(t) + '">×</span>';
                wrapper.insertBefore(chip, input);
            });
            hidden.value = tags.join(',');
        }
        wrapper.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-tag')) {
                const t = e.target.getAttribute('data-tag');
                tags = tags.filter(function(x) { return x !== t; });
                render();
            } else input.focus();
        });
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault();
                const val = this.value.trim().replace(/^#/, '').replace(/,/g, '');
                if (val && tags.indexOf(val) === -1) { tags.push(val); render(); }
                this.value = ''; hideSuggestions();
            } else if (e.key === 'Backspace' && this.value === '' && tags.length > 0) {
                tags.pop(); render();
            }
        });
        input.addEventListener('input', function() {
            const val = this.value.trim().toLowerCase();
            if (!val || !suggestions) { hideSuggestions(); return; }
            const allTags = Object.keys(allTagsFromServer || {});
            const matches = allTags.filter(function(t) { return t.toLowerCase().indexOf(val) !== -1 && tags.indexOf(t) === -1; }).slice(0, 8);
            if (!matches.length) { hideSuggestions(); return; }
            suggestions.innerHTML = matches.map(function(t) {
                return '<button type="button" data-tag="' + escapeHtml(t) + '">#' + escapeHtml(t) + '</button>';
            }).join('');
            suggestions.querySelectorAll('button').forEach(function(b) {
                b.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    const t = this.getAttribute('data-tag');
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
    const tagsEditCtl = setupTagsInput('tagsEditWrapper', 'tagsEditInput', 'tags_edit', 'tagsEditSuggestions');
    setupTagsInput('tagsAddWrapper', 'tagsAddInput', 'tags_add', 'tagsAddSuggestions');

    /* ---------- Duplicate check ---------- */
    const linkInput = $('link');
    const dupWarn = $('duplicateWarn');
    let dupTimer = null;
    let _dupAbort = null;
    if (linkInput && dupWarn) {
        linkInput.addEventListener('input', function() {
            clearTimeout(dupTimer);
            const val = this.value.trim();
            if (!val || val.length < 5) { dupWarn.style.display = 'none'; return; }
            dupTimer = setTimeout(function() {
                if (_dupAbort) try { _dupAbort.abort(); } catch (e) {}
                _dupAbort = new AbortController();
                apiFetch('/check_duplicate?url=' + encodeURIComponent(val), { signal: _dupAbort.signal })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (data.found && data.matches.length) {
                            const m = data.matches[0];
                            dupWarn.innerHTML = '⚠️ Похожая ссылка: <b>' + escapeHtml(m.name) + '</b>' + (m.category ? ' (' + escapeHtml(m.category) + ')' : '');
                            dupWarn.style.display = 'block';
                        } else dupWarn.style.display = 'none';
                    }).catch(function(err) { if (err && err.name === 'AbortError') return; });
            }, 400);
        });
    }

    /* ---------- Category picker ---------- */
    const categoryPickerModal = $('categoryPickerModal');
    const categoryPickerList = $('categoryPickerList');
    const categoryPickerNewInput = $('categoryPickerNewInput');
    const categoryPickerCreateBtn = $('categoryPickerCreateBtn');
    const categoryPickerCancelBtn = $('categoryPickerCancelBtn');
    const categoryPickerTitle = $('categoryPickerTitle');
    let _categoryPickerState = null;
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
        const cats = [];
        document.querySelectorAll('.cat-btn[data-cat-name]').forEach(function(b) {
            cats.push({
                name: b.getAttribute('data-cat-name'),
                count: parseInt(b.getAttribute('data-cat-count')) || 0,
                color: (window.getComputedStyle(b).getPropertyValue('--cat-color') || '').trim() || ''
            });
        });
        let html = '<button type="button" class="category-picker-item picker-none" data-cat="__none__">'
            + '<span class="picker-dot" style="--cat-color:#888888;"></span>'
            + '<span class="picker-name">— Без категории —</span></button>';
        cats.sort(function(a, b) { return a.name.localeCompare(b.name, 'ru'); });
        cats.forEach(function(c) {
            const isSel = currentCat && c.name === currentCat;
            const dotStyle = c.color ? '--cat-color: ' + c.color + ';' : '';
            html += '<button type="button" class="category-picker-item' + (isSel ? ' selected' : '') + '" data-cat="' + escapeHtml(c.name) + '">'
                + '<span class="picker-dot" style="' + dotStyle + '"></span>'
                + '<span class="picker-name">' + escapeHtml(c.name) + '</span>'
                + (c.count ? '<span class="picker-badge">' + c.count + '</span>' : '') + '</button>';
        });
        categoryPickerList.innerHTML = html;
        categoryPickerList.querySelectorAll('.category-picker-item').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const cat = this.getAttribute('data-cat');
                applyCategoryChange(cat === '__none__' ? '' : cat);
            });
        });
    }
    function applyCategoryChange(category) {
        if (!_categoryPickerState) return;
        const st = _categoryPickerState;
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
        const val = (categoryPickerNewInput ? categoryPickerNewInput.value : '').trim();
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


    /* ---------- Edit modal open ---------- */
    document.querySelectorAll('.edit-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation(); e.preventDefault();
            const id = this.getAttribute('data-id'); if (!id) return;
            api('/get_record/' + id).then(function(r) { return r.json(); }).then(function(data) {
                if (data.error) { alert(data.error); return; }
                $('edit_id').value = data.id;
                $('edit_name').value = data.name_del;
                $('edit_link').value = data.link_del;
                $('edit_desc').value = data.description || '';
                const tags = (data.tags || '').split(',').map(function(t) { return t.trim(); }).filter(Boolean);
                if (tagsEditCtl) tagsEditCtl.setTags(tags);
                const catSelect = $('edit_category');
                const catCustom = $('edit_category_custom');
                const category = data.category || '';
                let found = false;
                for (let i = 0; i < catSelect.options.length; i++) {
                    if (catSelect.options[i].value === category) { catSelect.selectedIndex = i; found = true; break; }
                }
                if (!found) { catSelect.value = '__other__'; catCustom.style.display = 'block'; catCustom.value = category; }
                else { catCustom.style.display = 'none'; catCustom.value = ''; }
                $('edit_category_hidden').value = (catSelect.value === '__other__') ? catCustom.value.trim() : catSelect.value;

                // Код
                const codeEl = $('code_edit');
                const langEl = $('code_lang_edit');
                const codeBody = $('codeEditorBodyEdit');
                const codeBtn = $('codeToggleBtnEdit');
                if (codeEl) codeEl.value = data.code || '';
                if (langEl) langEl.value = data.code_lang || '';
                if (codeBody && data.code) {
                    codeBody.classList.add('open');
                    if (codeBtn) codeBtn.textContent = '▲ Свернуть';
                } else if (codeBody) {
                    codeBody.classList.remove('open');
                    if (codeBtn) codeBtn.textContent = '▼ Раскрыть';
                }

                $('editModal').classList.add('active');
            }).catch(function() { alert('Ошибка'); });
        });
    });

    /* ---------- Smart link click ---------- */
    document.querySelectorAll('.smart-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (this.classList.contains('smart-link-nolink')) {
                e.preventDefault();
                return;
            }
            if (e.ctrlKey || e.metaKey || e.shiftKey || e.button === 1) return;
            const fullLink = this.getAttribute('data-full-link') || this.getAttribute('href') || '';
            if (!fullLink) return;
            const id = this.getAttribute('data-id');
            const isHttp = /^https?:\/\//i.test(fullLink);
            const preview = fullLink.length > 70 ? fullLink.substring(0, 70) + '…' : fullLink;
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

    /* ---------- Edit form ---------- */
    const editForm = $('editForm');
    if (editForm) {
        editForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const id = $('edit_id').value;
            const name = $('edit_name').value.trim();
            const link = $('edit_link').value.trim();
            const desc = $('edit_desc').value.trim();
            const category = $('edit_category_hidden').value.trim();
            const tags = $('tags_edit').value;
            const code = ($('code_edit') || {}).value || '';
            const codeLang = ($('code_lang_edit') || {}).value || '';

            const hasLink = !!link;
            const hasCode = !!code.trim();
            if (!name) { alert('Введите название.'); return; }
            if (!hasLink && !hasCode) {
                alert('Нужна ссылка ИЛИ код.');
                return;
            }
            apiWithLockGuard('/edit/' + id, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name, link: link, desc: desc,
                    category: category, tags: tags,
                    code: code, code_lang: codeLang
                })
            }).then(function(r) { if (r.ok) location.reload(); else alert('Ошибка сохранения'); })
              .catch(function(err) {
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

    /* ---------- Bulk panel ---------- */
    const bulkPanel = $('bulkPanel');
    const bulkCount = $('bulkCount');
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
            const card = this.closest('.card');
            const checked = this.checked;
            card.querySelectorAll('.bulk-checkbox').forEach(function(sub) {
                const id = sub.getAttribute('data-id');
                const li = sub.closest('.link-item');
                if (checked) { _selectedIds.add(id); if (li) li.classList.add('bulk-selected'); }
                else { _selectedIds.delete(id); if (li) li.classList.remove('bulk-selected'); }
            });
            updateBulkPanel();
        });
    });
    document.querySelectorAll('.bulk-checkbox').forEach(function(cb) {
        cb.addEventListener('click', function(e) {
            e.stopPropagation();
            const id = this.getAttribute('data-id');
            const li = this.closest('.link-item');
            if (this.checked) { _selectedIds.add(id); if (li) li.classList.add('bulk-selected'); }
            else { _selectedIds.delete(id); if (li) li.classList.remove('bulk-selected'); }
            updateBulkPanel();
        });
    });
    const bulkClearBtn = $('bulkClearBtn');
    if (bulkClearBtn) bulkClearBtn.addEventListener('click', function() {
        resetBulkSelection();
        updateBulkPanel();
    });
    function bulkCall(url, body) {
        const payload = { ids: Array.from(_selectedIds) };
        for (const k in body) payload[k] = body[k];
        return apiWithLockGuard(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).then(function(r) { return r.json(); });
    }
    const bulkFavoriteBtn = $('bulkFavoriteBtn');
    if (bulkFavoriteBtn) bulkFavoriteBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        bulkCall('/bulk/favorite', { value: 1 }).then(function(d) {
            showNotification('✅ В избранном: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot;
            _lastBulkOp = 'bulk_favorite';
            showBulkUndoToast('Добавлено в избранное: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    const bulkUnfavoriteBtn = $('bulkUnfavoriteBtn');
    if (bulkUnfavoriteBtn) bulkUnfavoriteBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        bulkCall('/bulk/favorite', { value: 0 }).then(function(d) {
            showNotification('✅ Убрано: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot;
            _lastBulkOp = 'bulk_favorite';
            showBulkUndoToast('Убрано из избранного: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    const bulkMoveBtn = $('bulkMoveBtn');
    if (bulkMoveBtn) bulkMoveBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        openCategoryPicker({
            mode: 'bulk', ids: Array.from(_selectedIds),
            title: '🏷️ Переместить ' + _selectedIds.size + ' записей'
        });
    });
    const bulkTagBtn = $('bulkTagBtn');
    if (bulkTagBtn) bulkTagBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        const tag = prompt('Тег для добавления:', '');
        if (!tag || !tag.trim()) return;
        bulkCall('/bulk/tags', { tag: tag.trim(), action: 'add' }).then(function(d) {
            showNotification('✅ Тег добавлен: ' + d.count, 'success');
            _lastBulkSnapshot = d.snapshot;
            _lastBulkOp = 'bulk_tags';
            showBulkUndoToast('Тег добавлен: ' + d.count);
            setTimeout(function() { location.reload(); }, 900);
        }).catch(function(err) {
            if (err && err.message === 'ExcelLock') return;
            showNotification('❌ Ошибка сети', 'error');
        });
    });
    const bulkGroupIconBtn = $('bulkGroupIconBtn');
    if (bulkGroupIconBtn) bulkGroupIconBtn.addEventListener('click', function() {
        const groups = [];
        document.querySelectorAll('.bulk-checkbox-card:checked').forEach(function(cb) {
            const g = cb.getAttribute('data-group');
            if (g && groups.indexOf(g) === -1) groups.push(g);
        });
        if (!groups.length && _selectedIds.size) {
            document.querySelectorAll('.card').forEach(function(card) {
                const g = card.getAttribute('data-group');
                if (!g) return;
                const links = card.querySelectorAll('.link-item');
                for (let i = 0; i < links.length; i++) {
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
    const bulkDeleteBtn = $('bulkDeleteBtn');
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
    const bulkExportBtn = $('bulkExportBtn');
    if (bulkExportBtn) bulkExportBtn.addEventListener('click', function() {
        if (!_selectedIds.size) return;
        const lines = [];
        document.querySelectorAll('.link-item.bulk-selected').forEach(function(li) {
            const card = li.closest('.card');
            const name = card ? card.getAttribute('data-group') : '';
            const sl = li.querySelector('.smart-link');
            const link = sl ? sl.getAttribute('data-full-link') : '';
            const descEl = li.querySelector('.desc');
            const desc = descEl ? descEl.getAttribute('data-original') : '';
            lines.push('- [' + name + '](' + link + ')' + (desc ? ' — ' + desc : ''));
        });
        const text = lines.join('\n');
        copyTextToClipboard(text).then(function() {
            showNotification('✅ Скопировано: ' + lines.length, 'success');
        }).catch(function() { alert('Не удалось скопировать:\n\n' + text); });
    });

    /* ---------- Inline desc edit ---------- */
    document.querySelectorAll('.desc[data-id]').forEach(function(descEl) {
        descEl.addEventListener('dblclick', function(e) {
            e.stopPropagation(); e.preventDefault();
            if (this.classList.contains('desc-editing')) return;
            const id = this.getAttribute('data-id'); if (!id) return;
            const originalText = this.getAttribute('data-original') || '';
            this.classList.add('desc-editing');
            this.textContent = originalText;
            const supportsPlaintextOnly = (function() {
                const el = document.createElement('div');
                el.setAttribute('contenteditable', 'plaintext-only');
                return el.contentEditable === 'plaintext-only';
            })();
            if (supportsPlaintextOnly) {
                this.setAttribute('contenteditable', 'plaintext-only');
            } else {
                this.setAttribute('contenteditable', 'true');
                this.addEventListener('paste', function _stripPaste(ev) {
                    ev.preventDefault();
                    const text = (ev.clipboardData || window.clipboardData)
                        .getData('text/plain');
                    document.execCommand('insertText', false, text);
                });
            }
            this.focus();
            try {
                const range = document.createRange();
                range.selectNodeContents(this); range.collapse(false);
                const sel = window.getSelection();
                sel.removeAllRanges(); sel.addRange(range);
            } catch (err) {}
            let finished = false;
            function finish(save) {
                if (finished) return; finished = true;
                descEl.removeEventListener('keydown', onKey);
                descEl.removeEventListener('blur', onBlur);
                descEl.removeAttribute('contenteditable');
                descEl.classList.remove('desc-editing');
                // снимаем возможный paste-обработчик
                descEl.replaceWith(descEl.cloneNode(true)); // можно, но упрощённо:
                // вместо replaceWith – клонируем событие не нужно, достаточно removeEventListener
                if (!save) { descEl.textContent = originalText; return; }
                const newText = (descEl.textContent || '').trim();
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

    /* ---------- Emoji picker ---------- */
    const EMOJI_CATEGORIES = [
        { name: 'Часто', icon: '⭐', list: ['📌','⭐','🔥','❤️','✅','💡','📁','📂','🗂️','📊','🎯','🏆','💎','🌟','✨','⚡','🚀','🎨','🛠️','🔧'] },
        { name: 'Технологии', icon: '💻', list: ['💻','🖥️','🖨️','⌨️','🖱️','💾','💿','📀','🧮','🔌','🔋','📡','🛰️','☎️','📞','📟','📠','📺','📻','🎥','📷','📹','🎞️','📼','🎬','📽️'] },
        { name: 'Работа', icon: '💼', list: ['💼','📁','📂','🗂️','🗃️','🗄️','📋','📌','📍','📎','🖇️','📏','📐','✂️','🖊️','🖋️','✒️','🖌️','🖍️','📝','✏️','🔍','🔎','🔏','🔐','🔒','🔓','📅','📆','🗓️','📇'] },
        { name: 'Символы', icon: '🔣', list: ['⚙️','🔧','🔨','⚒️','🛠️','⛏️','🔩','⚗️','🧪','🧬','🔬','🔭','📡','💡','🔦','🕯️','🪔','🧯','🛢️','💸','💵','💰','💳','🧾','💹','📈','📉','📊','📋'] },
        { name: 'Природа', icon: '🌿', list: ['🌍','🌎','🌏','🌕','🌖','🌗','🌘','🌑','🌒','🌓','🌔','🌙','⭐','🌟','✨','⚡','☄️','💥','🔥','🌪️','🌈','☀️','🌤️','⛅','🌥️','☁️','🌦️','🌧️','⛈️','🌩️','🌨️','❄️','🌊','💧'] },
        { name: 'Объекты', icon: '📦', list: ['📦','📫','📪','📬','📭','📮','🗳️','✉️','📧','📨','📩','📤','📥','🏠','🏢','🏣','🏤','🏥','🏦','🏨','🏪','🏫','🏬','🏭','🏯','🏰','🗼','🗽','⛪','🕌','🕍','🛕'] },
        { name: 'Дом/Сеть', icon: '🏠', list: ['🏠','🏡','🏘️','🏚️','🔌','💡','🛋️','🛏️','🚪','🚿','🛁','🧴','🧷','🧹','🧺','🧻','🧼','🪒','🧽','🪣','🛒','🛍️','🎁','🎀','🎊','🎉','🌐','📶','🔗','🔀'] },
        { name: 'Развлечения', icon: '🎮', list: ['🎮','🕹️','🎯','🎲','🎰','🎳','🎪','🎭','🎨','🎬','🎤','🎧','🎼','🎵','🎶','🎷','🎸','🎹','🎺','🎻','🥁','🎊','🎉','🎈','🎁','🎀','🎂','🍰','🍕','🍔'] }
    ];
    const emojiModal = $('emojiPickerModal');
    let currentEmojiGroups = [];
    let _emojiPickerMode = 'group';
    function renderEmojiCategories() {
        const container = $('emojiCategories'); if (!container) return;
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
        const grid = $('emojiGrid'); if (!grid) return;
        const cat = EMOJI_CATEGORIES[catIdx]; if (!cat) return;
        grid.innerHTML = cat.list.map(function(e) {
            return '<button type="button" class="emoji-btn" data-emoji="' + e + '">' + e + '</button>';
        }).join('');
        grid.querySelectorAll('.emoji-btn').forEach(function(btn) {
            btn.addEventListener('click', function() { applyEmojiIcon(this.getAttribute('data-emoji')); });
        });
    }
    function applyEmojiIcon(emoji) {
        if (_emojiPickerMode === 'add-form') {
            const iconBtn = $('addIconPickerBtn'), iconHidden = $('add_group_icon');
            if (iconBtn) iconBtn.textContent = emoji;
            if (iconHidden) iconHidden.value = emoji;
            if (emojiModal) emojiModal.classList.remove('active');
            _emojiPickerMode = 'group';
            return;
        }
        if (!currentEmojiGroups.length) return;
        const groups = currentEmojiGroups.slice();
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
                const prev = $('emojiPreview'); if (prev) prev.textContent = emoji;
                showNotification(groups.length === 1 ? '✅ Иконка обновлена' : '✅ Иконка обновлена для ' + groups.length + ' групп', 'success');
                if (emojiModal) emojiModal.classList.remove('active');
                currentEmojiGroups = [];
            } else showNotification('❌ Ошибка обновления', 'error');
        }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
    }
    window.openEmojiPicker = function(groupNames) {
        if (!emojiModal) return;
        _emojiPickerMode = 'group';
        const arr = Array.isArray(groupNames) ? groupNames.filter(Boolean) : [groupNames].filter(Boolean);
        if (!arr.length) return;
        currentEmojiGroups = arr;
        const nameEl = $('emojiGroupName');
        if (nameEl) {
            nameEl.textContent = arr.length === 1 ? arr[0] : arr.length + ' групп: ' + arr.slice(0, 3).join(', ') + (arr.length > 3 ? '…' : '');
        }
        let curIcon = '📌';
        document.querySelectorAll('.card-icon[data-group-name]').forEach(function(el) {
            if (el.getAttribute('data-group-name') === arr[0]) curIcon = (el.textContent || '').trim() || '📌';
        });
        const prev = $('emojiPreview'); if (prev) prev.textContent = curIcon;
        const customInput = $('emojiCustomInput'); if (customInput) customInput.value = '';
        renderEmojiCategories(); renderEmojiGrid(0);
        emojiModal.classList.add('active');
    };
    const addIconPickerBtn = $('addIconPickerBtn');
    if (addIconPickerBtn) addIconPickerBtn.addEventListener('click', function(e) {
        e.preventDefault(); e.stopPropagation();
        if (!emojiModal) return;
        _emojiPickerMode = 'add-form';
        currentEmojiGroups = [];
        const nameEl = $('emojiGroupName');
        if (nameEl) {
            const nameVal = ($('name') && $('name').value || '').trim();
            nameEl.textContent = nameVal || 'Новая группа';
        }
        const prev = $('emojiPreview'), iconHidden = $('add_group_icon');
        if (prev) prev.textContent = (iconHidden && iconHidden.value) || '📌';
        const customInput = $('emojiCustomInput'); if (customInput) customInput.value = '';
        renderEmojiCategories(); renderEmojiGrid(0);
        emojiModal.classList.add('active');
    });
    const closeEmojiPickerBtn = $('closeEmojiPickerBtn');
    if (closeEmojiPickerBtn && emojiModal) closeEmojiPickerBtn.addEventListener('click', function() {
        emojiModal.classList.remove('active');
        currentEmojiGroups = []; _emojiPickerMode = 'group';
    });
    if (emojiModal) emojiModal.addEventListener('click', function(e) {
        if (e.target === this) { this.classList.remove('active'); currentEmojiGroups = []; _emojiPickerMode = 'group'; }
    });
    const emojiApplyCustomBtn = $('emojiApplyCustomBtn');
    if (emojiApplyCustomBtn) emojiApplyCustomBtn.addEventListener('click', function() {
        const inp = $('emojiCustomInput'); if (!inp) return;
        const val = (inp.value || '').trim(); if (val) applyEmojiIcon(val);
    });
    const emojiCustomInput = $('emojiCustomInput');
    if (emojiCustomInput) emojiCustomInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); const val = (this.value || '').trim(); if (val) applyEmojiIcon(val); }
    });
    const emojiResetBtn = $('emojiResetBtn');
    if (emojiResetBtn) emojiResetBtn.addEventListener('click', function() { applyEmojiIcon('📌'); });
    document.querySelectorAll('.card-icon[data-group-name]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            const group = this.getAttribute('data-group-name'); if (!group) return;
            if (typeof window.openEmojiPicker === 'function') window.openEmojiPicker(group);
        });
    });
    document.querySelectorAll('.rename-group-btn[data-group-name]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            const group = this.getAttribute('data-group-name'); if (!group) return;
            if (typeof window.renameGroup === 'function') window.renameGroup(group);
        });
    });

    /* ---------- Profile settings modal ---------- */
    const settingsModal = $('settingsModal');
    const closeSettingsModalBtn = $('closeSettingsModalBtn');
    if (closeSettingsModalBtn && settingsModal) closeSettingsModalBtn.addEventListener('click', function() { settingsModal.classList.remove('active'); });
    if (settingsModal) settingsModal.addEventListener('click', function(e) { if (e.target === this) this.classList.remove('active'); });
    let customButtonsDraft = [];
    function openSettings() {
        fetch('/get_settings').then(function(r) { return r.json(); }).then(function(s) {
            const pn = $('profileNameInput'); if (pn) pn.value = (s.profile && s.profile.name) || 'Admin';
            const pc = $('profileColorInput'); if (pc) pc.value = (s.profile && s.profile.color) || '#f5d76e';
            customButtonsDraft = Array.isArray(s.custom_toolbar_buttons) ? s.custom_toolbar_buttons.slice() : [];
            renderCustomButtons();
        });
    }
    function renderCustomButtons() {
        const list = $('customButtonsList'); if (!list) return;
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
                const i = parseInt(this.getAttribute('data-idx'));
                const f = this.getAttribute('data-field');
                if (customButtonsDraft[i]) customButtonsDraft[i][f] = this.value;
            });
        });
        list.querySelectorAll('.remove-btn').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const i = parseInt(this.getAttribute('data-idx'));
                customButtonsDraft.splice(i, 1);
                renderCustomButtons();
            });
        });
    }
    const addCustomBtn = $('addCustomBtn');
    if (addCustomBtn) addCustomBtn.addEventListener('click', function() {
        if (customButtonsDraft.length >= 20) return;
        customButtonsDraft.push({ icon: '🔗', label: 'Ссылка', url: 'https://' });
        renderCustomButtons();
    });
    const saveSettingsBtn = $('saveSettingsBtn');
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', function() {
        const profile = {
            name: ($('profileNameInput').value || '').trim() || 'Admin',
            color: $('profileColorInput').value
        };
        const payload = { profile: profile, custom_toolbar_buttons: customButtonsDraft };
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
        const avatar = $('profileAvatar');
        if (avatar) {
            avatar.textContent = (profile.name || 'A').charAt(0).toUpperCase();
            avatar.style.background = profile.color || '#f5d76e';
            avatar.style.boxShadow = '0 0 10px ' + (profile.color || '#f5d76e');
        }
    }
    function applyCustomToolbarButtonsLocal(btns) {
        const container = $('customToolbarBtns'); if (!container) return;
        container.innerHTML = '';
        btns.forEach(function(b) {
            const btn = document.createElement('button');
            btn.className = 'custom-toolbar-btn';
            btn.textContent = (b.icon || '') + ' ' + (b.label || '');
            btn.title = b.url || '';
            btn.addEventListener('click', function() {
                if (b.url && b.url.indexOf('#category:') === 0) {
                    const cat = b.url.slice(10).trim();
                    const target = document.querySelector('.cat-btn[data-filter="' + cat + '"]');
                    if (target) target.click();
                } else if (b.url && /^https?:\/\//i.test(b.url)) {
                    window.open(b.url, '_blank', 'noopener,noreferrer');
                }
            });
            container.appendChild(btn);
        });
    }
    const profileWidget = $('profileWidget');
    if (profileWidget && settingsModal) profileWidget.addEventListener('click', function() {
        openSettings(); settingsModal.classList.add('active');
    });

    /* ---------- Plugins manager ---------- */
    const pluginsManagerList = $('pluginsManagerList');
    const pluginEditorModal = $('pluginEditorModal');
    const pluginEditorName = $('pluginEditorName');
    const pluginEditorCode = $('pluginEditorCode');
    const pluginEditorStatus = $('pluginEditorStatus');
    let _pluginEditorIsNew = false;
    window.loadPluginsList = function() {
        if (!pluginsManagerList) return;
        pluginsManagerList.innerHTML = '<div style="color:var(--meta-color); text-align:center; padding:14px 0;">Загрузка...</div>';
        fetch('/api/plugins/list').then(function(r) { return r.json(); })
            .then(function(data) { renderPluginsManager(data); })
            .catch(function() { pluginsManagerList.innerHTML = '<div style="color:#e74c3c; padding:10px 0;">Ошибка</div>'; });
    };
    function renderPluginsManager(data) {
        if (!pluginsManagerList) return;
        const plugins = (data && data.plugins) || [];
        const hooksActive = (data && data.hooks_active) || {};
        if (!plugins.length) {
            pluginsManagerList.innerHTML = '<div style="color:var(--meta-color); text-align:center; padding:14px 0; font-style:italic;">Плагины не установлены.</div>';
            return;
        }
        let html = '';
        plugins.forEach(function(p) {
            const dotColor = p.status_color || '#7a9ab5';
            const statusLabel = p.status_label || '—';
            const toggleLabel = p.enabled ? '⏸ Отключить' : '▶ Включить';
            const toggleClass = p.enabled ? 'plugin-toggle on' : 'plugin-toggle off';
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
                const row = this.closest('.plugin-row');
                const name = row ? row.getAttribute('data-name') : '';
                const action = this.getAttribute('data-action');
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
            const p = (data.plugins || []).find(function(x) { return x.name === name; });
            if (!p) { showNotification('❌ Не найден', 'error'); return; }
            const newState = !p.enabled;
            api('/api/plugins/toggle', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, enabled: newState })
            }).then(function(r) { return r.json(); }).then(function(res) {
                if (res.success) {
                    showNotification((newState ? '▶ Включён' : '⏸ Отключён') + '. Нажмите «🔁 Перезагрузить».', 'success');
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
                    if (res.success) { showNotification('✅ Удалено. Нажмите «🔁 Перезагрузить».', 'success'); window.loadPluginsList(); }
                    else showNotification('❌ ' + (res.error || 'Не удалось'), 'error');
                }).catch(function() { showNotification('❌ Ошибка сети', 'error'); });
            });
    }
    const pluginsRefreshBtn = $('pluginsRefreshBtn');
    if (pluginsRefreshBtn) pluginsRefreshBtn.addEventListener('click', window.loadPluginsList);
    const pluginsCreateBtn = $('pluginsCreateBtn');
    if (pluginsCreateBtn) pluginsCreateBtn.addEventListener('click', function() { openPluginEditor('', true); });

    const reloadPluginsBtn = $('reloadPluginsBtn');
    if (reloadPluginsBtn) reloadPluginsBtn.addEventListener('click', function() {
        const btn = this;
        btn.disabled = true;
        showNotification('🔄 Перезагрузка плагинов...', 'success');
        apiFetch('/api/plugins/reload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken() },
            body: '{}'
        }).then(function(r) { return r.json(); }).then(function(d) {
            if (d.success) {
                showNotification('✅ ' + (d.message || 'Готово'), 'success');
                setTimeout(function() { location.reload(); }, 900);
            } else {
                showNotification('❌ ' + (d.error || 'Ошибка'), 'error');
            }
        }).catch(function() {
            showNotification('❌ Ошибка сети', 'error');
        }).finally(function() { btn.disabled = false; });
    });

    const pluginEditorCloseBtn = $('pluginEditorCloseBtn');
    if (pluginEditorCloseBtn) pluginEditorCloseBtn.addEventListener('click', closePluginEditor);
    if (pluginEditorModal) pluginEditorModal.addEventListener('click', function(e) { if (e.target === this) closePluginEditor(); });
    const pluginEditorCheckBtn = $('pluginEditorCheckBtn');
    if (pluginEditorCheckBtn) pluginEditorCheckBtn.addEventListener('click', function() {
        const code = pluginEditorCode ? pluginEditorCode.value : '';
        const name = pluginEditorName ? pluginEditorName.value.trim() : 'plugin';
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
    const pluginEditorSaveBtn = $('pluginEditorSaveBtn');
    if (pluginEditorSaveBtn) pluginEditorSaveBtn.addEventListener('click', function() {
        const code = pluginEditorCode ? pluginEditorCode.value : '';
        const name = pluginEditorName ? pluginEditorName.value.trim() : '';
        if (!name) { showNotification('❌ Введите имя плагина', 'error'); return; }
        const url = _pluginEditorIsNew ? '/api/plugins/create' : '/api/plugins/save';
        api(url, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, code: code })
        }).then(function(r) { return r.json(); }).then(function(data) {
            if (data.success) {
                showNotification('✅ Сохранено. Нажмите «🔁 Перезагрузить плагины».', 'success');
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

    /* ---------- Keyboard shortcuts ---------- */
    document.addEventListener('keydown', function(e) {
        const tag = (e.target && e.target.tagName) || '';
        const isEditable = (e.target && e.target.isContentEditable) || tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (searchInput) { searchInput.focus(); searchInput.select(); }
            return;
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'm') {
            e.preventDefault();
            const m = $('addModal'); if (m) m.classList.add('active');
            if (window.__prepareAddModal) window.__prepareAddModal();
            setTimeout(function() { const n = $('name'); if (n) n.focus(); }, 100);
            return;
        }
        if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
            if (isEditable) return;
            if (triggerUndo()) { e.preventDefault(); return; }
        }
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === 'p') {
            e.preventDefault();
            document.body.classList.toggle('presentation-mode');
            const on = document.body.classList.contains('presentation-mode');
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
                    const id = li.getAttribute('data-id');
                    if (id) { _selectedIds.add(id); li.classList.add('bulk-selected'); }
                });
            });
            updateBulkPanel();
            return;
        }
        if (e.key === 'Escape') {
            if (isEditable) return;
            hideSortDropdown();
            const openModals = document.querySelectorAll('.modal.active');
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

    setupLinkTooltips();
}