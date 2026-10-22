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

# Реестр view-функций плагинов: endpoint -> current_view_function.
# Диспетчеры на реальном Flask читают отсюда. При reload мы просто
# подменяем значения — Flask.url_map не трогаем.
_PLUGIN_VIEWS = {}

# Информация о зарегистрированных роутах: endpoint -> {'rule', 'methods'}
_PLUGIN_ENDPOINT_INFO = {}

# endpoint'ы, уже добавленные в Flask.url_map (dispatch-обёртки)
_REGISTERED_ENDPOINTS = set()

# Какие endpoint'ы принадлежат какому плагину: plugin_name -> [endpoints]
_PLUGIN_NAME_ENDPOINTS = {}

_PLUGIN_NAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{0,63}$')
RESERVED_NAMES = {'__init__', 'app', 'plugins_loader'}


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
        pycache = plugins_dir / '__pycache__'
        if pycache.exists():
            for pc in pycache.glob(f'*{name}*'):
                try:
                    pc.unlink()
                except Exception:
                    pass
        return None
    except Exception as e:
        return f'Ошибка удаления: {e}'


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


class PluginAppProxy:
    """Прокси для Flask app, отдаваемый плагинам.

    Плагин вызывает @app.route(...), но регистрация происходит не на
    реальном Flask (это запрещено после первого запроса), а в локальный
    буфер `self.routes`. После отработки `register()` мы сами решаем,
    какие роуты добавить как диспетчеры, а какие — просто обновить.
    """
    def __init__(self, real_app, plugin_name):
        self._app = real_app
        self._plugin_name = plugin_name
        self.routes = []

    def route(self, rule, **options):
        # Копируем, чтобы не менять исходный dict
        opts = dict(options)
        def decorator(fn):
            ep = opts.pop('endpoint', None) or fn.__name__
            methods = opts.pop('methods', None)
            self.routes.append({
                'rule': rule,
                'endpoint': ep,
                'view': fn,
                'methods': methods,
                'options': opts,
            })
            return fn
        return decorator

    def __getattr__(self, name):
        # Делегируем всё остальное реальному Flask
        return getattr(self._app, name)


def _make_plugin_dispatcher(endpoint):
    """Создаёт view-функцию для Flask, которая при каждом запросе
    достаёт актуальный обработчик из _PLUGIN_VIEWS."""
    def dispatcher(**kwargs):
        view = _PLUGIN_VIEWS.get(endpoint)
        if view is None:
            return ('Plugin route not available', 503)
        return view(**kwargs)
    dispatcher.__name__ = f'plugin_dispatch_{endpoint}'
    dispatcher.__qualname__ = dispatcher.__name__
    return dispatcher


def _register_plugin_routes(real_app, plugin_name, proxy):
    """Регистрирует собранные proxy.routes на реальном Flask.
    - Если endpoint уже зарегистрирован — обновляем _PLUGIN_VIEWS.
    - Если новый — добавляем диспетчер в url_map.
    Возвращает список endpoint'ов плагина."""
    endpoints = []
    for r in proxy.routes:
        ep = r['endpoint']
        view = r['view']
        _PLUGIN_VIEWS[ep] = view
        _PLUGIN_ENDPOINT_INFO[ep] = {
            'rule': r['rule'],
            'methods': r['methods'],
        }
        endpoints.append(ep)

        if ep in _REGISTERED_ENDPOINTS:
            # endpoint уже был — просто обновили view, ничего не трогаем
            continue

        try:
            real_app.add_url_rule(
                r['rule'],
                endpoint=ep,
                view_func=_make_plugin_dispatcher(ep),
                methods=r['methods'],
                **r['options']
            )
            _REGISTERED_ENDPOINTS.add(ep)
        except AssertionError as e:
            # Flask уже обработал первый запрос — новые роуты не добавить.
            # Плагин загрузится, но его роуты не будут доступны до перезапуска.
            print(f"[PLUGIN] ⚠️  Новый роут {r['rule']} ({ep}) не зарегистрирован: "
                  f"требуется перезапуск сервера ({e})")
            # Не считаем это фатальной ошибкой — view уже в _PLUGIN_VIEWS
        except Exception as e:
            print(f"[PLUGIN] ✗ Не удалось зарегистрировать роут {r['rule']} ({ep}): {e}")

    _PLUGIN_NAME_ENDPOINTS[plugin_name] = endpoints
    return endpoints


def _call_register(register_fn, hooks, app, config, core):
    """Вызывает register() плагина, поддерживая сигнатуры:
        register(hooks, app, config)
        register(hooks, app, config, core)
    Любые лишние именованные аргументы отфильтровываются."""
    try:
        sig = inspect.signature(register_fn)
        params = sig.parameters
        accepts_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD
            for p in params.values()
        )
        kwargs = {'hooks': hooks, 'app': app, 'config': config}
        if 'core' in params or accepts_kwargs:
            kwargs['core'] = core
        if accepts_kwargs:
            register_fn(**kwargs)
        else:
            allowed = {k: v for k, v in kwargs.items() if k in params}
            if 'hooks' not in allowed:
                # Совсем нестандартная сигнатура — пробуем позиционно
                register_fn(hooks, app, config)
            else:
                register_fn(**allowed)
    except ValueError:
        register_fn(hooks, app, config)


