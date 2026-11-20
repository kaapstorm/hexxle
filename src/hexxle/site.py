"""Build the static site and serve it locally.

PyScript behaviour this module relies on, confirmed by experiment with
@pyscript/core 0.7.31 (PyScript 2026.7.3) and MicroPython 1.28.0-6:

- ``<script type="mpy" src="./main.py" config="./pyscript.json">``
  works: ``src`` is fetched relative to the page.
- A relative ``interpreter`` path works, and is resolved against the
  page, not the config file. Nothing is fetched from a CDN.
- ``files`` URLs are resolved against the config file. Their targets
  land relative to the interpreter's working directory, ``/``, and
  ``sys.path`` starts with ``''``, so ``./hexxle/...`` is importable.
  Without a mapping, ``import hexxle`` fails.
- Top-level ``await`` works in ``main.py`` without an ``async``
  attribute on the script tag.
"""

import functools
import json
import shutil
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

from hexxle.errors import HexxleError
from hexxle.repo import REPO

WEB = REPO / 'web'
WEB_TESTS = REPO / 'web_tests'
CORE_TESTS = REPO / 'tests' / 'core'
SRC = REPO / 'src'
NODE_MODULES = REPO / 'node_modules'
PYSCRIPT_DIST = NODE_MODULES / '@pyscript' / 'core' / 'dist'
MICROPYTHON = (
    NODE_MODULES / '@micropython' / 'micropython-webassembly-pyscript'
)
MICROPYTHON_FILES = ('micropython.mjs', 'micropython.wasm')


def build_site(dest: Path, with_tests: bool = False) -> None:
    """Assemble the static site in ``dest``.

    With ``with_tests``, also add ``tests.html``, which runs the core
    tests under MicroPython with a stand-in for Testsweet.
    """
    _require_npm_files()
    dest.mkdir(parents=True, exist_ok=True)
    page_files = _copy_files(sorted(WEB.iterdir()), WEB, dest)
    package_files = [SRC / 'hexxle' / '__init__.py']
    package_files += sorted((SRC / 'hexxle' / 'core').glob('*.py'))
    package_files = _copy_files(package_files, SRC, dest)

    shutil.copytree(PYSCRIPT_DIST, dest / 'pyscript', dirs_exist_ok=True)
    (dest / 'micropython').mkdir(exist_ok=True)
    for name in MICROPYTHON_FILES:
        shutil.copy2(MICROPYTHON / name, dest / 'micropython' / name)

    python_files = [name for name in page_files if name.endswith('.py')]
    _write_config(dest / 'pyscript.json', python_files + package_files)
    if with_tests:
        _add_tests(dest, package_files)


def _require_npm_files() -> None:
    """Raise ``HexxleError`` unless ``npm ci`` has installed PyScript."""
    needed = [PYSCRIPT_DIST] + [MICROPYTHON / name
                                for name in MICROPYTHON_FILES]
    for path in needed:
        if not path.exists():
            raise HexxleError(
                '%s is missing; run "npm ci" in %s first' % (path, REPO))


def _add_tests(dest: Path, package_files: list[str]) -> None:
    runner_files = _copy_files(sorted(WEB_TESTS.iterdir()), WEB_TESTS, dest)
    test_files = [REPO / 'tests' / '__init__.py']
    test_files += sorted(CORE_TESTS.glob('*.py'))
    test_files = _copy_files(test_files, REPO, dest)

    modules = [path.stem for path in sorted(CORE_TESTS.glob('test_*.py'))]
    manifest = 'tests/core/manifest.json'
    (dest / manifest).write_text(json.dumps(modules) + '\n')

    python_files = [name for name in runner_files if name.endswith('.py')]
    _write_config(
        dest / 'pyscript-tests.json',
        python_files + package_files + test_files + [manifest],
    )


def _copy_files(paths: list[Path], base: Path, dest: Path) -> list[str]:
    """Copy the files among ``paths`` to the same place under ``dest``.

    Returns their paths relative to ``base``.
    """
    copied = []
    for path in paths:
        if not path.is_file():
            continue
        relative = path.relative_to(base).as_posix()
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append(relative)
    return copied


def _write_config(path: Path, files: list[str]) -> None:
    config = {
        'interpreter': './micropython/micropython.mjs',
        'files': {'./' + name: './' + name for name in sorted(files)},
    }
    path.write_text(json.dumps(config, indent=2) + '\n')


@contextmanager
def site_server(
    puzzles_dir: Path | None = None,
    with_tests: bool = False,
    prefix: str = '',
) -> Iterator[str]:
    """Build the site into a temporary directory and serve it.

    Yields the base URL of the site, ending in ``/``. A non-empty
    ``prefix`` such as ``'sub/'`` serves the site under that path.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        site = root / prefix
        build_site(site, with_tests=with_tests)
        if puzzles_dir is not None:
            puzzles = site / 'puzzles'
            puzzles.mkdir()
            for path in sorted(puzzles_dir.glob('*.txt')):
                shutil.copy2(path, puzzles / path.name)

        handler = functools.partial(_QuietHandler, directory=str(root))
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address[:2]
            yield f'http://{host}:{port}/{prefix}'
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


class _QuietHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        '.mjs': 'text/javascript',
        '.wasm': 'application/wasm',
    }

    def log_message(self, format: str, *args) -> None:
        pass
