"""Экспорт реестра в JSON."""
import json
from datetime import datetime
from urllib.parse import quote

__version__ = "1.0"
__description__ = "Экспорт в JSON"


def register(hooks, app, config, core):
    @app.route('/export/json')
    def export_json():
        data = core.get_cached_data()
        export = {
            'exported_at': datetime.now().isoformat(),
            'total_records': data['total'] or 0,
            'categories': data['categories'] or [],
            'category_counts': data['category_counts'] or {},
            'all_tags': data['all_tags'] or {},
            'group_icons': core.load_group_icons(),
            'groups': data['groups'] or {},
        }
        content = json.dumps(export, ensure_ascii=False, indent=2)
        fa = f'reestr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        fu = f'реестр_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        r = app.response_class(response=content, status=200, mimetype='application/json; charset=utf-8')
        r.headers['Content-Disposition'] = f'attachment; filename="{fa}"; filename*=UTF-8\'\'{quote(fu)}'
        return r

    hooks['ui_data_tab'].append({
        'id': 'export_json_btn', 'icon': '💾',
        'label': 'Экспорт в JSON', 'action': 'download', 'url': '/export/json',
    })