def get_all_hooks():
    return _HOOKS


def reset_hooks():
    for name in _ALL_HOOKS:
        _HOOKS[name] = []


def load_plugins(plugins_dir, app, config_file, core=None):
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
            spec = importlib.util.spec_from_file_location(f'reestr_plugin_{plugin_name}', str(f))
            if spec is None or spec.loader is None:
                raise RuntimeError('Не удалось создать spec')
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            if not hasattr(mod, 'register'):
                raise RuntimeError('Отсутствует register()')

            # Запоминаем endpoint'ы до регистрации, чтобы потом вычислить новые
            config = PluginConfig(plugin_name, config_file)
            proxy = PluginAppProxy(app, plugin_name)
            _call_register(mod.register, _HOOKS, proxy, config, core)
            _register_plugin_routes(app, plugin_name, proxy)

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

    Роуты в Flask.url_map не трогаем — они уже зарегистрированы как
    диспетчеры. Мы только обнуляем реестр view-функций и перезагружаем
    модули. После reload диспетчеры подхватят свежие функции из
    _PLUGIN_VIEWS.

    Возвращает (loaded, errors).
    """
    with _RELOAD_LOCK:
        # 1. shutdown hook
        try:
            run_hook('on_shutdown')
        except Exception as e:
            print(f"[PLUGIN] on_shutdown при reload: {e}")

        # 2. Обнуляем view-функции всех плагинов. Сами url_map правила
        #    остаются — их диспетчеры возвращают 503, пока не придут
        #    новые view из перезагруженных плагинов.
        cleared = 0
        for pname in list(_PLUGIN_NAME_ENDPOINTS.keys()):
            for ep in _PLUGIN_NAME_ENDPOINTS[pname]:
                if ep in _PLUGIN_VIEWS:
                    del _PLUGIN_VIEWS[ep]
                    cleared += 1
        _PLUGIN_NAME_ENDPOINTS.clear()
        print(f"[PLUGIN] Сброшено view-функций: {cleared}")

        # 3. Чистим модули
        names_to_remove = [n for n in list(sys.modules.keys()) if n.startswith('reestr_plugin_')]
        for n in names_to_remove:
            try:
                del sys.modules[n]
            except Exception:
                pass

        # 4. Перезагружаем
        loaded, errors = load_plugins(plugins_dir, app, config_file, core=core)

        # 5. startup hook
        try:
            run_hook('on_startup')
        except Exception as e:
            print(f"[PLUGIN] on_startup после reload: {e}")

        # 6. Событие
        try:
            run_hook('on_plugins_reload', loaded=loaded, errors=errors)
        except Exception as e:
            print(f"[PLUGIN] on_plugins_reload: {e}")

        return loaded, errors


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
    """Вызывает все функции хука. Устойчив к несовпадению аргументов:
    если функция не принимает какие-то именованные параметры, они отфильтровываются."""
    if hook_name not in _HOOKS:
        return
    for fn in list(_HOOKS[hook_name]):
        if not callable(fn):
            continue
        try:
            fn(**kwargs)
        except TypeError as e:
            # Пытаемся отфильтровать неподходящие kwargs
            msg = str(e)
            if 'unexpected keyword argument' in msg:
                try:
                    sig = inspect.signature(fn)
                    accepts_kwargs = any(
                        p.kind == inspect.Parameter.VAR_KEYWORD
                        for p in sig.parameters.values()
                    )
                    if accepts_kwargs:
                        # Функция принимает **kwargs, но всё равно ошибка — не фильтруем
                        raise
                    allowed = set()
                    for pname, p in sig.parameters.items():
                        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                      inspect.Parameter.KEYWORD_ONLY):
                            allowed.add(pname)
                    filtered = {k: v for k, v in kwargs.items() if k in allowed}
                    fn(**filtered)
                    continue
                except Exception as e2:
                    print(f"[PLUGIN] Ошибка в хуке {hook_name} ({fn.__name__}): {e2}")
                    continue
            print(f"[PLUGIN] Ошибка в хуке {hook_name} ({getattr(fn, '__name__', '?')}): {e}")
        except Exception as e:
            print(f"[PLUGIN] Ошибка в хуке {hook_name} ({getattr(fn, '__name__', '?')}): {e}")


def _collect_slot(slot_name):
    out = []
    for item in _HOOKS.get(slot_name, []):
        if isinstance(item, dict):
            out.append(item)
    return out


# Допустимые группы для вкладки «Инструменты и данные»
_UI_GROUPS = ('tools', 'import', 'export')
_IMPORT_HINTS = ('import', 'импорт', 'upload', 'загруз')
_EXPORT_HINTS = ('export', 'экспорт', 'download', 'скач', 'выгруз')


def _guess_group(item, default='tools'):
    """Определяет группу для UI-слота.

    Приоритет:
      1) Явное поле `group` (если валидное) — используется как есть.
      2) Эвристика по action / label / url / modal_id.
      3) `default`.

    Это временная мера — пока плагины не проставляют `group` явно.
    """
    g = str(item.get('group', '') or '').strip().lower()
    if g in _UI_GROUPS:
        return g

    action = str(item.get('action', '') or '').lower()
    label = str(item.get('label', '') or '').lower()
    url = str(item.get('url', '') or '').lower()
    modal_id = str(item.get('modal_id', '') or '').lower()
    haystack = ' '.join((action, label, url, modal_id))

    for h in _IMPORT_HINTS:
        if h in haystack:
            return 'import'
    for h in _EXPORT_HINTS:
        if h in haystack:
            return 'export'
    return default


def _normalize_slot_item(item, default_group='tools'):
    """Приводит элемент слота к единому виду."""
    if not isinstance(item, dict):
        return None
    out = dict(item)
    out['group'] = _guess_group(out, default_group)
    try:
        out['order'] = int(out.get('order', 100))
    except (ValueError, TypeError):
        out['order'] = 100
    return out


def _collect_slot(slot_name, default_group='tools'):
    out = []
    for item in _HOOKS.get(slot_name, []):
        norm = _normalize_slot_item(item, default_group)
        if norm is not None:
            out.append(norm)
    # стабильная сортировка: сначала order, потом label
    out.sort(key=lambda x: (x.get('order', 100), str(x.get('label', ''))))
    return out


def collect_ui_slots():
    tools = _collect_slot('ui_tools_tab', 'tools')
    data = _collect_slot('ui_data_tab', 'tools')  # legacy-слот — по умолчанию tools
    # Объединяем оба legacy-слота в один пул и группируем
    merged = tools + data
    grouped = {'tools': [], 'import': [], 'export': []}
    for it in merged:
        g = it.get('group', 'tools')
        if g not in grouped:
            g = 'tools'
        grouped[g].append(it)
    for g in grouped:
        grouped[g].sort(key=lambda x: (x.get('order', 100), str(x.get('label', ''))))

    return {
        'data_tab': grouped['tools'] + grouped['import'] + grouped['export'],  # legacy-совместимость
        'tools_tab': grouped['tools'],
        'import_tab': grouped['import'],
        'export_tab': grouped['export'],
        'tools_grouped': grouped,
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
_FORBIDDEN_CSS_TOKENS = ('url(', 'expression(', '@import', '</style', 'javascript:')


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
    # dot тоже может содержать запрещённое
    if isinstance(dot, str):
        low = dot.lower()
        for bad in _FORBIDDEN_CSS_TOKENS:
            if bad in low:
                return f'Запрещённое содержимое в dot: {bad}'
    vars_ = theme.get('vars', {})
    if not isinstance(vars_, dict):
        return 'vars должен быть объектом'

    # Авто-разворачивание: если пользователь вставил {"gaming": { "--bg-start": ... }}
    # или {"name": "...", "vars": {...}}, пробуем распаковать.
    def _looks_like_var_block(d):
        if not isinstance(d, dict) or not d:
            return False
        for k in d.keys():
            if isinstance(k, str) and k.startswith('--'):
                return True
        return False

    if not _looks_like_var_block(vars_):
        # Верхний уровень — не переменные. Пробуем распаковать.
        for _v in vars_.values():
            if _looks_like_var_block(_v):
                vars_ = _v
                break
        else:
            # Возможно это структура вида {"name": ..., "dot": ..., "vars": {...}}
            inner = vars_.get('vars')
            if _looks_like_var_block(inner):
                vars_ = inner
    if not isinstance(vars_, dict) or not _looks_like_var_block(vars_):
        return ('Не найдено ни одной CSS-переменной. Вставь плоский объект вида '
                '{"--bg-start": "#151a2e", "--text-color": "#ffffff"}.')
    # пересохраняем развёрнутые vars обратно в тему
    theme['vars'] = vars_

    if len(vars_) > 200:
        return 'Слишком много переменных (макс. 200)'
    for k, v in vars_.items():
        if not isinstance(k, str):
            return f'Ключ переменной должен быть строкой, получено: {type(k).__name__}'
        if len(k) > 64:
            return f'Имя переменной слишком длинное (макс. 64): {k[:40]}…'
        if not k.startswith('--'):
            return (f'Ключ «{k}» должен начинаться с двух дефисов, например «--bg-start». '
                    f'Если ты вставил объект целиком — убери внешнюю обёртку и оставь '
                    f'только плоский список переменных.')
        if not isinstance(v, (str, int, float)):
            return f'Значение {k} должно быть строкой/числом'
        sv = str(v)
        if len(sv) > 500:
            return f'Значение {k} слишком длинное'
        low = sv.lower()
        for bad in _FORBIDDEN_CSS_TOKENS:
            if bad in low:
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

