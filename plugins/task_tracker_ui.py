"""UI-слой трекера задач: HTML + CSS + JS.
Тема трекера независима от темы реестра:
  - body.trk-theme-dark (по умолчанию)
  - body.trk-theme-light (светлая Material, teal+orange)
Выбор хранится в localStorage['reestr_tracker_theme'].
"""


def render(csrf_token):
    head = (
        '<!DOCTYPE html>\n'
        '<html lang="ru">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<meta name="csrf-token" content="' + csrf_token + '">\n'
        '<title>Трекер задач — Реестр</title>\n'
        '<script>\n'
        'window.REESTR_CSRF = "' + csrf_token + '";\n'
        '(function () {\n'
        '    try {\n'
        '        var t = localStorage.getItem("reestr_tracker_theme") || "dark";\n'
        '        if (t !== "light") t = "dark";\n'
        '        document.documentElement.setAttribute("data-trk-theme", t);\n'
        '        document.addEventListener("DOMContentLoaded", function() {\n'
        '            document.body.classList.add("trk-theme-" + t);\n'
        '        });\n'
        '    } catch (e) {}\n'
        ')();\n'
        '</script>\n'
    )
    return (head + '<style>' + _css() + '</style>\n</head>\n<body class="trk-theme-dark">\n'
            + _body() + '\n' + _js() + '\n</body>\n</html>\n')


