"""Экспорт реестра в CSV."""
import csv
import io
from datetime import datetime
from urllib.parse import quote

__version__ = "1.0"
__description__ = "Экспорт в CSV (совместим с Excel)"


def register(hooks, app, config, core):
    @app.route('/export/csv')
    def export_csv():
        wb = core.read_workbook()
        ws = wb.active
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(['id', 'name_del', 'link_del', 'description', 'category',
                         'priority', 'favorite', 'order_index', 'created_at', 'updated_at',
                         'deleted_at', 'tags', 'click_count', 'last_clicked_at'])
        for row in ws.iter_rows(min_row=2, values_only=True):
            writer.writerow([core.safe_str(v) if v is not None else '' for v in row])
        content = '\ufeff' + output.getvalue()
        fa = f'reestr_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        fu = f'реестр_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        r = app.response_class(response=content, status=200, mimetype='text/csv; charset=utf-8')
        r.headers['Content-Disposition'] = f'attachment; filename="{fa}"; filename*=UTF-8\'\'{quote(fu)}'
        return r

    hooks['ui_data_tab'].append({
        'id': 'export_csv_btn', 'icon': '📊',
        'label': 'Экспорт в CSV',
        'action': 'download', 'url': '/export/csv',
    })
