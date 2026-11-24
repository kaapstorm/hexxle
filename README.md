Hexxle
======

Similar to [Squaredle](https://squaredle.app/) but uses hexagonal tiles.
Implemented in Python using WebAssembly.

The game runs in the browser on [PyScript](https://pyscript.net/) with
MicroPython. The site is static files: a page, a stylesheet, the Python
sources, a copy of the PyScript runtime, and a `puzzles/` directory of
plain-text puzzle files. A command-line tool, `hexxle`, finds the words
on a board, checks a puzzle, and uploads puzzles and the game over sftp.


Setup
-----

You need [uv](https://docs.astral.sh/uv/) and npm.

```sh
uv sync                               # the tool and its test dependencies
npm ci                                # the pinned PyScript and MicroPython
uv run playwright install chromium    # the browser the tests drive
```

npm only fetches the PyScript runtime, which is copied into the site so
that nothing loads from a CDN.


Puzzle files
------------

A puzzle is one UTF-8 text file, named `YYYY-MM-DD.txt`, or
`YYYY-MM-DD_label.txt` when a date has more than one puzzle (the label is
lowercase letters, digits and underscores, for example
`2026-11-18_express.txt`). The name without `.txt` identifies the puzzle
everywhere.

```
 T A U
S C X L
 S E I
E D C N

---
EXACT
TAXI

--- bonus
LUXE
```

**The board** is everything before the first line that starts with `---`.
Each line is a row of tiles; each tile is an ASCII letter a–z, in either
case. The text is its own coordinate system, so the board looks on
screen as it does in the file:

- two tiles in the same row are neighbours when they are two columns
  apart (`S C` above);
- two tiles in adjacent rows are neighbours when they are one column
  apart (the `T` on the first line touches the `S` and the `C` below it).

So every tile in a row sits on columns of the same parity, and the next
row uses the other parity. Either parity may start the board. A space or
`_` is a gap, so ragged edges and holes need no special syntax. Blank
lines before and after the board are ignored; a blank line between rows
is an error, as is a tab.

**The words.** `---` alone starts the required words; `--- bonus` starts
the optional bonus words. `--- bonus` must come after `---`, each section
may appear only once, and any other line starting with `---` is an
error. One word per line, of ASCII letters a–z in either case; blank
lines are ignored, so you can group words by length. Words are at least
4 letters long, and a word may be in only one section. A word in neither
section does not count in the game, which is how you leave out a word
you would rather the player did not need.

A word may be followed by a space and an emoji, for example `RAIN 🌧️`,
to mark it as part of the puzzle's theme. The emoji is shown in the
message when the player finds the word. Only an emoji may follow a word:
ASCII characters are an error.

The player finishes the puzzle by finding every required word. Bonus
words are counted but never needed.


Authoring a puzzle
------------------

1. Write the board in a new file in a directory of your own, for example
   `puzzles/2026-11-20.txt`.
2. List every word on it:

   ```sh
   uv run hexxle solve puzzles/2026-11-20.txt
   ```

   This prints the board back in canonical form, then `---` and every
   dictionary word of 4 or more letters that can be traced on the board,
   grouped by length. Any word sections already in the file are ignored.
3. Paste the words under `---` in the file, then prune: delete words you
   do not want to count, and move the ones you want as extras under
   `--- bonus`. Rework the board and run `solve` again as often as you
   like.
4. Check the finished file:

   ```sh
   uv run hexxle check puzzles/2026-11-20.txt
   ```

   Errors (a malformed board or word section, a word that cannot be
   traced, a word that is too short, listed twice or in both sections, no
   required words, a bad file name) make it exit non-zero. Warnings list
   words that are not in the dictionary and dictionary words on the board
   that are in neither section, so you can see what you pruned.
5. Play it locally:

   ```sh
   uv run hexxle serve --puzzles puzzles
   ```

   and open <http://127.0.0.1:8000/>. `--host 0.0.0.0` makes it reachable
   from a phone on the same network; `--port` changes the port. It stops
   with an error if the puzzles directory does not exist, if the port
   cannot be used, or if `node_modules` is missing (run `npm ci`).
6. Publish it:

   ```sh
   uv run hexxle publish puzzles/2026-11-20.txt
   ```

   This runs the same checks and refuses on any error, uploads the file
   to the remote `puzzles/` directory, and uploads a new `index.json`
   built from that directory's listing. It will not replace a puzzle that
   is already published unless you add `--force`, for example to correct
   a mistake. Progress the player has saved survives a corrected puzzle:
   words no longer in it are dropped.

`solve`, `check` and `publish` take `-d DICT` to use a different word
list; `publish` and `deploy` take `--remote HOST:PATH`. A problem with
the input or the setup is reported as `error: …` with exit status 1.


Settings
--------

Copy `hexxle.example.toml` to `hexxle.toml` (git-ignored) in the
repository root and edit it. The tool always reads it from there,
whichever directory you run it in.

`remote` is where the site lives, as `host:directory`; the host can be
anything your SSH config understands. `dictionary` is the word list that
`solve`, `check` and `publish` use; it defaults to
`/usr/share/dict/words`, and a relative path is relative to the
repository root. Entries that start with a capital letter or contain
anything but the ASCII letters a–z are skipped. Both settings must be
strings. Command-line flags override both settings. Server addresses and
dictionary files are never committed.

Transfers run the system `sftp` command in batch mode, so your SSH keys
and configuration apply.


Deploying the game
------------------

The first time, and whenever the game itself changes, upload it:

```sh
uv run hexxle deploy
```

This builds the site (page, stylesheet, Python sources and the PyScript
runtime) and uploads it to `remote`. It never touches `puzzles/`, so
published puzzles stay where they are. Then publish at least one puzzle.
The Python sources are uploaded with `.txt` names (`main.txt`,
`hexxle/core/board.txt`), because some web servers try to run a `.py`
file instead of sending it; PyScript gives them their real names back in
the browser.
Every URL in the site is relative, so it can live in a subdirectory of a
website.


How it fits together
--------------------

- `src/hexxle/core/`: the rules, shared by the tool and the game: parsing
  puzzle files, the hex lattice, finding words on a board, and the game
  state. It is restricted to what MicroPython supports, and its tests run
  under both CPython and MicroPython.
- `web/`: the page, its stylesheet and the browser side of the game, in
  Python. `web/storage.js` is the one small JavaScript file: it wraps
  local storage, whose calls can throw (in a private window, say), because
  MicroPython cannot catch an exception thrown by a JavaScript function.
- `src/hexxle/`: the command-line tool (CPython, no third-party runtime
  dependencies).

Saved progress lives in the player's browser only.


Running the tests
-----------------

```sh
uv run testsweet      # everything, including the browser tests
uv run ruff check
```

Tests use [Testsweet](https://github.com/kaapstorm/testsweet). The
browser tests drive Chromium through Playwright, and one of them runs the
core tests under MicroPython in the browser:

```sh
uv run testsweet tests/browser/test_core_on_micropython.py
```
