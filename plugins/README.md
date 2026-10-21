# Плагины реестра ссылок

Каждый плагин — отдельный `.py`-файл в этой папке.

## Контракт

```python
def register(hooks, app, config, core):
    ...

# Или без core:
def register(hooks, app, config):
    ...