import tempfile
from pathlib import Path

from testsweet import catch_exceptions, params, test

from hexxle.config import CONFIG_PATH, load_config
from hexxle.errors import HexxleError
from hexxle.repo import REPO


@test
def defaults_when_there_is_no_file():
    with tempfile.TemporaryDirectory() as tmp:
        config = load_config(Path(tmp) / 'none.toml')
    assert config == {'remote': None,
                      'dictionary': '/usr/share/dict/words'}


@test
def reads_settings():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'hexxle.toml'
        path.write_text('remote = "host:/srv/hexxle"\n'
                        'dictionary = "words"\n')
        config = load_config(path)
    assert config == {'remote': 'host:/srv/hexxle', 'dictionary': 'words'}


@test
def rejects_unknown_settings():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'hexxle.toml'
        path.write_text('remot = "x"\n')
        with catch_exceptions() as caught:
            load_config(path)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)
    message = str(caught[0])
    assert 'remot' in message


@test
@params([
    ('remote = 5\n', 'remote'),
    ('dictionary = ["words"]\n', 'dictionary'),
])
def rejects_settings_that_are_not_strings(text, setting):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'hexxle.toml'
        path.write_text(text)
        with catch_exceptions() as caught:
            load_config(path)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)
    message = str(caught[0])
    assert repr(setting) in message
    assert 'string' in message


@test
def rejects_a_file_that_is_not_toml():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'hexxle.toml'
        path.write_text('remote = \n')
        with catch_exceptions() as caught:
            load_config(path)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)
    message = str(caught[0])
    assert 'hexxle.toml' in message


@test
def the_settings_file_is_in_the_repository_root():
    # Only the path is compared: the real file is never read by a test.
    assert CONFIG_PATH == REPO / 'hexxle.toml'
