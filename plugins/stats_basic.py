"""Базовая статистика реестра."""
from datetime import datetime, timedelta

__version__ = "1.0"
__description__ = "Статистика: топ ссылок, активность, тепловая карта"


def register(hooks, app, config, core):
    from flask import jsonify

    @app.route('/get_stats')
    def get_stats():
        wb = core.read_workbook(); ws = wb.active
        all_records, total_clicks = [], 0
        cat_counts, cat_clicks, activity, stale = {}, {}, {}, []
        now = datetime.now()
        cutoff_30 = (now - timedelta(days=30)).strftime('%Y-%m-%d')
        cutoff_180 = now - timedelta(days=180)
        for row in ws.iter_rows(min_row=2, values_only=True):
            if core.safe_str(row[10]) if len(row) > 10 else '':
                continue
            rid = core.safe_int(row[0], -1)
            name, link, cat = core.safe_str(row[1]), core.safe_str(row[2]), core.safe_str(row[4])
            clicks = core.safe_int(row[12] if len(row) > 12 else 0, 0)
            last_click = core.safe_str(row[13]) if len(row) > 13 else ''
            total_clicks += clicks
            if cat:
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                cat_clicks[cat] = cat_clicks.get(cat, 0) + clicks
            all_records.append({'id': rid, 'name': name, 'link': link, 'cat': cat,
                                'clicks': clicks, 'last_click': last_click})
            if last_click and last_click >= cutoff_30:
                day = last_click[:10]
                activity[day] = activity.get(day, 0) + 1
            stale_flag = False
            if not last_click:
                stale_flag = True
            else:
                try:
                    if datetime.strptime(last_click, '%Y-%m-%d %H:%M:%S') < cutoff_180:
                        stale_flag = True
                except Exception:
                    pass
            if stale_flag:
                stale.append({'id': rid, 'name': name, 'link': link, 'last_click': last_click})
        top_links = sorted(all_records, key=lambda x: -x['clicks'])[:10]
        labels, values = [], []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append(d); values.append(activity.get(d, 0))
        cats = [{'name': k, 'count': v, 'clicks': cat_clicks.get(k, 0)}
                for k, v in sorted(cat_counts.items(), key=lambda x: -x[1])]
        return jsonify({'total_links': len(all_records), 'total_clicks': total_clicks,
                        'top_links': top_links, 'categories': cats,
                        'activity': {'labels': labels, 'values': values},
                        'stale_links': stale[:20]})

    @app.route('/get_heatmap')
    def get_heatmap():
        wb = core.read_workbook(); ws = wb.active
        matrix = [[0] * 24 for _ in range(7)]
        total = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            if core.safe_str(row[10]) if len(row) > 10 else '':
                continue
            clicks = core.safe_int(row[12] if len(row) > 12 else 0, 0)
            last_click = core.safe_str(row[13]) if len(row) > 13 else ''
            if not last_click or clicks <= 0:
                continue
            try:
                dt = datetime.strptime(last_click, '%Y-%m-%d %H:%M:%S')
                matrix[dt.weekday()][dt.hour] += clicks
                total += clicks
            except Exception:
                pass
        max_val, max_cell = 0, {'day': 0, 'hour': 0, 'value': 0}
        for d in range(7):
            for h in range(24):
                if matrix[d][h] > max_val:
                    max_val = matrix[d][h]
                    max_cell = {'day': d, 'hour': h, 'value': matrix[d][h]}
        return jsonify({'matrix': matrix, 'max': max_val or 1,
                        'total': total, 'max_cell': max_cell})

    hooks['ui_tools_tab'].append({
        'id': 'show_stats_btn', 'icon': '📊',
        'label': 'Статистика', 'action': 'openModal',
        'modal_id': 'pluginStatsModal',
    })

    hooks['ui_modals'].append({
        'id': 'pluginStatsModal', 'title': '📊 Статистика', 'width': 'wide',
        'html': '<div id="pluginStatsContent"><p style="color:var(--meta-color);text-align:center;padding:20px 0;">Загрузка...</p></div><div class="modal-actions"><button type="button" class="btn btn-secondary" onclick="closePluginModal(\'pluginStatsModal\')">Закрыть</button></div>'
    })

    hooks['ui_scripts'].append({'html': '''<script>
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.querySelector('[data-plugin-modal="pluginStatsModal"]');
    if (btn) btn.addEventListener('click', function() {
        const c = document.getElementById('pluginStatsContent');
        if (!c) return;
        c.innerHTML = '<p style="text-align:center;padding:20px 0;">Загрузка...</p>';
        Promise.all([
            fetch('/get_stats').then(r => r.json()),
            fetch('/get_health_stats').then(r => r.json()).catch(() => null),
            fetch('/get_heatmap').then(r => r.json()).catch(() => null)
        ]).then(function(res) {
            const data = res[0], health = res[1], hm = res[2];
            const colors = ['#f5d76e','#f39c12','#e74c3c','#9b59b6','#3498db','#1abc9c','#2ecc71','#e67e22','#e91e63','#00bcd4'];
            let html = '<div class="stats-grid">'
                + '<div class="stat-card"><span class="stat-label">Всего ссылок</span><span class="stat-value">' + data.total_links + '</span></div>'
                + '<div class="stat-card"><span class="stat-label">Кликов</span><span class="stat-value">' + data.total_clicks + '</span></div>'
                + '<div class="stat-card"><span class="stat-label">Категорий</span><span class="stat-value">' + data.categories.length + '</span></div>'
                + '<div class="stat-card"><span class="stat-label">Давно не открывались</span><span class="stat-value">' + data.stale_links.length + '</span></div>'
                + '</div>';
            if (health && health.total > 0) {
                html += '<div class="stats-section"><h3>❤️ Здоровье ссылок</h3>'
                    + '<div class="health-bar-wrap"><div class="health-bar"><div class="health-bar-fill" style="width:' + (health.percent_ok || 0) + '%"></div></div>'
                    + '<div class="health-bar-text">' + (health.percent_ok || 0) + '% рабочих (' + health.ok + ' из ' + health.total + ')</div></div>'
                    + '<div class="health-legend"><span><span class="health-dot ok"></span>OK: ' + health.ok + '</span>'
                    + '<span><span class="health-dot warn"></span>Warn: ' + health.warn + '</span>'
                    + '<span><span class="health-dot error"></span>Error: ' + health.error + '</span>'
                    + '<span><span class="health-dot timeout"></span>Timeout: ' + health.timeout + '</span>'
                    + '<span><span class="health-dot unknown"></span>?: ' + health.unknown + '</span></div></div>';
            }
            const total = data.categories.reduce((s, c) => s + c.count, 0) || 1;
            let acc = 0;
            const segs = data.categories.map(function(c, i) {
                const start = acc / total * 100;
                acc += c.count;
                const end = acc / total * 100;
                return '<circle cx="50" cy="50" r="40" fill="transparent" stroke="' + colors[i % colors.length] + '" stroke-width="14" stroke-dasharray="' + (end - start) + ' ' + (100 - (end - start)) + '" stroke-dashoffset="' + (-start) + '" pathLength="100"></circle>';
            }).join('');
            const legend = data.categories.map((c, i) =>
                '<div class="donut-legend-item"><span class="donut-legend-dot" style="background:' + colors[i % colors.length] + ';"></span><span class="donut-legend-name">' + c.name + '</span><span class="donut-legend-value">' + c.count + ' (' + c.clicks + '👁)</span></div>').join('');
            html += '<div class="stats-section"><h3>🍩 Распределение</h3><div class="donut-wrap"><div class="donut-chart"><svg viewBox="0 0 100 100">' + segs + '</svg><div class="donut-center"><div class="donut-total">' + data.total_links + '</div><div class="donut-label">ссылок</div></div></div><div class="donut-legend">' + legend + '</div></div></div>';
            const maxVal = Math.max.apply(null, data.activity.values.concat([1]));
            const bars = data.activity.values.map((v, i) => {
                const h = Math.round(v / maxVal * 100);
                return '<div class="bar" style="height:' + h + '%;" data-count="' + v + '" title="' + data.activity.labels[i] + ': ' + v + '"></div>';
            }).join('');
            html += '<div class="stats-section"><h3>📈 Активность за 30 дней</h3><div class="bar-chart">' + bars + '</div><div class="bar-labels"><span>' + data.activity.labels[0] + '</span><span>' + data.activity.labels[data.activity.labels.length - 1] + '</span></div></div>';
            if (hm && hm.matrix) {
                const days = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
                let rows = '';
                for (let d = 0; d < 7; d++) {
                    let cells = '';
                    for (let h = 0; h < 24; h++) {
                        const v = hm.matrix[d][h] || 0;
                        const inten = hm.max > 0 ? v / hm.max : 0;
                        const alpha = v === 0 ? 0.05 : (0.12 + inten * 0.83);
                        cells += '<div class="heatmap-cell" style="background:rgba(245,215,110,' + alpha.toFixed(2) + ')" title="' + days[d] + ' ' + h + ':00 — ' + v + '"></div>';
                    }
                    rows += '<div class="heatmap-row"><span class="heatmap-label">' + days[d] + '</span>' + cells + '</div>';
                }
                html += '<div class="stats-section"><h3>🔥 Тепловая карта</h3><div class="heatmap-grid">' + rows + '</div></div>';
            }
            const topRows = data.top_links.filter(l => l.clicks > 0).map(l =>
                '<tr><td>' + l.name + '</td><td style="font-family:monospace;font-size:0.8rem;">' + l.link + '</td><td class="num-col">' + l.clicks + '</td></tr>').join('');
            if (topRows) {
                html += '<div class="stats-section"><h3>🔥 Топ-10</h3><table class="stats-table"><thead><tr><th>Название</th><th>Ссылка</th><th class="num-col">Кликов</th></tr></thead><tbody>' + topRows + '</tbody></table></div>';
            }
            c.innerHTML = html;
        }).catch(() => { c.innerHTML = '<p style="color:#e74c3c;text-align:center;">Ошибка загрузки</p>'; });
    });
});
</script>'''})