def _css():
    return r'''
    /* ============================================================
       ТЕМА ТРЕКЕРА (независима от темы реестра)
       base : тёмная
       .trk-theme-light : светлая Material (teal + orange)
       ============================================================ */
    :root {
        /* Тёмная тема трекера — реально тёмная, с золотыми контурами */
        --trk-bg: radial-gradient(ellipse at top, #1a1612 0%, #0d0d0d 40%, #050505 100%);
        --trk-text: #e8e8e8;
        --trk-card-bg: rgba(20,20,20,0.6);
        --trk-card-border: rgba(245,215,110,0.18);
        --trk-panel-bg: rgba(15,15,15,0.78);
        --trk-input-bg: rgba(30,30,30,0.7);
        --trk-input-border: rgba(245,215,110,0.22);
        --trk-input-focus: #f5d76e;
        --trk-modal-bg: #141414;
        --trk-modal-border: rgba(245,215,110,0.22);
        --trk-meta: #8a8a8a;
        --trk-desc: #b0b0b0;
        --trk-accent: #f5d76e;
        --trk-accent-2: #e6a81a;
        --trk-btn-text: #0a0a0a;
        --trk-btn-grad: linear-gradient(135deg, #f5d76e, #e6a81a);
        --trk-filter-border: rgba(245,215,110,0.22);
        --trk-filter-color: #c8c8c8;
        --trk-filter-active-bg: rgba(245,215,110,0.15);
        --trk-filter-active: #f5d76e;
        --trk-hover-row: rgba(255,255,255,0.03);
        --trk-glass-bg: rgba(15,15,15,0.78);
        --trk-shadow: 0 8px 32px rgba(0,0,0,0.55), 0 0 60px rgba(245,215,110,0.03);
        --trk-radius: 16px;
        --trk-link: #d0d0d0;
        --trk-link-hover: #f5d76e;
        --trk-ok: #2ecc71;
        --trk-warn: #f1c40f;
        --trk-err: #e74c3c;
        --trk-info: #3498db;
        --trk-weekend-bg: rgba(128,128,128,0.12);
        --trk-holiday-bg: rgba(231,76,60,0.16);
        --trk-holiday-text: #ff8474;

        /* Универсальные переменные для границ (используются в таблицах) */
        --trk-border-strong: rgba(245,215,110,0.32);
        --trk-border-medium: rgba(245,215,110,0.18);
        --trk-border-soft: rgba(245,215,110,0.10);
        --trk-header-bg: rgba(245,215,110,0.07);

        color-scheme: dark;
    }

    /* ---------- СВЕТЛАЯ ТЕМА (Material, teal + orange) ---------- */
    body.trk-theme-light {
        --trk-bg: linear-gradient(145deg, #f5f5f5 0%, #eceff1 50%, #cfd8dc 100%);
        --trk-text: #212121;
        --trk-card-bg: #ffffff;
        --trk-card-border: rgba(0,0,0,0.16);
        --trk-panel-bg: #ffffff;
        --trk-input-bg: #f5f5f5;
        --trk-input-border: rgba(0,0,0,0.22);
        --trk-input-focus: #00897b;
        --trk-modal-bg: #ffffff;
        --trk-modal-border: rgba(0,0,0,0.18);
        --trk-meta: #5a5a5a;
        --trk-desc: #3a3a3a;
        --trk-accent: #00897b;
        --trk-accent-2: #ef6c00;
        --trk-btn-text: #ffffff;
        --trk-btn-grad: linear-gradient(135deg, #00897b 0%, #ef6c00 100%);
        --trk-filter-border: rgba(0,0,0,0.22);
        --trk-filter-color: #37474f;
        --trk-filter-active-bg: rgba(0,137,123,0.12);
        --trk-filter-active: #00695c;
        --trk-hover-row: #fafafa;
        --trk-glass-bg: #ffffff;
        --trk-shadow: 0 1px 2px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.06);
        --trk-link: #00695c;
        --trk-link-hover: #ef6c00;
        --trk-ok: #2e7d32;
        --trk-warn: #ef6c00;
        --trk-err: #c62828;
        --trk-info: #0277bd;
        --trk-weekend-bg: rgba(96,125,139,0.14);
        --trk-holiday-bg: rgba(198,40,40,0.12);
        --trk-holiday-text: #c62828;
        /* Границы для таблиц */
        --trk-border-strong: rgba(0,0,0,0.24);
        --trk-border-medium: rgba(0,0,0,0.16);
        --trk-border-soft: rgba(0,0,0,0.10);
        --trk-header-bg: #eceff1;
        color-scheme: light;
    }

    /* Каркас (шапка, вкладки, панели) — чёткие контуры + мягкая тень */
    body.trk-theme-light .tracker-header,
    body.trk-theme-light .tracker-tabs,
    body.trk-theme-light .tracker-panel {
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
        border-width: 1px;
        border-color: rgba(0,0,0,0.14);
        box-shadow: 0 1px 2px rgba(0,0,0,0.06), 0 6px 16px rgba(0,0,0,0.06);
    }
    body.trk-theme-light .tracker-tabs { box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
    body.trk-theme-light .tracker-tab {
        border-color: transparent;
    }
    body.trk-theme-light .tracker-tab.active {
        box-shadow: 0 0 0 1px var(--trk-filter-active), 0 2px 8px rgba(0,137,123,0.15);
    }

    /* Плашки-элементы (сотрудники, задачи, отделы, отметки, задачи в карточке) */
    body.trk-theme-light .dict-item,
    body.trk-theme-light .day-entry,
    body.trk-theme-light .task-card-row,
    body.trk-theme-light .sum-extra-block,
    body.trk-theme-light .stats-overall .stat-card,
    body.trk-theme-light .vac-item,
    body.trk-theme-light .cal-cell,
    body.trk-theme-light .mini-heatmap,
    body.trk-theme-light .assignees-list,
    body.trk-theme-light .dept-multi-list,
    body.trk-theme-light .hm-table td,
    body.trk-theme-light .sum-table td,
    body.trk-theme-light .sum-table th,
    body.trk-theme-light .emp-day-head {
        border-width: 1px;
        border-color: rgba(0,0,0,0.14);
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    /* Явный hover */
    body.trk-theme-light .dict-item:hover,
    body.trk-theme-light .day-entry:hover,
    body.trk-theme-light .task-card-row:hover,
    body.trk-theme-light .cal-cell:hover {
        border-color: var(--trk-filter-active);
        box-shadow: 0 2px 8px rgba(0,137,123,0.18);
    }

    /* Календарь: клетка с данными — чуть заметнее */
    body.trk-theme-light .cal-cell.hours-1,
    body.trk-theme-light .cal-cell.hours-2,
    body.trk-theme-light .cal-cell.hours-3,
    body.trk-theme-light .cal-cell.hours-4 {
        border-color: rgba(46,125,50,0.25);
    }
    body.trk-theme-light .cal-cell.missing {
        border-color: rgba(198,40,40,0.35);
    }
    body.trk-theme-light .cal-cell.today {
        border-color: var(--trk-accent);
        box-shadow: inset 0 0 0 1px var(--trk-accent), 0 0 0 1px var(--trk-accent);
    }

    /* Модалки */
    body.trk-theme-light .modal-content {
        border-color: rgba(0,0,0,0.16);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12), 0 24px 60px rgba(0,0,0,0.18);
    }

    /* Формы — input/select/textarea */
    body.trk-theme-light .form-group input,
    body.trk-theme-light .form-group select,
    body.trk-theme-light .form-group textarea,
    body.trk-theme-light .cal-emp-filter select,
    body.trk-theme-light .sum-filter select,
    body.trk-theme-light .sum-filter input {
        border-color: rgba(0,0,0,0.22);
        background: #ffffff;
    }
    body.trk-theme-light .form-group input:focus,
    body.trk-theme-light .form-group select:focus,
    body.trk-theme-light .form-group textarea:focus {
        border-color: var(--trk-input-focus);
        box-shadow: 0 0 0 3px rgba(0,137,123,0.15);
    }

    /* Таблица свода: шапка и строки — разделители заметнее */
    body.trk-theme-light .sum-table th {
        background: #eceff1;
        color: #37474f;
    }
    body.trk-theme-light .sum-table td {
        background: #ffffff;
    }
    body.trk-theme-light .sum-table td.emp-cell {
        background: #f5f5f5;
        border-right: 1px solid rgba(0,0,0,0.10);
    }
    body.trk-theme-light .sum-table td.total-cell {
        background: rgba(0,137,123,0.10);
        color: #00695c;
    }

    /* Heatmap: ячейки без данных — заметная грань */
    body.trk-theme-light .hm-table td.empty-cell {
        background: #f5f5f5;
        border-color: rgba(0,0,0,0.10);
    }
    body.trk-theme-light .hm-table th.emp-col {
        background: #f5f5f5;
    }
    body.trk-theme-light .hm-table td.emp-cell {
        background: #f5f5f5;
        border-right: 1px solid rgba(0,0,0,0.10);
    }

    /* Легенды, маленькие плашки */
    body.trk-theme-light .grid-legend-swatch,
    body.trk-theme-light .hm-legend-swatch {
        border-color: rgba(0,0,0,0.20);
    }

    /* Кнопки primary — оставить с тенью */
    body.trk-theme-light .btn-primary {
        box-shadow: 0 2px 6px rgba(0,137,123,0.35);
    }
    body.trk-theme-light .btn-primary:hover {
        box-shadow: 0 4px 10px rgba(0,137,123,0.45);
    }
    body.trk-theme-light .btn-secondary {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.18);
        color: #37474f;
    }
    body.trk-theme-light .btn-secondary:hover {
        background: rgba(0,137,123,0.08);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
    }

    /* Активный таб, сегментированный переключатель */
    body.trk-theme-light .segmented {
        background: #eceff1;
        border-color: rgba(0,0,0,0.14);
    }
    body.trk-theme-light .segmented button.active {
        background: #ffffff;
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
        min-height: 100vh;
        background: var(--trk-bg);
        background-attachment: fixed;
        color: var(--trk-text);
        padding: 16px; font-size: 14px;
    }
    select, option, input, textarea, button { font-family: inherit; }
    select option, .form-group option {
        background: var(--trk-modal-bg);
        color: var(--trk-text);
    }

    .tracker-container { max-width: 1700px; margin: 0 auto; display: flex; flex-direction: column; gap: 14px; }
    .tracker-header {
        display: flex; align-items: center; gap: 14px; padding: 12px 18px;
        background: var(--trk-glass-bg);
        backdrop-filter: blur(20px) saturate(160%);
        -webkit-backdrop-filter: blur(20px) saturate(160%);
        border: 1px solid var(--trk-card-border);
        border-radius: var(--trk-radius);
        box-shadow: var(--trk-shadow);
        flex-wrap: wrap;
    }
    .tracker-title {
        display: flex; align-items: center; gap: 10px;
        font-size: 1.25rem; font-weight: 700;
        background: linear-gradient(135deg, var(--trk-accent), var(--trk-accent-2));
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-right: auto;
    }
    .tracker-back-btn {
        display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px;
        background: transparent;
        border: 1px solid var(--trk-filter-border);
        color: var(--trk-filter-color);
        border-radius: 20px; text-decoration: none;
        font-size: 0.85rem; font-weight: 600; transition: all 0.2s;
    }
    .tracker-back-btn:hover {
        background: var(--trk-filter-active-bg);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
    }
    .theme-toggle-btn {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 14px;
        background: transparent;
        border: 1px solid var(--trk-filter-border);
        color: var(--trk-filter-color);
        border-radius: 20px;
        cursor: pointer; font-size: 0.85rem; font-weight: 600;
        transition: all 0.2s; font-family: inherit;
    }
    .theme-toggle-btn:hover {
        background: var(--trk-filter-active-bg);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
    }
    .tracker-tabs {
        display: flex; gap: 4px; padding: 6px;
        background: var(--trk-panel-bg);
        border: 1px solid var(--trk-card-border);
        border-radius: var(--trk-radius);
        flex-wrap: wrap;
    }
    .tracker-tab {
        background: transparent; border: 1px solid transparent;
        color: var(--trk-filter-color);
        padding: 8px 16px; border-radius: 10px;
        cursor: pointer; font-size: 0.88rem; font-weight: 600;
        transition: all 0.18s; display: inline-flex; align-items: center; gap: 6px;
        font-family: inherit;
    }
    .tracker-tab:hover { color: var(--trk-filter-active); }
    .tracker-tab.active {
        background: var(--trk-filter-active-bg);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
        box-shadow: 0 0 14px var(--trk-filter-active-bg);
    }
    .tracker-panel {
        display: none; padding: 18px;
        background: var(--trk-panel-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--trk-card-border);
        border-radius: var(--trk-radius);
        box-shadow: var(--trk-shadow);
        min-height: 300px;
    }
    .tracker-panel.active { display: block; }

    .segmented {
        display: inline-flex; background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px; padding: 3px; gap: 2px;
    }
    .segmented button {
        background: transparent; border: 1px solid transparent;
        color: var(--trk-filter-color);
        padding: 6px 14px; border-radius: 7px;
        cursor: pointer; font-size: 0.82rem; font-weight: 600;
        transition: all 0.15s; white-space: nowrap; font-family: inherit;
    }
    .segmented button:hover { color: var(--trk-filter-active); }
    .segmented button.active {
        background: var(--trk-filter-active-bg);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
    }
    .cal-nav {
        display: inline-flex; gap: 2px; background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px; padding: 3px;
    }
    .cal-nav-btn {
        background: transparent; border: none;
        color: var(--trk-filter-color);
        padding: 6px 12px; border-radius: 7px;
        cursor: pointer; font-size: 0.9rem; transition: all 0.15s;
        font-weight: 600; font-family: inherit;
    }
    .cal-nav-btn:hover {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
    }
    .cal-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
    .cal-month-title {
        font-size: 1.15rem; font-weight: 700;
        color: var(--trk-text); min-width: 180px; text-align: center;
    }
    .cal-emp-filter {
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 0.82rem; color: var(--trk-meta);
    }
    .cal-emp-filter select, .sum-filter select, .sum-filter input {
        padding: 6px 10px;
        border: 1px solid var(--trk-input-border);
        border-radius: 8px;
        background: var(--trk-input-bg);
        color: var(--trk-text);
        font-size: 0.85rem; outline: none; font-family: inherit;
    }

    /* ===== Календарь ===== */
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
    .cal-dow {
        text-align: center; padding: 6px 4px;
        font-size: 0.72rem; font-weight: 800; color: var(--trk-meta);
        text-transform: uppercase; letter-spacing: 1px;
    }
    .cal-cell {
        min-height: 96px; padding: 6px 8px; border-radius: 10px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        cursor: pointer; position: relative; overflow: hidden;
        transition: all 0.15s; display: flex; flex-direction: column; gap: 3px;
    }
    .cal-cell:hover {
        border-color: var(--trk-filter-active);
        transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,0.2);
    }
    .cal-cell.out-month { opacity: 0.35; }
    .cal-cell.today { border-color: var(--trk-accent); box-shadow: inset 0 0 0 1px var(--trk-accent); }
    .cal-cell.today .cal-day-num { color: var(--trk-accent); font-weight: 900; }
    .cal-cell.weekend { background: var(--trk-weekend-bg); }
    .cal-cell.holiday { background: var(--trk-holiday-bg); }
    .cal-cell.holiday .cal-day-num { color: var(--trk-holiday-text); }
    .cal-cell.hours-1 { background: linear-gradient(135deg, rgba(46,204,113,0.10), rgba(46,204,113,0.20)); }
    .cal-cell.hours-2 { background: linear-gradient(135deg, rgba(46,204,113,0.18), rgba(46,204,113,0.32)); }
    .cal-cell.hours-3 { background: linear-gradient(135deg, rgba(46,204,113,0.28), rgba(46,204,113,0.45)); }
    .cal-cell.hours-4 { background: linear-gradient(135deg, rgba(46,204,113,0.40), rgba(46,204,113,0.58)); }
    .cal-cell.missing {
        background: repeating-linear-gradient(45deg,
            rgba(231,76,60,0.10) 0, rgba(231,76,60,0.10) 6px,
            rgba(231,76,60,0.18) 6px, rgba(231,76,60,0.18) 12px);
    }
    .cal-cell.has-overdue .cal-day-num::after { content: ' ⚠'; color: var(--trk-err); font-size: 0.8em; }
    .cal-day-head { display: flex; align-items: center; justify-content: space-between; gap: 4px; }
    .cal-day-num { font-size: 0.9rem; font-weight: 700; color: var(--trk-text); }
    .cal-day-hours {
        font-size: 0.7rem; font-weight: 700; color: var(--trk-accent);
        padding: 1px 6px; background: var(--trk-hover-row); border-radius: 8px;
    }
    .cal-day-entries { display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
    .cal-entry {
        font-size: 0.68rem; line-height: 1.3; padding: 2px 5px; border-radius: 5px;
        background: var(--trk-hover-row); color: var(--trk-text);
        overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
        display: flex; align-items: center; gap: 3px;
    }
    .cal-entry .entry-hours { font-weight: 700; opacity: 0.85; margin-left: auto; }
    .cal-entry .cal-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
    .cal-more {
        font-size: 0.65rem; color: var(--trk-meta);
        text-align: center; padding-top: 1px; font-style: italic;
    }
    .cal-badge-warn {
        position: absolute; top: 4px; right: 4px;
        background: rgba(231,76,60,0.9); color: #fff;
        font-size: 0.6rem; font-weight: 800; padding: 1px 5px;
        border-radius: 8px; z-index: 2;
    }
    .cal-badge-vac { position: absolute; bottom: 4px; right: 4px; font-size: 0.9rem; opacity: 0.7; }

    /* ===== Справочники ===== */
    .dict-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .dict-section { display: flex; flex-direction: column; gap: 10px; }
    .dict-section-head {
        display: flex; align-items: center; gap: 8px; padding-bottom: 8px;
        border-bottom: 1px solid var(--trk-card-border);
    }
    .dict-section-title { font-size: 0.95rem; font-weight: 700; color: var(--trk-text); margin-right: auto; }
    .dict-count {
        font-size: 0.72rem; padding: 2px 8px;
        background: var(--trk-filter-active-bg);
        border-radius: 10px;
        color: var(--trk-filter-active); font-weight: 700;
    }
    .dict-add-btn {
        background: var(--trk-btn-grad);
        border: none; color: var(--trk-btn-text);
        padding: 6px 14px; border-radius: 16px;
        cursor: pointer; font-size: 0.82rem; font-weight: 700;
        transition: transform 0.15s; font-family: inherit;
    }
    .dict-add-btn:hover { transform: scale(1.05); }
    .dict-list { display: flex; flex-direction: column; gap: 6px; max-height: 60vh; overflow-y: auto; padding-right: 4px; }
    .dict-item {
        display: flex; align-items: flex-start; gap: 10px; padding: 8px 12px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px; transition: all 0.15s;
    }
    .dict-item:hover {
        border-color: var(--trk-filter-active);
        background: var(--trk-filter-active-bg);
    }
    .dict-item-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; margin-top: 4px; }
    .dict-item-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 1px; }
    .dict-item-body { flex: 1; min-width: 0; }
    .dict-item-name {
        font-size: 0.9rem; font-weight: 600; color: var(--trk-text);
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .dict-item-name.overdue { color: var(--trk-err); }
    .dict-item-name.overdue::after { content: ' ⚠ просрочено'; font-size: 0.7rem; font-weight: 700; color: var(--trk-err); }
    .dict-item-meta {
        font-size: 0.72rem; color: var(--trk-meta);
        margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    .dict-item-meta .badge {
        display: inline-block; padding: 0 6px;
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        border-radius: 8px; font-weight: 700; font-size: 0.68rem; margin-right: 4px;
    }
    .dict-item-meta .badge-danger { background: rgba(231,76,60,0.2); color: var(--trk-err); }
    .dict-item-meta .badge-vac { background: rgba(52,152,219,0.2); color: var(--trk-info); }
    .dict-item-meta .badge-dept { background: rgba(122,154,181,0.2); color: var(--trk-info); }
    .dict-actions { display: flex; gap: 3px; flex-shrink: 0; }
    .dict-action-btn {
        background: transparent;
        border: 1px solid var(--trk-filter-border);
        color: var(--trk-filter-color);
        padding: 4px 8px; border-radius: 6px; cursor: pointer;
        font-size: 0.82rem; line-height: 1; transition: all 0.15s; font-family: inherit;
    }
    .dict-action-btn:hover {
        background: var(--trk-filter-active-bg);
        border-color: var(--trk-filter-active);
        color: var(--trk-filter-active);
    }
    .dict-action-btn.danger:hover { background: rgba(231,76,60,0.15); border-color: var(--trk-err); color: var(--trk-err); }
    .dict-empty { text-align: center; padding: 30px 10px; color: var(--trk-meta); font-style: italic; font-size: 0.85rem; }

    /* ===== Модалки ===== */
    .modal { display: none; position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); align-items: center; justify-content: center; padding: 20px; }
    .modal.active { display: flex; }
    .modal-content {
        background: var(--trk-modal-bg);
        border: 1px solid var(--trk-modal-border);
        border-radius: calc(var(--trk-radius) + 4px);
        padding: 22px 26px; max-width: 620px; width: 92%;
        max-height: 90vh; overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6);
        animation: trackerModalIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .modal-content.wide { max-width: 1000px; }
    @keyframes trackerModalIn {
        from { transform: scale(0.92) translateY(18px); opacity: 0; }
        to { transform: scale(1) translateY(0); opacity: 1; }
    }
    .modal-content h2 { color: var(--trk-text); margin-bottom: 14px; font-weight: 600; font-size: 1.2rem; }
    .form-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
    .form-group label { color: var(--trk-meta); font-size: 0.82rem; font-weight: 600; }
    .form-group input, .form-group select, .form-group textarea {
        padding: 8px 12px;
        border: 1px solid var(--trk-input-border);
        border-radius: 10px;
        background: var(--trk-input-bg);
        color: var(--trk-text);
        font-size: 0.92rem; outline: none; font-family: inherit;
    }
    .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
        border-color: var(--trk-input-focus);
    }
    .form-group textarea { min-height: 70px; resize: vertical; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; flex-wrap: wrap; }
    .btn {
        padding: 8px 20px; border-radius: 20px; cursor: pointer;
        border: none; font-size: 0.9rem; font-weight: 600;
        transition: all 0.15s; font-family: inherit;
    }
    .btn-primary { background: var(--trk-btn-grad); color: var(--trk-btn-text); }
    .btn-primary:hover { transform: scale(1.03); }
    .btn-secondary { background: var(--trk-hover-row); color: var(--trk-text); }
    .btn-secondary:hover { background: var(--trk-filter-active-bg); }
    .btn-danger { background: linear-gradient(135deg, #e74c3c, #c0392b); color: #fff; }
    .btn-danger:hover { transform: scale(1.03); }

    /* ===== Пикер иконки ===== */
    .icon-input-row { display: flex; gap: 6px; }
    .icon-input-row input { flex: 1; min-width: 0; }
    .icon-picker-btn {
        width: 44px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
        font-size: 1.3rem;
        border: 1px solid var(--trk-input-border);
        border-radius: 10px;
        background: var(--trk-input-bg);
        cursor: pointer; padding: 0; color: var(--trk-text);
        transition: all 0.15s; font-family: inherit;
    }
    .icon-picker-btn:hover { border-color: var(--trk-input-focus); background: var(--trk-filter-active-bg); }
    .emoji-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(44px, 1fr));
        gap: 4px; max-height: 380px; overflow-y: auto; padding: 6px;
        background: var(--trk-input-bg);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
    }
    .emoji-btn {
        background: transparent; border: 1px solid transparent;
        font-size: 1.5rem; line-height: 1; padding: 6px 0;
        cursor: pointer; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        transition: all 0.12s; color: inherit; font-family: inherit;
    }
    .emoji-btn:hover { background: var(--trk-filter-active-bg); border-color: var(--trk-filter-active); transform: scale(1.1); }

    .palette { display: flex; flex-wrap: wrap; gap: 6px; padding-top: 4px; }
    .palette-dot {
        width: 24px; height: 24px; border-radius: 50%;
        border: 2px solid transparent; cursor: pointer; transition: all 0.15s;
    }
    .palette-dot:hover { transform: scale(1.15); }
    .palette-dot.active { border-color: #fff; box-shadow: 0 0 0 2px var(--trk-accent); transform: scale(1.1); }

    /* ===== Assignees / Departments multi ===== */
    .assignees-list, .dept-multi-list {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 4px; max-height: 220px; overflow-y: auto; padding: 6px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
    }
    .dept-multi-list { max-height: 180px; }
    .assignees-item, .dept-multi-item {
        display: flex; align-items: center; gap: 8px;
        padding: 5px 10px; border-radius: 8px; cursor: pointer;
        font-size: 0.85rem; color: var(--trk-text);
        transition: all 0.12s; user-select: none;
    }
    .assignees-item:hover, .dept-multi-item:hover { background: var(--trk-filter-active-bg); }
    .assignees-item input[type="checkbox"], .dept-multi-item input[type="checkbox"] { margin: 0; accent-color: var(--trk-accent); }
    .assignees-dot, .dept-multi-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
    .assignees-hint {
        font-size: 0.72rem; color: var(--trk-meta);
        margin-top: 4px; font-style: italic;
    }

    /* ===== Отпуска ===== */
    .vac-list { display: flex; flex-direction: column; gap: 4px; margin-top: 6px; }
    .vac-item {
        display: flex; align-items: center; gap: 8px; padding: 6px 10px;
        background: rgba(52,152,219,0.10);
        border: 1px solid rgba(52,152,219,0.25);
        border-radius: 8px; font-size: 0.82rem;
    }
    .vac-item-body { flex: 1; min-width: 0; }
    .vac-item-dates { font-weight: 700; color: var(--trk-info); }
    .vac-item-comment { color: var(--trk-desc); font-size: 0.75rem; }
    .vac-empty { color: var(--trk-meta); font-size: 0.82rem; font-style: italic; padding: 6px 2px; }
    .vac-add-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 6px; margin-top: 6px; }
    .vac-add-row input {
        padding: 6px 10px;
        border: 1px solid var(--trk-input-border);
        border-radius: 8px;
        background: var(--trk-input-bg);
        color: var(--trk-text);
        font-size: 0.82rem; outline: none; font-family: inherit;
    }
    .vac-add-row button {
        padding: 6px 12px; border: none; border-radius: 8px;
        background: var(--trk-btn-grad);
        color: var(--trk-btn-text);
        font-weight: 700; cursor: pointer; font-size: 0.82rem; font-family: inherit;
    }

    /* ===== Свод ===== */
    .sum-toolbar {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 8px;
        align-items: center;
        margin-bottom: 14px;
    }
    .sum-toolbar .sum-group {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 3px 6px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
    }
    .sum-toolbar .sum-dash { color: var(--trk-meta); font-weight: 700; padding: 0 2px; }
    .sum-toolbar .sum-toggle {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        cursor: pointer;
        user-select: none;
        padding: 5px 10px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--trk-filter-color);
    }
    .sum-toolbar .sum-toggle input[type="checkbox"] {
        accent-color: var(--trk-accent);
        margin: 0;
        width: 14px;
        height: 14px;
        padding: 0;
        border: none;
        background: none;
        max-width: none;
    }
    .sum-filter {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.78rem;
        color: var(--trk-meta);
    }
    .sum-toolbar input[type="date"] {
        padding: 5px 8px;
        border: 1px solid var(--trk-input-border);
        border-radius: 8px;
        background: var(--trk-input-bg);
        color: var(--trk-text);
        font-size: 0.76rem;
        outline: none;
        font-family: inherit;
        max-width: 128px;
    }
    .sum-toolbar .sum-filter select {
        padding: 5px 8px;
        border: 1px solid var(--trk-input-border);
        border-radius: 8px;
        background: var(--trk-input-bg);
        color: var(--trk-text);
        font-size: 0.78rem;
        outline: none;
        font-family: inherit;
        min-width: 100px;
        max-width: 160px;
    }
    .sum-toolbar button.btn {
        padding: 5px 12px;
        font-size: 0.78rem;
        border-radius: 16px;
    }
    .sum-toolbar .segmented button {
        padding: 5px 10px;
        font-size: 0.76rem;
    }
    .sum-table-wrap { overflow-x: auto; padding-bottom: 4px; }
    .sum-table { border-collapse: separate; border-spacing: 3px; font-size: 0.82rem; min-width: 100%; }
    .sum-table th {
        padding: 8px 10px; background: var(--trk-hover-row);
        color: var(--trk-meta); font-weight: 700;
        font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px;
        border-radius: 8px; white-space: nowrap; text-align: center;
        position: relative;
    }
    .sum-table th.emp-col { text-align: left; min-width: 180px; position: sticky; left: 0; z-index: 2; }
    .sum-table th.total-col { background: var(--trk-filter-active-bg); color: var(--trk-filter-active); }
    .sum-table th.weekend-col { background: var(--trk-weekend-bg); color: var(--trk-meta); }
    .sum-table th.holiday-col { background: var(--trk-holiday-bg); color: var(--trk-holiday-text); }
    .sum-table th.today-col { box-shadow: inset 0 -3px 0 var(--trk-accent); }
    .sum-table td {
        padding: 8px 10px; background: var(--trk-hover-row);
        border-radius: 8px; color: var(--trk-text);
        vertical-align: top; min-width: 90px; max-width: 220px; text-align: center;
    }
    .sum-table td.emp-cell {
        text-align: left; font-weight: 700;
        position: sticky; left: 0; z-index: 1;
        background: var(--trk-hover-row); white-space: nowrap;
    }
    .sum-table td.emp-cell .emp-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
    }
    .sum-table td.total-cell {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        font-weight: 700;
    }
    .sum-table td.empty-cell { color: var(--trk-meta); opacity: 0.45; }
    .sum-table td.has-data { cursor: pointer; }
    .sum-table td.has-data:hover { outline: 1px solid var(--trk-filter-active); }

    .sum-cell-compact .sum-hours-main { font-weight: 800; font-size: 1.05rem; color: var(--trk-text); line-height: 1.1; }
    .sum-cell-compact .sum-tasks-count { font-size: 0.72rem; color: var(--trk-meta); margin-top: 2px; }
    .sum-cell-full .sum-hours-main { font-weight: 800; font-size: 0.95rem; color: var(--trk-accent); margin-bottom: 4px; line-height: 1.1; }
    .sum-cell-full .sum-task-row {
        display: flex; align-items: center; gap: 4px;
        font-size: 0.72rem; padding: 2px 4px;
        border-radius: 4px; margin-bottom: 1px;
        background: var(--trk-hover-row); text-align: left;
        overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    }
    .sum-cell-full .sum-task-row .task-name { flex: 1; overflow: hidden; text-overflow: ellipsis; color: var(--trk-text); }
    .sum-cell-full .sum-task-row .task-hours { color: var(--trk-accent); font-weight: 700; }
    .sum-cell-full .sum-task-row.overdue { background: rgba(231,76,60,0.18); }
    .sum-cell-full .sum-task-row .status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .sum-cell-full .sum-task-row.done .status-dot { background: #2ecc71; }
    .sum-cell-full .sum-task-row.in_progress .status-dot { background: #3498db; }
    .sum-cell-full .sum-task-row.planned .status-dot { background: #95a5a6; }
    .sum-cell-full .sum-task-row.blocked .status-dot { background: #e74c3c; }
    .sum-table tr.day-totals-row td { background: var(--trk-hover-row); font-weight: 700; color: var(--trk-accent); }
    .sum-empty { text-align: center; padding: 40px 20px; color: var(--trk-meta); font-style: italic; }

    /* Дополнительная статистика (под сводом) */
    .sum-extra-section {
        margin-top: 22px;
        padding-top: 16px;
        border-top: 2px dashed var(--trk-card-border);
    }
    .sum-extra-section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.75rem;
        font-weight: 800;
        color: var(--trk-filter-active);
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 12px;
    }
    .sum-extra-section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, var(--trk-card-border), transparent);
        opacity: 0.6;
    }
    .sum-extras { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .sum-extra-block {
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 12px; padding: 12px 14px;
    }
    .sum-extra-title {
        font-size: 0.75rem; font-weight: 800;
        color: var(--trk-filter-active);
        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
    }
    .sum-top-task {
        display: flex; align-items: center; gap: 8px;
        padding: 4px 0; font-size: 0.82rem;
        border-bottom: 1px dashed var(--trk-card-border);
    }
    .sum-top-task:last-child { border-bottom: none; }
    .sum-top-task .name { flex: 1; }
    .sum-top-task .hours { color: var(--trk-accent); font-weight: 700; }
    .sum-vac-row {
        display: flex; align-items: center; gap: 8px;
        padding: 4px 0; font-size: 0.82rem;
        border-bottom: 1px dashed var(--trk-card-border);
    }
    .sum-vac-row:last-child { border-bottom: none; }
    .sum-vac-row .dates { color: var(--trk-info); font-weight: 700; white-space: nowrap; }

    /* ===== GRID-СВОД ===== */
    .grid-table { font-size: 0.78rem; }
    .grid-table th.task-col { text-align: left; min-width: 160px; }
    .grid-table td.task-cell {
        text-align: left; min-width: 160px;
        font-size: 0.82rem;
    }
    .grid-table td.task-cell .task-ico { margin-right: 4px; }
    .grid-table td.task-cell .task-name-str { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .grid-table td.task-cell .task-period {
        display: block;
        font-size: 0.65rem;
        color: var(--trk-meta);
        margin-top: 1px;
    }
    .grid-table td.task-cell.empty { color: var(--trk-meta); font-style: italic; opacity: 0.6; }
    .grid-table td.day-cell {
        padding: 6px 6px; min-width: 42px; max-width: 60px;
        text-align: center; font-weight: 700; font-size: 0.82rem;
        cursor: pointer; transition: all 0.12s;
        border-radius: 6px;
    }
    .grid-table td.day-cell.status-done { background: rgba(46,204,113,0.20); color: #1a9c52; }
    .grid-table td.day-cell.status-in_progress { background: rgba(46,204,113,0.12); color: #1a9c52; }
    .grid-table td.day-cell.status-planned { background: rgba(149,165,166,0.24); color: #566573; }
    .grid-table td.day-cell.status-blocked { background: rgba(231,76,60,0.24); color: #c0392b; }
    .grid-table td.day-cell:hover { transform: scale(1.15); box-shadow: 0 0 8px rgba(0,0,0,0.3); z-index: 5; }
    .grid-table td.emp-cell { vertical-align: middle; font-size: 0.88rem; }
    .grid-table td.emp-cell .emp-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
    }
    .grid-table tr.emp-sep td {
        background: transparent !important;
        height: 8px; padding: 0; border: none;
    }
    .grid-table tr.day-totals-row td { font-weight: 700; background: var(--trk-hover-row); }
    .grid-table tr.day-totals-row td.day-cell { color: var(--trk-accent); }
    .grid-table td.day-cell.weekend-day { background: var(--trk-weekend-bg); }
    .grid-table td.day-cell.holiday-day { background: var(--trk-holiday-bg); color: var(--trk-holiday-text); }
    .grid-table td.day-cell.weekend-day.status-done,
    .grid-table td.day-cell.weekend-day.status-in_progress,
    .grid-table td.day-cell.weekend-day.status-planned,
    .grid-table td.day-cell.weekend-day.status-blocked { box-shadow: inset 0 0 0 1px var(--trk-weekend-bg); }
    .grid-table td.day-cell.holiday-day.status-done,
    .grid-table td.day-cell.holiday-day.status-in_progress,
    .grid-table td.day-cell.holiday-day.status-planned,
    .grid-table td.day-cell.holiday-day.status-blocked { box-shadow: inset 0 0 0 1px var(--trk-holiday-bg); }
    .grid-legend {
        display: flex; gap: 14px; flex-wrap: wrap;
        margin-top: 12px; font-size: 0.78rem;
        color: var(--trk-meta);
    }
    .grid-legend-item { display: inline-flex; align-items: center; gap: 5px; }
    .grid-legend-swatch { width: 16px; height: 16px; border-radius: 4px; }
    
    /* ============================================================
       ГРАНИЦЫ ТАБЛИЦ (Свод + Heatmap) — общие для обеих тем
       Цвета берутся из --trk-border-* переменных
       ============================================================ */
    .sum-table th,
    .hm-table th {
        border: 1px solid var(--trk-border-medium);
    }
    .sum-table th.emp-col,
    .hm-table th.emp-col {
        background: var(--trk-header-bg);
        color: var(--trk-filter-active);
        border: 1px solid var(--trk-border-strong);
        border-right-width: 2px;
    }
    .sum-table th.total-col,
    .hm-table th.total-col {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        border: 1px solid var(--trk-border-strong);
    }
    .sum-table th.weekend-col,
    .hm-table th.weekend-col {
        border-color: var(--trk-border-soft);
    }
    .sum-table th.holiday-col,
    .hm-table th.holiday-col {
        border-color: var(--trk-border-strong);
    }

    .sum-table td,
    .hm-table td {
        border: 1px solid var(--trk-border-soft);
    }
    .sum-table td.emp-cell,
    .hm-table td.emp-cell {
        background: var(--trk-header-bg);
        border: 1px solid var(--trk-border-strong);
        border-right-width: 2px;
    }
    .sum-table td.total-cell,
    .hm-table td.total-cell {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        font-weight: 700;
        border: 1px solid var(--trk-border-strong);
    }
    .sum-table td.day-cell,
    .sum-table td.has-data,
    .hm-table td[data-emp] {
        border-color: var(--trk-border-medium);
    }
    .sum-table td.empty-cell,
    .hm-table td.empty-cell {
        border-color: var(--trk-border-soft);
    }
    .grid-table td.task-cell,
    .grid-table td.task-cell.empty {
        border: 1px solid var(--trk-border-medium);
    }
    .sum-table tr.day-totals-row td {
        border-color: var(--trk-border-medium);
        background: var(--trk-header-bg);
    }
    .sum-table tr.day-totals-row td.emp-cell {
        background: var(--trk-header-bg);
    }
    .emp-vac-badge {
        display: inline-block;
        font-size: 0.7rem; color: var(--trk-info);
        padding: 0 6px; border-radius: 8px;
        background: rgba(52,152,219,0.15);
        margin-left: 4px;
    }
    .emp-dept {
        font-size: 0.7rem; color: var(--trk-meta);
        margin-top: 1px;
    }
    .grid-table td.day-cell.vacation-day {
        background: repeating-linear-gradient(45deg,
            rgba(52,152,219,0.15) 0, rgba(52,152,219,0.15) 4px,
            rgba(52,152,219,0.35) 4px, rgba(52,152,219,0.35) 8px) !important;
        color: var(--trk-info); font-weight: 700; cursor: help;
    }
    .stats-overall {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 10px; margin-bottom: 16px;
    }
    .stats-overall .stat-card {
        display: flex; flex-direction: column; gap: 4px;
        padding: 12px 14px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
    }
    .stats-overall .stat-label {
        font-size: 0.7rem; color: var(--trk-meta);
        text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700;
    }
    .stats-overall .stat-value {
        font-size: 1.6rem; font-weight: 800;
        color: var(--trk-accent); line-height: 1.1;
    }

    /* ===== Задачи в карточке сотрудника ===== */
    .task-card-row {
        display: flex; flex-direction: column; gap: 6px;
        padding: 10px 12px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
        margin-bottom: 8px;
    }
    .task-card-row.overdue { border-left: 4px solid var(--trk-err); }
    .task-card-row-head {
        display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    }
    .task-card-row-title {
        font-size: 0.95rem; font-weight: 700;
        color: var(--trk-text);
    }
    .task-card-row-title.overdue::after {
        content: ' ⚠'; color: var(--trk-err); font-size: 0.85em;
    }
    .task-card-row-meta {
        display: flex; gap: 10px; flex-wrap: wrap;
        font-size: 0.75rem; color: var(--trk-meta);
    }

    .coverage-bar {
        display: flex; align-items: center; gap: 8px;
        font-size: 0.72rem; color: var(--trk-meta);
    }
    .coverage-bar-track {
        flex: 1; height: 8px; border-radius: 4px;
        background: var(--trk-hover-row);
        overflow: hidden;
        min-width: 80px;
    }
    .coverage-bar-fill {
        height: 100%; border-radius: 4px;
        transition: width 0.3s ease;
    }
    .coverage-bar-fill.ok { background: linear-gradient(90deg, #2ecc71, #27ae60); }
    .coverage-bar-fill.warn { background: linear-gradient(90deg, #f1c40f, #d98b0e); }
    .coverage-bar-fill.err { background: linear-gradient(90deg, #e74c3c, #c0392b); }
    .coverage-bar-label { font-weight: 700; white-space: nowrap; }

    /* ===== Мини-heatmap ===== */
    .mini-heatmap {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(26px, 1fr));
        gap: 3px;
        padding: 8px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px;
        margin-top: 10px;
    }
    .mini-heatmap .mini-cell {
        aspect-ratio: 1;
        border-radius: 4px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.6rem; font-weight: 700;
        color: var(--trk-meta);
        background: rgba(128,128,128,0.10);
        cursor: default; transition: all 0.15s;
    }
    .mini-heatmap .mini-cell.workday { background: rgba(128,128,128,0.06); }
    .mini-heatmap .mini-cell.weekend { background: var(--trk-weekend-bg); }
    .mini-heatmap .mini-cell.holiday { background: var(--trk-holiday-bg); color: var(--trk-holiday-text); }
    .mini-heatmap .mini-cell.vacation {
        background: repeating-linear-gradient(45deg,
            rgba(52,152,219,0.15) 0, rgba(52,152,219,0.15) 3px,
            rgba(52,152,219,0.30) 3px, rgba(52,152,219,0.30) 6px) !important;
        color: var(--trk-info);
    }
    .mini-heatmap .mini-cell.missing { background: rgba(231,76,60,0.22); color: var(--trk-err); }
    .mini-heatmap .mini-cell.today { box-shadow: inset 0 0 0 2px var(--trk-accent); }
    .mini-heatmap .mini-cell .mini-h { font-size: 0.6rem; font-weight: 800; }

    /* ===== Блок «кто не заполнил» ===== */
    .day-missing-block {
        padding: 10px 12px;
        margin-bottom: 12px;
        background: rgba(231,76,60,0.10);
        border: 1px solid rgba(231,76,60,0.3);
        border-radius: 10px;
        font-size: 0.82rem;
        color: var(--trk-text);
    }
    .day-missing-block .dm-title { color: var(--trk-err); font-weight: 700; margin-bottom: 6px; }
    .day-missing-block .dm-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .day-missing-block .dm-item {
        display: inline-flex; align-items: center; gap: 5px;
        padding: 2px 10px; border-radius: 12px;
        background: var(--trk-hover-row);
        font-size: 0.78rem;
    }
    .day-missing-block .dm-dot { width: 8px; height: 8px; border-radius: 50%; }

    /* ===== Сводка за день ===== */
    .log-day-summary {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 12px; border-radius: 8px;
        font-size: 0.82rem; margin-bottom: 10px;
    }
    .log-day-summary.ok { background: rgba(46,204,113,0.12); border: 1px solid rgba(46,204,113,0.35); color: var(--trk-ok); }
    .log-day-summary.warn { background: rgba(241,196,15,0.12); border: 1px solid rgba(241,196,15,0.4); color: #d98b0e; }
    .log-day-summary.danger { background: rgba(231,76,60,0.12); border: 1px solid rgba(231,76,60,0.4); color: var(--trk-err); }
    .log-day-summary .lbl { flex: 1; }
    .log-day-summary .val { font-weight: 800; }

    /* ===== Heatmap ===== */
    .hm-toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
    .hm-table-wrap { overflow-x: auto; padding-bottom: 4px; }
    .hm-table { border-collapse: separate; border-spacing: 2px; font-size: 0.78rem; }
    .hm-table th {
        padding: 6px 8px; background: var(--trk-hover-row);
        color: var(--trk-meta); font-weight: 700;
        font-size: 0.68rem; border-radius: 6px; text-align: center; min-width: 30px;
    }
    .hm-table th.emp-col { text-align: left; min-width: 180px; padding-left: 12px; position: sticky; left: 0; z-index: 2; }
    .hm-table th.weekend-col { background: var(--trk-weekend-bg); }
    .hm-table th.holiday-col { background: var(--trk-holiday-bg); color: var(--trk-holiday-text); }
    .hm-table th.today-col {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        box-shadow: inset 0 -2px 0 var(--trk-filter-active);
    }
    .hm-table td {
        padding: 6px 8px; background: var(--trk-hover-row); border-radius: 6px;
        text-align: center; color: var(--trk-text);
        font-size: 0.72rem; min-width: 32px;
        transition: all 0.15s; cursor: pointer; position: relative;
    }
    .hm-table td:hover { transform: scale(1.08); z-index: 3; }
    .hm-table td.emp-cell {
        text-align: left; font-weight: 700;
        position: sticky; left: 0; z-index: 1;
        background: var(--trk-hover-row);
        padding-left: 12px; min-width: 180px; cursor: pointer;
    }
    .hm-table td.emp-cell:hover { background: var(--trk-filter-active-bg); }
    .hm-table td.emp-cell .emp-dot {
        display: inline-block; width: 9px; height: 9px;
        border-radius: 50%; margin-right: 6px; vertical-align: middle;
    }
    .hm-table td.empty-cell { color: var(--trk-meta); opacity: 0.35; }
    .hm-table td.weekend-cell { background: var(--trk-weekend-bg); cursor: default; }
    .hm-table td.weekend-cell:hover { transform: none; }
    .hm-table td.holiday-cell { background: var(--trk-holiday-bg); color: var(--trk-holiday-text); cursor: default; }
    .hm-table td.holiday-cell:hover { transform: none; }
    .hm-table td.vacation-cell {
        background: repeating-linear-gradient(45deg,
            rgba(52,152,219,0.15) 0, rgba(52,152,219,0.15) 6px,
            rgba(52,152,219,0.30) 6px, rgba(52,152,219,0.30) 12px) !important;
        color: var(--trk-info); font-weight: 700; cursor: pointer;
    }
    .hm-table td.missing-cell {
        background: rgba(231,76,60,0.22) !important;
        color: var(--trk-err); font-weight: 700; cursor: pointer;
    }
    .hm-table td.future-cell { opacity: 0.4; cursor: default; }
    .hm-table td.future-cell:hover { transform: none; }
    .hm-table td.today-cell { box-shadow: inset 0 0 0 2px var(--trk-accent); }
    .hm-table td.total-cell {
        background: var(--trk-filter-active-bg);
        color: var(--trk-filter-active);
        font-weight: 700; cursor: default;
    }
    .hm-table td.total-cell:hover { transform: none; }
    .hm-legend {
        display: flex; align-items: center; gap: 10px;
        margin-top: 14px; font-size: 0.75rem;
        color: var(--trk-meta); flex-wrap: wrap;
    }
    .hm-legend-item { display: inline-flex; align-items: center; gap: 5px; }
    .hm-legend-swatch {
        width: 16px; height: 16px; border-radius: 4px;
        border: 1px solid var(--trk-card-border);
    }
    .hm-legend-bar {
        display: flex; height: 14px; border-radius: 4px; overflow: hidden;
        border: 1px solid var(--trk-card-border);
    }
    .hm-legend-cell { width: 24px; }

    /* ===== Карточка сотрудника / задачи (общий шапка) ===== */
    .emp-day-head {
        display: flex; align-items: center; gap: 12px; padding: 12px 14px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 10px; margin-bottom: 12px; flex-wrap: wrap;
    }
    .emp-day-avatar {
        width: 44px; height: 44px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem; font-weight: 800; color: #ffffff; flex-shrink: 0;
    }
    .emp-day-info { flex: 1; min-width: 0; }
    .emp-day-name { font-size: 1.05rem; font-weight: 700; color: var(--trk-text); }
    .emp-day-role { font-size: 0.78rem; color: var(--trk-meta); }
    .emp-day-stats { display: flex; gap: 14px; flex-wrap: wrap; font-size: 0.82rem; }
    .emp-day-stat { display: flex; flex-direction: column; align-items: center; }
    .emp-day-stat .val { font-size: 1.15rem; font-weight: 800; color: var(--trk-accent); line-height: 1.1; }
    .emp-day-stat .lbl { font-size: 0.65rem; color: var(--trk-meta); text-transform: uppercase; letter-spacing: 0.5px; }
    .emp-day-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }
    .emp-day-badge.warn { background: rgba(231,76,60,0.18); color: var(--trk-err); }
    .emp-day-badge.vac { background: rgba(52,152,219,0.18); color: var(--trk-info); }
    .emp-day-badge.ok { background: rgba(46,204,113,0.18); color: var(--trk-ok); }

    /* ===== Список задач в модалке дня ===== */
    .day-modal-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
    .day-modal-date { font-size: 1.15rem; font-weight: 700; color: var(--trk-text); }
    .day-modal-total {
        font-size: 0.82rem; color: var(--trk-accent); font-weight: 700;
        padding: 2px 10px;
        background: var(--trk-filter-active-bg);
        border-radius: 12px;
    }
    .day-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
    .day-empty { text-align: center; padding: 24px 10px; color: var(--trk-meta); font-style: italic; font-size: 0.85rem; }

    .day-entry {
        display: grid;
        grid-template-columns: 40px 1fr auto;
        gap: 12px;
        padding: 12px 14px;
        background: var(--trk-hover-row);
        border: 1px solid var(--trk-card-border);
        border-radius: 12px;
        transition: all 0.15s;
        border-left: 4px solid transparent;
        position: relative;
    }
    .day-entry:hover { border-color: var(--trk-filter-active); box-shadow: 0 2px 10px rgba(0,0,0,0.15); }
    .day-entry.overdue { border-left-color: var(--trk-err); background: rgba(231,76,60,0.06); }
    .day-entry.done { border-left-color: var(--trk-ok); }
    .day-entry.in_progress { border-left-color: var(--trk-info); }
    .day-entry.planned { border-left-color: #95a5a6; }
    .day-entry.blocked { border-left-color: var(--trk-err); }

    .day-entry-avatar {
        width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; font-weight: 800;
        color: #ffffff; flex-shrink: 0;
        align-self: flex-start;
    }
    .day-entry-body { flex: 1; min-width: 0; }
    .day-entry-head {
        display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
        margin-bottom: 4px;
    }
    .day-entry-task {
        font-size: 0.95rem; font-weight: 700;
        color: var(--trk-text);
        display: inline-flex; align-items: center; gap: 4px;
    }
    .day-entry-task.overdue::after { content: ' ⚠'; color: var(--trk-err); font-size: 0.85em; }
    .day-entry-hours {
        font-size: 0.78rem; font-weight: 700;
        color: var(--trk-accent);
        padding: 2px 10px;
        background: var(--trk-filter-active-bg);
        border-radius: 10px;
    }
    .day-entry-status {
        font-size: 0.72rem;
        padding: 2px 10px;
        border-radius: 10px;
        font-weight: 700;
    }
    .day-entry-status.status-done { background: rgba(46,204,113,0.18); color: var(--trk-ok); }
    .day-entry-status.status-in_progress { background: rgba(52,152,219,0.18); color: var(--trk-info); }
    .day-entry-status.status-planned { background: rgba(149,165,166,0.20); color: #566573; }
    .day-entry-status.status-blocked { background: rgba(231,76,60,0.18); color: var(--trk-err); }

    .day-entry-employee-row {
        display: flex; align-items: center; gap: 6px;
        font-size: 0.78rem; color: var(--trk-meta);
        margin-bottom: 2px;
        flex-wrap: wrap;
    }
    .day-entry-employee-row .emp-name { font-weight: 600; color: var(--trk-text); }
    .day-entry-employee-row .emp-dept {
        font-size: 0.7rem; color: var(--trk-meta);
        padding: 0 6px; background: var(--trk-hover-row); border-radius: 8px;
    }
    .day-entry-meta {
        display: flex; gap: 10px; flex-wrap: wrap;
        font-size: 0.72rem; color: var(--trk-meta);
        margin-top: 4px;
    }
    .day-entry-meta .mi { display: inline-flex; align-items: center; gap: 3px; }
    .day-entry-meta .mi.warn { color: var(--trk-warn); font-weight: 700; }
    .day-entry-meta .mi.danger { color: var(--trk-err); font-weight: 700; }
    .day-entry-comment {
        font-size: 0.82rem; color: var(--trk-desc);
        line-height: 1.4; margin-top: 6px;
        word-break: break-word;
        padding: 6px 10px;
        background: var(--trk-hover-row);
        border-radius: 8px;
        border-left: 2px solid var(--trk-card-border);
    }
    .day-entry-link {
        font-size: 0.75rem; color: var(--trk-link);
        margin-top: 6px; font-family: monospace; word-break: break-all;
        text-decoration: none; display: inline-block;
    }
    .day-entry-link:hover { color: var(--trk-link-hover); text-decoration: underline; }
    .day-entry-actions {
        display: flex; flex-direction: column; gap: 3px;
        flex-shrink: 0; align-self: flex-start;
    }

    .day-modal-actions {
        display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap;
        margin-top: 16px;
    }
    .day-modal-actions-right { display: flex; gap: 8px; flex-wrap: wrap; }

    /* ===== Уведомления ===== */
    .tracker-notification {
        position: fixed; top: 20px; right: 20px; z-index: 2000;
        padding: 12px 20px; background: rgba(46,204,113,0.95); color: #fff;
        border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        max-width: 480px; font-size: 0.9rem;
        opacity: 0; transform: translateY(-10px);
        transition: opacity 0.25s, transform 0.25s;
        pointer-events: none; word-break: break-word;
    }
    .tracker-notification.show { opacity: 1; transform: translateY(0); }
    .tracker-notification.error { background: rgba(231,76,60,0.95); }

    @media (max-width: 900px) {
        .dict-grid, .sum-extras { grid-template-columns: 1fr; }
        .form-row { grid-template-columns: 1fr; }
        .cal-cell { min-height: 68px; padding: 4px 5px; }
        .cal-day-num { font-size: 0.78rem; }
        .cal-entry { font-size: 0.6rem; padding: 1px 3px; }
        .grid-table td.task-cell { min-width: 120px; font-size: 0.75rem; }
        .day-entry { grid-template-columns: 34px 1fr auto; gap: 8px; padding: 10px; }
        .day-entry-avatar { width: 34px; height: 34px; font-size: 0.75rem; }
    }
    '''


