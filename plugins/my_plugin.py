__version__ = "1.0"
__description__ = "Мой первый плагин"

def register(hooks, app, config):
    # Подписка на событие
    hooks['on_add'].append(handle_add)

    # Своя настройка
    if config.get('greeting') is None:
        config.set('greeting', 'Привет')

    # Свой эндпоинт
    @app.route('/my-plugin/ping')
    def ping():
        return config.get('greeting', 'Привет')

def handle_add(record_id, name, link, description, category, tags):
    print(f"[MY-PLUGIN] Добавлено: {name} → {link}")
