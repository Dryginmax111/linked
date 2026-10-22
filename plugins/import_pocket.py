"""Импорт из Pocket (HTML-экспорт)."""
import sys
from pathlib import Path

__version__ = "1.0"
__description__ = "Импорт ссылок из Pocket"

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from import_bookmarks import BookmarkParser
except Exception:
    BookmarkParser = None


def register(hooks, app, config, core):
    from flask import request, jsonify

    @app.route('/import/pocket', methods=['POST'])
    def import_pocket():
        if BookmarkParser is None:
            return jsonify({'success': False, 'error': 'Парсер недоступен'}), 500
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не загружен'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'success': False, 'error': 'Пустое имя'}), 400
        default_cat = request.form.get('default_category', 'Pocket').strip() or 'Pocket'
        use_folders = request.form.get('use_folders', 'false') == 'true'
        try:
            content = f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return jsonify({'success': False, 'error': f'Чтение: {e}'}), 400
        parser = BookmarkParser()
        try:
            parser.feed(content)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Парсинг: {e}'}), 400
        if not parser.bookmarks:
            return jsonify({'success': False, 'error': 'Не найдено закладок'}), 400
        added = 0
        for bm in parser.bookmarks:
            url = core.sanitize_link(bm['url'])
            if not url:
                continue
            name = (bm['title'] or '').strip() or bm['url']
            folder = (bm['folder'] or '').strip() if use_folders else default_cat
            if not folder:
                folder = default_cat
            try:
                if core.add_record(name=name, link=url, desc='', category=folder, favorite=0):
                    added += 1
            except Exception as e:
                print(f"[POCKET] {e}")
        core.log_action('import_pocket', None, '', {'count': added, 'category': default_cat})
        core.run_hook('on_import', source='pocket', added=added,
                      extra={'file': f.filename, 'category': default_cat})
        return jsonify({'success': True, 'added': added, 'total': len(parser.bookmarks)})

    hooks['ui_data_tab'].append({
        'id': 'import_pocket_btn', 'icon': '📖',
        'label': 'Импорт Pocket', 'action': 'openModal',
        'modal_id': 'importPocketModal',
    })

    hooks['ui_modals'].append({
        'id': 'importPocketModal', 'title': '📖 Импорт из Pocket', 'width': 'normal',
        'html': '''
<div style="font-size:0.85rem; color:var(--meta-color); line-height:1.5; margin-bottom:14px;">
    <p>Экспортируйте из Pocket: <b>Настройки → Экспорт → HTML-файл</b>.</p>
</div>
<div class="form-group">
    <label for="pluginPocketCat">Категория</label>
    <input type="text" id="pluginPocketCat" value="Pocket" maxlength="100">
</div>
<label class="data-btn" for="pluginPocketFile" style="justify-content:center;">
    <span class="data-icon">📁</span><span>Выбрать файл (.html)</span>
</label>
<input type="file" id="pluginPocketFile" accept=".html,.htm" style="display:none;">
<div id="pluginPocketProgress" style="display:none; margin-top:12px; color:var(--meta-color); font-size:0.9rem;"></div>
<div class="modal-actions">
    <button type="button" class="btn btn-secondary" onclick="closePluginModal('importPocketModal')">Закрыть</button>
</div>
'''
    })

    hooks['ui_scripts'].append({'html': '''<script>
document.addEventListener('DOMContentLoaded', function() {
    const inp = document.getElementById('pluginPocketFile');
    if (!inp) return;
    inp.addEventListener('change', function() {
        const file = this.files[0]; if (!file) return;
        const cat = (document.getElementById('pluginPocketCat') || {}).value || 'Pocket';
        const prog = document.getElementById('pluginPocketProgress');
        if (prog) { prog.style.display = 'block'; prog.textContent = '⏳ Загрузка...'; }
        const fd = new FormData(); fd.append('file', file);
        fd.append('default_category', cat); fd.append('use_folders', 'false');
        var _csrf = window.REESTR_CSRF || (document.querySelector('meta[name="csrf-token"]') || {getAttribute:function(){return ''}}).getAttribute('content') || '';
        fetch('/import/pocket', {
            method: 'POST',
            body: fd
        })
            .then(r => r.json())
            .then(d => {
                if (d.success) {
                    if (prog) prog.textContent = '✅ Добавлено: ' + d.added;
                    setTimeout(() => location.reload(), 1500);
                } else { if (prog) prog.textContent = '❌ ' + (d.error || 'Ошибка'); }
            })
            .catch(() => { if (prog) prog.textContent = '❌ Ошибка сети'; })
            .finally(() => { inp.value = ''; });
    });
});
</script>'''})