def _body():
    return '''
<div class="tracker-container">
    <div class="tracker-header">
        <a class="tracker-back-btn" href="/"><span>📚</span><span>Реестр</span></a>
        <div class="tracker-title"><span>📅</span><span>Трекер задач</span></div>
        <button class="theme-toggle-btn" id="trkThemeToggle" title="Переключить тему трекера">
            <span id="trkThemeIcon">☀️</span>
            <span id="trkThemeLabel">Светлая</span>
        </button>
    </div>

    <div class="tracker-tabs">
        <button class="tracker-tab active" data-tab="calendar"><span>📅</span><span>Календарь</span></button>
        <button class="tracker-tab" data-tab="tasks"><span>📋</span><span>Задачи</span></button>
        <button class="tracker-tab" data-tab="heatmap"><span>🔥</span><span>Тепловая карта</span></button>
        <button class="tracker-tab" data-tab="summary"><span>📊</span><span>Свод</span></button>
        <button class="tracker-tab" data-tab="stats"><span>📈</span><span>Статистика</span></button>
        <button class="tracker-tab" data-tab="dicts"><span>⚙️</span><span>Справочники</span></button>
    </div>

    <!-- ==================== Календарь ==================== -->
    <div class="tracker-panel active" id="panel-calendar">
        <div class="cal-toolbar">
            <div class="cal-nav">
                <button class="cal-nav-btn" id="calPrevBtn" title="Предыдущий месяц">◀</button>
                <button class="cal-nav-btn" id="calTodayBtn" title="Текущий месяц">Сегодня</button>
                <button class="cal-nav-btn" id="calNextBtn" title="Следующий месяц">▶</button>
            </div>
            <div class="cal-month-title" id="calMonthTitle">—</div>
            <div class="segmented" id="calViewMode">
                <button class="active" data-mode="tasks">📋 По задачам</button>
                <button data-mode="employees">👥 По сотрудникам</button>
            </div>
            <label class="cal-emp-filter" style="margin-left:auto;">
                <span>🏢</span>
                <select id="calDeptFilter"><option value="">Все отделы</option></select>
            </label>
            <label class="cal-emp-filter">
                <span>👤</span>
                <select id="calEmployeeFilter"><option value="">Все сотрудники</option></select>
            </label>
        </div>
        <div class="cal-grid" id="calGrid">
            <div class="cal-dow">Пн</div><div class="cal-dow">Вт</div><div class="cal-dow">Ср</div>
            <div class="cal-dow">Чт</div><div class="cal-dow">Пт</div><div class="cal-dow">Сб</div>
            <div class="cal-dow">Вс</div>
        </div>
    </div>

    <!-- ==================== Задачи ==================== -->
    <div class="tracker-panel" id="panel-tasks">
        <div class="sum-toolbar">
            <label class="sum-filter"><span>🏢</span>
                <select id="tskDeptFilter"><option value="">Все отделы</option></select>
            </label>
            <label class="sum-filter"><span>👤</span>
                <select id="tskEmployeeFilter"><option value="">Все сотрудники</option></select>
            </label>
            <div class="segmented" id="tskViewMode" style="margin-left:auto;">
                <button class="active" data-mode="all">Все</button>
                <button data-mode="active">Активные</button>
                <button data-mode="overdue">Просроченные</button>
                <button data-mode="done">Выполненные</button>
                <button data-mode="archived">Архив</button>
            </div>
            <button class="dict-add-btn" id="addTaskBtn2">➕ Новая задача</button>
        </div>
        <div class="dict-list" id="tasksFullList" style="max-height:none;"><div class="dict-empty">Загрузка...</div></div>
    </div>

    <!-- ==================== Тепловая карта ==================== -->
    <div class="tracker-panel" id="panel-heatmap">
        <div class="hm-toolbar">
            <div class="cal-nav">
                <button class="cal-nav-btn" id="hmPrevBtn">◀</button>
                <button class="cal-nav-btn" id="hmTodayBtn">Сегодня</button>
                <button class="cal-nav-btn" id="hmNextBtn">▶</button>
            </div>
            <div class="cal-month-title" id="hmMonthTitle">—</div>
            <label class="sum-filter" style="margin-left:auto;"><span>🏢</span>
                <select id="hmDeptFilter"><option value="">Все отделы</option></select>
            </label>
            <label class="sum-filter"><span>С</span>
                <input type="date" id="hmDateFrom">
            </label>
            <label class="sum-filter"><span>По</span>
                <input type="date" id="hmDateTo">
            </label>
            <button class="btn btn-secondary" id="hmApplyBtn" style="padding:6px 14px; font-size:0.82rem;">Применить</button>
            <button class="btn btn-secondary" id="hmMonthBtn" style="padding:6px 14px; font-size:0.82rem;">Текущий месяц</button>
        </div>
        <div class="hm-table-wrap" id="hmWrap"><div class="sum-empty">Загрузка...</div></div>
        <div class="hm-legend">
            <span>Загрузка:</span>
            <div class="hm-legend-bar" id="hmLegendBar"></div>
            <span style="margin-left:12px;">Прочее:</span>
            <span class="hm-legend-item"><span class="hm-legend-swatch" style="background: repeating-linear-gradient(45deg, rgba(52,152,219,0.15) 0, rgba(52,152,219,0.15) 4px, rgba(52,152,219,0.30) 4px, rgba(52,152,219,0.30) 8px);"></span>Отпуск</span>
            <span class="hm-legend-item"><span class="hm-legend-swatch" style="background: rgba(231,76,60,0.22);"></span>Не заполнено</span>
            <span class="hm-legend-item"><span class="hm-legend-swatch" style="background: var(--trk-weekend-bg);"></span>Выходной</span>
            <span class="hm-legend-item"><span class="hm-legend-swatch" style="background: var(--trk-holiday-bg);"></span>Праздник</span>
        </div>
    </div>

    <!-- ==================== Свод ==================== -->
    <div class="tracker-panel" id="panel-summary">
        <div class="sum-toolbar">
            <div class="sum-group">
                <input type="date" id="sumDateFrom">
                <span class="sum-dash">—</span>
                <input type="date" id="sumDateTo">
            </div>

            <button class="btn btn-secondary" id="sumWeekBtn" title="Текущая неделя (Пн–Вс)">📅 Неделя</button>
            <button class="btn btn-secondary" id="sumMonthBtn" title="Текущий месяц">📆 Месяц</button>
            <button class="btn btn-primary" id="sumApplyBtn">✓ Применить</button>

            <label class="sum-toggle" title="Показывать строку «Итого за день»">
                <input type="checkbox" id="sumShowDayTotals" checked>
                <span>Итоги</span>
            </label>

            <div class="segmented" id="sumViewMode">
                <button class="active" data-mode="grid" title="Сетка по задачам">📋 Задачи</button>
                <button data-mode="compact" title="Кратко по дням">📊 Кратко</button>
                <button data-mode="full" title="Подробно по дням">🔍 Подробно</button>
            </div>

            <label class="sum-filter" title="Фильтр по отделу">
                <span>🏢</span>
                <select id="sumDeptFilter"><option value="">Все отделы</option></select>
            </label>
            <label class="sum-filter" title="Фильтр по сотруднику">
                <span>👤</span>
                <select id="sumEmployeeFilter"><option value="">Все сотрудники</option></select>
            </label>
            <label class="sum-filter" title="Фильтр по задаче">
                <span>📋</span>
                <select id="sumTaskFilter"><option value="">Все задачи</option></select>
            </label>
        </div>
        <div class="sum-table-wrap" id="sumWrap"><div class="sum-empty">Загрузка...</div></div>
        <div id="sumExtras"></div>
    </div>

    <!-- ==================== Статистика ==================== -->
    <div class="tracker-panel" id="panel-stats">
        <div class="sum-toolbar">
            <label class="sum-filter"><span>📅</span><input type="date" id="stDateFrom"></label>
            <label class="sum-filter"><span>→</span><input type="date" id="stDateTo"></label>
            <button class="btn btn-secondary" id="stApplyBtn" style="padding:6px 14px; font-size:0.82rem;">Применить</button>
            <button class="btn btn-secondary" id="stMonthBtn" style="padding:6px 14px; font-size:0.82rem;">Текущий месяц</button>
            <label class="sum-filter"><span>🏢</span><select id="stDeptFilter"><option value="">Все отделы</option></select></label>
            <label class="sum-filter"><span>👤</span><select id="stEmployeeFilter"><option value="">Все сотрудники</option></select></label>
        </div>
        <div id="stOverall" class="stats-overall"></div>
        <div id="stOverdue" class="sum-extra-block" style="margin-bottom:14px; display:none;"></div>
        <div id="stExtras"></div>
    </div>

    <!-- ==================== Справочники ==================== -->
    <div class="tracker-panel" id="panel-dicts">
        <div class="dict-grid">
            <div class="dict-section">
                <div class="dict-section-head">
                    <span class="dict-section-title">👥 Сотрудники</span>
                    <span class="dict-count" id="employeesCount">0</span>
                    <button class="dict-add-btn" id="addEmployeeBtn">➕ Добавить</button>
                </div>
                <div class="dict-list" id="employeesList"><div class="dict-empty">Загрузка...</div></div>
            </div>
            <div class="dict-section">
                <div class="dict-section-head">
                    <span class="dict-section-title">🏢 Отделы</span>
                    <span class="dict-count" id="departmentsCount">0</span>
                    <button class="dict-add-btn" id="addDepartmentBtn">➕ Добавить</button>
                </div>
                <div class="dict-list" id="departmentsList"><div class="dict-empty">Загрузка...</div></div>
            </div>
        </div>
        <div class="dict-grid" style="margin-top:16px;">
            <div class="dict-section" style="grid-column: 1 / -1;">
                <div class="dict-section-head">
                    <span class="dict-section-title">📋 Задачи</span>
                    <span class="dict-count" id="tasksCount">0</span>
                    <button class="dict-add-btn" id="addTaskBtn">➕ Добавить</button>
                </div>
                <div class="dict-list" id="tasksList"><div class="dict-empty">Загрузка...</div></div>
            </div>
        </div>
    </div>
</div>

<!-- ========= Модалка: сотрудник ========= -->
<div class="modal" id="employeeModal">
    <div class="modal-content">
        <h2 id="employeeModalTitle">Новый сотрудник</h2>
        <input type="hidden" id="emp_id">
        <div class="form-group"><label>Имя <span style="color:#e74c3c;">*</span></label>
            <input type="text" id="emp_name" placeholder="Иванов И.И." maxlength="100"></div>
        <div class="form-row">
            <div class="form-group"><label>Цвет</label>
                <input type="color" id="emp_color" value="#00897b" style="height:38px; padding:2px;">
                <div class="palette" id="empPalette"></div>
            </div>
            <div class="form-group"><label>Роль</label>
                <input type="text" id="emp_role" placeholder="engineer / manager" maxlength="50"></div>
        </div>
        <div class="form-group"><label>🏢 Отдел</label>
            <select id="emp_department_select"><option value="">— не указан —</option></select>
        </div>
        <div class="form-group" id="vacSection" style="display:none;">
            <label>🏖 Отпуска</label>
            <div class="vac-list" id="vacList"></div>
            <div class="vac-add-row">
                <input type="date" id="vac_from"><input type="date" id="vac_to"><button type="button" id="vacAddBtn">➕</button>
            </div>
            <input type="text" id="vac_comment" placeholder="Комментарий (необязательно)" maxlength="200"
                   style="margin-top:4px; padding:6px 10px; border:1px solid var(--trk-input-border); border-radius:8px; background:var(--trk-input-bg); color:var(--trk-text); font-size:0.82rem; outline:none; font-family:inherit;">
        </div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="employeeModal">Отмена</button>
            <button class="btn btn-primary" id="saveEmployeeBtn">💾 Сохранить</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: отдел ========= -->
<div class="modal" id="departmentModal">
    <div class="modal-content">
        <h2 id="departmentModalTitle">Новый отдел</h2>
        <input type="hidden" id="dep_id">
        <div class="form-group"><label>Название <span style="color:#e74c3c;">*</span></label>
            <input type="text" id="dep_name" placeholder="Отдел разработки" maxlength="80"></div>
        <div class="form-group"><label>Цвет</label>
            <input type="color" id="dep_color" value="#00897b" style="height:38px; padding:2px; width:80px;"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="departmentModal">Отмена</button>
            <button class="btn btn-primary" id="saveDepartmentBtn">💾 Сохранить</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: задача ========= -->
<div class="modal" id="taskModal">
    <div class="modal-content">
        <h2 id="taskModalTitle">Новая задача</h2>
        <input type="hidden" id="task_id">
        <div class="form-row">
            <div class="form-group"><label>Иконка</label>
                <div class="icon-input-row">
                    <input type="text" id="task_icon" placeholder="🚀" maxlength="8">
                    <button type="button" class="icon-picker-btn" id="taskIconPickBtn" title="Выбрать значок">🚀</button>
                </div>
            </div>
            <div class="form-group"><label>Название <span style="color:#e74c3c;">*</span></label>
                <input type="text" id="task_name" placeholder="Разработка API" maxlength="200"></div>
        </div>
        <div class="form-group"><label>Описание</label>
            <textarea id="task_description" placeholder="Краткое описание задачи"></textarea></div>
        <div class="form-row">
            <div class="form-group"><label>Статус</label>
                <select id="task_status">
                    <option value="active">Активна</option>
                    <option value="done">Выполнена</option>
                    <option value="paused">Приостановлена</option>
                    <option value="archived">Архив</option>
                </select>
            </div>
            <div class="form-group"><label>🚀 Начало</label>
                <input type="date" id="task_start_date"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>⏰ Дедлайн</label>
                <input type="date" id="task_deadline"></div>
            <div class="form-group"><label>🏷️ Теги (через запятую)</label>
                <input type="text" id="task_tags" placeholder="backend, priority" maxlength="300"></div>
        </div>

        <div class="form-group"><label>🏢 Отделы (можно несколько)</label>
            <div class="dept-multi-list" id="taskDepartmentsList"></div>
            <div class="assignees-hint" id="taskDepartmentsHint">Отметьте один или несколько отделов</div>
        </div>

        <div class="form-group"><label>👥 Назначено сотрудникам</label>
            <div class="assignees-list" id="taskAssigneesList"></div>
            <div class="assignees-hint" id="taskAssigneesHint"></div>
        </div>

        <div class="form-group"><label>📁 Папка с файлами</label>
            <input type="text" id="task_folder" placeholder="\\\\server\\share\\project\\" maxlength="500"></div>
        <div class="form-group"><label>📄 Приказ / распоряжение</label>
            <input type="text" id="task_order_ref" placeholder="Приказ №45 от 01.10.2026" maxlength="200"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="taskModal">Отмена</button>
            <button class="btn btn-primary" id="saveTaskBtn">💾 Сохранить</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: эмодзи ========= -->
<div class="modal" id="emojiModal">
    <div class="modal-content">
        <h2>🎨 Выбор значка</h2>
        <div class="emoji-grid" id="emojiGrid"></div>
        <div class="modal-actions"><button class="btn btn-secondary" data-close="emojiModal">Закрыть</button></div>
    </div>
</div>

<!-- ========= Модалка: день ========= -->
<div class="modal" id="dayModal">
    <div class="modal-content wide">
        <div class="day-modal-head">
            <div class="day-modal-date" id="dayModalDate">—</div>
            <div class="day-modal-total" id="dayModalTotal">0 ч</div>
        </div>
        <div id="dayMissingBlock" class="day-missing-block" style="display:none;"></div>
        <div class="day-list" id="dayList"></div>
        <div class="day-modal-actions">
            <div class="day-modal-actions-right" id="dayModalLeftActions">
                <button class="btn btn-primary" id="dayAddBtn">➕ Добавить отметку</button>
                <button class="btn btn-secondary" id="dayCopyPrevBtn" title="Скопировать вчерашние отметки">📎 Как вчера</button>
                <button class="btn btn-secondary" id="dayTodayBtn" title="Перейти к сегодня">📅 Сегодня</button>
            </div>
            <div class="day-modal-actions-right">
                <button class="btn btn-danger" id="dayClearBtn" title="Удалить все отметки за день">🗑 Очистить день</button>
                <button class="btn btn-secondary" data-close="dayModal">Закрыть</button>
            </div>
        </div>
    </div>
</div>

<!-- ========= Модалка: отметка ========= -->
<div class="modal" id="logModal">
    <div class="modal-content">
        <h2 id="logModalTitle">Новая отметка</h2>
        <input type="hidden" id="log_id">
        <div id="logDayExisting" style="display:none; margin-bottom:12px;">
            <div style="font-size:0.75rem; color:var(--trk-meta); text-transform:uppercase; letter-spacing:1px; font-weight:700; margin-bottom:6px;">
                Уже заведено за этот день
            </div>
            <div class="day-list" id="logDayExistingList" style="margin-bottom:0;"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>📅 Дата отметки <span style="color:#e74c3c;">*</span></label>
                <input type="date" id="log_date"></div>
            <div class="form-group"><label>⏱ Часы</label>
                <input type="number" id="log_hours" min="0" max="24" step="0.25" value="8"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>👤 Сотрудник <span style="color:#e74c3c;">*</span></label>
                <select id="log_employee"></select></div>
            <div class="form-group"><label>📋 Задача <span style="color:#e74c3c;">*</span></label>
                <select id="log_task"></select></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>📌 Статус</label>
                <select id="log_status">
                    <option value="in_progress">🔵 В работе</option>
                    <option value="done">✅ Готово</option>
                    <option value="planned">📝 Запланировано</option>
                    <option value="blocked">🔴 Заблокировано</option>
                </select></div>
        </div>
        <div id="logDaySummary" class="log-day-summary" style="display:none;"></div>
        <div class="form-group"><label>💬 Комментарий</label>
            <textarea id="log_comment" placeholder="Что именно сделано"></textarea></div>
        <div class="form-group"><label>🔗 Ссылка на результат</label>
            <input type="text" id="log_link" placeholder="https://... или \\\\server\\..." maxlength="500"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="logModal">Отмена</button>
            <button class="btn btn-primary" id="saveLogBtn">💾 Сохранить</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: карточка сотрудника ========= -->
<div class="modal" id="empCardModal">
    <div class="modal-content wide">
        <div class="emp-day-head" id="empCardHead"></div>
        <div id="empCardHeatmap" class="mini-heatmap"></div>
        <div id="empCardTasks" style="margin-top:14px;"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="empCardModal">Закрыть</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: карточка задачи ========= -->
<div class="modal" id="taskCardModal">
    <div class="modal-content wide">
        <div class="emp-day-head" id="taskCardHead"></div>
        <div id="taskCardHeatmap" class="mini-heatmap"></div>
        <div id="taskCardEmployees" class="day-list" style="margin-top:14px;"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="taskCardModal">Закрыть</button>
        </div>
    </div>
</div>

<!-- ========= Модалка: карточка сотрудника за день ========= -->
<div class="modal" id="empDayModal">
    <div class="modal-content wide">
        <div class="emp-day-head" id="empDayHead"></div>
        <div class="day-list" id="empDayList"></div>
        <div class="modal-actions">
            <button class="btn btn-secondary" data-close="empDayModal">Закрыть</button>
        </div>
    </div>
</div>

<div class="tracker-notification" id="trackerNotif"></div>
'''


