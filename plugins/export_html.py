"""Экспорт реестра в статический HTML."""
from datetime import datetime
from urllib.parse import quote
from markupsafe import escape

__version__ = "1.1"
__description__ = "Экспорт в статический HTML-файл (с поддержкой кода)"


def _render(groups, category_colors, total, core):
    p = []
    p.append('<!DOCTYPE html><html lang="ru"><head><meta charset="UTF-8">')
    p.append('<meta name="viewport" content="width=device-width,initial-scale=1.0">')
    p.append('<title>Реестр полезных ссылок</title>')
    p.append('''<style>
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
background:linear-gradient(145deg,#0b1a2e,#1b3a5c,#2a4b6e);color:#e8edf3;padding:20px;min-height:100vh;}
h1{text-align:center;color:#f5d76e;}.sub{text-align:center;color:#7a9ab5;margin-bottom:30px;}
.cards{max-width:1600px;margin:0 auto;column-count:2;column-gap:16px;}
@media(max-width:900px){.cards{column-count:1;}}
.card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.08);border-radius:16px;margin-bottom:16px;break-inside:avoid;}
.card-header{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.07);display:flex;gap:10px;}
.card-title{font-size:1.15rem;font-weight:700;flex:1;}
.card-count{background:rgba(245,215,110,.15);color:#f5d76e;padding:2px 10px;border-radius:20px;}
.links{padding:12px 14px;}
.link-item{padding:10px 12px;border-radius:10px;background:rgba(255,255,255,.02);margin-bottom:6px;}
.smart-link{color:#cfe2f2;text-decoration:none;font-family:monospace;font-size:.95rem;word-break:break-all;display:block;}
.smart-link:hover{color:#f5d76e;text-decoration:underline;}
.desc{font-size:.88rem;color:#9ab8d0;margin-top:6px;font-style:italic;}
.tag{display:inline-block;background:rgba(245,215,110,.15);color:#f5d76e;padding:1px 8px;border-radius:10px;font-size:.7rem;margin-right:6px;margin-top:6px;}
.link-code{margin-top:8px;border:1px solid rgba(255,255,255,0.1);border-radius:8px;overflow:hidden;}
.link-code .code-header{padding:3px 8px;background:rgba(0,0,0,0.25);font-size:0.7rem;color:#f5d76e;font-family:monospace;font-weight:700;letter-spacing:0.5px;}
.link-code pre{margin:0;padding:8px 12px;background:rgba(0,0,0,0.3);font-family:'Consolas','Monaco','Courier New',monospace;font-size:0.78rem;line-height:1.4;overflow-x:auto;color:#e8edf3;white-space:pre;max-height:200px;}
</style></head><body>''')
    p.append('<h1>📂 Реестр полезных ссылок</h1>')
    p.append(f'<div class="sub">экспортировано {datetime.now().strftime("%d.%m.%Y %H:%M")} · всего: {total}</div>')
    p.append('<div class="cards">')
    for name, items in groups.items():
        p.append('<div class="card"><div class="card-header">')
        p.append(f'<span class="card-title">{escape(name)}</span>')
        p.append(f'<span class="card-count">{len(items)}</span></div><div class="links">')
        for item in items:
            link = escape(item['link'])
            href = link
            if core.is_network_path(item['link']):
                href = escape('file://' + item['link'].replace('\\', '/'))
            p.append(f'<div class="link-item"><a class="smart-link" href="{href}" target="_blank" rel="noopener noreferrer">{link}</a>')
            if item['description']:
                p.append(f'<div class="desc">{escape(item["description"])}</div>')

            code_text = item.get('code', '') or ''
            code_lang = item.get('code_lang', '') or 'plaintext'
            if code_text.strip():
                p.append(
                    f'<div class="link-code">'
                    f'<div class="code-header">{escape(code_lang.upper())}</div>'
                    f'<pre>{escape(code_text)}</pre>'
                    f'</div>'
                )

            if item['category']:
                cc = category_colors.get(item['category'], '')
                style = f' style="background:{cc}33;color:{cc};"' if cc else ''
                p.append(f'<span class="tag"{style}>{escape(item["category"])}</span>')
            for t in item.get('tags', []):
                p.append(f'<span class="tag">#{escape(t)}</span>')
            p.append('</div>')
        p.append('</div></div>')
    p.append('</div></body></html>')
    return ''.join(p)


def register(hooks, app, config, core):
    @app.route('/export/html')
    def export_html():
        data = core.get_cached_data()
        html = _render(data['groups'] or {}, core.load_category_colors(), data['total'] or 0, core)
        fa = f'reestr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        fu = f'реестр_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        r = app.response_class(response=html, status=200, mimetype='text/html; charset=utf-8')
        r.headers['Content-Disposition'] = f'attachment; filename="{fa}"; filename*=UTF-8\'\'{quote(fu)}'
        return r

    hooks['ui_data_tab'].append({
        'id': 'export_html_btn', 'icon': '🌍',
        'label': 'Экспорт в HTML', 'action': 'download', 'url': '/export/html',
    })
