"""Импорт закладок браузера (HTML-экспорт)."""
from html.parser import HTMLParser

__version__ = "1.0"
__description__ = "Импорт закладок из браузера"


class BookmarkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.bookmarks = []
        self.stack = []
        self._pending_h3 = None
        self._in_h3 = False
        self._h3 = []
        self._in_a = False
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == 'h3':
            self._in_h3 = True; self._h3 = []
        elif t == 'a':
            d = dict((k.lower(), v) for k, v in attrs)
            self._href = d.get('href', ''); self._text = []; self._in_a = True
        elif t == 'dl':
            if self._pending_h3 is not None:
                self.stack.append(self._pending_h3); self._pending_h3 = None
            else:
                self.stack.append('')

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == 'h3':
            self._in_h3 = False
            self._pending_h3 = ''.join(self._h3).strip()
        elif t == 'a':
            if self._href:
                folder = self.stack[-1] if self.stack else ''
                self.bookmarks.append({'url': self._href.strip(),
                                       'title': ''.join(self._text).strip(),
                                       'folder': folder})
            self._in_a = False; self._href = None
        elif t == 'dl':
            if self.stack: self.stack.pop()

    def handle_data(self, data):
        if self._in_h3: self._h3.append(data)
        elif self._in_a: self._text.append(data)


def register(hooks, app, config, core):
    from flask import request, jsonify

    @app.route('/import/bookmarks', methods=['POST'])
    def import_bookmarks():
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не загружен'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'success': False, 'error': 'Пустое имя'}), 400
        try:
            content = f.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return jsonify({'success': False, 'error': f'Ошибка чтения: {e}'}), 400
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
            folder = (bm['folder'] or '').strip()
            try:
                if core.add_record(name=name, link=url, desc='', category=folder, favorite=0):
                    added += 1
            except Exception as e:
                print(f"[BOOKMARKS] {e}")
        core.log_action('import_bookmarks', None, '', {'count': added, 'file': f.filename})
        core.run_hook('on_import', source='bookmarks', added=added, extra={'file': f.filename})
        return jsonify({'success': True, 'added': added, 'total': len(parser.bookmarks)})

    hooks['ui_data_tab'].append({
        'id': 'import_bookmarks_btn', 'icon': '🌐',
        'label': 'Импорт закладок', 'action': 'openModal',
        'modal_id': 'importBookmarksModal',
    })

    hooks['ui_modals'].append({
        'id': 'importBookmarksModal',
        'title': '🌐 Импорт закладок из браузера',
        'width': 'normal',
        'html': '''
<div style="font-size:0.85rem; color:var(--meta-color); line-height:1.5; margin-bottom:14px;">
    <p><b>Chrome / Edge:</b> Меню → Закладки → Диспетчер закладок → ⋮ → Экспорт</p>
    <p><b>Firefox:</b> Меню → Закладки → Управление → Импорт и резервные копии → Экспорт в HTML</p>
    <p><b>Safari:</b> Файл → Экспортировать → Закладки</p>
</div>
<label class="data-btn" for="pluginImportBookmarksFile" style="justify-content:center;">
    <span class="data-icon">📁</span><span>Выбрать файл (.html)</span>
</label>
<input type="file" id="pluginImportBookmarksFile" accept=".html,.htm" style="display:none;">
<div id="pluginImportBookmarksProgress" style="display:none; margin-top:12px; color:var(--meta-color); font-size:0.9rem;"></div>
<div class="modal-actions">
    <button type="button" class="btn btn-secondary" onclick="closePluginModal('importBookmarksModal')">Закрыть</button>
</div>
'''
    })

    hooks['ui_scripts'].append({'html': '''<script>
document.addEventListener('DOMContentLoaded', function() {
    const inp = document.getElementById('pluginImportBookmarksFile');
    if (!inp) return;
    inp.addEventListener('change', function() {
        const file = this.files[0]; if (!file) return;
        const prog = document.getElementById('pluginImportBookmarksProgress');
        if (prog) { prog.style.display = 'block'; prog.textContent = '⏳ Загрузка...'; }
        const fd = new FormData(); fd.append('file', file);
        fetch('/import/bookmarks', {
            method: 'POST',
            body: fd,
            headers: window.reestrCsrfHeader()
        })
        .then(r => r.json())
            .then(d => {
                if (d.success) {
                    if (prog) prog.textContent = '✅ Добавлено: ' + d.added + ' из ' + d.total;
                    setTimeout(() => location.reload(), 1500);
                } else {
                    if (prog) prog.textContent = '❌ ' + (d.error || 'Ошибка');
                }
            })
            .catch(() => { if (prog) prog.textContent = '❌ Ошибка сети'; })
            .finally(() => { inp.value = ''; });
    });
});
</script>'''})