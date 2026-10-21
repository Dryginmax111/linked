"""
Загрузчик плагинов, хуков и UI-слотов.
"""
import json
import threading
import importlib.util
import re
import shutil
import uuid
import inspect
import sys
import os
from pathlib import Path
from datetime import datetime

HOOK_NAMES = (
    'on_startup', 'on_shutdown',
    'on_add', 'on_edit', 'on_delete', 'on_hard_delete',
    'on_restore', 'on_move_to_group', 'on_category_change', 'on_click',
    'on_import', 'on_bulk_delete', 'on_bulk_move',
    'on_status_check_start', 'on_status_check_end',
    'on_category_rename', 'on_category_delete', 'on_group_rename',
    'on_plugins_reload',
)

UI_SLOT_NAMES = (
    'ui_data_tab', 'ui_tools_tab', 'ui_appearance_tab',
    'ui_sidebar', 'ui_topbar', 'ui_modals',
    'ui_scripts', 'ui_styles', 'ui_themes',
)

_ALL_HOOKS = HOOK_NAMES + UI_SLOT_NAMES

_HOOKS = {name: [] for name in _ALL_HOOKS}
_LOADED = []
_LOAD_ERRORS = []
_CONFIG_LOCK = threading.Lock()
_THEMES_LOCK = threading.Lock()
_RELOAD_LOCK = threading.Lock()
_RELOAD_IN_PROGRESS = threading.Event()

_PLUGIN_NAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{0,63}$')
RESERVED_NAMES = {'__init__', 'app', 'plugins_loader', 'hot_reload'}


class PluginConfig:
    def __init__(self, plugin_name, file_path):
        self.plugin_name = plugin_name
        self.file_path = Path(file_path)

    def _load_all(self):
        if not self.file_path.exists():
            return {}
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_all(self, data):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PLUGIN-CONFIG] Ошибка сохранения: {e}")

    def get(self, key, default=None):
        with _CONFIG_LOCK:
            return self._load_all().get(self.plugin_name, {}).get(key, default)

    def set(self, key, value):
        with _CONFIG_LOCK:
            data = self._load_all()
            data.setdefault(self.plugin_name, {})
            data[self.plugin_name][key] = value
            self._save_all(data)

    def all(self):
        with _CONFIG_LOCK:
            return dict(self._load_all().get(self.plugin_name, {}))


def validate_plugin_name(name):
    if not name:
        return 'Имя не может быть пустым'
    if name.startswith('_'):
        return 'Имя не может начинаться с подчёркивания'
    if not _PLUGIN_NAME_RE.match(name):
        return 'Только латиница, цифры и _ (до 64), первая — буква'
    if name in RESERVED_NAMES:
        return f'Имя «{name}» зарезервировано'
    return None


def check_syntax(code, filename='<plugin>'):
    try:
        compile(code, filename, 'exec')
        return None
    except SyntaxError as e:
        return f'Строка {e.lineno}: {e.msg}'
    except Exception as e:
        return str(e)


def read_plugin_code(plugins_dir, name):
    if validate_plugin_name(name):
        return None
    path = Path(plugins_dir) / f'{name}.py'
    if not path.exists():
        return None
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return None


