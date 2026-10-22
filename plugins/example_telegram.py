"""
Пример плагина: отправка уведомлений в Telegram.

Для реальной работы: заполните token и chat_id в plugins.json
(секция «example_telegram»), либо через /my-plugin/telegram/set.

Плагин демонстрирует:
  - чтение/запись своих настроек через config
  - собственный эндпоинт
  - отправку через фоновый поток (не блокирует UI)
"""

import threading
import json
import urllib.request
import urllib.parse
import urllib.error

__version__ = "1.0"
__description__ = "Пример отправки уведомлений в Telegram (заглушка)"


def _send_telegram(token, chat_id, text):
    """Отправляет сообщение в Telegram. Работает в фоновом потоке."""
    if not token or not chat_id:
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true',
    }).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        with urllib.request.urlopen(req, timeout=6) as resp:
            resp.read()
    except Exception as e:
        print(f"[TELEGRAM-PLUGIN] Ошибка отправки: {e}")


def _notify_async(config, text):
    token = config.get('token', '')
    chat_id = config.get('chat_id', '')
    if not token or not chat_id:
        return
    threading.Thread(
        target=_send_telegram,
        args=(token, chat_id, text),
        daemon=True,
    ).start()


# ---------- Обработчики ----------

def on_add(record_id, name, link, description, category, tags):
    pass  # Здесь можно включить, если хотите получать уведомление на каждое добавление


def on_delete(record_id, name, link, category):
    pass  # Например: уведомление об удалении


def on_bulk_delete(count, ids):
    # Заглушка: настроить telegram в /my-plugin/telegram/set
    print(f"[TELEGRAM-PLUGIN] (dry-run) Было бы отправлено: массовое удаление {count} записей")


def on_status_check_end(results):
    pass  # Пример: отправка отчёта о проверке ссылок


def register(hooks, app, config):
    """Регистрируем хуки + свои эндпоинты + настройки."""
    # Подписки (по умолчанию отключены, чтобы не спамить)
    hooks['on_bulk_delete'].append(on_bulk_delete)

    # Дефолтные значения настроек (если ещё не заданы)
    if config.get('token') is None:
        config.set('token', '')
    if config.get('chat_id') is None:
        config.set('chat_id', '')

    # --- Свои эндпоинты ---

    @app.route('/my-plugin/telegram/status', methods=['GET'])
    def telegram_status():
        from flask import jsonify
        return jsonify({
            'configured': bool(config.get('token')) and bool(config.get('chat_id')),
            'chat_id': config.get('chat_id', ''),
        })

    @app.route('/my-plugin/telegram/set', methods=['POST'])
    def telegram_set():
        from flask import request, jsonify
        data = request.get_json() or {}
        token = str(data.get('token', '')).strip()
        chat_id = str(data.get('chat_id', '')).strip()
        if token:
            config.set('token', token)
        if chat_id:
            config.set('chat_id', chat_id)
        return jsonify({'success': True})

    @app.route('/my-plugin/telegram/test', methods=['POST'])
    def telegram_test():
        from flask import jsonify
        _notify_async(config, '🧪 <b>Тестовое сообщение</b> из реестра ссылок')
        return jsonify({'success': True, 'message': 'Сообщение отправлено (если настроен токен)'})
