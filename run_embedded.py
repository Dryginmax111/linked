"""
Автозапуск реестра на embedded Python (runtime\\embedded\\python313).

Скрипт кладёт в sys.path:
  1. runtime\\embedded\\python313\\Lib\\site-packages — зависимости проекта;
  2. корень проекта — чтобы import app / import plugins_loader работали.

Затем запускает app.py так, как если бы он был запущен напрямую.
Venv не требуется.
"""
import os
import sys
import runpy

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(ROOT, "runtime", "embedded", "python313", "Lib", "site-packages")

for p in (SITE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

if __name__ == "__main__":
    sys.argv[0] = os.path.join(ROOT, "app.py")
    runpy.run_path(sys.argv[0], run_name="__main__")