def save_plugin_code(plugins_dir, name, code, create_backup=True):
    err = validate_plugin_name(name)
    if err:
        return err
    syn_err = check_syntax(code, f'{name}.py')
    if syn_err:
        return f'Синтаксическая ошибка: {syn_err}'
    path = Path(plugins_dir) / f'{name}.py'
    try:
        if create_backup and path.exists():
            bak = path.with_suffix(f'.py.bak-{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(path, bak)
        path.write_text(code, encoding='utf-8')
        return None
    except Exception as e:
        return f'Ошибка записи: {e}'


def delete_plugin(plugins_dir, name):
    err = validate_plugin_name(name)
    if err:
        return err
    plugins_dir = Path(plugins_dir)
    path = plugins_dir / f'{name}.py'
    if not path.exists():
        return 'Файл не найден'
    try:
        trash = plugins_dir / '.trash'
        trash.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.move(str(path), str(trash / f'{name}.py.{stamp}'))
        for bak in plugins_dir.glob(f'{name}.py.bak-*'):
            try:
                shutil.move(str(bak), str(trash / bak.name))
            except Exception:
                pass
        _clear_pycache(plugins_dir, name)
        return None
    except Exception as e:
        return f'Ошибка удаления: {e}'


def _clear_pycache(plugins_dir, name=None):
    """Удаляет .pyc-файлы для плагина (или все, если name=None)."""
    try:
        pycache = Path(plugins_dir) / '__pycache__'
        if not pycache.exists():
            return
        if name:
            # Точное совпадение: `<name>.cpython-312.pyc`, `<name>.cpython-312.opt-1.pyc` и т.п.
            pattern = f'{name}.*.pyc'
        else:
            pattern = '*.pyc'
        for pc in pycache.glob(pattern):
            try:
                pc.unlink()
            except Exception:
                pass
    except Exception:
        pass


def set_enabled(config_file, name, enabled):
    err = validate_plugin_name(name)
    if err:
        return err
    with _CONFIG_LOCK:
        data = {}
        cf = Path(config_file)
        if cf.exists():
            try:
                data = json.loads(cf.read_text(encoding='utf-8'))
                if not isinstance(data, dict):
                    data = {}
            except Exception:
                data = {}
        data.setdefault(name, {})
        data[name]['enabled'] = bool(enabled)
        try:
            cf.parent.mkdir(parents=True, exist_ok=True)
            cf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            return f'Ошибка сохранения: {e}'
    return None


def is_enabled(config_file, name):
    try:
        cf = Path(config_file)
        if not cf.exists():
            return True
        data = json.loads(cf.read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            return True
        return data.get(name, {}).get('enabled', True)
    except Exception:
        return True


def _call_register(register_fn, hooks, app, config, core):
    try:
        sig = inspect.signature(register_fn)
        params = sig.parameters
        kwargs = {'hooks': hooks, 'app': app, 'config': config}
        if 'core' in params:
            kwargs['core'] = core
        register_fn(**kwargs)
    except (TypeError, ValueError):
        # Фолбэк для register(hooks, app, config)
        register_fn(hooks, app, config)


def get_all_hooks():
    return _HOOKS


def reset_hooks():
    for name in _ALL_HOOKS:
        _HOOKS[name] = []


def _purge_plugin_modules():
    """Удаляет reestr_plugin_* из sys.modules."""
    removed = 0
    for n in list(sys.modules.keys()):
        if n.startswith('reestr_plugin_'):
            try:
                del sys.modules[n]
                removed += 1
            except Exception:
                pass
    return removed


def load_plugins(plugins_dir, app, config_file, core=None):
    """Загружает (или перезагружает) все плагины из папки.

    ВАЖНО: при повторном вызове — hooks полностью сбрасываются,
    модули переимпортируются. Роуты Flask не удаляются (см. hot_reload.py).
    """
    global _LOADED, _LOAD_ERRORS
    _LOADED = []
    _LOAD_ERRORS = []
    for name in _ALL_HOOKS:
        _HOOKS[name] = []

    plugins_dir = Path(plugins_dir)
    if not plugins_dir.exists():
        try:
            plugins_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"[PLUGIN] Не удалось создать {plugins_dir}: {e}")
            return _LOADED, _LOAD_ERRORS

    for f in sorted(plugins_dir.glob('*.py')):
        if f.name.startswith('_') or f.name == '__init__.py':
            continue
        plugin_name = f.stem

        if not is_enabled(config_file, plugin_name):
            _LOADED.append({'name': plugin_name, 'file': f.name,
                            'version': '—', 'description': '(отключён)',
                            'enabled': False, 'status': 'disabled'})
            print(f"[PLUGIN] ⊘ Отключён: {plugin_name}")
            continue

        try:
            _clear_pycache(plugins_dir, plugin_name)
            spec = importlib.util.spec_from_file_location(f'reestr_plugin_{plugin_name}', str(f))
            if spec is None or spec.loader is None:
                raise RuntimeError('Не удалось создать spec')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, 'register'):
                raise RuntimeError('Отсутствует register()')

            config = PluginConfig(plugin_name, config_file)
            _call_register(mod.register, _HOOKS, app, config, core)

            version = str(getattr(mod, '__version__', '—'))
            _LOADED.append({
                'name': plugin_name, 'file': f.name,
                'version': version,
                'description': str(getattr(mod, '__description__', '')),
                'enabled': True, 'status': 'active',
            })
            print(f"[PLUGIN] ✓ Загружен: {plugin_name} (v{version})")
        except Exception as e:
            _LOAD_ERRORS.append({'file': f.name, 'error': str(e)})
            print(f"[PLUGIN] ✗ Ошибка загрузки {f.name}: {e}")

    return _LOADED, _LOAD_ERRORS


