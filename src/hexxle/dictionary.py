from pathlib import Path

from hexxle.core.board import is_letter
from hexxle.core.paths import MIN_WORD_LENGTH


def load_dictionary(path: Path) -> set[str]:
    """Uppercase plain words from a one-word-per-line file."""
    words = set()
    with open(path, encoding='utf-8') as handle:
        for line in handle:
            word = line.strip()
            if len(word) < MIN_WORD_LENGTH or word[0].isupper():
                continue
            if all(is_letter(char) for char in word):
                words.add(word.upper())
    return words