def _js():
    return r'''<script>
(function() {
'use strict';

var state = {
    employees: [], tasks: [], log: [], emoji: [], palette: [], departments: [],
    holidays: {},
    statusLabels: {}, taskStatusLabels: {},
    calendar: null, heatmap: null, summary: null,
    currentYM: '', currentEmployee: '', currentDepartment: '', currentDay: '',
    calViewMode: 'tasks',
    tskViewMode: 'all',
    hmYM: '', hmDateFrom: '', hmDateTo: '',
    sumViewMode: 'grid', sumShowDayTotals: true,
    today: '',
    theme: 'dark',
};

var MONTHS_RU = ['Январь','Февраль','Март','Апрель','Май','Июнь',
                 'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'];

var csrf = window.REESTR_CSRF || '';
var meta = document.querySelector('meta[name="csrf-token"]');
if (!csrf && meta) csrf = meta.getAttribute('content') || '';

function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
        return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];
    });
}
function $(id) { return document.getElementById(id); }
function notify(msg, kind) {
    var n = $('trackerNotif'); if (!n) return;
    n.textContent = msg;
    n.className = 'tracker-notification show' + (kind === 'error' ? ' error' : '');
    setTimeout(function() { n.classList.remove('show'); }, 4500);
}
function apiJson(url, options) {
    options = options || {};
    options.headers = Object.assign({}, options.headers || {});
    if (csrf && options.method && options.method !== 'GET') options.headers['X-CSRF-Token'] = csrf;
    if (!options.credentials) options.credentials = 'same-origin';
    return fetch(url, options).then(function(r) {
        if (!r.ok) {
            return r.text().then(function(t) {
                var msg = 'HTTP ' + r.status;
                try { var j = JSON.parse(t); if (j && j.error) msg += ' — ' + j.error; }
                catch (e) { if (t) msg += ' — ' + t.slice(0, 200); }
                throw new Error(msg);
            });
        }
        return r.json();
    });
}
function todayYM() {
    var t = new Date();
    return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0');
}
function todayISO() {
    var t = new Date();
    return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-' + String(t.getDate()).padStart(2, '0');
}
function firstOfMonthISO(ym) { return ym + '-01'; }
function firstOfMonthISOFromDate(d) {
    var t = d || new Date();
    return t.getFullYear() + '-' + String(t.getMonth() + 1).padStart(2, '0') + '-01';
}
function getMondayISO() {
    var t = new Date();
    var wd = t.getDay();
    var diff = (wd === 0) ? -6 : (1 - wd);
    var mon = new Date(t.getTime() + diff * 86400000);
    return mon.getFullYear() + '-' + String(mon.getMonth() + 1).padStart(2, '0') + '-' + String(mon.getDate()).padStart(2, '0');
}
function getSundayISO() {
    var mon = getMondayISO();
    var sun = new Date(new Date(mon + 'T00:00:00').getTime() + 6 * 86400000);
    return sun.getFullYear() + '-' + String(sun.getMonth() + 1).padStart(2, '0') + '-' + String(sun.getDate()).padStart(2, '0');
}
/* Текущая неделя — Пн..Вс */
function setDefaultWeekRange() {
    $('sumDateFrom').value = getMondayISO();
    $('sumDateTo').value = getSundayISO();
}
function setMonthRange() {
    var t = new Date();
    $('sumDateFrom').value = firstOfMonthISOFromDate(t);
    $('sumDateTo').value = todayISO();
}
function formatDateHuman(iso) {
    try {
        var p = iso.split('-');
        return parseInt(p[2], 10) + ' ' + MONTHS_RU[parseInt(p[1], 10) - 1].toLowerCase() + ' ' + p[0];
    } catch (e) { return iso; }
}
function formatDateShort(iso) {
    try { var p = iso.split('-'); return parseInt(p[2], 10) + '.' + p[1]; }
    catch (e) { return iso; }
}
function formatHours(h) {
    h = Number(h) || 0;
    if (h === Math.floor(h)) return h + ' ч';
    return h.toFixed(2).replace(/0+$/, '').replace(/\.$/, '') + ' ч';
}
function shortHours(h) {
    h = Number(h) || 0;
    if (h === Math.floor(h)) return String(h);
    return h.toFixed(2).replace(/0+$/, '').replace(/\.$/, '');
}
function hoursClass(h) {
    h = Number(h) || 0;
    if (h <= 0) return '';
    if (h < 2) return 'hours-1';
    if (h < 4) return 'hours-2';
    if (h < 6) return 'hours-3';
    return 'hours-4';
}
function heatmapColor(hours) {
    if (!hours) return '';
    var h = Number(hours);
    if (h < 8) {
        var r = h / 8;
        var hue = 45 + (130 - 45) * r;
        var sat = 70 - 10 * r;
        var light = 62 - 7 * r;
        return 'hsl(' + hue + ', ' + sat + '%, ' + light + '%)';
    }
    if (h === 8) return 'hsl(130, 60%, 50%)';
    var r2 = Math.min((h - 8) / 8, 1);
    var hue2 = 195 + (285 - 195) * r2;
    var sat2 = 60 + 15 * r2;
    var light2 = 55 - 10 * r2;
    return 'hsl(' + hue2 + ', ' + sat2 + '%, ' + light2 + '%)';
}
function cellLightGreen(hours) {
    if (!hours) return '';
    var h = Math.min(Number(hours) / 8, 1.5);
    var alpha = 0.10 + Math.min(h, 1) * 0.20;
    if (h > 1) alpha = 0.30 + (h - 1) * 0.10;
    return 'rgba(46,204,113,' + alpha.toFixed(2) + ')';
}
function initials(name) {
    var parts = String(name || '').trim().split(/\s+/);
    if (!parts.length) return '?';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + (parts[1][0] || '')).toUpperCase();
}
function statusClass(s) {
    if (s === 'done') return 'status-done';
    if (s === 'in_progress') return 'status-in_progress';
    if (s === 'planned') return 'status-planned';
    if (s === 'blocked') return 'status-blocked';
    return '';
}

/* ============ Тема трекера ============ */
function applyTrkTheme(theme) {
    if (theme !== 'light' && theme !== 'dark') theme = 'dark';
    state.theme = theme;
    document.body.classList.remove('trk-theme-dark', 'trk-theme-light');
    document.body.classList.add('trk-theme-' + theme);
    document.documentElement.setAttribute('data-trk-theme', theme);
    try { localStorage.setItem('reestr_tracker_theme', theme); } catch (e) {}
    var iconEl = $('trkThemeIcon');
    var labelEl = $('trkThemeLabel');
    if (iconEl) iconEl.textContent = theme === 'dark' ? '☀️' : '🌙';
    if (labelEl) labelEl.textContent = theme === 'dark' ? 'Светлая' : 'Тёмная';
}
function toggleTrkTheme() {
    applyTrkTheme(state.theme === 'dark' ? 'light' : 'dark');
}
(function initTrkTheme() {
    var saved = 'dark';
    try { saved = localStorage.getItem('reestr_tracker_theme') || 'dark'; } catch (e) {}
    applyTrkTheme(saved);
})();
var _themeBtn = $('trkThemeToggle');
if (_themeBtn) _themeBtn.addEventListener('click', toggleTrkTheme);

/* ============ Табы ============ */
document.querySelectorAll('.tracker-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
        var id = this.getAttribute('data-tab');
        document.querySelectorAll('.tracker-tab').forEach(function(t) { t.classList.toggle('active', t === tab); });
        document.querySelectorAll('.tracker-panel').forEach(function(p) { p.classList.toggle('active', p.id === 'panel-' + id); });
        try { localStorage.setItem('tracker_activeTab', id); } catch (e) {}
        if (id === 'tasks') renderTasksFull();
        if (id === 'heatmap') loadHeatmap();
        if (id === 'summary') loadSummary();
        if (id === 'stats') {
            if (!$('stDateFrom').value) {
                $('stDateFrom').value = firstOfMonthISO(todayYM());
                $('stDateTo').value = todayISO();
            }
            loadStats();
        }
    });
});
try {
    var savedTab = localStorage.getItem('tracker_activeTab');
    if (savedTab && savedTab !== 'calendar') {
        var tabBtn = document.querySelector('.tracker-tab[data-tab="' + savedTab + '"]');
        if (tabBtn) setTimeout(function() { tabBtn.click(); }, 50);
    }
    var savedDept = localStorage.getItem('tracker_calDept');
    if (savedDept) state.currentDepartment = savedDept;
} catch (e) {}

function setupSegmented(elId, initial, onChange) {
    var wrap = $(elId); if (!wrap) return;
    var btns = wrap.querySelectorAll('button');
    btns.forEach(function(b) {
        b.classList.toggle('active', b.getAttribute('data-mode') === initial);
        b.addEventListener('click', function() {
            btns.forEach(function(x) { x.classList.remove('active'); });
            this.classList.add('active');
            onChange(this.getAttribute('data-mode'));
        });
    });
}
setupSegmented('calViewMode', state.calViewMode, function(mode) { state.calViewMode = mode; renderCalendar(); });
setupSegmented('sumViewMode', state.sumViewMode, function(mode) { state.sumViewMode = mode; loadSummary(); });
setupSegmented('tskViewMode', state.tskViewMode, function(mode) { state.tskViewMode = mode; renderTasksFull(); });

/* ============ State ============ */
function loadState() {
    return apiJson('/api/tracker/state').then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка загрузки');
        state.employees = d.employees || [];
        state.tasks = d.tasks || [];
        state.log = d.log || [];
        state.emoji = d.emoji || [];
        state.palette = d.palette || [];
        state.departments = d.departments || [];
        state.holidays = d.holidays || {};
        state.today = d.today || todayISO();
        if (d.status_labels) state.statusLabels = d.status_labels;
        if (d.task_status_labels) state.taskStatusLabels = d.task_status_labels;
        renderDepartments();
        renderEmployees();
        renderTasks();
        renderPalette();
        renderEmojiGrid();
        fillDepartmentFilters();
        fillEmployeeFilter();
        fillEmployeeSelect();
        fillTaskSelect();
        fillSummaryFilters();
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

/* ============ Отделы ============ */
function renderDepartments() {
    var list = $('departmentsList'), cnt = $('departmentsCount');
    if (!list) return;
    var deps = state.departments || [];
    if (cnt) cnt.textContent = deps.length;
    if (!deps.length) {
        list.innerHTML = '<div class="dict-empty">Пока нет отделов</div>';
        return;
    }
    var html = '';
    deps.forEach(function(dep) {
        var count = (state.employees || []).filter(function(e) { return e.department_id === dep.id; }).length;
        html += '<div class="dict-item" data-id="' + escapeHtml(dep.id) + '">'
            + '<span class="dict-item-dot" style="background:' + escapeHtml(dep.color || '#7a9ab5') + '; box-shadow:0 0 8px ' + escapeHtml(dep.color || '#7a9ab5') + ';"></span>'
            + '<div class="dict-item-body"><div class="dict-item-name">' + escapeHtml(dep.name) + '</div>'
            + '<div class="dict-item-meta"><span class="badge">👥 ' + count + '</span></div>'
            + '</div><div class="dict-actions">'
            + '<button class="dict-action-btn" data-act="edit">✏️</button>'
            + '<button class="dict-action-btn danger" data-act="delete">🗑</button></div></div>';
    });
    list.innerHTML = html;
    list.querySelectorAll('.dict-item').forEach(function(item) {
        var id = item.getAttribute('data-id');
        item.querySelector('[data-act="edit"]').addEventListener('click', function() {
            var dep = (state.departments || []).find(function(x) { return x.id === id; });
            if (dep) openDepartmentModal(dep);
        });
        item.querySelector('[data-act="delete"]').addEventListener('click', function() { deleteDepartment(id); });
    });
}

function renderPalette() {
    var wrap = $('empPalette'); if (!wrap) return;
    var colors = state.palette.length ? state.palette : ['#00897b','#ef6c00','#c62828','#0277bd','#2e7d32','#6d4c41'];
    wrap.innerHTML = colors.map(function(c) { return '<span class="palette-dot" style="background:' + c + ';" data-color="' + c + '" title="' + c + '"></span>'; }).join('');
    wrap.querySelectorAll('.palette-dot').forEach(function(dot) {
        dot.addEventListener('click', function() {
            var c = this.getAttribute('data-color');
            $('emp_color').value = c;
            wrap.querySelectorAll('.palette-dot').forEach(function(d) { d.classList.remove('active'); });
            this.classList.add('active');
        });
    });
}

/* ============ Сотрудники ============ */
function renderEmployees() {
    var list = $('employeesList'), cnt = $('employeesCount');
    if (cnt) cnt.textContent = state.employees.length;
    if (!state.employees.length) { list.innerHTML = '<div class="dict-empty">Пока нет сотрудников</div>'; return; }
    var html = '';
    state.employees.forEach(function(e) {
        var color = e.color || '#00897b';
        var vacCount = (e.vacations || []).length;
        var vacBadge = vacCount ? '<span class="badge badge-vac">🏖 ' + vacCount + '</span>' : '';
        var metaParts = [];
        if (e.department) metaParts.push('<span class="badge">🏢 ' + escapeHtml(e.department) + '</span>');
        if (e.role) metaParts.push(escapeHtml(e.role));
        html += '<div class="dict-item" data-id="' + escapeHtml(e.id) + '">'
            + '<span class="dict-item-dot" style="background:' + escapeHtml(color) + '; box-shadow:0 0 8px ' + escapeHtml(color) + ';"></span>'
            + '<div class="dict-item-body"><div class="dict-item-name">' + escapeHtml(e.name) + '</div>'
            + (metaParts.length || vacBadge ? '<div class="dict-item-meta">' + vacBadge + metaParts.join(' ') + '</div>' : '')
            + '</div><div class="dict-actions">'
            + '<button class="dict-action-btn" data-act="edit">✏️</button>'
            + '<button class="dict-action-btn danger" data-act="delete">🗑</button></div></div>';
    });
    list.innerHTML = html;
    list.querySelectorAll('.dict-item').forEach(function(item) {
        var id = item.getAttribute('data-id');
        item.querySelector('[data-act="edit"]').addEventListener('click', function() {
            var emp = state.employees.find(function(x) { return x.id === id; });
            if (emp) openEmployeeModal(emp);
        });
        item.querySelector('[data-act="delete"]').addEventListener('click', function() { deleteEmployee(id); });
    });
}

/* ============ Задачи ============ */
function renderTasks() {
    var list = $('tasksList'), cnt = $('tasksCount');
    if (!list) return;
    if (cnt) cnt.textContent = state.tasks.length;
    if (!state.tasks.length) { list.innerHTML = '<div class="dict-empty">Пока нет задач</div>'; return; }
    var html = '';
    state.tasks.forEach(function(t) { html += taskCardRow(t); });
    list.innerHTML = html;
    bindTaskCardActions(list, '.dict-item');
    renderTasksFull();
}

function _deptBadgesForTask(t) {
    var ids = t.department_ids || [];
    if (!ids.length) return '';
    var names = ids.map(function(id) {
        var d = (state.departments || []).find(function(x) { return x.id === id; });
        return d ? d.name : id;
    });
    var limit = 2;
    var shown = names.slice(0, limit).map(function(n) {
        return '<span class="badge badge-dept">🏢 ' + escapeHtml(n) + '</span>';
    }).join('');
    if (names.length > limit) {
        shown += '<span class="badge badge-dept" title="' + escapeHtml(names.join(', ')) + '">+' + (names.length - limit) + '</span>';
    }
    return shown;
}

function taskCardRow(t) {
    var metaParts = [];
    if (t.overdue) metaParts.push('<span class="badge badge-danger">⚠ просрочено</span>');
    if (t.status && t.status !== 'active') {
        var lbl = state.taskStatusLabels[t.status] || t.status;
        metaParts.push('<span class="badge">' + escapeHtml(lbl) + '</span>');
    }
    var deptBadges = _deptBadgesForTask(t);
    if (deptBadges) metaParts.push(deptBadges);
    if (t.start_date) metaParts.push('🚀 ' + escapeHtml(t.start_date));
    if (t.deadline) metaParts.push('⏰ ' + escapeHtml(t.deadline));
    if (t.assignees && t.assignees.length) {
        var names = t.assignees.map(function(aid) {
            var e = state.employees.find(function(x) { return x.id === aid; });
            return e ? e.name : '?';
        }).slice(0, 3);
        metaParts.push('👥 ' + names.map(escapeHtml).join(', ') + (t.assignees.length > 3 ? ' +' + (t.assignees.length - 3) : ''));
    }
    if (t.tags && t.tags.length) t.tags.slice(0, 3).forEach(function(tag) { metaParts.push('#' + escapeHtml(tag)); });
    return '<div class="dict-item" data-id="' + escapeHtml(t.id) + '">'
        + '<span class="dict-item-icon">' + escapeHtml(t.icon || '📋') + '</span>'
        + '<div class="dict-item-body"><div class="dict-item-name' + (t.overdue ? ' overdue' : '') + '">' + escapeHtml(t.name) + '</div>'
        + (metaParts.length ? '<div class="dict-item-meta">' + metaParts.join(' · ') + '</div>' : '')
        + '</div><div class="dict-actions">'
        + '<button class="dict-action-btn" data-act="card" title="Карточка задачи">📊</button>'
        + '<button class="dict-action-btn" data-act="edit" title="Редактировать">✏️</button>'
        + '<button class="dict-action-btn danger" data-act="delete" title="Удалить">🗑</button></div></div>';
}

function bindTaskCardActions(container, sel) {
    container.querySelectorAll(sel || '.dict-item').forEach(function(item) {
        var id = item.getAttribute('data-id');
        var cardBtn = item.querySelector('[data-act="card"]');
        var editBtn = item.querySelector('[data-act="edit"]');
        var delBtn = item.querySelector('[data-act="delete"]');
        if (cardBtn) cardBtn.addEventListener('click', function() { openTaskCardModal(id); });
        if (editBtn) editBtn.addEventListener('click', function() {
            var t = state.tasks.find(function(x) { return x.id === id; });
            if (t) openTaskModal(t);
        });
        if (delBtn) delBtn.addEventListener('click', function() { deleteTask(id); });
    });
}

function _taskMatchesDept(t, deptId) {
    if (!deptId) return true;
    var ids = t.department_ids || [];
    if (ids.indexOf(deptId) !== -1) return true;
    if (!ids.length) {
        var empDeptIds = (t.assignees || []).map(function(aid) {
            var e = state.employees.find(function(x) { return x.id === aid; });
            return e ? e.department_id : '';
        });
        return empDeptIds.indexOf(deptId) !== -1;
    }
    return false;
}

function renderTasksFull() {
    var list = $('tasksFullList'); if (!list) return;
    var dept = $('tskDeptFilter') ? ($('tskDeptFilter').value || '') : '';
    var emp = $('tskEmployeeFilter') ? ($('tskEmployeeFilter').value || '') : '';
    var mode = state.tskViewMode || 'all';
    var tasks = state.tasks.slice();
    if (dept) tasks = tasks.filter(function(t) { return _taskMatchesDept(t, dept); });
    if (emp) tasks = tasks.filter(function(t) { return (t.assignees || []).indexOf(emp) !== -1; });
    if (mode === 'active') tasks = tasks.filter(function(t) { return t.status === 'active' && !t.overdue; });
    else if (mode === 'overdue') tasks = tasks.filter(function(t) { return t.overdue; });
    else if (mode === 'done') tasks = tasks.filter(function(t) { return t.status === 'done'; });
    else if (mode === 'archived') tasks = tasks.filter(function(t) { return t.status === 'archived'; });

    if (!tasks.length) {
        list.innerHTML = '<div class="dict-empty">Нет задач по фильтру</div>';
        return;
    }
    var html = '';
    tasks.forEach(function(t) { html += taskCardRow(t); });
    list.innerHTML = html;
    bindTaskCardActions(list, '.dict-item');
}

/* ============ Эмодзи-пикер ============ */
function renderEmojiGrid() {
    var grid = $('emojiGrid'); if (!grid) return;
    var list = state.emoji.length ? state.emoji : ['🚀','📋','💼','📊','🎯','💡','📁','📌','🔖','📅','👥','💻'];
    grid.innerHTML = list.map(function(e) { return '<button type="button" class="emoji-btn" data-emoji="' + escapeHtml(e) + '">' + e + '</button>'; }).join('');
    grid.querySelectorAll('.emoji-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var em = this.getAttribute('data-emoji');
            $('task_icon').value = em; $('taskIconPickBtn').textContent = em || '🚀';
            $('emojiModal').classList.remove('active');
        });
    });
}

/* ============ Фильтры ============ */
function fillDepartmentFilters() {
    var deps = state.departments || [];
    ['calDeptFilter','hmDeptFilter','sumDeptFilter','stDeptFilter','tskDeptFilter'].forEach(function(elId) {
        var sel = $(elId); if (!sel) return;
        var cur = sel.value;
        sel.innerHTML = '<option value="">Все отделы</option>'
            + deps.map(function(d) { return '<option value="' + escapeHtml(d.id) + '">' + escapeHtml(d.name) + '</option>'; }).join('');
        sel.value = cur;
    });
    var cal = $('calDeptFilter');
    if (cal && state.currentDepartment) cal.value = state.currentDepartment;
}

function fillEmployeeFilter() {
    var sel = $('calEmployeeFilter'); if (!sel) return;
    var cur = sel.value;
    var deptId = state.currentDepartment || '';
    var emps = state.employees;
    if (deptId) emps = emps.filter(function(e) { return e.department_id === deptId; });
    sel.innerHTML = '<option value="">Все сотрудники</option>'
        + emps.map(function(e) { return '<option value="' + escapeHtml(e.id) + '">' + escapeHtml(e.name) + '</option>'; }).join('');
    sel.value = cur || state.currentEmployee || '';
}

function fillEmployeeSelect() {
    var sel = $('log_employee'); if (!sel) return;
    sel.innerHTML = state.employees.map(function(e) { return '<option value="' + escapeHtml(e.id) + '">' + escapeHtml(e.name) + '</option>'; }).join('');
}

function fillTaskSelect() {
    var sel = $('log_task'); if (!sel) return;
    var active = state.tasks.filter(function(t) { return t.status !== 'archived'; });
    sel.innerHTML = active.map(function(t) {
        var mark = t.overdue ? ' ⚠' : '';
        return '<option value="' + escapeHtml(t.id) + '">' + escapeHtml((t.icon || '📋') + ' ' + t.name) + mark + '</option>';
    }).join('');
}

function fillSummaryFilters() {
    var selEmp = $('sumEmployeeFilter');
    if (selEmp) {
        var c1 = selEmp.value;
        selEmp.innerHTML = '<option value="">Все сотрудники</option>'
            + state.employees.map(function(e) { return '<option value="' + escapeHtml(e.id) + '">' + escapeHtml(e.name) + '</option>'; }).join('');
        selEmp.value = c1;
    }
    var selTask = $('sumTaskFilter');
    if (selTask) {
        var c2 = selTask.value;
        selTask.innerHTML = '<option value="">Все задачи</option>'
            + state.tasks.map(function(t) { return '<option value="' + escapeHtml(t.id) + '">' + escapeHtml((t.icon || '📋') + ' ' + t.name) + '</option>'; }).join('');
        selTask.value = c2;
    }
    var stDept = $('stDeptFilter');
    if (stDept) {
        var sd2 = stDept.value;
        stDept.innerHTML = '<option value="">Все отделы</option>'
            + (state.departments || []).map(function(d) { return '<option value="' + escapeHtml(d.id) + '">' + escapeHtml(d.name) + '</option>'; }).join('');
        stDept.value = sd2;
    }
    var stEmp = $('stEmployeeFilter');
    if (stEmp) {
        var se2 = stEmp.value;
        stEmp.innerHTML = '<option value="">Все сотрудники</option>'
            + state.employees.map(function(e) { return '<option value="' + escapeHtml(e.id) + '">' + escapeHtml(e.name) + '</option>'; }).join('');
        stEmp.value = se2;
    }
    var tskEmp = $('tskEmployeeFilter');
    if (tskEmp) {
        var te = tskEmp.value;
        tskEmp.innerHTML = '<option value="">Все сотрудники</option>'
            + state.employees.map(function(e) { return '<option value="' + escapeHtml(e.id) + '">' + escapeHtml(e.name) + '</option>'; }).join('');
        tskEmp.value = te;
    }
}

/* ============ Календарь ============ */
function loadCalendar() {
    var ym = state.currentYM || todayYM();
    state.currentYM = ym;
    var emp = state.currentEmployee || '';
    var dept = state.currentDepartment || '';
    return apiJson('/api/tracker/calendar?ym=' + encodeURIComponent(ym)
            + '&employee=' + encodeURIComponent(emp)
            + '&department=' + encodeURIComponent(dept))
        .then(function(d) { state.calendar = d; renderCalendar(); })
        .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

function renderCalendar() {
    var cal = state.calendar; if (!cal) return;
    $('calMonthTitle').textContent = MONTHS_RU[cal.month - 1] + ' ' + cal.year;
    var grid = $('calGrid');
    grid.querySelectorAll('.cal-cell').forEach(function(c) { c.remove(); });
    var today = todayISO();
    cal.days.forEach(function(day) {
        var cell = document.createElement('div');
        cell.className = 'cal-cell';
        if (!day.in_month) cell.classList.add('out-month');
        if (day.date === today) cell.classList.add('today');
        if (day.is_weekend && !day.is_holiday) cell.classList.add('weekend');
        if (day.is_holiday) cell.classList.add('holiday');
        if (day.total_hours > 0) cell.classList.add(hoursClass(day.total_hours));
        if (day.missing && day.missing.length) cell.classList.add('missing');
        if (day.overdue_tasks && day.overdue_tasks.length) cell.classList.add('has-overdue');
        cell.setAttribute('data-date', day.date);
        if (day.is_holiday) cell.setAttribute('title', '🎉 ' + (day.holiday_name || 'Праздник'));
        var entriesHtml = '';
        var shown = day.entries.slice(0, 3);
        if (state.calViewMode === 'tasks') {
            shown.forEach(function(en) {
                entriesHtml += '<div class="cal-entry" title="' + escapeHtml(en.task_name + (en.comment ? ' — ' + en.comment : '')) + '">'
                    + '<span>' + escapeHtml(en.task_icon) + '</span>'
                    + '<span style="overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(en.task_name) + '</span>'
                    + '<span class="entry-hours">' + formatHours(en.hours) + '</span></div>';
            });
        } else {
            var empTotals = {}, empColors = {}, empNames = {};
            day.entries.forEach(function(en) {
                empTotals[en.employee_id] = (empTotals[en.employee_id] || 0) + en.hours;
                empColors[en.employee_id] = en.employee_color;
                empNames[en.employee_id] = en.employee_name;
            });
            var empIds = Object.keys(empTotals).sort(function(a, b) { return empTotals[b] - empTotals[a]; });
            empIds.slice(0, 4).forEach(function(eid) {
                entriesHtml += '<div class="cal-entry" title="' + escapeHtml((empNames[eid] || '?') + ' — ' + formatHours(empTotals[eid])) + '">'
                    + '<span class="cal-dot" style="background:' + escapeHtml(empColors[eid]) + ';"></span>'
                    + '<span style="overflow:hidden;text-overflow:ellipsis;">' + escapeHtml(empNames[eid] || '?') + '</span>'
                    + '<span class="entry-hours">' + formatHours(empTotals[eid]) + '</span></div>';
            });
            if (empIds.length > 4) entriesHtml += '<div class="cal-more">+' + (empIds.length - 4) + ' ещё</div>';
        }
        var moreHtml = '';
        if (state.calViewMode === 'tasks' && day.entries.length > shown.length) {
            moreHtml = '<div class="cal-more">+' + (day.entries.length - shown.length) + ' ещё</div>';
        }
        var warnBadge = '';
        if (day.missing && day.missing.length) {
            warnBadge = '<span class="cal-badge-warn" title="Не заполнено: ' + day.missing.map(function(m) { return escapeHtml(m.name); }).join(', ') + '">!' + day.missing.length + '</span>';
        }
        var vacBadge = '';
        if (day.vacation && day.vacation.length) {
            vacBadge = '<span class="cal-badge-vac" title="В отпуске: ' + day.vacation.map(function(vid) {
                var e = state.employees.find(function(x) { return x.id === vid; });
                return escapeHtml(e ? e.name : '?');
            }).join(', ') + '">🏖</span>';
        }
        cell.innerHTML = warnBadge + vacBadge
            + '<div class="cal-day-head"><span class="cal-day-num">' + parseInt(day.date.split('-')[2], 10) + '</span>'
            + (day.total_hours > 0 ? '<span class="cal-day-hours">' + formatHours(day.total_hours) + '</span>' : '')
            + '</div><div class="cal-day-entries">' + entriesHtml + moreHtml + '</div>';
        cell.addEventListener('click', function() { openDayModal(day.date); });
        grid.appendChild(cell);
    });
}

function shiftMonth(delta) {
    if (!state.currentYM) state.currentYM = todayYM();
    var p = state.currentYM.split('-'); var y = parseInt(p[0], 10), m = parseInt(p[1], 10);
    m += delta;
    while (m < 1) { m += 12; y -= 1; }
    while (m > 12) { m -= 12; y += 1; }
    state.currentYM = y + '-' + String(m).padStart(2, '0');
    loadCalendar();
}
$('calPrevBtn').addEventListener('click', function() { shiftMonth(-1); });
$('calNextBtn').addEventListener('click', function() { shiftMonth(1); });
$('calTodayBtn').addEventListener('click', function() { state.currentYM = todayYM(); loadCalendar(); });
$('calEmployeeFilter').addEventListener('change', function() {
    state.currentEmployee = this.value;
    loadCalendar();
});
$('calDeptFilter').addEventListener('change', function() {
    state.currentDepartment = this.value;
    try { localStorage.setItem('tracker_calDept', this.value); } catch (e) {}
    if (state.currentEmployee) {
        var emp = state.employees.find(function(e) { return e.id === state.currentEmployee; });
        if (emp && this.value && emp.department_id !== this.value) {
            state.currentEmployee = '';
        }
    }
    fillEmployeeFilter();
    loadCalendar();
});

/* ============ Модалка дня ============ */
function openDayModal(dateStr) {
    state.currentDay = dateStr;
    $('dayModalDate').textContent = formatDateHuman(dateStr);
    var day = null;
    if (state.calendar) day = state.calendar.days.find(function(d) { return d.date === dateStr; });
    renderDayList(day ? day.entries : [], day ? day.total_hours : 0, day);
    $('dayModal').classList.add('active');
    $('dayModalLeftActions').style.display = '';
    $('dayClearBtn').style.display = '';
}

function renderDayList(entries, totalHours, day) {
    var list = $('dayList');
    var extra = '';
    if (day && day.missing && day.missing.length) extra += ' · не заполнено: ' + day.missing.length;
    $('dayModalTotal').textContent = formatHours(totalHours) + ' · ' + entries.length + ' записей' + extra;

    var missingBlock = $('dayMissingBlock');
    if (missingBlock) {
        if (day && day.missing && day.missing.length) {
            missingBlock.style.display = 'block';
            var items = day.missing.map(function(m) {
                return '<span class="dm-item">'
                    + '<span class="dm-dot" style="background:' + escapeHtml(m.color) + '; box-shadow:0 0 6px ' + escapeHtml(m.color) + ';"></span>'
                    + escapeHtml(m.name)
                    + (m.department ? ' <span style="opacity:0.7;font-size:0.72rem;">(' + escapeHtml(m.department) + ')</span>' : '')
                    + '</span>';
            }).join('');
            missingBlock.innerHTML = '<div class="dm-title">⚠ Не заполнили день (' + day.missing.length + '):</div>'
                + '<div class="dm-list">' + items + '</div>';
        } else {
            missingBlock.style.display = 'none';
            missingBlock.innerHTML = '';
        }
    }

    if (!entries.length) {
        list.innerHTML = '<div class="day-empty">Пока пусто. Нажмите «Добавить отметку».</div>';
        return;
    }
    var html = '';
    entries.forEach(function(en) { html += dayEntryCard(en, false); });
    list.innerHTML = html;
    bindDayEntryActions(list, entries);
}

function dayEntryCard(en, compact) {
    var stClass = 'day-entry';
    if (en.overdue) stClass += ' overdue';
    if (en.status) stClass += ' ' + en.status;

    var initialsHtml = initials(en.employee_name || '?');
    var avatarColor = en.employee_color || '#888888';
    var statusLabel = en.status_label || (state.statusLabels[en.status] || '');
    var statusCls = 'day-entry-status ' + statusClass(en.status);

    var metaParts = [];
    if (en.task_start_date) metaParts.push('<span class="mi">🚀 ' + escapeHtml(formatDateHuman(en.task_start_date)) + '</span>');
    if (en.task_deadline) {
        var dlCls = 'mi';
        if (en.task_deadline < todayISO() && en.status !== 'done') dlCls += ' danger';
        metaParts.push('<span class="' + dlCls + '">⏰ ' + escapeHtml(formatDateHuman(en.task_deadline)) + '</span>');
    }
    if (en.task_start_date) {
        var sd = new Date(en.task_start_date + 'T00:00:00');
        var ed = new Date((en.date || todayISO()) + 'T00:00:00');
        var daysInWork = Math.floor((ed - sd) / 86400000) + 1;
        if (daysInWork > 0) metaParts.push('<span class="mi">📆 В работе ' + daysInWork + ' дн.</span>');
    }

    var commentHtml = en.comment
        ? '<div class="day-entry-comment">' + escapeHtml(en.comment) + '</div>'
        : '';
    var linkHtml = en.link
        ? '<a class="day-entry-link" href="' + escapeHtml(en.link) + '" target="_blank" rel="noopener">🔗 ' + escapeHtml(en.link) + '</a>'
        : '';

    var compactCls = compact ? ' style="padding:8px 10px;"' : '';
    return '<div class="' + stClass + '" data-id="' + en.id + '"' + compactCls + '>'
        + '<div class="day-entry-avatar" style="background:' + escapeHtml(avatarColor) + '; box-shadow:0 0 10px ' + escapeHtml(avatarColor) + ';">'
        +     escapeHtml(initialsHtml) + '</div>'
        + '<div class="day-entry-body">'
        +     '<div class="day-entry-head">'
        +         '<span class="day-entry-task' + (en.overdue ? ' overdue' : '') + '">'
        +             escapeHtml(en.task_icon || '📋') + ' ' + escapeHtml(en.task_name || '')
        +         '</span>'
        +         '<span class="day-entry-hours">' + formatHours(en.hours) + '</span>'
        +         (statusLabel ? '<span class="' + statusCls + '">' + escapeHtml(statusLabel) + '</span>' : '')
        +     '</div>'
        +     '<div class="day-entry-employee-row">'
        +         '<span class="emp-name">' + escapeHtml(en.employee_name || '') + '</span>'
        +         (en.employee_department ? '<span class="emp-dept">🏢 ' + escapeHtml(en.employee_department) + '</span>' : '')
        +     '</div>'
        +     (metaParts.length ? '<div class="day-entry-meta">' + metaParts.join('') + '</div>' : '')
        +     commentHtml
        +     linkHtml
        + '</div>'
        + '<div class="day-entry-actions">'
        +     '<button class="dict-action-btn" data-act="edit" title="Редактировать">✏️</button>'
        +     '<button class="dict-action-btn danger" data-act="delete" title="Удалить">🗑</button>'
        + '</div>'
        + '</div>';
}

function bindDayEntryActions(list, entries) {
    list.querySelectorAll('.day-entry').forEach(function(item) {
        var id = parseInt(item.getAttribute('data-id'), 10);
        var entry = entries.find(function(x) { return x.id === id; });
        var editBtn = item.querySelector('[data-act="edit"]');
        var delBtn = item.querySelector('[data-act="delete"]');
        if (editBtn) editBtn.addEventListener('click', function() { if (entry) openLogModal(entry); });
        if (delBtn) delBtn.addEventListener('click', function() {
            if (!confirm('Удалить эту отметку?')) return;
            apiJson('/api/tracker/log/delete', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id: id }),
            }).then(function() {
                notify('✅ Удалено', 'success');
                loadCalendar().then(function() { openDayModal(state.currentDay); });
            }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
        });
    });
}

$('dayAddBtn').addEventListener('click', function() { openLogModal(null); });
$('dayTodayBtn').addEventListener('click', function() {
    var dk = todayISO();
    state.currentDay = dk;
    $('dayModal').classList.remove('active');
    state.currentYM = todayYM();
    loadCalendar().then(function() { openDayModal(dk); });
});
$('dayCopyPrevBtn').addEventListener('click', function() {
    if (!state.currentDay) return;
    var cur = new Date(state.currentDay + 'T00:00:00');
    var prev = new Date(cur.getTime() - 86400000);
    var srcISO = prev.getFullYear() + '-' + String(prev.getMonth() + 1).padStart(2, '0') + '-' + String(prev.getDate()).padStart(2, '0');
    if (!confirm('Скопировать все отметки за ' + formatDateHuman(srcISO) + ' в ' + formatDateHuman(state.currentDay) + '?')) return;
    apiJson('/api/tracker/log/copy_day', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ source: srcISO, target: state.currentDay, employee: state.currentEmployee || '' })
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        notify('✅ Скопировано: ' + d.copied, 'success');
        return loadCalendar();
    }).then(function() { openDayModal(state.currentDay); })
    .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
});
$('dayClearBtn').addEventListener('click', function() {
    if (!state.currentDay) return;
    if (!confirm('Удалить ВСЕ отметки за ' + formatDateHuman(state.currentDay) + '? Это действие нельзя отменить.')) return;
    apiJson('/api/tracker/log/clear_day', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ date: state.currentDay, employee: state.currentEmployee || '' })
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        notify('✅ Удалено: ' + d.deleted, 'success');
        return loadCalendar();
    }).then(function() { openDayModal(state.currentDay); })
    .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
});

/* ============ Модалка отметки ============ */
function openLogModal(entry) {
    entry = entry || null;
    if (!state.employees.length) { notify('❌ Сначала добавьте сотрудника', 'error'); return; }
    if (!state.tasks.length) { notify('❌ Сначала добавьте задачу', 'error'); return; }
    $('logModalTitle').textContent = entry ? 'Редактировать отметку' : 'Новая отметка';
    $('log_id').value = entry ? entry.id : '';
    var dk = state.currentDay || todayISO();
    $('log_date').value = entry ? (entry.date || dk) : dk;
    $('log_employee').value = entry ? entry.employee_id : (state.employees[0] || {}).id;
    $('log_task').value = entry ? entry.task_id : (state.tasks[0] || {}).id;
    $('log_hours').value = entry ? entry.hours : 8;
    $('log_status').value = entry ? entry.status : 'in_progress';
    $('log_comment').value = entry ? entry.comment : '';
    $('log_link').value = entry ? entry.link : '';
    updateDayHoursSummary();
    renderExistingDayEntries($('log_date').value, entry ? entry.id : null);
    $('logModal').classList.add('active');
    setTimeout(function() { $('log_hours').focus(); }, 50);
}

function updateDayHoursSummary() {
    var block = $('logDaySummary');
    if (!block) return;
    var dk = $('log_date').value;
    var empId = $('log_employee').value;
    var curId = $('log_id').value ? parseInt($('log_id').value, 10) : null;
    if (!dk || !empId) { block.style.display = 'none'; return; }

    var total = 0;
    var tasksList = [];
    if (state.calendar) {
        var day = state.calendar.days.find(function(d) { return d.date === dk; });
        if (day) {
            day.entries.forEach(function(en) {
                if (en.employee_id !== empId) return;
                if (curId && en.id === curId) return;
                total += en.hours;
                tasksList.push(en.task_icon + ' ' + en.task_name + ' (' + en.hours + 'ч)');
            });
        }
    }
    var planned = parseFloat($('log_hours').value) || 0;
    var willBe = total + planned;
    var empObj = state.employees.find(function(e) { return e.id === empId; }) || {};
    var empName = empObj.name || '';

    block.style.display = 'flex';
    block.className = 'log-day-summary';
    var txt = 'За ' + formatDateHuman(dk) + ' у ' + empName + ': уже <b>' + total + ' ч</b>';
    if (planned > 0) txt += ' + ' + planned + ' ч';
    txt += ' = <b>' + willBe + ' ч</b>';
    if (tasksList.length) {
        txt += '<div style="font-size:0.72rem; opacity:0.75; margin-top:3px;">' + tasksList.join(' · ') + '</div>';
    }
    if (willBe > 24) {
        block.classList.add('danger');
        txt = '⚠ Превышение 24 ч! ' + txt;
    } else if (willBe > 8) {
        block.classList.add('warn');
        txt = '⚠ Больше 8 ч. ' + txt;
    } else if (willBe === 8) {
        block.classList.add('ok');
        txt = '✓ Ровно 8 ч. ' + txt;
    } else {
        block.classList.add('warn');
    }
    block.innerHTML = '<span class="lbl">' + txt + '</span>';
}

function renderExistingDayEntries(dateStr, excludeId) {
    var wrap = $('logDayExisting'); var list = $('logDayExistingList');
    if (!wrap || !list) return;
    var entries = [];
    if (state.calendar) {
        var day = state.calendar.days.find(function(d) { return d.date === dateStr; });
        if (day) entries = day.entries;
    }
    entries = entries.filter(function(en) { return en.id !== excludeId; });
    if (!entries.length) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    var html = '';
    entries.forEach(function(en) { html += dayEntryCard(en, true); });
    list.innerHTML = html;
}

function saveLog() {
    var payload = {
        id: $('log_id').value || null,
        employee_id: $('log_employee').value,
        task_id: $('log_task').value,
        date: $('log_date').value,
        hours: parseFloat($('log_hours').value) || 0,
        status: $('log_status').value,
        comment: $('log_comment').value.trim(),
        link: $('log_link').value.trim(),
    };
    if (!payload.employee_id) { notify('❌ Выберите сотрудника', 'error'); return; }
    if (!payload.task_id) { notify('❌ Выберите задачу', 'error'); return; }
    if (!payload.date) { notify('❌ Некорректная дата', 'error'); return; }
    apiJson('/api/tracker/log/save', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        notify('✅ Сохранено', 'success');
        $('logModal').classList.remove('active');
        return loadCalendar();
    }).then(function() { if (state.currentDay) openDayModal(state.currentDay); })
    .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}
$('log_date').addEventListener('change', function() {
    updateDayHoursSummary();
    renderExistingDayEntries(this.value, $('log_id').value ? parseInt($('log_id').value, 10) : null);
});
$('log_employee').addEventListener('change', updateDayHoursSummary);
$('log_hours').addEventListener('input', updateDayHoursSummary);
$('saveLogBtn').addEventListener('click', saveLog);
$('log_comment').addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); saveLog(); }
});

/* ============ Отделы ============ */
function openDepartmentModal(dep) {
    dep = dep || null;
    $('departmentModalTitle').textContent = dep ? 'Редактировать отдел' : 'Новый отдел';
    $('dep_id').value = dep ? dep.id : '';
    $('dep_name').value = dep ? dep.name : '';
    $('dep_color').value = (dep && dep.color) || '#00897b';
    $('departmentModal').classList.add('active');
    setTimeout(function() { $('dep_name').focus(); }, 50);
}
function saveDepartment() {
    var name = $('dep_name').value.trim();
    if (!name) { notify('❌ Укажите название', 'error'); return; }
    var payload = { id: $('dep_id').value || '', name: name, color: $('dep_color').value };
    apiJson('/api/tracker/department/save', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload),
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        notify('✅ Сохранено', 'success');
        $('departmentModal').classList.remove('active');
        return loadState();
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}
function deleteDepartment(id) {
    var dep = (state.departments || []).find(function(x) { return x.id === id; });
    if (!dep) return;
    if (!confirm('Удалить отдел «' + dep.name + '»?\nСотрудники останутся без отдела, задачи потеряют привязку.')) return;
    apiJson('/api/tracker/department/delete', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id }),
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        notify('✅ Удалено (' + d.employees_affected + ' сотр., ' + (d.tasks_affected || 0) + ' задач)', 'success');
        return loadState();
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

/* ============ Сотрудник ============ */
var _vacDraftEmpId = null;
function openEmployeeModal(emp) {
    emp = emp || null;
    _vacDraftEmpId = emp ? emp.id : null;
    $('employeeModalTitle').textContent = emp ? 'Редактировать сотрудника' : 'Новый сотрудник';
    $('emp_id').value = emp ? emp.id : '';
    $('emp_name').value = emp ? emp.name : '';
    var color = (emp && emp.color) || '#00897b';
    $('emp_color').value = color;
    $('emp_role').value = (emp && emp.role) || '';
    var deptSel = $('emp_department_select');
    if (deptSel) {
        deptSel.innerHTML = '<option value="">— не указан —</option>'
            + (state.departments || []).map(function(d) {
                return '<option value="' + escapeHtml(d.id) + '">' + escapeHtml(d.name) + '</option>';
            }).join('');
        deptSel.value = (emp && emp.department_id) || '';
    }
    var wrap = $('empPalette');
    if (wrap) wrap.querySelectorAll('.palette-dot').forEach(function(d) {
        d.classList.toggle('active', d.getAttribute('data-color') === color);
    });
    $('vacSection').style.display = emp ? '' : 'none';
    renderVacations(emp);
    $('vac_from').value = ''; $('vac_to').value = ''; $('vac_comment').value = '';
    $('employeeModal').classList.add('active');
    setTimeout(function() { $('emp_name').focus(); }, 50);
}
function renderVacations(emp) {
    var list = $('vacList'); if (!list) return;
    var vac = (emp && emp.vacations) || [];
    if (!vac.length) { list.innerHTML = '<div class="vac-empty">Пока нет периодов отпуска</div>'; return; }
    var html = '';
    vac.forEach(function(v, i) {
        html += '<div class="vac-item"><div class="vac-item-body">'
            + '<div class="vac-item-dates">🏖 ' + escapeHtml(formatDateHuman(v.from || '')) + ' — ' + escapeHtml(formatDateHuman(v.to || '')) + '</div>'
            + (v.comment ? '<div class="vac-item-comment">' + escapeHtml(v.comment) + '</div>' : '')
            + '</div><button class="dict-action-btn danger" data-idx="' + i + '" type="button">🗑</button></div>';
    });
    list.innerHTML = html;
    list.querySelectorAll('.dict-action-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var idx = parseInt(this.getAttribute('data-idx'), 10);
            if (!_vacDraftEmpId) return;
            apiJson('/api/tracker/employee/vacation/delete', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ employee_id: _vacDraftEmpId, index: idx })
            }).then(function(d) { if (!d.success) throw new Error(d.error || 'Ошибка'); return loadState(); })
            .then(function() {
                var emp2 = state.employees.find(function(x) { return x.id === _vacDraftEmpId; });
                renderVacations(emp2);
            })
            .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
        });
    });
}
$('vacAddBtn').addEventListener('click', function() {
    if (!_vacDraftEmpId) return;
    var from = $('vac_from').value, to = $('vac_to').value, comment = $('vac_comment').value.trim();
    if (!from || !to) { notify('❌ Укажите даты', 'error'); return; }
    apiJson('/api/tracker/employee/vacation/add', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ employee_id: _vacDraftEmpId, from: from, to: to, comment: comment })
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        $('vac_from').value = ''; $('vac_to').value = ''; $('vac_comment').value = '';
        return loadState();
    }).then(function() {
        var emp2 = state.employees.find(function(x) { return x.id === _vacDraftEmpId; });
        renderVacations(emp2);
    })
    .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
});
function saveEmployee() {
    var name = $('emp_name').value.trim();
    if (!name) { notify('❌ Укажите имя', 'error'); return; }
    var deptSel = $('emp_department_select');
    var payload = {
        id: $('emp_id').value || '',
        name: name,
        color: $('emp_color').value,
        role: $('emp_role').value.trim(),
        department_id: deptSel ? (deptSel.value || '') : '',
    };
    apiJson('/api/tracker/employee/save', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        $('employeeModal').classList.remove('active');
        return loadState().then(loadCalendar);
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}
function deleteEmployee(id) {
    var emp = state.employees.find(function(x) { return x.id === id; });
    if (!emp) return;
    if (!confirm('Удалить сотрудника «' + emp.name + '»?\n\nОтметки останутся, но перестанут быть привязаны.')) return;
    apiJson('/api/tracker/employee/delete', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id })
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        return loadState().then(loadCalendar);
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

/* ============ Задача: мультиотделы ============ */
function renderTaskDepartmentsList(selectedIds) {
    var list = $('taskDepartmentsList'); if (!list) return;
    selectedIds = selectedIds || [];
    var deps = state.departments || [];
    if (!deps.length) {
        list.innerHTML = '<div class="dict-empty" style="padding:10px;">Нет отделов — создайте их в Справочниках</div>';
        return;
    }
    var html = '';
    deps.forEach(function(d) {
        var checked = selectedIds.indexOf(d.id) !== -1 ? ' checked' : '';
        html += '<label class="dept-multi-item"><input type="checkbox" value="' + escapeHtml(d.id) + '"' + checked + '>'
            + '<span class="dept-multi-dot" style="background:' + escapeHtml(d.color || '#7a9ab5') + ';"></span>'
            + '<span>' + escapeHtml(d.name) + '</span></label>';
    });
    list.innerHTML = html;
    list.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
        cb.addEventListener('change', function() {
            renderAssigneesList(getSelectedAssignees(), getSelectedTaskDepartments());
        });
    });
}
function getSelectedTaskDepartments() {
    var list = $('taskDepartmentsList'); if (!list) return [];
    var out = [];
    list.querySelectorAll('input[type="checkbox"]:checked').forEach(function(cb) { out.push(cb.value); });
    return out;
}

function renderAssigneesList(selectedIds, deptIds) {
    var list = $('taskAssigneesList'); if (!list) return;
    var hint = $('taskAssigneesHint');
    if (!state.employees.length) {
        list.innerHTML = '<div class="dict-empty" style="padding:10px;">Сначала добавьте сотрудников</div>';
        if (hint) hint.textContent = '';
        return;
    }
    selectedIds = selectedIds || [];
    deptIds = deptIds || [];
    var emps = state.employees;

    if (deptIds.length) {
        emps = emps.filter(function(e) { return deptIds.indexOf(e.department_id) !== -1; });
        if (hint) hint.textContent = 'Показаны сотрудники из выбранных отделов (' + deptIds.length + ')';
    } else {
        if (hint) hint.textContent = 'Отметьте отделы выше, чтобы сузить список';
    }
    if (!emps.length) {
        list.innerHTML = '<div class="dict-empty" style="padding:10px;">В выбранных отделах нет сотрудников</div>';
        return;
    }
    var html = '';
    emps.forEach(function(e) {
        var checked = selectedIds.indexOf(e.id) !== -1 ? ' checked' : '';
        html += '<label class="assignees-item"><input type="checkbox" value="' + escapeHtml(e.id) + '"' + checked + '>'
            + '<span class="assignees-dot" style="background:' + escapeHtml(e.color || '#888') + ';"></span>'
            + '<span>' + escapeHtml(e.name) + '</span></label>';
    });
    list.innerHTML = html;
}
function getSelectedAssignees() {
    var list = $('taskAssigneesList'); if (!list) return [];
    var out = [];
    list.querySelectorAll('input[type="checkbox"]:checked').forEach(function(cb) { out.push(cb.value); });
    return out;
}

function openTaskModal(task) {
    task = task || null;
    $('taskModalTitle').textContent = task ? 'Редактировать задачу' : 'Новая задача';
    $('task_id').value = task ? task.id : '';
    $('task_icon').value = (task && task.icon) || '🚀';
    $('taskIconPickBtn').textContent = (task && task.icon) || '🚀';
    $('task_name').value = task ? task.name : '';
    $('task_description').value = (task && task.description) || '';
    $('task_status').value = (task && task.status) || 'active';
    var sd = $('task_start_date');
    if (sd) sd.value = (task && task.start_date) || '';
    $('task_deadline').value = (task && task.deadline) || '';
    $('task_folder').value = (task && task.folder) || '';
    $('task_order_ref').value = (task && task.order_ref) || '';
    $('task_tags').value = (task && task.tags) ? task.tags.join(', ') : '';
    var depIds = (task && task.department_ids) ? task.department_ids.slice() : [];
    renderTaskDepartmentsList(depIds);
    renderAssigneesList((task && task.assignees) || [], depIds);
    $('taskModal').classList.add('active');
    setTimeout(function() { $('task_name').focus(); }, 50);
}
function saveTask() {
    var name = $('task_name').value.trim();
    if (!name) { notify('❌ Укажите название', 'error'); return; }
    var tagsRaw = $('task_tags').value.trim();
    var tags = tagsRaw ? tagsRaw.split(',').map(function(t) { return t.trim(); }).filter(Boolean) : [];
    var sd = $('task_start_date');
    var payload = {
        id: $('task_id').value || '',
        name: name,
        icon: $('task_icon').value.trim() || '🚀',
        description: $('task_description').value.trim(),
        status: $('task_status').value,
        start_date: sd ? sd.value.trim() : '',
        deadline: $('task_deadline').value.trim(),
        folder: $('task_folder').value.trim(),
        order_ref: $('task_order_ref').value.trim(),
        tags: tags,
        assignees: getSelectedAssignees(),
        department_ids: getSelectedTaskDepartments(),
    };
    apiJson('/api/tracker/task/save', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        $('taskModal').classList.remove('active');
        return loadState().then(loadCalendar);
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}
function deleteTask(id) {
    var task = state.tasks.find(function(x) { return x.id === id; });
    if (!task) return;
    if (!confirm('Удалить задачу «' + task.name + '»?\n\nОтметки останутся, но перестанут быть привязаны.')) return;
    apiJson('/api/tracker/task/delete', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: id })
    }).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        return loadState().then(loadCalendar);
    }).catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}
$('taskIconPickBtn').addEventListener('click', function() { $('emojiModal').classList.add('active'); });
$('task_icon').addEventListener('input', function() { $('taskIconPickBtn').textContent = this.value.trim() || '🚀'; });

/* ============ Свод ============ */
function loadSummary() {
    var from = $('sumDateFrom').value, to = $('sumDateTo').value;
    if (!from) { from = firstOfMonthISO(todayYM()); $('sumDateFrom').value = from; }
    if (!to) { to = todayISO(); $('sumDateTo').value = to; }
    var emp = $('sumEmployeeFilter').value || '';
    var task = $('sumTaskFilter').value || '';
    var dept = $('sumDeptFilter') ? ($('sumDeptFilter').value || '') : '';
    var view = state.sumViewMode || 'grid';
    var wrap = $('sumWrap');
    wrap.innerHTML = '<div class="sum-empty">Загрузка...</div>';
    var qs = '?from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to)
        + '&employee=' + encodeURIComponent(emp) + '&task=' + encodeURIComponent(task)
        + '&department=' + encodeURIComponent(dept);
    var url = (view === 'grid') ? ('/api/tracker/summary_grid' + qs) : ('/api/tracker/summary' + qs + '&view=' + encodeURIComponent(view));
    apiJson(url).then(function(d) {
        state.summary = d;
        state.summaryIsGrid = (view === 'grid');
        if (view === 'grid') renderSummaryGrid();
        else renderSummary();
    }).catch(function(err) {
        wrap.innerHTML = '<div class="sum-empty" style="color:#e74c3c;">❌ ' + escapeHtml(err.message || 'Ошибка') + '</div>';
    });
}

function _summaryLegendHtml() {
    return '<div class="grid-legend">'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: rgba(46,204,113,0.24);"></span>✅ Готово</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: rgba(52,152,219,0.24);"></span>🔵 В работе</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: rgba(149,165,166,0.24);"></span>📝 Запланировано</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: rgba(231,76,60,0.24);"></span>🔴 Заблокировано</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: repeating-linear-gradient(45deg, rgba(52,152,219,0.15) 0, rgba(52,152,219,0.15) 4px, rgba(52,152,219,0.30) 4px, rgba(52,152,219,0.30) 8px);"></span>🏖 Отпуск</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: var(--trk-weekend-bg);"></span>Выходной</span>'
        + '<span class="grid-legend-item"><span class="grid-legend-swatch" style="background: var(--trk-holiday-bg);"></span>🎉 Праздник</span>'
        + '<span style="margin-left:auto; opacity:0.75;">Клик по сотруднику / задаче — карточка с mini-heatmap</span>'
        + '</div>';
}

function _summaryExtrasHtml(d) {
    var topHtml = '';
    var vacHtml = '';

    if (d.top_tasks && d.top_tasks.length) {
        topHtml = '<div class="sum-extra-block">'
            + '<div class="sum-extra-title">🏆 Топ задач за период</div>';
        d.top_tasks.forEach(function(t) {
            topHtml += '<div class="sum-top-task">'
                + '<span>' + escapeHtml(t.task_icon) + '</span>'
                + '<span class="name">' + escapeHtml(t.task_name) + '</span>'
                + '<span class="hours">' + formatHours(t.hours) + '</span>'
                + '</div>';
        });
        topHtml += '</div>';
    }

    if (d.vacations && d.vacations.length) {
        vacHtml = '<div class="sum-extra-block">'
            + '<div class="sum-extra-title">🏖 Отпуска в периоде</div>';
        d.vacations.forEach(function(v) {
            vacHtml += '<div class="sum-vac-row">'
                + '<span class="emp-dot" style="display:inline-block; width:10px; height:10px; border-radius:50%; background:' + escapeHtml(v.employee_color) + '; box-shadow:0 0 6px ' + escapeHtml(v.employee_color) + ';"></span>'
                + '<span style="flex:1;">' + escapeHtml(v.employee_name) + '</span>'
                + '<span class="dates">' + escapeHtml(formatDateShort(v.from)) + ' — ' + escapeHtml(formatDateShort(v.to)) + '</span>'
                + '</div>';
        });
        vacHtml += '</div>';
    }

    if (!topHtml && !vacHtml) return '';

    return '<div class="sum-extra-section">'
        + '<div class="sum-extra-section-title"><span>📌</span><span>Дополнительная статистика</span></div>'
        + '<div class="sum-extras">'
        + (topHtml || '<div></div>')
        + (vacHtml || '<div></div>')
        + '</div>'
        + '</div>';
}

function renderSummaryGrid() {
    var d = state.summary;
    var wrap = $('sumWrap'), extrasWrap = $('sumExtras');
    if (!d || !d.rows.length) {
        wrap.innerHTML = '<div class="sum-empty">Нет данных за выбранный период.</div>';
        extrasWrap.innerHTML = '';
        return;
    }
    var days = d.days;
    var dm = d.day_meta || {};
    var todayStr = todayISO();

    var head = '<tr><th class="emp-col">Сотрудник</th><th class="task-col">Задача</th>';
    days.forEach(function(dk) {
        var m = dm[dk] || {};
        var cls = [];
        if (m.is_weekend) cls.push('weekend-col');
        if (m.is_holiday) cls.push('holiday-col');
        if (m.is_today || dk === todayStr) cls.push('today-col');
        var titleParts = [dk];
        if (m.is_holiday) titleParts.push('🎉 ' + (m.holiday_name || 'Праздник'));
        else if (m.is_weekend) titleParts.push('Выходной');
        head += '<th' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + ' title="' + escapeHtml(titleParts.join(' · ')) + '">'
            + escapeHtml(formatDateShort(dk))
            + '</th>';
    });
    head += '<th class="total-col">Итого</th></tr>';

    var body = '';
    d.rows.forEach(function(r, ri) {
        var tasks = r.tasks || [];
        var vacSet = {};
        (r.vacation_days || []).forEach(function(dk) { vacSet[dk] = true; });
        var empCellExtra = (r.vacation_days && r.vacation_days.length)
            ? ' <span class="emp-vac-badge">🏖 ' + r.vacation_days.length + '</span>' : '';
        var deptHtml = r.employee_department
            ? '<div class="emp-dept">🏢 ' + escapeHtml(r.employee_department) + '</div>' : '';

        if (!tasks.length) {
            body += '<tr>'
                + '<td class="emp-cell" data-emp="' + escapeHtml(r.employee_id) + '">'
                + '<span class="emp-dot" style="background:' + escapeHtml(r.employee_color) + '; box-shadow:0 0 6px ' + escapeHtml(r.employee_color) + ';"></span>'
                + escapeHtml(r.employee_name) + empCellExtra + deptHtml + '</td>'
                + '<td class="task-cell empty">— нет задач —</td>'
                + days.map(function(dk) {
                    var m = dm[dk] || {};
                    var cls = ['empty-cell'];
                    if (vacSet[dk]) cls.push('vacation-day');
                    else if (m.is_holiday) cls.push('holiday-day');
                    else if (m.is_weekend) cls.push('weekend-day');
                    var tip = dk + (m.is_holiday ? ' — 🎉 ' + (m.holiday_name || 'Праздник') : (m.is_weekend ? ' — выходной' : ''));
                    var content = vacSet[dk] ? '🏖' : '·';
                    return '<td class="' + cls.join(' ') + '" title="' + escapeHtml(tip) + '">' + content + '</td>';
                }).join('')
                + '<td class="total-cell">0 ч</td></tr>';
            return;
        }
        var rowCount = tasks.length;
        tasks.forEach(function(t, ti) {
            body += '<tr>';
            if (ti === 0) {
                body += '<td class="emp-cell" rowspan="' + rowCount + '" data-emp="' + escapeHtml(r.employee_id) + '">'
                    + '<span class="emp-dot" style="background:' + escapeHtml(r.employee_color) + '; box-shadow:0 0 6px ' + escapeHtml(r.employee_color) + ';"></span>'
                    + escapeHtml(r.employee_name) + empCellExtra + deptHtml + '</td>';
            }
            var periodLine = '';
            if (t.start_date || t.deadline) {
                periodLine = '<span class="task-period">'
                    + (t.start_date ? '🚀 ' + escapeHtml(formatDateShort(t.start_date)) : '')
                    + (t.start_date && t.deadline ? ' — ' : '')
                    + (t.deadline ? '⏰ ' + escapeHtml(formatDateShort(t.deadline)) : '')
                    + (t.overdue ? ' ⚠' : '')
                    + '</span>';
            }
            var taskTip = t.task_name;
            if (t.start_date) taskTip += '\n🚀 Начало: ' + t.start_date;
            if (t.deadline) taskTip += '\n⏰ Дедлайн: ' + t.deadline;
            if (t.overdue) taskTip += '\n⚠ Просрочено';
            body += '<td class="task-cell' + (t.overdue ? ' overdue' : '') + '" data-task="' + escapeHtml(t.task_id) + '">'
                + '<span class="task-ico">' + escapeHtml(t.task_icon) + '</span>'
                + '<span class="task-name-str' + (t.overdue ? ' overdue' : '') + '" title="' + escapeHtml(taskTip) + '">'
                + escapeHtml(t.task_name) + (t.overdue ? ' ⚠' : '') + '</span>'
                + periodLine
                + '</td>';
            days.forEach(function(dk) {
                var m = dm[dk] || {};
                var cell = t.cells[dk];
                if (!cell || !cell.hours) {
                    var cls = [];
                    if (vacSet[dk]) cls.push('vacation-day');
                    else if (m.is_holiday) cls.push('holiday-day');
                    else if (m.is_weekend) cls.push('weekend-day');
                    else cls.push('empty-cell');
                    var tip = dk + (m.is_holiday ? ' — 🎉 ' + (m.holiday_name || 'Праздник') : (m.is_weekend ? ' — выходной' : ''));
                    var content = vacSet[dk] ? '🏖' : '·';
                    body += '<td class="day-cell ' + cls.join(' ') + '" title="' + escapeHtml(tip) + '">' + content + '</td>';
                    return;
                }
                var extraCls = '';
                if (vacSet[dk]) extraCls = ' vacation-day';
                else if (m.is_holiday) extraCls = ' holiday-day';
                else if (m.is_weekend) extraCls = ' weekend-day';
                var tip = formatHours(cell.hours) + ' · ' + (cell.status_label || '');
                if (m.is_holiday) tip += ' · 🎉 ' + (m.holiday_name || 'Праздник');
                else if (m.is_weekend) tip += ' · выходной';
                cell.entries.forEach(function(e) { if (e.comment) tip += '\n' + e.comment; });
                body += '<td class="day-cell status-' + escapeHtml(cell.status) + extraCls + '" '
                    + 'data-emp="' + escapeHtml(r.employee_id) + '" data-task="' + escapeHtml(t.task_id) + '" data-date="' + escapeHtml(dk) + '" '
                    + 'title="' + escapeHtml(tip) + '">' + shortHours(cell.hours) + '</td>';
            });
            body += '<td class="total-cell">' + (t.total_hours ? formatHours(t.total_hours) : '—') + '</td>';
            body += '</tr>';
        });
        if (ri < d.rows.length - 1) {
            body += '<tr class="emp-sep"><td colspan="' + (2 + days.length + 1) + '"></td></tr>';
        }
    });

    var totalsRow = '';
    if (state.sumShowDayTotals) {
        totalsRow = '<tr class="day-totals-row"><td class="emp-cell" colspan="2">Итого за день</td>';
        days.forEach(function(dk) {
            var v = d.day_totals[dk] || 0;
            var m = dm[dk] || {};
            var cls = ['day-cell'];
            if (m.is_holiday) cls.push('holiday-day');
            else if (m.is_weekend) cls.push('weekend-day');
            totalsRow += '<td class="' + cls.join(' ') + '">' + (v > 0 ? shortHours(v) : '—') + '</td>';
        });
        totalsRow += '<td class="total-cell">' + formatHours(d.grand_total) + '</td></tr>';
    }

    wrap.innerHTML = '<table class="sum-table grid-table"><thead>' + head + '</thead><tbody>' + body + totalsRow + '</tbody></table>';

    wrap.querySelectorAll('td.day-cell[data-emp]').forEach(function(td) {
        td.addEventListener('click', function(e) {
            e.stopPropagation();
            openGridCellDetails(this.getAttribute('data-emp'), this.getAttribute('data-task'), this.getAttribute('data-date'));
        });
    });
    wrap.querySelectorAll('td.task-cell[data-task]').forEach(function(td) {
        td.style.cursor = 'pointer';
        td.addEventListener('click', function() { openTaskCardModal(this.getAttribute('data-task')); });
    });
    wrap.querySelectorAll('td.emp-cell[data-emp]').forEach(function(td) {
        td.style.cursor = 'pointer';
        td.addEventListener('click', function() { openEmpCardModal(this.getAttribute('data-emp')); });
    });

    extrasWrap.innerHTML = _summaryLegendHtml() + _summaryExtrasHtml(d);
}

function openGridCellDetails(empId, taskId, dateStr) {
    var d = state.summary;
    if (!d || !d.rows) return;
    var row = d.rows.find(function(r) { return r.employee_id === empId; });
    if (!row) return;
    var t = (row.tasks || []).find(function(x) { return x.task_id === taskId; });
    if (!t) return;
    var cell = t.cells[dateStr];
    if (!cell) return;

    $('dayModalDate').textContent = formatDateHuman(dateStr) + ' — ' + row.employee_name;
    $('dayModalTotal').textContent = formatHours(cell.hours) + ' · ' + (cell.status_label || '');
    var html = '';
    cell.entries.forEach(function(e) {
        var en = {
            id: e.id,
            task_id: taskId,
            task_name: t.task_name,
            task_icon: t.task_icon,
            hours: e.hours,
            comment: e.comment,
            status: e.status,
            status_label: e.status_label,
            link: e.link,
            employee_name: row.employee_name,
            employee_color: row.employee_color,
            employee_department: row.employee_department || '',
            date: dateStr,
            task_start_date: t.start_date || '',
            task_deadline: t.deadline || '',
            overdue: t.overdue,
        };
        html += dayEntryCard(en, false);
    });
    $('dayList').innerHTML = html;
    $('dayModalLeftActions').style.display = 'none';
    $('dayClearBtn').style.display = 'none';
    $('dayModal').classList.add('active');
}

function renderSummary() {
    var d = state.summary;
    var wrap = $('sumWrap'), extrasWrap = $('sumExtras');
    if (!d || !d.rows.length) {
        wrap.innerHTML = '<div class="sum-empty">Нет данных за выбранный период.</div>';
        extrasWrap.innerHTML = '';
        return;
    }
    var days = d.days;
    var dm = d.day_meta || {};
    var todayStr = todayISO();
    var view = state.sumViewMode || 'compact';
    var cellClass = view === 'full' ? 'sum-cell-full' : 'sum-cell-compact';

    var head = '<tr><th class="emp-col">Сотрудник</th>';
    days.forEach(function(dk) {
        var m = dm[dk] || {};
        var cls = [];
        if (m.is_weekend) cls.push('weekend-col');
        if (m.is_holiday) cls.push('holiday-col');
        if (m.is_today || dk === todayStr) cls.push('today-col');
        head += '<th' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + ' title="' + escapeHtml(dk) + '">' + escapeHtml(formatDateShort(dk)) + '</th>';
    });
    head += '<th class="total-col">Итого</th></tr>';
    var rowsHtml = '';
    d.rows.forEach(function(r) {
        rowsHtml += '<tr><td class="emp-cell"><span class="emp-dot" style="background:' + escapeHtml(r.employee_color) + '; box-shadow:0 0 6px ' + escapeHtml(r.employee_color) + ';"></span>' + escapeHtml(r.employee_name) + '</td>';
        days.forEach(function(dk) {
            var cell = r.cells[dk];
            var m = dm[dk] || {};
            var extraCls = '';
            if (m.is_holiday) extraCls = ' holiday-day';
            else if (m.is_weekend) extraCls = ' weekend-day';
            if (!cell || !cell.hours) {
                rowsHtml += '<td class="empty-cell' + extraCls + '">—</td>';
                return;
            }
            var inner = '';
            if (view === 'full') {
                inner += '<div class="sum-hours-main">' + formatHours(cell.hours) + '</div>';
                cell.tasks.forEach(function(t) {
                    var stCls = t.entries.length ? t.entries[0].status : 'done';
                    var overdueCls = t.overdue ? ' overdue' : '';
                    inner += '<div class="sum-task-row ' + stCls + overdueCls + '" title="' + escapeHtml(t.task_name + ' · ' + formatHours(t.hours)) + '">'
                        + '<span class="status-dot"></span><span>' + escapeHtml(t.task_icon) + '</span>'
                        + '<span class="task-name">' + escapeHtml(t.task_name) + '</span>'
                        + '<span class="task-hours">' + t.hours + '</span></div>';
                });
            } else {
                inner += '<div class="sum-hours-main">' + formatHours(cell.hours) + '</div>';
                inner += '<div class="sum-tasks-count">' + cell.tasks.length + ' задач' + (cell.tasks.length ? ' · ' + cell.tasks.map(function(t) { return t.task_icon; }).slice(0, 4).join(' ') : '') + '</div>';
            }
            rowsHtml += '<td class="has-data ' + cellClass + extraCls + '" data-emp="' + escapeHtml(r.employee_id) + '" data-date="' + escapeHtml(dk) + '">' + inner + '</td>';
        });
        rowsHtml += '<td class="total-cell">' + formatHours(r.total_hours) + '</td></tr>';
    });
    var totalsRow = '<tr class="day-totals-row"><td class="emp-cell">Итого за день</td>';
    days.forEach(function(dk) {
        var v = d.day_totals[dk] || 0;
        var m = dm[dk] || {};
        var cls = [];
        if (m.is_holiday) cls.push('holiday-day');
        else if (m.is_weekend) cls.push('weekend-day');
        totalsRow += '<td' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + '>' + (v > 0 ? formatHours(v) : '—') + '</td>';
    });
    totalsRow += '<td class="total-cell">' + formatHours(d.grand_total) + '</td></tr>';
    wrap.innerHTML = '<table class="sum-table"><thead>' + head + '</thead><tbody>' + rowsHtml + totalsRow + '</tbody></table>';
    wrap.querySelectorAll('td.has-data').forEach(function(td) {
        td.addEventListener('click', function() { openSummaryCell(this.getAttribute('data-emp'), this.getAttribute('data-date')); });
    });
    extrasWrap.innerHTML = _summaryLegendHtml() + _summaryExtrasHtml(d);
}

function openSummaryCell(empId, dateStr) {
    var d = state.summary; if (!d) return;
    var row = d.rows.find(function(r) { return r.employee_id === empId; }); if (!row) return;
    var cell = row.cells[dateStr]; if (!cell) return;
    $('dayModalDate').textContent = formatDateHuman(dateStr) + ' — ' + row.employee_name;
    $('dayModalTotal').textContent = formatHours(cell.hours) + ' · ' + cell.tasks.length + ' задач';
    var html = '';
    cell.tasks.forEach(function(t) {
        t.entries.forEach(function(e) {
            var en = {
                id: e.id,
                task_id: t.task_id,
                task_name: t.task_name,
                task_icon: t.task_icon,
                hours: e.hours,
                comment: e.comment,
                status: e.status,
                status_label: e.status_label,
                link: e.link,
                employee_name: row.employee_name,
                employee_color: row.employee_color,
                employee_department: row.employee_department || '',
                date: dateStr,
                task_start_date: '',
                task_deadline: '',
                overdue: t.overdue,
            };
            html += dayEntryCard(en, false);
        });
    });
    $('dayList').innerHTML = html;
    $('dayModalLeftActions').style.display = 'none';
    $('dayClearBtn').style.display = 'none';
    $('dayModal').classList.add('active');
}

/* ============ Карточка сотрудника ============ */
function openEmpCardModal(empId) {
    var from = $('sumDateFrom') ? $('sumDateFrom').value : '';
    var to = $('sumDateTo') ? $('sumDateTo').value : '';
    if (!from || !to) {
        var t = new Date();
        from = firstOfMonthISOFromDate(t);
        to = todayISO();
    }
    var qs = '?employee=' + encodeURIComponent(empId)
        + '&from=' + encodeURIComponent(from)
        + '&to=' + encodeURIComponent(to);
    apiJson('/api/tracker/employee/card' + qs)
        .then(function(d) {
            if (!d.success) throw new Error(d.error || 'Ошибка');
            renderEmpCardModal(d);
            $('empCardModal').classList.add('active');
        })
        .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

function _coverageBar(coverage) {
    var cls = 'err';
    if (coverage >= 70) cls = 'ok';
    else if (coverage >= 40) cls = 'warn';
    var w = Math.max(0, Math.min(coverage, 100));
    return '<div class="coverage-bar">'
        + '<span class="coverage-bar-label">📊 Покрытие:</span>'
        + '<div class="coverage-bar-track"><div class="coverage-bar-fill ' + cls + '" style="width:' + w + '%;"></div></div>'
        + '<span class="coverage-bar-label">' + coverage + '%</span>'
        + '</div>';
}

function renderEmpCardModal(d) {
    var emp = d.employee || {};
    var color = emp.color || '#00897b';
    var periodLabel = d.from ? (formatDateHuman(d.from) + ' — ' + formatDateHuman(d.to)) : '';
    var deptLabel = emp.department ? ' · 🏢 ' + escapeHtml(emp.department) : '';
    $('empCardHead').innerHTML = '<div class="emp-day-avatar" style="background:' + escapeHtml(color) + '; box-shadow: 0 0 12px ' + escapeHtml(color) + ';">'
        + escapeHtml(initials(emp.name)) + '</div>'
        + '<div class="emp-day-info"><div class="emp-day-name">' + escapeHtml(emp.name || '—') + '</div>'
        + '<div class="emp-day-role">' + escapeHtml(emp.role || '') + deptLabel + ' · ' + escapeHtml(periodLabel) + '</div></div>'
        + '<div class="emp-day-stats">'
        + '<div class="emp-day-stat"><span class="val">' + formatHours(d.total_hours) + '</span><span class="lbl">часов</span></div>'
        + '<div class="emp-day-stat"><span class="val">' + d.tasks.length + '</span><span class="lbl">задач</span></div>'
        + '</div>';

    $('empCardHeatmap').innerHTML = renderMiniCells(d.cells);

    var list = $('empCardTasks');
    if (!d.tasks.length) {
        list.innerHTML = '<div class="day-empty">За этот период отметок нет.</div>';
        return;
    }
    var html = '';
    d.tasks.forEach(function(t) {
        var statusLabel = state.taskStatusLabels[t.status] || t.status || '';
        html += '<div class="task-card-row' + (t.overdue ? ' overdue' : '') + '">'
            + '<div class="task-card-row-head">'
            +   '<span class="task-card-row-title' + (t.overdue ? ' overdue' : '') + '">'
            +     escapeHtml(t.task_icon) + ' ' + escapeHtml(t.task_name) + '</span>'
            +   '<span class="day-entry-hours">' + formatHours(t.total_hours) + '</span>'
            +   (statusLabel ? '<span class="day-entry-status status-' + escapeHtml(t.status) + '">' + escapeHtml(statusLabel) + '</span>' : '')
            + '</div>'
            + '<div class="task-card-row-meta">'
            +   (t.start_date ? '<span>🚀 ' + escapeHtml(formatDateHuman(t.start_date)) + '</span>' : '')
            +   (t.deadline ? '<span>⏰ ' + escapeHtml(formatDateHuman(t.deadline)) + '</span>' : '')
            +   '<span>📅 ' + t.active_days + ' из ' + t.possible_days + ' раб. дней</span>'
            + '</div>'
            + _coverageBar(t.coverage)
            + '<div class="mini-heatmap">' + renderMiniCells(t.cells) + '</div>'
            + '</div>';
    });
    list.innerHTML = html;
}

/* ============ Мини-heatmap ============ */
function renderMiniCells(cells) {
    if (!cells || !cells.length) return '';
    var out = '';
    cells.forEach(function(c) {
        var cls = 'mini-cell';
        var title = c.date;
        var content = '';
        if (c.is_vacation) {
            cls += ' vacation';
            content = '🏖';
            title += ' — отпуск';
        } else if (c.hours > 0) {
            var col = cellLightGreen(c.hours);
            content = '<span class="mini-h">' + shortHours(c.hours) + '</span>';
            title += ' — ' + formatHours(c.hours);
            if (c.is_today) cls += ' today';
            out += '<div class="' + cls + '" style="background:' + col + '; color:#1a9c52;" title="' + escapeHtml(title) + '">' + content + '</div>';
            return;
        } else if (c.is_holiday) {
            cls += ' holiday';
            content = '🎉';
            title += ' — праздник';
        } else if (c.is_weekend) {
            cls += ' weekend';
            content = '';
            title += ' — выходной';
        } else if (c.missing) {
            cls += ' missing';
            content = '!';
            title += ' — не заполнено';
        } else if (c.is_workday) {
            cls += ' workday';
            content = '';
            title += ' — не заполнено';
        } else {
            content = '';
        }
        if (c.is_today) cls += ' today';
        out += '<div class="' + cls + '" title="' + escapeHtml(title) + '">' + content + '</div>';
    });
    return out;
}

/* ============ Карточка задачи ============ */
function openTaskCardModal(taskId) {
    var from = $('sumDateFrom') ? $('sumDateFrom').value : '';
    var to = $('sumDateTo') ? $('sumDateTo').value : '';
    if (!from || !to) {
        var t = new Date();
        from = firstOfMonthISOFromDate(t);
        to = todayISO();
    }
    var qs = '?task=' + encodeURIComponent(taskId)
        + '&from=' + encodeURIComponent(from)
        + '&to=' + encodeURIComponent(to);
    apiJson('/api/tracker/task/card' + qs)
        .then(function(d) {
            if (!d.success) throw new Error(d.error || 'Ошибка');
            renderTaskCardModal(d);
            $('taskCardModal').classList.add('active');
        })
        .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

function renderTaskCardModal(d) {
    var task = d.task || {};
    var periodLabel = d.from ? (formatDateHuman(d.from) + ' — ' + formatDateHuman(d.to)) : '';
    $('taskCardHead').innerHTML = '<div class="emp-day-avatar" style="background: var(--trk-filter-active-bg); font-size: 1.6rem;">'
        + escapeHtml(task.icon || '📋') + '</div>'
        + '<div class="emp-day-info"><div class="emp-day-name' + (task.overdue ? ' overdue' : '') + '">' + escapeHtml(task.name || '—') + (task.overdue ? ' ⚠' : '') + '</div>'
        + '<div class="emp-day-role">' + escapeHtml(periodLabel)
        + (task.start_date ? ' · 🚀 ' + escapeHtml(formatDateHuman(task.start_date)) : '')
        + (task.deadline ? ' · ⏰ ' + escapeHtml(formatDateHuman(task.deadline)) : '') + '</div></div>'
        + '<div class="emp-day-stats">'
        + '<div class="emp-day-stat"><span class="val">' + formatHours(d.total_hours) + '</span><span class="lbl">часов</span></div>'
        + '<div class="emp-day-stat"><span class="val">' + d.active_days + ' / ' + (d.possible_days || 0) + '</span><span class="lbl">дней</span></div>'
        + '</div>';

    $('taskCardHeatmap').innerHTML = renderMiniCells(d.cells);

    var covHtml = (typeof d.coverage === 'number') ? _coverageBar(d.coverage) : '';
    var list = $('taskCardEmployees');
    if (!d.employees.length) {
        list.innerHTML = covHtml + '<div class="day-empty">За этот период отметок нет.</div>';
        return;
    }
    var html = covHtml;
    d.employees.forEach(function(e) {
        html += '<div class="day-entry">'
            + '<div class="day-entry-avatar" style="background:' + escapeHtml(e.employee_color) + '; box-shadow: 0 0 10px ' + escapeHtml(e.employee_color) + ';">'
            + escapeHtml(initials(e.employee_name)) + '</div>'
            + '<div class="day-entry-body"><div class="day-entry-head">'
            + '<span class="day-entry-task">' + escapeHtml(e.employee_name) + '</span>'
            + '<span class="day-entry-hours">' + formatHours(e.total_hours) + '</span>'
            + '<span class="day-entry-status status-in_progress">' + e.active_days + ' дн.</span>'
            + '</div>'
            + '<div class="day-entry-employee-row">'
            + (e.employee_department ? '<span class="emp-dept">🏢 ' + escapeHtml(e.employee_department) + '</span>' : '')
            + '</div></div>'
            + '</div>';
    });
    list.innerHTML = html;
}

/* ============ Статистика ============ */
function loadStats() {
    var from = $('stDateFrom').value, to = $('stDateTo').value;
    if (!from) { from = firstOfMonthISO(todayYM()); $('stDateFrom').value = from; }
    if (!to) { to = todayISO(); $('stDateTo').value = to; }
    var emp = $('stEmployeeFilter').value || '';
    var dept = $('stDeptFilter').value || '';
    var qs = '?from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to)
        + '&employee=' + encodeURIComponent(emp) + '&department=' + encodeURIComponent(dept);
    apiJson('/api/tracker/stats' + qs).then(function(d) {
        if (!d.success) throw new Error(d.error || 'Ошибка');
        renderStats(d);
    }).catch(function(err) {
        $('stOverall').innerHTML = '<div class="sum-empty" style="color:#e74c3c;">❌ ' + escapeHtml(err.message || 'Ошибка') + '</div>';
        $('stExtras').innerHTML = '';
    });
}

function renderStats(d) {
    var o = d.overall || {};
    $('stOverall').innerHTML =
        '<div class="stat-card"><span class="stat-label">Сотрудников</span><span class="stat-value">' + (o.employees_count || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">Всего задач</span><span class="stat-value">' + (o.tasks_total || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">Закрыто</span><span class="stat-value" style="color:#2ecc71;">' + (o.tasks_done || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">В работе</span><span class="stat-value" style="color:#3498db;">' + (o.tasks_active || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">Просрочено</span><span class="stat-value" style="color:#e74c3c;">' + (o.tasks_overdue || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">Досрочно</span><span class="stat-value" style="color:#9b59b6;">' + (o.early_done || 0) + '</span></div>'
        + '<div class="stat-card"><span class="stat-label">Часов всего</span><span class="stat-value">' + formatHours(o.hours_total || 0) + '</span></div>';

    var ovBlock = $('stOverdue');
    if (ovBlock) {
        var details = d.overdue_details || [];
        if (!details.length) {
            ovBlock.style.display = 'none';
            ovBlock.innerHTML = '';
        } else {
            ovBlock.style.display = '';
            var h = '<div class="sum-extra-title" style="color:#e74c3c;">⚠ Просроченные задачи (' + details.length + ')</div>'
                + '<div class="sum-table-wrap"><table class="sum-table grid-table"><thead><tr>'
                + '<th class="task-col">Задача</th>'
                + '<th>Дедлайн</th>'
                + '<th title="Дней с момента дедлайна">Просрочка</th>'
                + '<th>Назначено</th>'
                + '</tr></thead><tbody>';
            details.forEach(function(t) {
                var ass = (t.assignees || []).map(function(a) {
                    return '<span class="emp-dot" style="display:inline-block; width:8px; height:8px; border-radius:50%; background:' + escapeHtml(a.color) + '; margin-right:4px;"></span>' + escapeHtml(a.name);
                }).join(', ') || '—';
                h += '<tr>'
                    + '<td class="task-cell overdue" style="text-align:left;">'
                    + '<span class="task-ico">' + escapeHtml(t.task_icon) + '</span>'
                    + escapeHtml(t.task_name) + '</td>'
                    + '<td>' + escapeHtml(t.deadline) + '</td>'
                    + '<td style="color:#e74c3c; font-weight:700;">' + t.days_overdue + ' дн.</td>'
                    + '<td style="text-align:left; font-size:0.78rem;">' + ass + '</td>'
                    + '</tr>';
            });
            h += '</tbody></table></div>';
            ovBlock.innerHTML = h;
        }
    }

    var extras = '';
    extras += '<div class="sum-extra-block" style="margin-bottom:14px;">'
        + '<div class="sum-extra-title">👥 По сотрудникам</div>'
        + '<div class="sum-table-wrap"><table class="sum-table grid-table"><thead>'
        + '<tr><th class="emp-col">Сотрудник</th><th>Отдел</th>'
        + '<th title="Часы за период">Часов</th>'
        + '<th title="Всего релевантных задач">Задач</th>'
        + '<th title="Задачи со статусом «Выполнена»">Закрыто</th>'
        + '<th title="Активные задачи">В работе</th>'
        + '<th title="Просроченные задачи">Просроч.</th>'
        + '<th title="Задачи, закрытые до дедлайна">Досрочно</th>'
        + '<th title="Дней отпуска в периоде">🏖</th>'
        + '</tr></thead><tbody>';
    d.by_employee.forEach(function(r) {
        extras += '<tr>'
            + '<td class="emp-cell"><span class="emp-dot" style="background:' + escapeHtml(r.employee_color) + ';"></span>' + escapeHtml(r.employee_name) + '</td>'
            + '<td>' + escapeHtml(r.employee_department || '—') + '</td>'
            + '<td class="total-cell">' + formatHours(r.hours) + '</td>'
            + '<td>' + r.total_tasks + '</td>'
            + '<td style="color:#2ecc71; font-weight:700;">' + r.done_tasks + '</td>'
            + '<td style="color:#3498db; font-weight:700;">' + r.active_tasks + '</td>'
            + '<td style="color:#e74c3c; font-weight:700;">' + r.overdue_tasks + '</td>'
            + '<td style="color:#9b59b6;">' + r.early_done + '</td>'
            + '<td>' + (r.vacation_days || 0) + '</td>'
            + '</tr>';
    });
    extras += '</tbody></table></div></div>';

    extras += '<div class="sum-extra-block">'
        + '<div class="sum-extra-title">📋 По задачам</div>'
        + '<div class="sum-table-wrap"><table class="sum-table grid-table"><thead>'
        + '<tr><th class="task-col">Задача</th><th>Статус</th><th>Дедлайн</th>'
        + '<th>Назначено</th><th>Работали</th><th title="Суммарно часов">Часов</th>'
        + '</tr></thead><tbody>';
    d.by_task.forEach(function(t) {
        var statusLabel = ({'active':'Активна','done':'✅ Выполнена','paused':'Пауза','archived':'Архив'})[t.status] || t.status;
        var overdue = t.overdue ? ' <span style="color:#e74c3c;">⚠</span>' : '';
        extras += '<tr>'
            + '<td class="task-cell' + (t.overdue ? ' overdue' : '') + '" style="text-align:left;">'
            + '<span class="task-ico">' + escapeHtml(t.task_icon) + '</span>'
            + escapeHtml(t.task_name) + overdue + '</td>'
            + '<td>' + escapeHtml(statusLabel) + '</td>'
            + '<td>' + escapeHtml(t.deadline || '—') + '</td>'
            + '<td>' + t.assigned_count + '</td>'
            + '<td>' + t.workers_count + '</td>'
            + '<td class="total-cell">' + formatHours(t.hours) + '</td>'
            + '</tr>';
    });
    extras += '</tbody></table></div></div>';
    $('stExtras').innerHTML = extras;
}

/* ============ Heatmap ============ */
function loadHeatmap() {
    var qs = '';
    if (state.hmDateFrom && state.hmDateTo) {
        qs = '?from=' + encodeURIComponent(state.hmDateFrom) + '&to=' + encodeURIComponent(state.hmDateTo);
    } else {
        var ym = state.hmYM || todayYM();
        state.hmYM = ym;
        qs = '?ym=' + encodeURIComponent(ym);
    }
    var dept = $('hmDeptFilter') ? ($('hmDeptFilter').value || '') : '';
    if (dept) qs += '&department=' + encodeURIComponent(dept);
    var wrap = $('hmWrap');
    wrap.innerHTML = '<div class="sum-empty">Загрузка...</div>';
    apiJson('/api/tracker/heatmap' + qs)
        .then(function(d) { state.heatmap = d; renderHeatmap(); })
        .catch(function(err) {
            wrap.innerHTML = '<div class="sum-empty" style="color:#e74c3c;">❌ ' + escapeHtml(err.message || 'Ошибка') + '</div>';
        });
}

function renderHeatmap() {
    var d = state.heatmap;
    var wrap = $('hmWrap');
    if (!d || !d.rows.length) {
        wrap.innerHTML = '<div class="sum-empty">Нет сотрудников или данных за период.</div>';
        return;
    }
    var periodLabel = d.from ? (formatDateHuman(d.from) + ' — ' + formatDateHuman(d.to)) : '';
    $('hmMonthTitle').textContent = periodLabel;

    var today = todayISO();
    var head = '<tr><th class="emp-col">Сотрудник</th>';
    d.days.forEach(function(dk) {
        var wd = new Date(dk + 'T00:00:00').getDay();
        var cls = [];
        if (wd === 0 || wd === 6) cls.push('weekend-col');
        if (dk === today) cls.push('today-col');
        head += '<th' + (cls.length ? ' class="' + cls.join(' ') + '"' : '') + ' title="' + escapeHtml(dk) + '">' + escapeHtml(formatDateShort(dk)) + '</th>';
    });
    head += '<th class="total-col">Итого</th></tr>';

    var body = '';
    d.rows.forEach(function(r) {
        body += '<tr>';
        body += '<td class="emp-cell" data-emp="' + escapeHtml(r.employee_id) + '" title="Показать календарь сотрудника">'
            + '<span class="emp-dot" style="background:' + escapeHtml(r.employee_color) + '; box-shadow:0 0 6px ' + escapeHtml(r.employee_color) + ';"></span>'
            + escapeHtml(r.employee_name) + '</td>';
        r.cells.forEach(function(c) {
            var cls = [];
            var titleParts = [c.date];
            var content = '';
            if (c.is_vacation) {
                cls.push('vacation-cell');
                titleParts.push('🏖 Отпуск');
                content = '🏖';
            } else if (c.is_holiday) {
                cls.push('holiday-cell');
                titleParts.push('🎉 Праздник');
                content = '🎉';
            } else if (c.missing) {
                cls.push('missing-cell');
                titleParts.push('⚠ Не заполнено');
                content = '!';
            } else if (c.is_weekend) {
                cls.push('weekend-cell');
                titleParts.push('Выходной');
                content = '';
            } else if (c.hours > 0) {
                var color = cellLightGreen(c.hours);
                titleParts.push(formatHours(c.hours));
                content = c.hours;
                if (c.is_today) cls.push('today-cell');
                var clsAttr = cls.length ? ' class="' + cls.join(' ') + '"' : '';
                body += '<td' + clsAttr + ' style="background:' + color + '; color:#1a9c52; font-weight:700;" data-emp="' + escapeHtml(r.employee_id) + '" data-date="' + escapeHtml(c.date) + '" title="' + escapeHtml(titleParts.join(' · ')) + '">' + content + '</td>';
                return;
            } else {
                titleParts.push('—');
            }
            if (c.is_today) cls.push('today-cell');
            var clsAttr = cls.length ? ' class="' + cls.join(' ') + '"' : '';
            body += '<td' + clsAttr + ' data-emp="' + escapeHtml(r.employee_id) + '" data-date="' + escapeHtml(c.date) + '" title="' + escapeHtml(titleParts.join(' · ')) + '">' + content + '</td>';
        });
        body += '<td class="total-cell">' + formatHours(r.total_hours) + '</td></tr>';
    });
    wrap.innerHTML = '<table class="hm-table"><thead>' + head + '</thead><tbody>' + body + '</tbody></table>';

    wrap.querySelectorAll('td[data-emp][data-date]').forEach(function(td) {
        if (td.classList.contains('total-cell')) return;
        if (td.classList.contains('emp-cell')) {
            td.addEventListener('click', function() {
                var empId = this.getAttribute('data-emp');
                var emp = state.employees.find(function(x) { return x.id === empId; });
                if (!emp) return;
                if (confirm('Показать календарь сотрудника «' + emp.name + '»?')) {
                    document.querySelector('.tracker-tab[data-tab="calendar"]').click();
                    $('calEmployeeFilter').value = empId;
                    state.currentEmployee = empId;
                    loadCalendar();
                }
            });
            return;
        }
        td.addEventListener('click', function() {
            openEmpDayModal(this.getAttribute('data-emp'), this.getAttribute('data-date'));
        });
    });

    var legend = $('hmLegendBar');
    if (legend) {
        var steps = 6;
        var html = '';
        for (var j = 0; j <= steps; j++) {
            var h = 8 * (j / steps);
            html += '<span class="hm-legend-cell" style="background:' + (h ? heatmapColor(h) : 'rgba(128,128,128,0.15)') + ';"></span>';
        }
        legend.innerHTML = html;
    }
}

$('hmPrevBtn').addEventListener('click', function() {
    state.hmDateFrom = ''; state.hmDateTo = '';
    $('hmDateFrom').value = ''; $('hmDateTo').value = '';
    if (!state.hmYM) state.hmYM = todayYM();
    var p = state.hmYM.split('-');
    var y = parseInt(p[0], 10), m = parseInt(p[1], 10);
    m -= 1; if (m < 1) { m = 12; y -= 1; }
    state.hmYM = y + '-' + String(m).padStart(2, '0');
    loadHeatmap();
});
$('hmNextBtn').addEventListener('click', function() {
    state.hmDateFrom = ''; state.hmDateTo = '';
    $('hmDateFrom').value = ''; $('hmDateTo').value = '';
    if (!state.hmYM) state.hmYM = todayYM();
    var p = state.hmYM.split('-');
    var y = parseInt(p[0], 10), m = parseInt(p[1], 10);
    m += 1; if (m > 12) { m = 1; y += 1; }
    state.hmYM = y + '-' + String(m).padStart(2, '0');
    loadHeatmap();
});
$('hmTodayBtn').addEventListener('click', function() {
    state.hmDateFrom = ''; state.hmDateTo = '';
    $('hmDateFrom').value = ''; $('hmDateTo').value = '';
    state.hmYM = todayYM();
    loadHeatmap();
});
$('hmApplyBtn').addEventListener('click', function() {
    var f = $('hmDateFrom').value;
    var t = $('hmDateTo').value;
    if (!f || !t) { notify('❌ Укажите обе даты', 'error'); return; }
    state.hmDateFrom = f; state.hmDateTo = t;
    loadHeatmap();
});
$('hmMonthBtn').addEventListener('click', function() {
    state.hmDateFrom = ''; state.hmDateTo = '';
    var t = new Date();
    var y = t.getFullYear(); var m = t.getMonth() + 1;
    var last = new Date(y, m, 0).getDate();
    state.hmDateFrom = y + '-' + String(m).padStart(2, '0') + '-01';
    state.hmDateTo = y + '-' + String(m).padStart(2, '0') + '-' + String(last).padStart(2, '0');
    $('hmDateFrom').value = state.hmDateFrom;
    $('hmDateTo').value = state.hmDateTo;
    loadHeatmap();
});
$('hmDeptFilter').addEventListener('change', loadHeatmap);

/* ============ Карточка сотрудника за день ============ */
function openEmpDayModal(empId, dateStr) {
    apiJson('/api/tracker/employee/day?employee=' + encodeURIComponent(empId) + '&date=' + encodeURIComponent(dateStr))
        .then(function(d) {
            if (!d.success) throw new Error(d.error || 'Ошибка');
            renderEmpDayModal(d);
            $('empDayModal').classList.add('active');
        })
        .catch(function(err) { notify('❌ ' + (err.message || 'Ошибка'), 'error'); });
}

function renderEmpDayModal(d) {
    var emp = d.employee || {}, entries = d.entries || [];
    var badge = '';
    if (d.in_vacation) badge = '<span class="emp-day-badge vac">🏖 Отпуск</span>';
    else if (d.is_workday && entries.length === 0) badge = '<span class="emp-day-badge warn">⚠ Не заполнено</span>';
    else if (entries.length > 0) badge = '<span class="emp-day-badge ok">✓ Заполнено</span>';
    var deptLabel = emp.department ? ' · 🏢 ' + escapeHtml(emp.department) : '';
    $('empDayHead').innerHTML = '<div class="emp-day-avatar" style="background:' + escapeHtml(emp.color || '#00897b') + '; box-shadow: 0 0 12px ' + escapeHtml(emp.color || '#00897b') + ';">'
        + escapeHtml(initials(emp.name)) + '</div>'
        + '<div class="emp-day-info"><div class="emp-day-name">' + escapeHtml(emp.name || '—') + '</div>'
        + '<div class="emp-day-role">' + escapeHtml(emp.role || '') + deptLabel + ' · ' + escapeHtml(formatDateHuman(d.date)) + '</div></div>'
        + '<div class="emp-day-stats">'
        + '<div class="emp-day-stat"><span class="val">' + formatHours(d.total_hours) + '</span><span class="lbl">часов</span></div>'
        + '<div class="emp-day-stat"><span class="val">' + entries.length + '</span><span class="lbl">задач</span></div>'
        + '</div>' + badge;

    var list = $('empDayList');
    if (!entries.length) {
        list.innerHTML = '<div class="day-empty">За этот день отметок нет.</div>';
        return;
    }
    var html = '';
    entries.forEach(function(en) {
        var enFull = Object.assign({}, en);
        enFull.employee_name = emp.name;
        enFull.employee_color = emp.color;
        enFull.employee_department = emp.department;
        enFull.date = d.date;
        html += dayEntryCard(enFull, false);
    });
    list.innerHTML = html;
}

/* ============ Слушатели ============ */
$('addEmployeeBtn').addEventListener('click', function() { openEmployeeModal(null); });
$('addTaskBtn').addEventListener('click', function() { openTaskModal(null); });
$('addTaskBtn2').addEventListener('click', function() { openTaskModal(null); });
$('addDepartmentBtn').addEventListener('click', function() { openDepartmentModal(null); });
$('saveEmployeeBtn').addEventListener('click', saveEmployee);
$('saveTaskBtn').addEventListener('click', saveTask);
$('saveDepartmentBtn').addEventListener('click', saveDepartment);

document.querySelectorAll('[data-close]').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var id = this.getAttribute('data-close');
        var m = $(id);
        if (m) m.classList.remove('active');
        if (id === 'dayModal') {
            $('dayModalLeftActions').style.display = '';
            $('dayClearBtn').style.display = '';
        }
    });
});
document.querySelectorAll('.modal').forEach(function(m) {
    m.addEventListener('click', function(e) {
        if (e.target === m) {
            m.classList.remove('active');
            if (m.id === 'dayModal') {
                $('dayModalLeftActions').style.display = '';
                $('dayClearBtn').style.display = '';
            }
        }
    });
});
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(function(m) { m.classList.remove('active'); });
        $('dayModalLeftActions').style.display = '';
        $('dayClearBtn').style.display = '';
    }
});

$('sumApplyBtn').addEventListener('click', loadSummary);
$('sumWeekBtn').addEventListener('click', function() {
    setDefaultWeekRange();
    loadSummary();
});
$('sumMonthBtn').addEventListener('click', function() {
    setMonthRange();
    loadSummary();
});
$('sumEmployeeFilter').addEventListener('change', loadSummary);
$('sumTaskFilter').addEventListener('change', loadSummary);
$('sumDeptFilter').addEventListener('change', loadSummary);

var sdt = $('sumShowDayTotals');
if (sdt) {
    sdt.checked = state.sumShowDayTotals;
    sdt.addEventListener('change', function() {
        state.sumShowDayTotals = this.checked;
        if (state.summary) {
            if (state.summaryIsGrid) renderSummaryGrid();
            else renderSummary();
        }
    });
}

$('stApplyBtn').addEventListener('click', loadStats);
$('stMonthBtn').addEventListener('click', function() {
    $('stDateFrom').value = firstOfMonthISO(todayYM());
    $('stDateTo').value = todayISO();
    loadStats();
});
$('stDeptFilter').addEventListener('change', loadStats);
$('stEmployeeFilter').addEventListener('change', loadStats);

var _tskDept = $('tskDeptFilter');
if (_tskDept) _tskDept.addEventListener('change', renderTasksFull);
var _tskEmp = $('tskEmployeeFilter');
if (_tskEmp) _tskEmp.addEventListener('change', renderTasksFull);

/* ============ Старт ============ */
state.currentYM = todayYM();
state.hmYM = todayYM();
setDefaultWeekRange();
if (!$('stDateFrom').value) {
    $('stDateFrom').value = firstOfMonthISO(todayYM());
    $('stDateTo').value = todayISO();
}

loadState().then(function() {
    fillDepartmentFilters();
    fillEmployeeFilter();
    loadCalendar();
});

})();
</script>'''

