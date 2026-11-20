"""The settings file, ``hexxle.toml`` in the repository root."""

import tomllib
from pathlib import Path

from hexxle.errors import HexxleError
from hexxle.repo import REPO

CONFIG_PATH = REPO / 'hexxle.toml'
DEFAULTS = {'remote': None, 'dictionary': '/usr/share/dict/words'}


def load_config(path: Path = CONFIG_PATH) -> dict:
    """The settings in ``path``, with defaults for any it leaves out.

    A missing file gives the defaults. Raises ``HexxleError`` for a file
    that is not TOML, an unknown setting or one that is not a string.
    """
    config = dict(DEFAULTS)
    if not path.exists():
        return config
    try:
        with open(path, 'rb') as handle:
            settings = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise HexxleError('%s: %s' % (path, error)) from None
    for key, value in settings.items():
        if key not in DEFAULTS:
            raise HexxleError('unknown setting %r in %s' % (key, path))
        if not isinstance(value, str):
            raise HexxleError(
                'setting %r in %s must be a string' % (key, path))
    config.update(settings)
    return config
