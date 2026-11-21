import tempfile
from pathlib import Path

from testsweet import catch_exceptions, params, test

from hexxle.config import load_config
from hexxle.errors import HexxleError


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
@params([
    ('remot = "x"\n', ['remot']),
    ('remote = 5\n', ["'remote'", 'string']),
    ('dictionary = ["words"]\n', ["'dictionary'", 'string']),
    ('remote = \n', ['hexxle.toml']),      # not TOML
])
def rejects_bad_settings(text, expected_fragments):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'hexxle.toml'
        path.write_text(text)
        with catch_exceptions() as caught:
            load_config(path)
    assert len(caught) == 1
    assert isinstance(caught[0], HexxleError)
    message = str(caught[0])
    for fragment in expected_fragments:
        assert fragment in message, fragment
