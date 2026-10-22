"""Экспорт реестра в XLSX."""
from datetime import datetime
from pathlib import Path

__version__ = "1.0"
__description__ = "Экспорт в XLSX (копия реестра)"


def register(hooks, app, config, core):
    from flask import send_file

    @app.route('/export/xlsx')
    def export_xlsx():
        if not Path(core.EXCEL_FILE).exists():
            return 'Нет данных', 404
        core.read_workbook()
        return send_file(core.EXCEL_FILE, as_attachment=True,
                         download_name=f'реестр_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    hooks['ui_data_tab'].append({
        'id': 'export_xlsx_btn', 'icon': '📤',
        'label': 'Экспорт в XLSX',
        'action': 'download', 'url': '/export/xlsx',
    })
