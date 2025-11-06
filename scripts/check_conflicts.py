#!/usr/bin/env python3
import os
import sys
from pathlib import Path

EXCLUDED_DIRS = {'.git', 'venv', '__pycache__', 'node_modules'}
MARKERS = (
    ''.join('<' for _ in range(7)),
    ''.join('=' for _ in range(7)),
    ''.join('>' for _ in range(7)),
)


def has_marker(path: Path) -> bool:
    try:
        with path.open('r', encoding='utf-8', errors='ignore') as handle:
            for line in handle:
                if any(marker in line for marker in MARKERS):
                    return True
    except (OSError, UnicodeError):
        return False
    return False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    found = []
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for filename in files:
            if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2')):
                continue
            file_path = Path(root) / filename
            if has_marker(file_path):
                found.append(str(file_path.relative_to(repo_root)))
    if found:
        print('Обнаружены маркеры конфликтов в файлах:')
        for entry in found:
            print(f' - {entry}')
        return 1
    print('Конфликтных маркеров не найдено.')
    return 0


if __name__ == '__main__':
    sys.exit(main())