def reload_plugins(plugins_dir, app, config_file, core=None):
    """Горячая перезагрузка всех плагинов.

    Порядок:
    1. on_shutdown у загруженных
    2. Очистка sys.modules + __pycache__
    3. Заново загружаем
    4. on_startup
    5. on_plugins_reload

    Возвращает (loaded, errors).
    """
    if _RELOAD_IN_PROGRESS.is_set():
        return _LOADED, _LOAD_ERRORS

    with _RELOAD_LOCK:
        _RELOAD_IN_PROGRESS.set()
        try:
            # 1. shutdown
            try:
                run_hook('on_shutdown')
            except Exception as e:
                print(f"[PLUGIN] on_shutdown при reload: {e}")

            # 2. чистим модули
            removed = _purge_plugin_modules()
            print(f"[PLUGIN] Очищено модулей: {removed}")
            _clear_pycache(plugins_dir)

            # 3. reload
            loaded, errors = load_plugins(plugins_dir, app, config_file, core=core)

            # 4. startup
            try:
                run_hook('on_startup')
            except Exception as e:
                print(f"[PLUGIN] on_startup после reload: {e}")

            # 5. событие
            try:
                run_hook('on_plugins_reload', loaded=loaded, errors=errors)
            except Exception as e:
                print(f"[PLUGIN] on_plugins_reload: {e}")

            return loaded, errors
        finally:
            _RELOAD_IN_PROGRESS.clear()


def _compute_status(name, enabled, loaded_names, error_names):
    if name in error_names:
        return 'error', '#e74c3c', 'Ошибка загрузки'
    if not enabled:
        return 'disabled', '#7a9ab5', 'Отключён'
    if name in loaded_names:
        return 'active', '#2ecc71', 'Активен'
    return 'pending', '#f1c40f', 'Загрузится после перезапуска'


def get_plugins_info(plugins_dir, config_file):
    plugins_dir = Path(plugins_dir)
    result = {'plugins': [], 'errors': list(_LOAD_ERRORS)}
    loaded_names = {p['name'] for p in _LOADED}
    error_names = {Path(e['file']).stem for e in _LOAD_ERRORS}
    if not plugins_dir.exists():
        return result
    for f in sorted(plugins_dir.glob('*.py')):
        if f.name.startswith('_') or f.name == '__init__.py':
            continue
        name = f.stem
        enabled = is_enabled(config_file, name)
        meta = next((p for p in _LOADED if p['name'] == name), None)
        try:
            stat = f.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            size = 0
            mtime = '—'
        status, color, label = _compute_status(name, enabled, loaded_names, error_names)
        result['plugins'].append({
            'name': name, 'file': f.name, 'size': size, 'mtime': mtime,
            'enabled': enabled, 'loaded': name in loaded_names,
            'has_error': name in error_names,
            'version': (meta or {}).get('version', '—'),
            'description': (meta or {}).get('description', '') or (
                'Ошибка загрузки' if name in error_names else ''),
            'status': status, 'status_color': color, 'status_label': label,
        })
    return result


def run_hook(hook_name, **kwargs):
    if hook_name not in _HOOKS:
        return
    for fn in list(_HOOKS[hook_name]):
        if not callable(fn):
            continue
        try:
            fn(**kwargs)
        except Exception as e:
            print(f"[PLUGIN] Ошибка в хуке {hook_name}: {e}")


def _collect_slot(slot_name):
    out = []
    for item in _HOOKS.get(slot_name, []):
        if isinstance(item, dict):
            out.append(item)
    return out


def collect_ui_slots():
    return {
        'data_tab': _collect_slot('ui_data_tab'),
        'tools_tab': _collect_slot('ui_tools_tab'),
        'appearance_tab': _collect_slot('ui_appearance_tab'),
        'sidebar': _collect_slot('ui_sidebar'),
        'topbar': _collect_slot('ui_topbar'),
        'modals': _collect_slot('ui_modals'),
        'scripts': _collect_slot('ui_scripts'),
        'styles': _collect_slot('ui_styles'),
        'themes': _collect_slot('ui_themes'),
    }


