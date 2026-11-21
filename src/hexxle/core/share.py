"""The text a player shares about a puzzle: no words, so no spoilers."""

from hexxle.core.puzzle import describe_identifier

NAME = 'Hexxle'
SEPARATOR = ' · '


def _count(number, noun):
    if number == 1:
        return '1 %s' % noun
    return '%d %ss' % (number, noun)


def progress_line(game):
    found, total, bonus = game.progress()
    if game.is_complete():
        line = 'Puzzle completed! Found %s' % _count(total, 'word')
    else:
        line = 'Found %d of %s' % (found, _count(total, 'word'))
    if bonus:
        line += ' and %s' % _count(bonus, 'bonus word')
    return line + '.'


def share_text(ident, game, url):
    """What to copy for the puzzle ``ident``, played as far as ``game``.

    ``url`` is the address of that puzzle.
    """
    date, label = describe_identifier(ident)
    heading = [NAME, date]
    if label:
        heading.append(label)
    return '\n'.join([SEPARATOR.join(heading), progress_line(game), url])
