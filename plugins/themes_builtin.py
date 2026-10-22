"""Метаданные встроенных тем."""
__version__ = "1.0"
__description__ = "Регистрирует список встроенных тем"


def register(hooks, app, config, core):
    hooks['ui_themes'].append({
        'id': 'dark', 'name': 'Тёмная', 'builtin': True,
        'dot': 'linear-gradient(135deg, #0b1a2e, #2a4b6e)',
    })
    hooks['ui_themes'].append({'id': 'light', 'name': 'Светлая', 'builtin': True,
        'dot': 'linear-gradient(135deg, #eef2f7, #bcc8d9)'})
    hooks['ui_themes'].append({'id': 'black', 'name': 'Чёрная', 'builtin': True,
        'dot': 'linear-gradient(135deg, #000, #1a1a1a, #f5d76e)'})
    hooks['ui_themes'].append({'id': 'cinema', 'name': 'Кинематограф', 'builtin': True,
        'dot': 'radial-gradient(circle at 50% 35%, #ffb800 0%, #ff6b1a 28%, #3a1500 55%, #000 100%)'})
    hooks['ui_themes'].append({'id': 'neon', 'name': 'Neon Dashboard', 'builtin': True,
        'dot': 'radial-gradient(circle at 25% 25%, #00e5ff 0%, transparent 55%), radial-gradient(circle at 75% 75%, #ff0080 0%, transparent 55%), linear-gradient(135deg, #0a0e27, #1a1f4e)'})
    hooks['ui_themes'].append({'id': 'material', 'name': 'Material Night', 'builtin': True,
        'dot': 'radial-gradient(circle at 30% 30%, rgba(255,71,87,0.85) 0%, transparent 50%), radial-gradient(circle at 70% 75%, rgba(0,205,205,0.8) 0%, transparent 50%), linear-gradient(135deg, #2b2f38, #44474f)'})
    hooks['ui_themes'].append({'id': 'material-glass', 'name': 'Material Glass', 'builtin': True,
        'dot': 'radial-gradient(circle at 30% 30%, rgba(140,200,255,0.9) 0%, transparent 55%), radial-gradient(circle at 70% 75%, rgba(179,157,255,0.8) 0%, transparent 55%), linear-gradient(135deg, #202329, #2a2d35)'})
    hooks['ui_themes'].append({'id': 'neumorphism-dark', 'name': 'Neumorphism Dark', 'builtin': True,
        'dot': 'linear-gradient(135deg, #2a2d34, #383c44)'})
    hooks['ui_themes'].append({'id': 'material-you', 'name': 'Material You', 'builtin': True,
        'dot': 'radial-gradient(circle at 30% 30%, #d0bcff 0%, transparent 60%), radial-gradient(circle at 75% 75%, #8ea1ff 0%, transparent 60%), linear-gradient(135deg, #1c1b1f, #2b2930)'})
    hooks['ui_themes'].append({'id': 'ios-glass', 'name': 'iOS Glass', 'builtin': True,
        'dot': 'linear-gradient(135deg, #a8c0ff, #fbc2eb, #ffecd2)'})
    hooks['ui_themes'].append({'id': 'midnight', 'name': 'Полночь', 'builtin': True,
        'dot': 'linear-gradient(135deg, #1a0033, #4a0066, #ff006e)'})
    hooks['ui_themes'].append({'id': 'ocean', 'name': 'Океан', 'builtin': True,
        'dot': 'linear-gradient(135deg, #003049, #006494, #00b4d8)'})
    hooks['ui_themes'].append({'id': 'nord', 'name': 'Nord', 'builtin': True,
        'dot': 'linear-gradient(135deg, #2e3440, #4c566a, #88c0d0)'})
    hooks['ui_themes'].append({'id': 'solarized', 'name': 'Solarized', 'builtin': True,
        'dot': 'linear-gradient(135deg, #002b36, #b58900)'})
    hooks['ui_themes'].append({'id': 'dracula', 'name': 'Dracula', 'builtin': True,
        'dot': 'linear-gradient(135deg, #282a36, #bd93f9, #ff79c6)'})
    hooks['ui_themes'].append({'id': 'gruvbox', 'name': 'Gruvbox', 'builtin': True,
        'dot': 'linear-gradient(135deg, #282828, #fabd2f, #d65d0e)'})