def get_loaded_plugins():
    return {
        'loaded': list(_LOADED),
        'errors': list(_LOAD_ERRORS),
        'hooks': {name: len(_HOOKS[name]) for name in _ALL_HOOKS if _HOOKS[name]},
    }


_BUILTIN_THEME_IDS = {
    'dark', 'light', 'black', 'cinema', 'neon', 'material',
    'material-glass', 'neumorphism-dark', 'material-you',
    'ios-glass', 'midnight', 'ocean', 'nord', 'solarized',
    'dracula', 'gruvbox',
}
_CUSTOM_THEME_ID_RE = re.compile(r'^[a-z][a-z0-9_]{0,31}$')
_FORBIDDEN_CSS_PATTERNS = (
    re.compile(r'url\s*\(', re.IGNORECASE),
    re.compile(r'expression\s*\(', re.IGNORECASE),
    re.compile(r'@import', re.IGNORECASE),
    re.compile(r'</\s*style', re.IGNORECASE),
    re.compile(r'javascript\s*:', re.IGNORECASE),
    re.compile(r'behavior\s*:', re.IGNORECASE),
    re.compile(r'-moz-binding\s*:', re.IGNORECASE),
)


def _contains_forbidden_css(text):
    if not text:
        return None
    for pat in _FORBIDDEN_CSS_PATTERNS:
        if pat.search(text):
            return pat.pattern
    return None

def load_custom_themes(file_path):
    if not Path(file_path).exists():
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_custom_themes(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[THEMES] Ошибка записи: {e}")


def _validate_theme(theme):
    if not isinstance(theme, dict):
        return 'Тема должна быть объектом'
    name = str(theme.get('name', '')).strip()
    if not name or len(name) > 60:
        return 'Имя темы: 1–60 символов'
    dot = theme.get('dot', '')
    if dot and (not isinstance(dot, str) or len(dot) > 500):
        return 'Поле dot: строка до 500 символов'
    if isinstance(dot, str):
        bad = _contains_forbidden_css(dot)
        if bad:
            return f'Запрещённое содержимое в dot: {bad}'
    vars_ = theme.get('vars', {})
    if not isinstance(vars_, dict):
        return 'vars должен быть объектом'
    if len(vars_) > 200:
        return 'Слишком много переменных (макс. 200)'
    for k, v in vars_.items():
        if not isinstance(k, str) or not k.startswith('--') or len(k) > 64:
            return f'Имя переменной некорректно: {k}'
        if not isinstance(v, (str, int, float)):
            return f'Значение {k} должно быть строкой/числом'
        sv = str(v)
        if len(sv) > 500:
            return f'Значение {k} слишком длинное'
        bad = _contains_forbidden_css(sv)
        if bad:
            return f'Запрещённое содержимое в {k}: {bad}'
    return None


def add_custom_theme(file_path, theme_id, theme):
    if not theme_id:
        theme_id = 'custom_' + uuid.uuid4().hex[:8]
    theme_id = theme_id.lower().strip()
    if not _CUSTOM_THEME_ID_RE.match(theme_id):
        return 'ID темы: строчная латиница, цифры, _, до 32 символов'
    if theme_id in _BUILTIN_THEME_IDS:
        return f'ID «{theme_id}» занят встроенной темой'
    err = _validate_theme(theme)
    if err:
        return err
    with _THEMES_LOCK:
        data = load_custom_themes(file_path)
        data[theme_id] = theme
        save_custom_themes(file_path, data)
    return None


def delete_custom_theme(file_path, theme_id):
    with _THEMES_LOCK:
        data = load_custom_themes(file_path)
        if theme_id not in data:
            return 'Тема не найдена'
        del data[theme_id]
        save_custom_themes(file_path, data)
    return None


def get_custom_themes(file_path):
    data = load_custom_themes(file_path)
    return [{'id': tid, 'name': theme.get('name', tid),
             'dot': theme.get('dot', ''), 'vars': theme.get('vars', {})}
            for tid, theme in data.items()]