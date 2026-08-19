"""Tests for controls/fitness/design_adherence.py (DEC-1).

Gate-enforced: this file runs under `uv run pytest` / `make test` / `make check`,
so a future round that reintroduces one of these defects fails the build, not just
a manual repro someone has to remember to run.

Each case is driven straight through `find_hex_violations_css`,
`find_font_violations_css`, and `find_hex_violations_ts` — the same functions
`scan_file` calls — rather than round-tripping through real files on disk, so a
case is one string literal, not a fixture file to keep track of.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from design_adherence import (
    find_font_violations_css,
    find_hex_violations_css,
    find_hex_violations_ts,
    find_parse_failure,
    scan_file,
)

CSS_PATH = Path('app/src/example.css')
TSX_PATH = Path('app/src/example.tsx')


def hex_css(text: str) -> list[str]:
    return [v.text for v in find_hex_violations_css(CSS_PATH, text)]


def font_css(text: str) -> list[str]:
    return [v.text for v in find_font_violations_css(CSS_PATH, text)]


def hex_ts(text: str) -> list[str]:
    return [v.text for v in find_hex_violations_ts(TSX_PATH, text)]


# --- must FAIL: hex colours in CSS -------------------------------------------


@pytest.mark.parametrize(
    ('css', 'expected'),
    [
        ('.x { color: #abcdef; }', ['#abcdef']),
        ('.x { border: 1px solid #ff0000; }', ['#ff0000']),  # round 1's gap
        ('.x { box-shadow: 0 1px 2px #00ff00; }', ['#00ff00']),
        ('.x { outline: 2px dashed #fedcba; }', ['#fedcba']),
        (
            '.x { background: linear-gradient(to right, #0000ff, #123456); }',
            ['#0000ff', '#123456'],
        ),
    ],
)
def test_hex_css_violations_caught(css: str, expected: list[str]) -> None:
    assert hex_css(css) == expected


def test_hex_css_survives_quoted_brace_before_it() -> None:
    """Defect 1: a `}` inside a string must not desync brace-depth tracking and
    hide a real violation that follows it."""
    css = """
    .icon::before {
      content: "}";
      color: #123abc;
    }
    """
    assert hex_css(css) == ['#123abc']


def test_hex_css_inside_media_block_declaration() -> None:
    css = """
    @media (max-width: 600px) {
      .x { color: #abc123; }
    }
    """
    assert hex_css(css) == ['#abc123']


# --- must FAIL: font-family / font shorthand ---------------------------------


def test_font_shorthand_family_caught() -> None:
    """Defect 3: the `font` shorthand's trailing family component is not
    exempt just because the property isn't spelled `font-family`."""
    css = ".fancy { font: italic bold 12px/1.5 'Comic Sans MS', fantasy; }"
    assert font_css(css) == ['Comic Sans MS']


def test_font_family_disallowed_caught() -> None:
    css = ".fancy { font-family: 'Comic Sans MS'; }"
    assert font_css(css) == ['Comic Sans MS']


# --- must FAIL: TS/TSX hex colours --------------------------------------------


@pytest.mark.parametrize(
    ('src', 'expected'),
    [
        ("const c = ['#ff0000', '#00ff00'];", ['#ff0000', '#00ff00']),
        ("function f() { return '#123abc'; }", ['#123abc']),
        ('const c = `#dddddd`;', ['#dddddd']),
        ('const c = "#eeeeee";', ['#eeeeee']),
    ],
)
def test_hex_ts_violations_caught(src: str, expected: list[str]) -> None:
    assert hex_ts(src) == expected


# --- must PASS: correct code, never flagged -----------------------------------


@pytest.mark.parametrize(
    'css',
    [
        '#decisions { max-width: 720px; }',
        '#decisions th,\n#decisions td { text-align: left; }',
        'a:hover, #root { color: red; }',
        '@media (max-width: 600px) {\n  #fff123 {\n    padding: 4px;\n  }\n}',  # defect 2
        '/* a hex value like #dead00 belongs in a comment sometimes */\n.x { color: red; }',
        ':root {\n  @media (max-width: 600px) {\n    font-size: 15px;\n  }\n}',
        '.x { color: var(--color-danger); }',
    ],
)
def test_hex_css_survives_correct_code(css: str) -> None:
    assert hex_css(css) == []


def test_font_family_allowed_values_pass() -> None:
    css = (
        ".a { font-family: 'Cormorant Garamond'; }\n"
        ".b { font-family: 'Lora'; }\n"
        '.c { font-family: var(--font-heading); }\n'
        '.d { font: 16px/145% var(--font-body); }\n'
        '.e { font: inherit; }\n'
    )
    assert font_css(css) == []


def test_media_selector_not_treated_as_declaration() -> None:
    """Defect 2, isolated: a hex-shaped selector nested inside an at-rule must
    never be scanned — its prelude is never declaration territory, at any
    nesting depth."""
    css = '@media (max-width: 600px) {\n  #fff123 {\n    padding: 4px;\n  }\n}'
    assert hex_css(css) == []


@pytest.mark.parametrize(
    'relative_path',
    [
        'app/src/App.css',
        'app/src/App.tsx',
        'app/src/App.test.tsx',
        'app/src/index.css',
        'app/src/main.tsx',
        'app/src/lib/decisions.ts',
    ],
)
def test_real_files_are_clean(relative_path: str) -> None:
    """Every real (non-exempt) file currently under app/src/ must pass both
    checks — the control proving itself against the actual tree, not just
    against hand-picked snippets."""
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    text = path.read_text(encoding='utf-8')
    if path.suffix == '.css':
        assert find_hex_violations_css(path, text) == []
        assert find_font_violations_css(path, text) == []
    else:
        assert find_hex_violations_ts(path, text) == []


# --- must FAIL: unparseable CSS is a failure, never a silent pass ------------
#
# tinycss2 does not surface "a block was never closed before EOF" as an error —
# the CSS Syntax spec calls that a parse error but doesn't require reporting one,
# and tinycss2 follows the spec's silent recovery. A governance control cannot
# accept that: ambiguity must fail closed, not report a partial scan as if it
# were a complete one.


def test_unclosed_block_with_a_real_violation_inside_still_fails() -> None:
    """A hex colour sitting inside the malformed region must not be silently
    dropped just because the file around it doesn't parse — the file fails as
    a whole, distinctly from an adherence violation."""
    css = '.broken { color: #ff0000\n@@@ unparseable {{{\n'
    failure = find_parse_failure(CSS_PATH, css)
    assert failure is not None
    assert failure.kind == 'parse-error'
    assert hex_css(css) == []  # the raw scanner alone would miss it — this is why
    # scan_file must check find_parse_failure first, not rely on the scanner to
    # notice its own confusion.
    assert scan_file_violations(css, suffix='.css') == ['cannot parse CSS — refusing to report clean']


def test_unclosed_block_with_no_violations_still_fails() -> None:
    """Unparseable is unparseable regardless of whether the visible part of the
    file happens to contain a design-value violation — the file is refused
    either way, because the control cannot tell what it isn't seeing."""
    css = '.broken { color: red\n@@@ unparseable {{{\n'
    failure = find_parse_failure(CSS_PATH, css)
    assert failure is not None
    assert failure.kind == 'parse-error'


def test_violation_before_the_broken_region_is_not_silently_dropped() -> None:
    """A real violation earlier in the same file, followed by a malformed
    region, must not produce a clean scan that quietly omits it — the whole
    file fails instead of returning a partial, misleadingly-complete answer."""
    css = '.a { color: #ff0000; }\n.broken { color: red\n@@@ unparseable {{{\n'
    assert find_parse_failure(CSS_PATH, css) is not None
    assert scan_file_violations(css, suffix='.css') == ['cannot parse CSS — refusing to report clean']


@pytest.mark.parametrize(
    'relative_path',
    [
        'app/src/App.css',
        'app/src/index.css',
        'app/src/tokens-local.css',
        'app/src/classical.css',
    ],
)
def test_real_css_files_parse_cleanly(relative_path: str) -> None:
    """The fail-closed check must never fire on the current tree — every real
    `.css` file, including the exempt token files, is well-formed CSS."""
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    text = path.read_text(encoding='utf-8')
    assert find_parse_failure(path, text) is None


def scan_file_violations(text: str, *, suffix: str) -> list[str]:
    """Round-trip a snippet through `scan_file` itself (not the lower-level
    finders) via a real temp file, so the parse-failure short-circuit in
    `scan_file` is exercised the same way the control's own `main()` uses it.
    """
    with tempfile.NamedTemporaryFile('w', suffix=suffix, delete=False) as handle:
        handle.write(text)
        path = Path(handle.name)
    try:
        return [v.text for v in scan_file(path)]
    finally:
        path.unlink()
