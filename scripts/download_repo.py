#!/usr/bin/env python3
"""Download and unpack a GitHub repository archive using Python 3.6.

Usage:
    python scripts/download_repo.py --repo https://github.com/user/project.git \
        [--branch main] [--dest /path/to/dir]

If Git is not installed on the hosting environment, this script lets you
bootstrap the project by downloading the ZIP archive for a given branch and
extracting it to the destination directory.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from typing import Optional

try:
    from urllib.request import urlopen
except ImportError:  # pragma: no cover - Python <3 fallback (not expected)
    from urllib2 import urlopen  # type: ignore

try:
    import zipfile
except ImportError as exc:  # pragma: no cover
    raise SystemExit("zipfile module is required") from exc


def build_archive_url(repo_url: str, branch: str) -> str:
    """Convert a Git repository URL to a downloadable ZIP archive URL."""
    cleaned = repo_url.rstrip('/')
    if cleaned.endswith('.git'):
        cleaned = cleaned[:-4]
    return "{}/archive/refs/heads/{}.zip".format(cleaned, branch)


def ensure_empty_dir(path: str) -> None:
    if os.path.isdir(path):
        if os.listdir(path):
            raise SystemExit(
                "Каталог '{}' не пуст. Укажите пустую директорию или новую "
                "папку через --dest.".format(path)
            )
    else:
        os.makedirs(path)


def download_archive(url: str, target_path: str) -> None:
    with urlopen(url) as response, open(target_path, 'wb') as archive:
        shutil.copyfileobj(response, archive)


def extract_archive(archive_path: str, dest_dir: str) -> str:
    with zipfile.ZipFile(archive_path) as zf:
        top_level: Optional[str] = None
        for member in zf.namelist():
            if member.endswith('/') and '/' not in member.rstrip('/'):
                top_level = member.rstrip('/')
                break
        zf.extractall(dest_dir)
    if top_level:
        return os.path.join(dest_dir, top_level)
    return dest_dir


def move_contents(extracted_root: str, dest_dir: str) -> None:
    for entry in os.listdir(extracted_root):
        src_path = os.path.join(extracted_root, entry)
        dest_path = os.path.join(dest_dir, entry)
        if os.path.exists(dest_path):
            raise SystemExit(
                "Файл '{}' уже существует в директории назначения.".format(dest_path)
            )
        shutil.move(src_path, dest_path)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Download Git repo via Python")
    parser.add_argument(
        "--repo", required=True, help="HTTPS-ссылка на репозиторий (GitHub)"
    )
    parser.add_argument(
        "--branch", default="main", help="Имя ветки (по умолчанию main)"
    )
    parser.add_argument(
        "--dest",
        default="./repo_download",
        help="Путь, куда распаковать проект (создаётся автоматически)",
    )
    args = parser.parse_args(argv)

    ensure_empty_dir(args.dest)
    archive_url = build_archive_url(args.repo, args.branch)

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = os.path.join(tmp_dir, "repo.zip")
        print("Скачивание архива: {}".format(archive_url))
        download_archive(archive_url, archive_path)
        print("Распаковка архива...")
        extracted_root = extract_archive(archive_path, tmp_dir)
        print("Перемещение файлов в {}".format(os.path.abspath(args.dest)))
        move_contents(extracted_root, args.dest)

    print("Готово. Проект расположен в {}".format(os.path.abspath(args.dest)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
