"""Проверка дубликатов URL через индекс ядра."""
__version__ = "1.0"
__description__ = "Проверка дубликатов URL"


def register(hooks, app, config, core):
    from flask import jsonify, request

    @app.route('/check_duplicate')
    def check_duplicate():
        url = request.args.get('url', '').strip()
        exclude_id = request.args.get('exclude_id', '').strip()
        if not url:
            return jsonify({'found': False})
        norm = core.normalize_url_for_dup(url)
        if not norm:
            return jsonify({'found': False})
        data = core.get_cached_data()
        url_index = data.get('url_index') or {}
        matches = []
        for entry in url_index.get(norm, []):
            if exclude_id and str(entry['id']) == str(exclude_id):
                continue
            matches.append({'id': entry['id'], 'name': entry['name'],
                            'category': entry['category'], 'link': entry['link']})
        return jsonify({'found': len(matches) > 0, 'matches': matches})